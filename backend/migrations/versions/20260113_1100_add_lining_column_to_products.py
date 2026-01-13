"""Add lining column to products table

Revision ID: 20260113_1100
Revises: 20260113_0900
Create Date: 2026-01-13

Changes:
- Add lining column to products table (FK to product_attributes.linings)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

from logging import getLogger

logger = getLogger(__name__)

# revision identifiers, used by Alembic.
revision: str = '20260113_1100'
down_revision: Union[str, None] = '20260113_0900'
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

    # Add to all user schemas
    for schema in schemas:
        if not table_exists(conn, schema, 'products'):
            logger.info(f"Table products does not exist in {schema}, skipping")
            continue

        if not column_exists(conn, schema, 'products', 'lining'):
            op.add_column(
                'products',
                sa.Column(
                    'lining',
                    sa.String(100),
                    nullable=True,
                    comment='Lining type (FK product_attributes.linings)'
                ),
                schema=schema
            )
            logger.info(f"Added lining column to {schema}.products")

    # Also update template_tenant schema
    if table_exists(conn, 'template_tenant', 'products'):
        if not column_exists(conn, 'template_tenant', 'products', 'lining'):
            op.add_column(
                'products',
                sa.Column(
                    'lining',
                    sa.String(100),
                    nullable=True,
                    comment='Lining type (FK product_attributes.linings)'
                ),
                schema='template_tenant'
            )
            logger.info("Added lining column to template_tenant.products")

    logger.info("Migration completed successfully")


def downgrade() -> None:
    conn = op.get_bind()
    schemas = get_user_schemas(conn)

    # Remove from all user schemas
    for schema in schemas:
        if table_exists(conn, schema, 'products') and column_exists(conn, schema, 'products', 'lining'):
            op.drop_column('products', 'lining', schema=schema)
            logger.info(f"Removed lining column from {schema}.products")

    # Remove from template_tenant
    if table_exists(conn, 'template_tenant', 'products') and column_exists(conn, 'template_tenant', 'products', 'lining'):
        op.drop_column('products', 'lining', schema='template_tenant')
        logger.info("Removed lining column from template_tenant.products")

    logger.info("Rollback completed successfully")
