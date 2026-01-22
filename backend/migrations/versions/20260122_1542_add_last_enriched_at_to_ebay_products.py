"""add_last_enriched_at_to_ebay_products

Add last_enriched_at column to ebay_products table to track when
offer data was last fetched. This allows skipping enrichment for
products enriched less than 3 hours ago.

Revision ID: d7af6191fc35
Revises: 8a7c2e3f4d5b
Create Date: 2026-01-22 15:42:51.408955+01:00

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'd7af6191fc35'
down_revision: Union[str, None] = '9bb2236304c8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def get_user_schemas(conn) -> list:
    """Get all user schemas."""
    result = conn.execute(text("""
        SELECT schema_name FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%'
        ORDER BY schema_name
    """))
    return [row[0] for row in result]


def column_exists(conn, schema: str, table: str, column: str) -> bool:
    """Check if column exists in table."""
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
    conn = op.get_bind()

    # Add to template_tenant
    if not column_exists(conn, 'template_tenant', 'ebay_products', 'last_enriched_at'):
        conn.execute(text("""
            ALTER TABLE template_tenant.ebay_products
            ADD COLUMN last_enriched_at TIMESTAMP WITH TIME ZONE
        """))

    # Add to all user schemas
    for schema in get_user_schemas(conn):
        if not column_exists(conn, schema, 'ebay_products', 'last_enriched_at'):
            conn.execute(text(f"""
                ALTER TABLE {schema}.ebay_products
                ADD COLUMN last_enriched_at TIMESTAMP WITH TIME ZONE
            """))


def downgrade() -> None:
    conn = op.get_bind()

    # Remove from template_tenant
    if column_exists(conn, 'template_tenant', 'ebay_products', 'last_enriched_at'):
        conn.execute(text("""
            ALTER TABLE template_tenant.ebay_products
            DROP COLUMN last_enriched_at
        """))

    # Remove from all user schemas
    for schema in get_user_schemas(conn):
        if column_exists(conn, schema, 'ebay_products', 'last_enriched_at'):
            conn.execute(text(f"""
                ALTER TABLE {schema}.ebay_products
                DROP COLUMN last_enriched_at
            """))
