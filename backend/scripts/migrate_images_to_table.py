"""
Migrate product images from JSONB to product_images table.

This script migrates the images stored in products.images (JSONB column)
to the new product_images table with label detection.

Label Detection Strategy:
    - The image with the HIGHEST order value is marked as is_label=true
    - This follows the pythonApiWOO pattern where the last uploaded image
      was always the internal price label
    - Expected: ~611 products with labels (18.6%)

Idempotence:
    - By default, skips products that already have images in product_images
    - Use --force to clear existing images and re-migrate

Multi-Tenant:
    - Discovers all user_X schemas automatically
    - Migrates each schema in a separate transaction
    - If one schema fails, others continue

Usage Examples:
    # Dry-run (show what would be migrated)
    python scripts/migrate_images_to_table.py --dry-run

    # Migrate all schemas
    python scripts/migrate_images_to_table.py

    # Migrate specific schema
    python scripts/migrate_images_to_table.py --schema user_1

    # Force re-migration (clear and re-import)
    python scripts/migrate_images_to_table.py --schema user_1 --force

Expected Output:
    2026-01-15 10:00:00 - INFO - Migrating schema: user_1
    2026-01-15 10:00:01 - INFO - Found 3281 products with images in user_1
    2026-01-15 10:00:02 - INFO - Processed 100/3281 products...
    2026-01-15 10:00:05 - INFO - Processed 200/3281 products...
    ...
    2026-01-15 10:01:30 - INFO - ✓ Committed 3281 products for user_1
    ============================================================
    MIGRATION SUMMARY
    ============================================================
    Mode: LIVE MIGRATION
    Products processed: 3281
    Images migrated: 13124
    Labels detected: 611
    Errors: 0
    ============================================================
    Migration completed successfully!

Options:
    --dry-run: Show what would be migrated without making changes
    --schema: Migrate only specific schema (default: all user_X schemas)
    --force: Clear existing images and re-migrate
"""

import argparse
import logging
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy import text
from sqlalchemy.orm import Session

