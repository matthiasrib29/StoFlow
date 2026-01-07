"""
Fix Alembic Version Mismatch

This script updates the alembic_version table to the correct revision
when Alembic cannot locate the current revision in the migrations directory.
"""

from sqlalchemy import create_engine, text
import os
import sys

# Add parent directory to path to import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.config import settings


def fix_alembic_version():
    """Update alembic_version table to the last valid revision."""

    # Use the database URL from settings
    engine = create_engine(settings.database_url)

    # The revision before our new migration (make_ai_generation_log_product_id_nullable)
    # This is the down_revision of our migration
    target_revision = "4d2e58dae912"

    print(f"Connecting to database: {settings.database_url.split('@')[1]}")

    with engine.connect() as conn:
        # Check current version
        result = conn.execute(text("SELECT version_num FROM alembic_version"))
        current_version = result.scalar()
        print(f"Current alembic version in DB: {current_version}")

        # Update to target revision
        print(f"Updating to revision: {target_revision}")
        conn.execute(text(f"UPDATE alembic_version SET version_num = '{target_revision}'"))
        conn.commit()

        # Verify update
        result = conn.execute(text("SELECT version_num FROM alembic_version"))
        new_version = result.scalar()
        print(f"✓ Alembic version updated to: {new_version}")
        print("\nYou can now run: alembic upgrade head")


if __name__ == "__main__":
    fix_alembic_version()
