#!/usr/bin/env python3
"""
Migrate Local Images to R2 CDN

This script migrates product images stored as local file paths to Cloudflare R2 CDN.
It reads local files, uploads them to R2, and updates the database URLs.

Usage:
    cd backend
    source venv/bin/activate
    python scripts/migrate_local_images_to_r2.py --user-id 1 --dry-run
    python scripts/migrate_local_images_to_r2.py --user-id 1
    python scripts/migrate_local_images_to_r2.py --user-id 1 --workers 20

Options:
    --user-id       User ID to migrate (required)
    --dry-run       Show what would be done without making changes
    --workers       Number of parallel workers (default: 20)
    --batch-size    Number of products per batch (default: 100)
    --product-id    Migrate only a specific product (for testing)
    --limit         Limit total number of products to process
"""

import argparse
import asyncio
import json
import os
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import ThreadedConnectionPool

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.r2_service import r2_service
from shared.config import settings
from shared.logging_setup import get_logger

logger = get_logger(__name__)

# Database configuration (from environment or defaults for dev)
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5433)),
    "dbname": os.getenv("DB_NAME", "stoflow_db"),
    "user": os.getenv("DB_USER", "stoflow_user"),
    "password": os.getenv("DB_PASSWORD", "stoflow_dev_password_2024"),
}


class MigrationStats:
    """Track migration statistics (thread-safe)."""

    def __init__(self):
        self._lock = threading.Lock()
        self.products_processed = 0
        self.products_updated = 0
        self.products_skipped = 0
        self.products_failed = 0
        self.images_migrated = 0
        self.images_skipped_cdn = 0
        self.images_failed: List[Tuple[str, str]] = []  # (path, error)
        self.start_time = time.time()

    def increment(self, field: str, value: int = 1):
        """Thread-safe increment."""
        with self._lock:
            setattr(self, field, getattr(self, field) + value)

    def add_failed_image(self, path: str, error: str):
        """Thread-safe add failed image."""
        with self._lock:
            self.images_failed.append((path, error))

    def report(self) -> str:
        """Generate final report."""
        duration = time.time() - self.start_time
        minutes = int(duration // 60)
        seconds = int(duration % 60)

        report = f"""
╔══════════════════════════════════════════════════════════════╗
║                    MIGRATION REPORT                          ║
╠══════════════════════════════════════════════════════════════╣
║  Products processed  : {self.products_processed:>6}                              ║
║  Products updated    : {self.products_updated:>6}                              ║
║  Products skipped    : {self.products_skipped:>6}                              ║
║  Products failed     : {self.products_failed:>6}                              ║
╠══════════════════════════════════════════════════════════════╣
║  Images migrated     : {self.images_migrated:>6}                              ║
║  Images skipped (CDN): {self.images_skipped_cdn:>6}                              ║
║  Images failed       : {len(self.images_failed):>6}                              ║
╠══════════════════════════════════════════════════════════════╣
║  Duration            : {minutes:>3}m {seconds:02d}s                              ║
╚══════════════════════════════════════════════════════════════╝
"""
        if self.images_failed:
            report += "\nFailed images:\n"
            for path, error in self.images_failed[:20]:  # Show first 20
                report += f"  - {path[:60]}... ({error})\n"
            if len(self.images_failed) > 20:
                report += f"  ... and {len(self.images_failed) - 20} more\n"

        return report


def is_local_path(url: str) -> bool:
    """Check if URL is a local file path (not a CDN URL)."""
    if not url:
        return False
    # Local paths start with / or contain /home/
    return url.startswith("/") and not url.startswith("http")


def is_cdn_url(url: str) -> bool:
    """Check if URL is already a CDN URL."""
    if not url:
        return False
    return url.startswith("https://") or url.startswith("http://")


def get_products_with_local_images(
    conn, user_id: int, product_id: Optional[int] = None, limit: Optional[int] = None
) -> List[Dict]:
    """
    Get products that have local file paths in their images.

    Args:
        conn: Database connection
        user_id: User ID (schema)
        product_id: Optional specific product ID
        limit: Optional limit on number of products

    Returns:
        List of products with their images
    """
    schema = f"user_{user_id}"

    query = f"""
        SELECT id, title, images
        FROM {schema}.products
        WHERE deleted_at IS NULL
          AND images IS NOT NULL
          AND jsonb_array_length(images) > 0
          AND images::text LIKE '%/home/%'
    """

    if product_id:
        query += f" AND id = {product_id}"

    query += " ORDER BY id"

    if limit:
        query += f" LIMIT {limit}"

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query)
        return cur.fetchall()


