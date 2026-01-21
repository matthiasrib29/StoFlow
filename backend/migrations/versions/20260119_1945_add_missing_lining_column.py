"""add_missing_lining_column

Revision ID: 7a8b9c0d1e2f
Revises: b08ea57b8754
Create Date: 2026-01-19 19:45:00.000000+01:00

This migration ensures the lining column exists in all products tables.
It's a safety net for when the original lining migration (20260113_1100)
was skipped due to alembic path issues.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '7a8b9c0d1e2f'
down_revision: Union[str, None] = 'b08ea57b8754'
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
    """Add lining column to products tables if missing."""
    conn = op.get_bind()
    schemas = get_user_schemas(conn)
    print(f"  [lining-fix] Found {len(schemas)} user schemas: {schemas}")

    added_count = 0

    # Add to all user schemas
    for schema in schemas:
        if not table_exists(conn, schema, 'products'):
            print(f"  - Table products does not exist in {schema}, skipping")
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
            print(f"  ✓ Added lining column to {schema}.products")
            added_count += 1
        else:
            print(f"  - lining column already exists in {schema}.products")

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
            print("  ✓ Added lining column to template_tenant.products")
            added_count += 1
        else:
            print("  - lining column already exists in template_tenant.products")

    print(f"  ✓ Lining fix completed ({added_count} columns added)")


def downgrade() -> None:
    """Remove lining column (should not be needed)."""
    pass  # Don't remove the column on downgrade - it's a safety migration
