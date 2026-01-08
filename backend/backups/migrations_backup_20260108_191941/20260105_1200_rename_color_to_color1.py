"""Rename color to color1 in vinted_products

Revision ID: 20260105_1200
Revises: 20260105_1100
Create Date: 2026-01-05 12:00:00.000000

Renames the 'color' column to 'color1' for consistency with Vinted API
which uses color1/color2 naming convention.
"""
from alembic import op
from sqlalchemy import text
from logging import getLogger

logger = getLogger(__name__)

# revision identifiers, used by Alembic.
revision = '20260105_1200'
down_revision = '20260105_1100'
branch_labels = None
depends_on = None


def upgrade():
    """Rename color to color1 in vinted_products in all user schemas."""
    conn = op.get_bind()

    # Get all user schemas
    result = conn.execute(text("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%'
        ORDER BY schema_name
    """))
    user_schemas = [row[0] for row in result]

    if not user_schemas:
        logger.info("No user schemas found, skipping migration")
        return

    logger.info(f"Found {len(user_schemas)} user schemas to migrate")

    for schema in user_schemas:
        # Check if table exists in this schema
        table_exists = conn.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = :schema AND table_name = 'vinted_products'
            )
        """), {"schema": schema}).scalar()

        if not table_exists:
            logger.info(f"  {schema}: vinted_products table not found, skipping")
            continue

        # Check if 'color' column exists (old name)
        color_exists = conn.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = :schema
                AND table_name = 'vinted_products'
                AND column_name = 'color'
            )
        """), {"schema": schema}).scalar()

        if color_exists:
            conn.execute(text(f"""
                ALTER TABLE {schema}.vinted_products
                RENAME COLUMN color TO color1
            """))
            logger.info(f"  {schema}: renamed color -> color1")
        else:
            # Check if color1 already exists
            color1_exists = conn.execute(text("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = :schema
                    AND table_name = 'vinted_products'
                    AND column_name = 'color1'
                )
            """), {"schema": schema}).scalar()

            if color1_exists:
                logger.info(f"  {schema}: color1 already exists, skipping")
            else:
                logger.info(f"  {schema}: neither color nor color1 found, skipping")

    logger.info("Migration completed successfully")


def downgrade():
    """Rename color1 back to color in vinted_products in all user schemas."""
    conn = op.get_bind()

    # Get all user schemas
    result = conn.execute(text("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%'
        ORDER BY schema_name
    """))
    user_schemas = [row[0] for row in result]

    if not user_schemas:
        return

    for schema in user_schemas:
        table_exists = conn.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = :schema AND table_name = 'vinted_products'
            )
        """), {"schema": schema}).scalar()

        if not table_exists:
            continue

        # Check if 'color1' column exists
        color1_exists = conn.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = :schema
                AND table_name = 'vinted_products'
                AND column_name = 'color1'
            )
        """), {"schema": schema}).scalar()

        if color1_exists:
            conn.execute(text(f"""
                ALTER TABLE {schema}.vinted_products
                RENAME COLUMN color1 TO color
            """))
