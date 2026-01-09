"""add stretch column to products

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-01-07 19:01:00.000000+01:00

Purpose:
    Add stretch column to all user_X.products tables (multi-tenant fan-out).

    For each user schema:
    1. Add stretch VARCHAR(100) column
    2. Add FK constraint to product_attributes.stretches
    3. Create index on stretch column
"""
from typing import Sequence, Union


from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

from logging import getLogger

logger = getLogger(__name__)


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def get_user_schemas(conn):
    """Get list of user schemas (user_X + template_tenant)."""
    result = conn.execute(text("""
        SELECT schema_name FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%' OR schema_name = 'template_tenant'
        ORDER BY schema_name
    """))
    return [row[0] for row in result]


def table_exists(conn, schema, table):
    """Check if a table exists in a schema."""
    result = conn.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = :schema AND table_name = :table
        )
    """), {"schema": schema, "table": table})
    return result.scalar()


def upgrade() -> None:
    """Add stretch column to all user products tables."""
    conn = op.get_bind()

    logger.info("\n" + "=" * 70)
    logger.info("📊 ADDING STRETCH COLUMN TO PRODUCTS")
    logger.info("=" * 70 + "\n")

    schemas = get_user_schemas(conn)
    logger.info(f"Found {len(schemas)} user schemas to process\n")

    success_count = 0
    skip_count = 0

    for schema in schemas:
        if not table_exists(conn, schema, 'products'):
            logger.info(f"⚠️  Skipping {schema} - products table not found")
            skip_count += 1
            continue

        try:
            # Add column
            conn.execute(text(f"""
                ALTER TABLE {schema}.products
                ADD COLUMN stretch VARCHAR(100);
            """))

            # Add FK constraint
            conn.execute(text(f"""
                ALTER TABLE {schema}.products
                ADD CONSTRAINT fk_products_stretch
                FOREIGN KEY (stretch)
                REFERENCES product_attributes.stretches(name_en)
                ON UPDATE CASCADE
                ON DELETE SET NULL;
            """))

            # Create index
            conn.execute(text(f"""
                CREATE INDEX idx_products_stretch ON {schema}.products(stretch);
            """))

            logger.info(f"✅ {schema}: Added stretch column with FK and index")
            success_count += 1

        except Exception as e:
            logger.info(f"❌ {schema}: Error - {str(e)}")
            # Continue with other schemas even if one fails
            continue

    logger.info("\n" + "=" * 70)
    logger.info(f"✅ STRETCH COLUMN ADDED")
    logger.info(f"   Success: {success_count} schemas")
    logger.info(f"   Skipped: {skip_count} schemas")
    logger.info("=" * 70)


def downgrade() -> None:
    """Remove stretch column from all user products tables."""
    conn = op.get_bind()

    logger.info("\n⚠️  Removing stretch column from products tables...")

    schemas = get_user_schemas(conn)

    for schema in schemas:
        if not table_exists(conn, schema, 'products'):
            continue

        try:
            # DROP COLUMN CASCADE removes column, FK constraint, and index
            conn.execute(text(f"""
                ALTER TABLE {schema}.products
                DROP COLUMN IF EXISTS stretch CASCADE;
            """))
            logger.info(f"✅ {schema}: Removed stretch column")

        except Exception as e:
            logger.info(f"❌ {schema}: Error - {str(e)}")
            continue

    logger.info("✅ Stretch column removed from all schemas")
