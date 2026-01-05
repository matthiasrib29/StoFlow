#!/usr/bin/env python3
"""
Fix Corrupted Images Script

This script fixes products that have corrupted image data (all images with order=0).
It reads the correct image order from python-api-woo database, uploads images to CDN,
and updates the StoFlow database with correct order.

Affected products: IDs 3236-3286 (50 products with all images at order=0)

Usage:
    python scripts/fix_corrupted_images.py [--dry-run] [--product-id ID]

Options:
    --dry-run       Show what would be done without making changes
    --product-id    Fix only a specific product (for testing)
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.r2_service import r2_service
from shared.config import settings
from shared.logging_setup import get_logger

logger = get_logger(__name__)

# Database configurations
STOFLOW_DB = {
    "host": "localhost",
    "port": 5433,
    "dbname": "stoflow_db",
    "user": "stoflow_user",
    "password": "stoflow_dev_password_2024",
}

WOO_DB = {
    "host": "localhost",
    "port": 5432,
    "dbname": "appdb",
    "user": "appuser",
    "password": "apppass",
}

# Local images base path
LOCAL_IMAGES_PATH = "/home/maribeiro/Bureau/STO/SITE/PRISE DE PHOTO/product_images"

# User ID for StoFlow (user_1 schema)
USER_ID = 1


def get_corrupted_products(stoflow_conn, product_id=None):
    """
    Get products with corrupted images (all images have order=0).

    Args:
        stoflow_conn: StoFlow database connection
        product_id: Optional specific product ID to fix

    Returns:
        list: List of product IDs with corrupted images
    """
    query = """
        SELECT p.id, p.title,
               jsonb_array_length(p.images) as nb_images,
               p.images
        FROM user_1.products p,
             jsonb_array_elements(COALESCE(p.images, '[]'::jsonb)) as img
        WHERE p.deleted_at IS NULL
          AND jsonb_array_length(COALESCE(p.images, '[]'::jsonb)) > 1
    """

    if product_id:
        query += f" AND p.id = {product_id}"

    query += """
        GROUP BY p.id, p.title, p.images
        HAVING COUNT(*) FILTER (WHERE (img->>'order')::int = 0) = jsonb_array_length(p.images)
        ORDER BY p.id
    """

    with stoflow_conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query)
        return cur.fetchall()


def get_woo_images(woo_conn, sku):
    """
    Get images from Woo database with correct order.

    Args:
        woo_conn: Woo database connection
        sku: Product SKU (same as StoFlow product ID)

    Returns:
        list: List of dicts with image_path and display_order
    """
    query = """
        SELECT image_path, display_order
        FROM product.product_images
        WHERE sku = %s
        ORDER BY display_order
    """

    with woo_conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, (sku,))
        return cur.fetchall()


def get_current_cdn_images(stoflow_conn, product_id):
    """
    Get current CDN image URLs for a product.

    Args:
        stoflow_conn: StoFlow database connection
        product_id: Product ID

    Returns:
        list: List of CDN URLs to delete
    """
    query = """
        SELECT images
        FROM user_1.products
        WHERE id = %s
    """

    with stoflow_conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, (product_id,))
        result = cur.fetchone()

        if not result or not result["images"]:
            return []

        images = result["images"]
        if isinstance(images, str):
            images = json.loads(images)

        # Only return CDN URLs (not local paths)
        return [
            img["url"] for img in images
            if img.get("url", "").startswith("https://cdn.stoflow.io")
        ]


async def delete_cdn_images(cdn_urls, dry_run=False):
    """
    Delete images from CDN.

    Args:
        cdn_urls: List of CDN URLs to delete
        dry_run: If True, don't actually delete

    Returns:
        int: Number of images deleted
    """
    deleted = 0

    for url in cdn_urls:
        if dry_run:
            logger.info(f"[DRY-RUN] Would delete: {url}")
            deleted += 1
        else:
            try:
                success = await r2_service.delete_image(url)
                if success:
                    deleted += 1
                    logger.debug(f"Deleted: {url}")
            except Exception as e:
                logger.warning(f"Failed to delete {url}: {e}")

    return deleted


async def upload_image_to_cdn(local_path, product_id, dry_run=False):
    """
    Upload a local image to CDN.

    Args:
        local_path: Path to local image file
        product_id: Product ID
        dry_run: If True, don't actually upload

    Returns:
        str: CDN URL of uploaded image, or None if failed
    """
    if not os.path.exists(local_path):
        logger.error(f"Local image not found: {local_path}")
        return None

    # Determine extension and content type
    ext = Path(local_path).suffix.lower().lstrip(".")
    if ext == "jpg":
        ext = "jpeg"
    content_type = f"image/{ext}"

    if dry_run:
        fake_url = f"https://cdn.stoflow.io/{USER_ID}/products/{product_id}/fake_{Path(local_path).name}"
        logger.info(f"[DRY-RUN] Would upload: {local_path} -> {fake_url}")
        return fake_url

    try:
        with open(local_path, "rb") as f:
            content = f.read()

        url = await r2_service.upload_image(
            user_id=USER_ID,
            product_id=product_id,
            content=content,
            extension=ext,
            content_type=content_type,
        )

        logger.debug(f"Uploaded: {local_path} -> {url}")
        return url

    except Exception as e:
        logger.error(f"Failed to upload {local_path}: {e}")
        return None


def update_product_images(stoflow_conn, product_id, images_json, dry_run=False):
    """
    Update product images in StoFlow database.

    Args:
        stoflow_conn: StoFlow database connection
        product_id: Product ID
        images_json: List of image dicts with url, order, created_at
        dry_run: If True, don't actually update
    """
    if dry_run:
        logger.info(f"[DRY-RUN] Would update product {product_id} with {len(images_json)} images")
        return

    query = """
        UPDATE user_1.products
        SET images = %s::jsonb,
            updated_at = NOW()
        WHERE id = %s
    """

    with stoflow_conn.cursor() as cur:
        cur.execute(query, (json.dumps(images_json), product_id))

    stoflow_conn.commit()
    logger.info(f"Updated product {product_id} with {len(images_json)} images")


async def fix_product(stoflow_conn, woo_conn, product_id, title, dry_run=False):
    """
    Fix a single product's images.

    Args:
        stoflow_conn: StoFlow database connection
        woo_conn: Woo database connection
        product_id: Product ID to fix
        title: Product title (for logging)
        dry_run: If True, don't make changes

    Returns:
        bool: True if successful
    """
    logger.info(f"Processing product {product_id}: {title}")

    # 1. Get correct images from Woo
    woo_images = get_woo_images(woo_conn, product_id)

    if not woo_images:
        logger.warning(f"No images found in Woo for product {product_id}")
        return False

    logger.info(f"  Found {len(woo_images)} images in Woo")

    # 2. Get current CDN images to delete
    cdn_urls = get_current_cdn_images(stoflow_conn, product_id)

    if cdn_urls:
        logger.info(f"  Deleting {len(cdn_urls)} existing CDN images")
        await delete_cdn_images(cdn_urls, dry_run)

    # 3. Upload new images with correct order
    new_images = []
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    for woo_img in woo_images:
        local_path = woo_img["image_path"]
        display_order = woo_img["display_order"]

        # Upload to CDN
        cdn_url = await upload_image_to_cdn(local_path, product_id, dry_run)

        if cdn_url:
            new_images.append({
                "url": cdn_url,
                "order": display_order - 1,  # Convert from 1-based to 0-based
                "created_at": now,
            })
        else:
            logger.error(f"  Failed to upload image: {local_path}")

    if not new_images:
        logger.error(f"  No images uploaded for product {product_id}")
        return False

    # Sort by order
    new_images.sort(key=lambda x: x["order"])

    # 4. Update database
    update_product_images(stoflow_conn, product_id, new_images, dry_run)

    logger.info(f"  Successfully fixed product {product_id} with {len(new_images)} images")
    return True


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Fix corrupted product images")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    parser.add_argument("--product-id", type=int, help="Fix only specific product ID")
    args = parser.parse_args()

    if args.dry_run:
        logger.info("=== DRY RUN MODE - No changes will be made ===")

    # Check R2 availability
    if not args.dry_run and not r2_service.is_available:
        logger.error("R2 service not available. Check configuration.")
        sys.exit(1)

    # Connect to databases
    try:
        stoflow_conn = psycopg2.connect(**STOFLOW_DB)
        woo_conn = psycopg2.connect(**WOO_DB)
        logger.info("Connected to both databases")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        sys.exit(1)

    try:
        # Get corrupted products
        corrupted = get_corrupted_products(stoflow_conn, args.product_id)

        if not corrupted:
            logger.info("No corrupted products found")
            return

        logger.info(f"Found {len(corrupted)} corrupted products")

        # Process each product
        success = 0
        failed = 0

        for product in corrupted:
            try:
                result = await fix_product(
                    stoflow_conn,
                    woo_conn,
                    product["id"],
                    product["title"],
                    args.dry_run,
                )
                if result:
                    success += 1
                else:
                    failed += 1
            except Exception as e:
                logger.error(f"Error fixing product {product['id']}: {e}")
                failed += 1

        logger.info(f"=== DONE ===")
        logger.info(f"Success: {success}")
        logger.info(f"Failed: {failed}")

    finally:
        stoflow_conn.close()
        woo_conn.close()


if __name__ == "__main__":
    asyncio.run(main())
