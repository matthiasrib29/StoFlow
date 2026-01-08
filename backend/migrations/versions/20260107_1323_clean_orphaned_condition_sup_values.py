"""clean_orphaned_condition_sup_values

Revision ID: d4d7725adb3a
Revises: 312dfe0a7c07
Create Date: 2026-01-07 13:23:23.162581+01:00

Clean orphaned values in products.condition_sup JSONB arrays:
- Remove "good condition", "excellent condition", "like new", "very good condition"
- These values were removed from condition_sup table but still exist in products
- Total: ~113 products affected
"""
from typing import Sequence, Union


from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

from logging import getLogger

logger = getLogger(__name__)


# revision identifiers, used by Alembic.
revision: str = 'd4d7725adb3a'
down_revision: Union[str, None] = '312dfe0a7c07'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def get_user_schemas(conn):
    """Get list of user schemas."""
    result = conn.execute(text("""
        SELECT schema_name FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%'
        ORDER BY schema_name
    """))
    return [row[0] for row in result]


def table_exists(conn, schema, table):
    """Check if a table exists."""
    result = conn.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = :schema AND table_name = :table
        )
    """), {"schema": schema, "table": table})
    return result.scalar()


def upgrade() -> None:
    """Clean orphaned values from condition_sup JSONB arrays."""
    conn = op.get_bind()

    # Orphaned values to remove
    orphaned_values = [
        'acceptable condition',
        'excellent condition',
        'good condition',
        'like new',
        'very good condition'
    ]

    logger.info("=" * 70)
    logger.info("🧹 CLEANING ORPHANED CONDITION_SUP VALUES")
    logger.info("=" * 70)

    # Get user schemas
    user_schemas = get_user_schemas(conn)
    logger.info(f"\nFound {len(user_schemas)} user schemas\n")

    total_cleaned = 0

    for schema in user_schemas:
        if not table_exists(conn, schema, 'products'):
            continue

        logger.info(f"Cleaning products in {schema}...")

        for orphan in orphaned_values:
            # Remove orphaned value from JSONB array
            # Using PostgreSQL JSONB operator to filter array elements
            orphan_json = f'["{orphan}"]'

            result = conn.execute(text(f"""
                UPDATE {schema}.products
                SET condition_sup = (
                    SELECT jsonb_agg(elem)
                    FROM jsonb_array_elements_text(condition_sup) AS elem
                    WHERE elem != :orphan
                )
                WHERE condition_sup @> cast(:orphan_json as jsonb)
                AND deleted_at IS NULL
            """), {
                "orphan": orphan,
                "orphan_json": orphan_json
            })

            count = result.rowcount
            if count > 0:
                logger.info(f"  🗑️  Removed '{orphan}' from {count} products")
                total_cleaned += count

    logger.info("\n" + "=" * 70)
    logger.info(f"✅ CLEANING COMPLETE: {total_cleaned} product entries cleaned")
    logger.info("=" * 70)


def downgrade() -> None:
    """Cannot restore orphaned values (data lost)."""
    logger.info("⚠️  Downgrade not possible: orphaned values cannot be restored")
    logger.info("   Original data was already inconsistent and has been cleaned")
