"""link_ebay_products_by_sku

Revision ID: d687e39bd2a0
Revises: 9d045c61f0bd
Create Date: 2026-01-19 12:40:11.580472+01:00

Business Rules:
- eBay SKU format: "PRODUCT_ID-COUNTRY_CODE" (e.g., "2438-NL", "1770-FR")
- One StoFlow product can have multiple eBay listings (one per marketplace/country)
- Drop UNIQUE constraint on product_id to allow 1:N relationship
- Extract product_id from ebay_sku and link to products table
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd687e39bd2a0'
down_revision: Union[str, None] = '9d045c61f0bd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Link eBay products to StoFlow products by extracting ID from ebay_sku.

    Steps:
    1. Drop UNIQUE constraint on product_id (allows 1:N relationship)
    2. Extract product_id from ebay_sku (format: "123-FR" -> 123)
    3. Update product_id where product exists
    """
    conn = op.get_bind()

    # Get all user schemas
    schemas_result = conn.execute(sa.text("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%'
    """))
    user_schemas = [row[0] for row in schemas_result.fetchall()]

    total_linked = 0

    for schema in user_schemas:
        # Check if ebay_products table exists
        table_exists = conn.execute(sa.text(f"""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = '{schema}'
                AND table_name = 'ebay_products'
            )
        """)).scalar()

        if not table_exists:
            continue

        # Step 1: Drop UNIQUE constraint on product_id if it exists
        constraint_exists = conn.execute(sa.text(f"""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.table_constraints
                WHERE table_schema = '{schema}'
                AND table_name = 'ebay_products'
                AND constraint_name = 'ebay_products_product_id_key'
            )
        """)).scalar()

        if constraint_exists:
            conn.execute(sa.text(f"""
                ALTER TABLE {schema}.ebay_products
                DROP CONSTRAINT ebay_products_product_id_key
            """))
            print(f"  {schema}: dropped UNIQUE constraint on product_id")

        # Step 2: Link eBay products by extracting product_id from ebay_sku
        # SKU format: "123-FR" -> extract 123
        result = conn.execute(sa.text(f"""
            UPDATE {schema}.ebay_products ep
            SET product_id = extracted.pid::integer
            FROM (
                SELECT
                    id,
                    (regexp_match(ebay_sku, '^(\\d+)'))[1] as pid
                FROM {schema}.ebay_products
                WHERE ebay_sku ~ '^\\d+'
                AND product_id IS NULL
            ) extracted
            WHERE ep.id = extracted.id
            AND extracted.pid IS NOT NULL
            AND EXISTS (
                SELECT 1 FROM {schema}.products p
                WHERE p.id = extracted.pid::integer
            )
        """))

        linked = result.rowcount
        total_linked += linked

        if linked > 0:
            print(f"  {schema}: linked {linked} eBay products")

    print(f"  Total: {total_linked} eBay products linked to StoFlow products")


def downgrade() -> None:
    """
    Remove product_id links and restore UNIQUE constraint.
    """
    conn = op.get_bind()

    # Get all user schemas
    schemas_result = conn.execute(sa.text("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%'
    """))
    user_schemas = [row[0] for row in schemas_result.fetchall()]

    for schema in user_schemas:
        # Check if ebay_products table exists
        table_exists = conn.execute(sa.text(f"""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = '{schema}'
                AND table_name = 'ebay_products'
            )
        """)).scalar()

        if not table_exists:
            continue

        # Set product_id back to NULL
        conn.execute(sa.text(f"""
            UPDATE {schema}.ebay_products
            SET product_id = NULL
            WHERE ebay_sku ~ '^\\d+'
            AND product_id IS NOT NULL
        """))

        # Note: We don't restore the UNIQUE constraint because it would fail
        # if there are duplicates. The constraint can be manually added if needed.

    print("  Removed product_id links from eBay products")
    print("  Note: UNIQUE constraint NOT restored (would fail with duplicates)")