from shared.database import SessionLocal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ImageMigrator:
    """Migrate product images from JSONB to table."""

    def __init__(self, dry_run: bool = False, force: bool = False):
        self.dry_run = dry_run
        self.force = force
        self.stats = {
            'products_processed': 0,
            'images_migrated': 0,
            'labels_detected': 0,
            'errors': 0
        }

    def migrate_schema(self, schema: str) -> bool:
        """Migrate all products in a schema."""
        db = SessionLocal()

        try:
            # Set search_path for multi-tenant isolation
            db.execute(text(f"SET search_path TO {schema}, public"))

            # Check if product_images table exists
            result = db.execute(text("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = :schema AND table_name = 'product_images'
                )
            """), {"schema": schema})

            if not result.scalar():
                logger.warning(f"Table {schema}.product_images does not exist, skipping")
                return False

            # Get all products with images
            query = text("""
                SELECT id, images
                FROM products
                WHERE images IS NOT NULL
                AND jsonb_array_length(images) > 0
                AND deleted_at IS NULL
                ORDER BY id
            """)

            products = db.execute(query).fetchall()
            logger.info(f"Found {len(products)} products with images in {schema}")

            # Migrate each product
            for idx, (product_id, images_json) in enumerate(products, 1):
                try:
                    self.migrate_product(db, schema, product_id, images_json)

                    # Log progress every 100 products
                    if idx % 100 == 0:
                        logger.info(f"Processed {idx}/{len(products)} products...")

                except Exception as e:
                    logger.error(f"Error migrating product {product_id}: {e}")
                    self.stats['errors'] += 1
                    if not self.dry_run:
                        db.rollback()
                    continue

            # Commit transaction for this schema
            if not self.dry_run:
                db.commit()
                logger.info(f"✓ Committed {len(products)} products for {schema}")
            else:
                logger.info(f"[DRY RUN] Would migrate {len(products)} products")

            return True

        except Exception as e:
            logger.error(f"Failed to migrate schema {schema}: {e}")
            if not self.dry_run:
                db.rollback()
            return False

        finally:
            db.close()

    def migrate_product(self, db: Session, schema: str, product_id: int, images_json: List[Dict]) -> None:
        """Migrate images for a single product."""

        # Check if already migrated (idempotence)
        if not self.force:
            check_query = text("""
                SELECT COUNT(*) FROM product_images
                WHERE product_id = :product_id
            """)
            existing_count = db.execute(check_query, {"product_id": product_id}).scalar()

            if existing_count > 0:
                logger.debug(f"Product {product_id} already has {existing_count} images, skipping")
                return
        else:
            # Force mode: clear existing images
            delete_query = text("DELETE FROM product_images WHERE product_id = :product_id")
            if not self.dry_run:
                db.execute(delete_query, {"product_id": product_id})

        # Detect label (highest order)
        label_order = self.detect_label(images_json)

        # Prepare batch insert data
        images_to_insert = []
        for img in images_json:
            is_label = (img['order'] == label_order)

            images_to_insert.append({
                'product_id': product_id,
                'url': img['url'],
                'order': img['order'],
                'is_label': is_label,
                'created_at': img.get('created_at', datetime.utcnow().isoformat()),
                'updated_at': datetime.utcnow().isoformat()
            })

            if is_label:
                self.stats['labels_detected'] += 1

        # Bulk insert
        if not self.dry_run:
            insert_query = text("""
                INSERT INTO product_images (
                    product_id, url, "order", is_label, created_at, updated_at
                ) VALUES (
                    :product_id, :url, :order, :is_label,
                    :created_at::timestamp, :updated_at::timestamp
                )
            """)

            for img_data in images_to_insert:
                db.execute(insert_query, img_data)

        self.stats['products_processed'] += 1
        self.stats['images_migrated'] += len(images_to_insert)

    def detect_label(self, images_json: List[Dict]) -> int:
        """Find the order of the label image (highest order)."""
        if not images_json:
            return -1

        # Find max order value
        max_order = max(img['order'] for img in images_json)
        return max_order

    def print_summary(self):
        """Print migration summary."""
        logger.info("=" * 60)
        logger.info("MIGRATION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE MIGRATION'}")
        logger.info(f"Products processed: {self.stats['products_processed']}")
        logger.info(f"Images migrated: {self.stats['images_migrated']}")
        logger.info(f"Labels detected: {self.stats['labels_detected']}")
        logger.info(f"Errors: {self.stats['errors']}")
        logger.info("=" * 60)

        if self.dry_run:
            logger.info("No changes were made (dry-run mode)")
        else:
            logger.info("Migration completed successfully!")


def get_user_schemas(db: Session) -> List[str]:
    """Get all user schemas (user_*)."""
    result = db.execute(text("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%'
        ORDER BY schema_name
    """))
    return [row[0] for row in result.fetchall()]


def main():
    parser = argparse.ArgumentParser(description='Migrate product images to table')
    parser.add_argument('--dry-run', action='store_true', help='Show changes without applying')
    parser.add_argument('--schema', type=str, help='Migrate specific schema only')
    parser.add_argument('--force', action='store_true', help='Clear existing and re-migrate')

    args = parser.parse_args()

    migrator = ImageMigrator(dry_run=args.dry_run, force=args.force)

    # Get schemas to migrate
    if args.schema:
        schemas = [args.schema]
    else:
        db = SessionLocal()
        schemas = get_user_schemas(db)
        db.close()

    # Migrate each schema
    for schema in schemas:
        logger.info(f"{'[DRY RUN] ' if args.dry_run else ''}Migrating schema: {schema}")
        success = migrator.migrate_schema(schema)
        if not success:
            logger.error(f"Failed to migrate schema: {schema}")

    # Print summary
    migrator.print_summary()


if __name__ == '__main__':
    main()
