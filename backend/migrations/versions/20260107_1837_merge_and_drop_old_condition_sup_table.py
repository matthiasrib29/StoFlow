"""merge and drop old condition_sup table

Revision ID: 9c7c0b878bb4
Revises: 0dea6c4e2c82
Create Date: 2026-01-07 18:37:13.809682+01:00

Purpose:
    Clean up duplicate condition supplement tables in product_attributes schema.

    There are two tables:
    - condition_sup (singular, 28 values) - OLD table
    - condition_sups (plural, 19 values) - NEW table

    This migration:
    1. Merges values from old table to new table
    2. Drops the old condition_sup (singular) table

"""
from typing import Sequence, Union


from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

from logging import getLogger

logger = getLogger(__name__)


# revision identifiers, used by Alembic.
revision: str = '9c7c0b878bb4'
down_revision: Union[str, None] = '0dea6c4e2c82'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Merge old condition_sup table into condition_sups and drop it."""
    conn = op.get_bind()

    logger.info("\n" + "=" * 70)
    logger.info("📊 MERGING CONDITION_SUP TABLES")
    logger.info("=" * 70 + "\n")

    # Check if old table exists
    result = conn.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'product_attributes'
            AND table_name = 'condition_sup'
        );
    """))
    table_exists = result.scalar()

    if not table_exists:
        logger.info("⏭️  Old condition_sup table doesn't exist (already merged or renamed)")
        logger.info("  ✅ Migration already applied, skipping")
        return

    # Step 1: Copy all values from old table to new table (ignore duplicates)
    logger.info("📋 Copying values from condition_sup → condition_sups...")
    result = conn.execute(text("""
        INSERT INTO product_attributes.condition_sups
            (name_en, name_fr, name_de, name_it, name_es, name_nl, name_pl)
        SELECT name_en, name_fr, name_de, name_it, name_es, name_nl, name_pl
        FROM product_attributes.condition_sup
        ON CONFLICT (name_en) DO NOTHING;
    """))
    copied = result.rowcount
    logger.info(f"  ✅ Copied {copied} new values")

    # Step 2: Check total count in new table
    result = conn.execute(text("""
        SELECT COUNT(*) FROM product_attributes.condition_sups;
    """))
    total = result.scalar()
    logger.info(f"  📊 Total values in condition_sups: {total}")

    # Step 3: Drop old table
    logger.info("\n🗑️  Dropping old condition_sup table...")
    conn.execute(text("""
        DROP TABLE IF EXISTS product_attributes.condition_sup CASCADE;
    """))
    logger.info("  ✅ Dropped")

    logger.info("\n" + "=" * 70)
    logger.info("✅ MERGE COMPLETE")
    logger.info("=" * 70)
    logger.info(f"\nOnly product_attributes.condition_sups (plural) remains with {total} values.")
    logger.info("=" * 70)


def downgrade() -> None:
    """Cannot recreate dropped table."""
    logger.info("\n⚠️  Downgrade not supported (would require recreating condition_sup table)")
