"""Remove unused fields from vinted_products

Revision ID: 20260105_1100
Revises: 20260105_1000
Create Date: 2026-01-05 11:00:00.000000

Removes columns that were never populated:
- category: catalog_id is used instead
- material: never extracted from Vinted API
- measurements: measurement_width/length/unit are used instead
- condition_id: duplicate of status_id, never used
- buyer_protection_fee: never extracted
- shipping_price: never extracted
"""
from alembic import op
from sqlalchemy import text
from logging import getLogger

logger = getLogger(__name__)

# revision identifiers, used by Alembic.
revision = '20260105_1100'
down_revision = '20260105_1000'
branch_labels = None
depends_on = None


COLUMNS_TO_DROP = [
    "category",
    "material",
    "measurements",
    "condition_id",
    "buyer_protection_fee",
    "shipping_price",
]


def upgrade():
    """Remove unused columns from vinted_products in all user schemas."""
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

        # Drop each column if it exists
        for column in COLUMNS_TO_DROP:
            column_exists = conn.execute(text("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = :schema
                    AND table_name = 'vinted_products'
                    AND column_name = :column
                )
            """), {"schema": schema, "column": column}).scalar()

            if column_exists:
                conn.execute(text(f"""
                    ALTER TABLE {schema}.vinted_products
                    DROP COLUMN IF EXISTS {column}
                """))
                logger.info(f"  {schema}: dropped column {column}")

    logger.info("Migration completed successfully")


def downgrade():
    """Re-add the removed columns to vinted_products in all user schemas."""
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

    # Column definitions for recreation
    columns_to_add = [
        ("category", "VARCHAR(200) DEFAULT NULL"),
        ("material", "VARCHAR(100) DEFAULT NULL"),
        ("measurements", "VARCHAR(100) DEFAULT NULL"),
        ("condition_id", "INTEGER DEFAULT NULL"),
        ("buyer_protection_fee", "NUMERIC(10,2) DEFAULT NULL"),
        ("shipping_price", "NUMERIC(10,2) DEFAULT NULL"),
    ]

    for schema in user_schemas:
        table_exists = conn.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = :schema AND table_name = 'vinted_products'
            )
        """), {"schema": schema}).scalar()

        if not table_exists:
            continue

        for column_name, column_type in columns_to_add:
            column_exists = conn.execute(text("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = :schema
                    AND table_name = 'vinted_products'
                    AND column_name = :column
                )
            """), {"schema": schema, "column": column_name}).scalar()

            if not column_exists:
                conn.execute(text(f"""
                    ALTER TABLE {schema}.vinted_products
                    ADD COLUMN {column_name} {column_type}
                """))
