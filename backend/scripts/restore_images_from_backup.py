#!/usr/bin/env python3
"""
Restore images from backup to product_images table.

This script:
1. Creates a temporary database from backup
2. Extracts images from JSONB column
3. Inserts into product_images table in main database
4. Cleans up temporary database

Usage:
    python scripts/restore_images_from_backup.py --backup backups/stoflow_db_full_backup_20260115_091652.dump --schema user_1
"""
import argparse
import subprocess
import sys
from datetime import datetime, timezone

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

# Database URLs
MAIN_DB_URL = "postgresql://stoflow_user:stoflow_dev_password_2024@localhost:5433/stoflow_db"
TEMP_DB_NAME = "stoflow_restore_temp"
TEMP_DB_URL = f"postgresql://stoflow_user:stoflow_dev_password_2024@localhost:5433/{TEMP_DB_NAME}"


def run_command(cmd: list[str], description: str) -> bool:
    """Run shell command and return success status."""
    print(f"🔄 {description}...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"✅ {description} - Success")
        return True
    else:
        print(f"❌ {description} - Failed")
        if result.stderr:
            print(f"   Error: {result.stderr[:500]}")
        return False


def create_temp_database():
    """Create temporary database for restoration."""
    print("\n📦 Step 1: Creating temporary database...")

    # Drop if exists
    run_command(
        ["docker", "exec", "stoflow_postgres", "dropdb", "-U", "stoflow_user", "--if-exists", TEMP_DB_NAME],
        "Dropping existing temp database"
    )

    # Create new
    success = run_command(
        ["docker", "exec", "stoflow_postgres", "createdb", "-U", "stoflow_user", TEMP_DB_NAME],
        "Creating temporary database"
    )

    if not success:
        print("❌ Failed to create temporary database")
        sys.exit(1)

    print(f"✅ Temporary database '{TEMP_DB_NAME}' created")


def restore_backup_to_temp(backup_path: str):
    """Restore backup file to temporary database."""
    print(f"\n📂 Step 2: Restoring backup to temporary database...")
    print(f"   Backup: {backup_path}")

    # Use docker exec with stdin redirection
    cmd = f"docker exec -i stoflow_postgres pg_restore -U stoflow_user -d {TEMP_DB_NAME} --no-owner --no-privileges"

    with open(backup_path, 'rb') as f:
        result = subprocess.run(
            cmd.split(),
            stdin=f,
            capture_output=True,
            text=False
        )

    if result.returncode != 0:
        # pg_restore returns non-zero even on warnings, check if it's fatal
        stderr = result.stderr.decode('utf-8', errors='ignore')
        if "ERROR" in stderr and "already exists" not in stderr:
            print(f"❌ Restore failed: {stderr[:500]}")
            sys.exit(1)

    print("✅ Backup restored to temporary database")


def extract_and_migrate_images(schema: str):
    """Extract images from temp DB and insert into main DB."""
    print(f"\n🔄 Step 3: Extracting images from backup for schema '{schema}'...")

    # Connect to both databases
    temp_engine = create_engine(TEMP_DB_URL)
    main_engine = create_engine(MAIN_DB_URL)

    temp_db = Session(temp_engine)
    main_db = Session(main_engine)

    try:
        # Check if schema exists in temp database
        schema_exists = temp_db.execute(text(f"""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.schemata
                WHERE schema_name = '{schema}'
            )
        """)).scalar()

        if not schema_exists:
            print(f"❌ Schema '{schema}' not found in backup")
            sys.exit(1)

        # Extract products with images from temp database
        print(f"   Extracting products with images from {schema}.products...")

        result = temp_db.execute(text(f"""
            SELECT id, images
            FROM {schema}.products
            WHERE images IS NOT NULL
            AND jsonb_array_length(images) > 0
            AND deleted_at IS NULL
            ORDER BY id
        """))

        products = result.fetchall()
        print(f"   Found {len(products)} products with images in backup")

        if len(products) == 0:
            print("⚠️  No products with images found in backup")
            return

        # Clear existing product_images data in main database
        print(f"   Clearing existing data in {schema}.product_images...")
        main_db.execute(text(f"DELETE FROM {schema}.product_images"))
        main_db.commit()

        # Migrate images
        total_images = 0
        total_labels = 0

        for product_id, images_jsonb in products:
            images = images_jsonb if isinstance(images_jsonb, list) else []

            if not images:
                continue

            # Detect label: last image if product has 2+ images
            has_label = len(images) >= 2

            for img in images:
                url = img.get('url', '')
                order = img.get('order', 0)
                created_at = img.get('created_at')

                # Determine if this is the label
                is_label = has_label and (order == max(i.get('order', 0) for i in images))

                if is_label:
                    total_labels += 1

                # Parse datetime
                if created_at and isinstance(created_at, str):
                    try:
                        created_at_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    except:
                        created_at_dt = datetime.now(timezone.utc)
                else:
                    created_at_dt = datetime.now(timezone.utc)

                # Insert into product_images
                main_db.execute(text(f"""
                    INSERT INTO {schema}.product_images
                    (product_id, url, "order", is_label, created_at, updated_at)
                    VALUES (:product_id, :url, :order, :is_label, :created_at, :updated_at)
                """), {
                    'product_id': product_id,
                    'url': url,
                    'order': order,
                    'is_label': is_label,
                    'created_at': created_at_dt,
                    'updated_at': created_at_dt
                })

                total_images += 1

            # Commit every 100 products
            if product_id % 100 == 0:
                main_db.commit()
                print(f"   Progress: {product_id} products processed...")

        # Final commit
        main_db.commit()

        print(f"\n✅ Migration complete!")
        print(f"   📊 Total images migrated: {total_images}")
        print(f"   🏷️  Labels detected: {total_labels}")
        print(f"   📸 Photos (non-labels): {total_images - total_labels}")

        # Validation
        print(f"\n🔍 Validation:")
        count = main_db.execute(text(f"SELECT COUNT(*) FROM {schema}.product_images")).scalar()
        labels = main_db.execute(text(f"SELECT COUNT(*) FROM {schema}.product_images WHERE is_label = true")).scalar()
        print(f"   ✓ Images in table: {count}")
        print(f"   ✓ Labels: {labels}")

    finally:
        temp_db.close()
        main_db.close()
        temp_engine.dispose()
        main_engine.dispose()


def cleanup_temp_database():
    """Drop temporary database."""
    print(f"\n🧹 Step 4: Cleaning up temporary database...")

    run_command(
        ["docker", "exec", "stoflow_postgres", "dropdb", "-U", "stoflow_user", "--if-exists", TEMP_DB_NAME],
        "Dropping temporary database"
    )

    print("✅ Cleanup complete")


def main():
    parser = argparse.ArgumentParser(description="Restore images from backup")
    parser.add_argument("--backup", required=True, help="Path to backup dump file")
    parser.add_argument("--schema", required=True, help="Schema to restore (e.g., user_1)")
    parser.add_argument("--skip-cleanup", action="store_true", help="Keep temporary database for inspection")

    args = parser.parse_args()

    print("="*60)
    print("🔄 RESTORE IMAGES FROM BACKUP")
    print("="*60)
    print(f"Backup file: {args.backup}")
    print(f"Target schema: {args.schema}")
    print(f"Temporary database: {TEMP_DB_NAME}")
    print("="*60)

    try:
        # Step 1: Create temp database
        create_temp_database()

        # Step 2: Restore backup to temp database
        restore_backup_to_temp(args.backup)

        # Step 3: Extract and migrate images
        extract_and_migrate_images(args.schema)

        # Step 4: Cleanup (unless --skip-cleanup)
        if not args.skip_cleanup:
            cleanup_temp_database()
        else:
            print(f"\n⚠️  Temporary database '{TEMP_DB_NAME}' kept for inspection")
            print(f"   Drop manually: docker exec stoflow_postgres dropdb -U stoflow_user {TEMP_DB_NAME}")

        print("\n" + "="*60)
        print("✅ SUCCESS - Images restored from backup!")
        print("="*60)

    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
        cleanup_temp_database()
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        cleanup_temp_database()
        sys.exit(1)


if __name__ == "__main__":
    main()
