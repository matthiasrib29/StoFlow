"""refactor: remove unused ebay_product columns and add complete api fields

Revision ID: 83c5d2952134
Revises: ef2af2d8a1c3
Create Date: 2026-01-07 09:55:14.170896+01:00

Changes:
- Remove unused columns: location, country, category_name
- Add package dimensions: length, width, height (with units)
- Add offer details: merchant_location_key, secondary_category_id, lot_size,
  quantity_limit_per_buyer, listing_description, sold_quantity, available_quantity
"""
from typing import Sequence, Union


from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

from logging import getLogger

logger = getLogger(__name__)


# revision identifiers, used by Alembic.
revision: str = '83c5d2952134'
down_revision: Union[str, None] = 'ef2af2d8a1c3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def table_exists(conn, schema: str, table: str) -> bool:
    """Check if table exists in schema."""
    result = conn.execute(
        text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = :schema AND table_name = :table
            )
        """),
        {"schema": schema, "table": table}
    )
    return result.scalar()


def column_exists(conn, schema: str, table: str, column: str) -> bool:
    """Check if column exists in table."""
    result = conn.execute(
        text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = :schema
                AND table_name = :table
                AND column_name = :column
            )
        """),
        {"schema": schema, "table": table, "column": column}
    )
    return result.scalar()


def get_user_schemas(conn) -> list[str]:
    """Get all user_* schemas."""
    result = conn.execute(
        text("""
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name LIKE 'user_%'
            ORDER BY schema_name
        """)
    )
    return [row[0] for row in result]


def upgrade() -> None:
    conn = op.get_bind()
    schemas = get_user_schemas(conn)

    if not schemas:
        logger.info("No user schemas found, skipping migration")
        return

    for schema in schemas:
        if not table_exists(conn, schema, 'ebay_products'):
            logger.info(f"Table ebay_products does not exist in {schema}, skipping")
            continue

        logger.info(f"Migrating {schema}.ebay_products...")

        # Remove unused columns
        for column in ['location', 'country', 'category_name']:
            if column_exists(conn, schema, 'ebay_products', column):
                op.drop_column('ebay_products', column, schema=schema)
                logger.info(f"  - Removed column: {column}")

        # Add package dimensions (from Inventory API)
        dimensions = [
            ('package_length_value', sa.Numeric(10, 2)),
            ('package_length_unit', sa.String(10)),
            ('package_width_value', sa.Numeric(10, 2)),
            ('package_width_unit', sa.String(10)),
            ('package_height_value', sa.Numeric(10, 2)),
            ('package_height_unit', sa.String(10)),
        ]

        for col_name, col_type in dimensions:
            if not column_exists(conn, schema, 'ebay_products', col_name):
                op.add_column(
                    'ebay_products',
                    sa.Column(col_name, col_type, nullable=True),
                    schema=schema
                )
                logger.info(f"  + Added column: {col_name}")

        # Add offer details (from Offer API)
        offer_columns = [
            ('merchant_location_key', sa.String(50), 'Inventory location identifier'),
            ('secondary_category_id', sa.String(50), 'Secondary category if dual-listed'),
            ('lot_size', sa.Integer, 'Number of items in lot listing'),
            ('quantity_limit_per_buyer', sa.Integer, 'Max quantity per buyer'),
            ('listing_description', sa.Text, 'Listing description (may differ from product)'),
            ('sold_quantity', sa.Integer, 'Number of units sold'),
            ('available_quantity', sa.Integer, 'Available quantity for purchase'),
        ]

        for col_name, col_type, comment in offer_columns:
            if not column_exists(conn, schema, 'ebay_products', col_name):
                op.add_column(
                    'ebay_products',
                    sa.Column(col_name, col_type, nullable=True, comment=comment),
                    schema=schema
                )
                logger.info(f"  + Added column: {col_name}")

    # Also update template_tenant schema if it exists
    if table_exists(conn, 'template_tenant', 'ebay_products'):
        logger.info("Migrating template_tenant.ebay_products...")

        # Remove unused columns
        for column in ['location', 'country', 'category_name']:
            if column_exists(conn, 'template_tenant', 'ebay_products', column):
                op.drop_column('ebay_products', column, schema='template_tenant')
                logger.info(f"  - Removed column: {column}")

        # Add all new columns
        for col_name, col_type in dimensions:
            if not column_exists(conn, 'template_tenant', 'ebay_products', col_name):
                op.add_column(
                    'ebay_products',
                    sa.Column(col_name, col_type, nullable=True),
                    schema='template_tenant'
                )

        for col_name, col_type, comment in offer_columns:
            if not column_exists(conn, 'template_tenant', 'ebay_products', col_name):
                op.add_column(
                    'ebay_products',
                    sa.Column(col_name, col_type, nullable=True, comment=comment),
                    schema='template_tenant'
                )

    logger.info("Migration completed successfully")


def downgrade() -> None:
    conn = op.get_bind()
    schemas = get_user_schemas(conn)

    for schema in schemas:
        if not table_exists(conn, schema, 'ebay_products'):
            continue

        logger.info(f"Rolling back {schema}.ebay_products...")

        # Remove added columns
        new_columns = [
            'package_length_value', 'package_length_unit',
            'package_width_value', 'package_width_unit',
            'package_height_value', 'package_height_unit',
            'merchant_location_key', 'secondary_category_id',
            'lot_size', 'quantity_limit_per_buyer',
            'listing_description', 'sold_quantity', 'available_quantity'
        ]

        for column in new_columns:
            if column_exists(conn, schema, 'ebay_products', column):
                op.drop_column('ebay_products', column, schema=schema)

        # Re-add removed columns
        op.add_column('ebay_products', sa.Column('location', sa.String(100), nullable=True), schema=schema)
        op.add_column('ebay_products', sa.Column('country', sa.String(2), nullable=True), schema=schema)
        op.add_column('ebay_products', sa.Column('category_name', sa.String(255), nullable=True), schema=schema)

    # Rollback template_tenant
    if table_exists(conn, 'template_tenant', 'ebay_products'):
        for column in new_columns:
            if column_exists(conn, 'template_tenant', 'ebay_products', column):
                op.drop_column('ebay_products', column, schema='template_tenant')

        op.add_column('ebay_products', sa.Column('location', sa.String(100), nullable=True), schema='template_tenant')
        op.add_column('ebay_products', sa.Column('country', sa.String(2), nullable=True), schema='template_tenant')
        op.add_column('ebay_products', sa.Column('category_name', sa.String(255), nullable=True), schema='template_tenant')

    logger.info("Rollback completed successfully")
