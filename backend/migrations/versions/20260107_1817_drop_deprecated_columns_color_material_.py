"""drop deprecated columns color material condition_sup

Revision ID: 0dea6c4e2c82
Revises: dd7f6b1ded75
Create Date: 2026-01-07 18:17:24.675409+01:00

Purpose:
    Remove deprecated single-value columns from products table after successful
    migration to M2M relationships.

    Columns to drop:
    - color (String) → Replaced by product_colors M2M table
    - material (String) → Replaced by product_materials M2M table
    - condition_sup (JSONB) → Replaced by product_condition_sups M2M table

    ⚠️  WARNING: This migration is ONE-WAY and IRREVERSIBLE.
    Backup database before running in production.

"""
from typing import Sequence, Union


from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

from logging import getLogger

logger = getLogger(__name__)


# revision identifiers, used by Alembic.
revision: str = '0dea6c4e2c82'
down_revision: Union[str, None] = 'dd7f6b1ded75'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def get_user_schemas(conn):
    """Get all user schemas (template_tenant + user_X)."""
    result = conn.execute(text("""
        SELECT schema_name FROM information_schema.schemata
        WHERE schema_name = 'template_tenant'
        OR schema_name LIKE 'user_%'
        ORDER BY schema_name
    """))
    return [row[0] for row in result.fetchall()]


def table_exists(conn, schema, table):
    """Check if a table exists in a schema."""
    result = conn.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = :schema AND table_name = :table
        )
    """), {"schema": schema, "table": table})
    return result.scalar()


def column_exists(conn, schema, table, column):
    """Check if a column exists in a table."""
    result = conn.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = :schema
            AND table_name = :table
            AND column_name = :column
        )
    """), {"schema": schema, "table": table, "column": column})
    return result.scalar()


def upgrade() -> None:
    """Drop deprecated columns color, material, condition_sup."""
    conn = op.get_bind()

    logger.info("\n" + "=" * 70)
    logger.info("⚠️  DROPPING DEPRECATED COLUMNS (IRREVERSIBLE)")
    logger.info("=" * 70)
    logger.info("\n⚠️  WARNING: This operation is ONE-WAY and cannot be undone!")
    logger.info("   Make sure M2M tables are properly populated before proceeding.")
    logger.info("=" * 70 + "\n")

    schemas = get_user_schemas(conn)
    columns_to_drop = ['color', 'material', 'condition_sup']

    total_columns_dropped = 0

    for schema in schemas:
        if not table_exists(conn, schema, 'products'):
            continue

        logger.info(f"📦 Processing {schema}...")

        for column in columns_to_drop:
            if column_exists(conn, schema, 'products', column):
                logger.info(f"  🗑️  Dropping column '{column}'...")
                conn.execute(text(f"""
                    ALTER TABLE {schema}.products
                    DROP COLUMN IF EXISTS {column} CASCADE;
                """))
                total_columns_dropped += 1
                logger.info(f"     ✅ Dropped")
            else:
                logger.info(f"  ⏭️  Column '{column}' already dropped")

    logger.info("\n" + "=" * 70)
    logger.info("📊 DROP SUMMARY")
    logger.info("=" * 70)
    logger.info(f"  Total columns dropped: {total_columns_dropped}")
    logger.info("=" * 70)
    logger.info("✅ DROP COMPLETE")
    logger.info("=" * 70)
    logger.info("\n💡 Migration from single-value to M2M is now complete!")
    logger.info("   Use product_colors, product_materials, product_condition_sups tables.")
    logger.info("=" * 70)


def downgrade() -> None:
    """Cannot restore dropped columns (data loss would occur)."""
    logger.info("\n" + "=" * 70)
    logger.info("⚠️  DOWNGRADE NOT SUPPORTED")
    logger.info("=" * 70)
    logger.info("\nThis migration drops columns permanently.")
    logger.info("Downgrade would require recreating columns from M2M data,")
    logger.info("which is complex and may lose information (multiple values → single value).")
    logger.info("\nTo rollback:")
    logger.info("  1. Restore database from backup")
    logger.info("  2. Run: alembic downgrade -1")
    logger.info("=" * 70)