async def upload_local_image(
    local_path: str, user_id: int, product_id: int, dry_run: bool = False
) -> Optional[str]:
    """
    Upload a local image to R2 CDN.

    Args:
        local_path: Path to local image file
        user_id: User ID for R2 path
        product_id: Product ID for R2 path
        dry_run: If True, don't actually upload

    Returns:
        CDN URL of uploaded image, or None if failed
    """
    if not os.path.exists(local_path):
        raise FileNotFoundError(f"File not found: {local_path}")

    # Determine extension and content type
    ext = Path(local_path).suffix.lower().lstrip(".")
    if ext == "jpg":
        ext = "jpeg"

    content_type = f"image/{ext}"

    if dry_run:
        fake_url = f"https://cdn.stoflow.io/{user_id}/products/{product_id}/dry_run_{Path(local_path).name}"
        return fake_url

    # Read and upload file
    with open(local_path, "rb") as f:
        content = f.read()

    url = await r2_service.upload_image(
        user_id=user_id,
        product_id=product_id,
        content=content,
        extension=ext,
        content_type=content_type,
    )

    return url


def update_product_images(
    conn, user_id: int, product_id: int, images_json: List[Dict], dry_run: bool = False
) -> None:
    """
    Update product images in database.

    Args:
        conn: Database connection
        user_id: User ID (schema)
        product_id: Product ID
        images_json: New images list
        dry_run: If True, don't update
    """
    if dry_run:
        return

    schema = f"user_{user_id}"

    query = f"""
        UPDATE {schema}.products
        SET images = %s::jsonb,
            updated_at = NOW()
        WHERE id = %s
    """

    with conn.cursor() as cur:
        cur.execute(query, (json.dumps(images_json), product_id))

    conn.commit()


async def migrate_product(
    pool: ThreadedConnectionPool,
    user_id: int,
    product: Dict,
    stats: MigrationStats,
    semaphore: asyncio.Semaphore,
    dry_run: bool = False,
) -> bool:
    """
    Migrate a single product's images.

    Args:
        pool: Database connection pool
        user_id: User ID
        product: Product dict with id, title, images
        stats: Migration statistics tracker
        semaphore: Semaphore for limiting concurrency
        dry_run: If True, don't make changes

    Returns:
        True if any images were migrated
    """
    async with semaphore:
        product_id = product["id"]
        title = product["title"]
        images = product["images"]

        if isinstance(images, str):
            images = json.loads(images)

        if not images:
            stats.increment("products_skipped")
            return False

        logger.info(f"Processing product {product_id}: {title[:50]}...")

        new_images = []
        images_changed = False

        for img in images:
            url = img.get("url", "")

            # Already a CDN URL - keep as is
            if is_cdn_url(url):
                new_images.append(img)
                stats.increment("images_skipped_cdn")
                continue

            # Local path - needs migration
            if is_local_path(url):
                try:
                    cdn_url = await upload_local_image(url, user_id, product_id, dry_run)

                    if cdn_url:
                        new_images.append({
                            "url": cdn_url,
                            "order": img.get("order", 0),
                            "created_at": img.get(
                                "created_at",
                                datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                            ),
                        })
                        stats.increment("images_migrated")
                        images_changed = True
                        logger.debug(f"  Migrated: {url[:50]}... -> {cdn_url}")
                    else:
                        # Upload returned None - keep original
                        new_images.append(img)
                        stats.add_failed_image(url, "Upload returned None")

                except FileNotFoundError:
                    stats.add_failed_image(url, "FileNotFoundError")
                    logger.warning(f"  File not found: {url}")
                    # Keep original URL for manual fix later
                    new_images.append(img)

                except Exception as e:
                    stats.add_failed_image(url, str(e)[:50])
                    logger.error(f"  Error uploading {url}: {e}")
                    new_images.append(img)

            else:
                # Unknown format - keep as is
                new_images.append(img)
                logger.warning(f"  Unknown URL format: {url[:50]}")

        # Update database if images changed
        if images_changed:
            conn = pool.getconn()
            try:
                update_product_images(conn, user_id, product_id, new_images, dry_run)
            finally:
                pool.putconn(conn)
            stats.increment("products_updated")
            logger.info(f"  Updated product {product_id} with {len(new_images)} images")
            return True
        else:
            stats.increment("products_skipped")
            return False


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Migrate local images to R2 CDN",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Dry run for user 1
    python scripts/migrate_local_images_to_r2.py --user-id 1 --dry-run

    # Migrate single product (test)
    python scripts/migrate_local_images_to_r2.py --user-id 1 --product-id 409 --dry-run

    # Full migration with 20 parallel workers
    python scripts/migrate_local_images_to_r2.py --user-id 1 --workers 20
        """,
    )
    parser.add_argument("--user-id", type=int, required=True, help="User ID to migrate")
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be done"
    )
    parser.add_argument(
        "--workers", type=int, default=20, help="Number of parallel workers (default: 20)"
    )
    parser.add_argument(
        "--batch-size", type=int, default=100, help="Products per progress update (default: 100)"
    )
    parser.add_argument(
        "--product-id", type=int, help="Migrate only specific product ID"
    )
    parser.add_argument(
        "--limit", type=int, help="Limit total products to process"
    )

    args = parser.parse_args()

    print(f"""
╔══════════════════════════════════════════════════════════════╗
║          LOCAL IMAGES TO R2 CDN MIGRATION                    ║
╠══════════════════════════════════════════════════════════════╣
║  User ID    : {args.user_id:<10}                                    ║
║  Workers    : {args.workers:<10}                                    ║
║  Batch size : {args.batch_size:<10}                                    ║
║  Dry run    : {str(args.dry_run):<10}                                    ║
╚══════════════════════════════════════════════════════════════╝
""")

    if args.dry_run:
        logger.info("=== DRY RUN MODE - No changes will be made ===")

    # Check R2 availability
    if not args.dry_run and not r2_service.is_available:
        logger.error("R2 service not available. Check configuration.")
        logger.error("Required env vars: R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_ENDPOINT")
        sys.exit(1)

    # Create connection pool for parallel access
    try:
        pool = ThreadedConnectionPool(
            minconn=5,
            maxconn=args.workers + 5,
            **DB_CONFIG
        )
        # Get one connection for reading products
        conn = pool.getconn()
        logger.info(f"Connected to database: {DB_CONFIG['dbname']} (pool: {args.workers + 5} connections)")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        sys.exit(1)

    stats = MigrationStats()
    semaphore = asyncio.Semaphore(args.workers)

    try:
        # Get products to migrate
        products = get_products_with_local_images(
            conn, args.user_id, args.product_id, args.limit
        )
        pool.putconn(conn)

        if not products:
            logger.info("No products with local images found")
            return

        logger.info(f"Found {len(products)} products with local images")
        logger.info(f"Starting migration with {args.workers} parallel workers...")

        # Process all products in parallel with semaphore limiting concurrency
        async def process_with_progress(product, idx, total):
            stats.increment("products_processed")
            try:
                await migrate_product(pool, args.user_id, product, stats, semaphore, args.dry_run)
            except Exception as e:
                logger.error(f"Error processing product {product['id']}: {e}")
                stats.increment("products_failed")

            # Progress update every batch_size products
            if stats.products_processed % args.batch_size == 0 or stats.products_processed == total:
                pct = (stats.products_processed / total) * 100
                elapsed = time.time() - stats.start_time
                rate = stats.images_migrated / elapsed if elapsed > 0 else 0
                logger.info(
                    f"Progress: {stats.products_processed}/{total} ({pct:.1f}%) - "
                    f"Images: {stats.images_migrated} migrated, {len(stats.images_failed)} failed - "
                    f"Rate: {rate:.1f} img/s"
                )

        # Create all tasks and run them concurrently
        tasks = [
            process_with_progress(product, i, len(products))
            for i, product in enumerate(products)
        ]

        await asyncio.gather(*tasks)

    finally:
        pool.closeall()

    # Final report
    print(stats.report())


if __name__ == "__main__":
    asyncio.run(main())
