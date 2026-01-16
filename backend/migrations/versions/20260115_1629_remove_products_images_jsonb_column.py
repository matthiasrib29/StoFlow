"""remove products.images jsonb column

Revision ID: e6514e0300aa
Revises: 077dc55ef8d0
Create Date: 2026-01-15 16:29:29.362381+01:00

This migration removes the deprecated products.images JSONB column.
All image data has been migrated to the product_images table in Phase 2.

The downgrade() function provides rollback capability by reconstructing
the JSONB column from the product_images table if needed.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'e6514e0300aa'
down_revision: Union[str, None] = '077dc55ef8d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def get_user_schemas(conn) -> list[str]:
    """Get all user schemas (user_*)."""
    result = conn.execute(
        text("""
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name LIKE 'user_%'
            ORDER BY schema_name
        """)
    )
    return [row[0] for row in result.fetchall()]


def column_exists(conn, schema: str, table: str, column: str) -> bool:
    """Check if column exists in table."""
    result = conn.execute(
        text("""
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = :schema
                AND table_name = :table
                AND column_name = :column
            )
        """),
        {"schema": schema, "table": table, "column": column}
    )
    return result.scalar()


def upgrade() -> None:
    """Drop the deprecated products.images JSONB column."""
    conn = op.get_bind()

    # Get all user schemas + template
    user_schemas = get_user_schemas(conn)
    if "template_tenant" not in user_schemas:
        user_schemas.append("template_tenant")

    for schema in user_schemas:
        # Check if column exists (idempotent)
        if not column_exists(conn, schema, "products", "images"):
            print(f"✓ Column {schema}.products.images already dropped, skipping")
            continue

        print(f"Dropping {schema}.products.images column...")

        # Drop the JSONB column
        conn.execute(text(f"""
            ALTER TABLE {schema}.products
            DROP COLUMN IF EXISTS images
        """))

        print(f"✓ Dropped {schema}.products.images")


def downgrade() -> None:
    """Restore the products.images JSONB column from product_images table."""
    conn = op.get_bind()

    # Get all user schemas + template
    user_schemas = get_user_schemas(conn)
    if "template_tenant" not in user_schemas:
        user_schemas.append("template_tenant")

    for schema in user_schemas:
        # Check if column already exists (idempotent)
        if column_exists(conn, schema, "products", "images"):
            print(f"✓ Column {schema}.products.images already exists, skipping")
            continue

        print(f"Restoring {schema}.products.images column...")

        # 1. Add the JSONB column back
        conn.execute(text(f"""
            ALTER TABLE {schema}.products
            ADD COLUMN images JSONB
        """))

        # 2. Reconstruct JSONB from product_images table
        # Format: [{"url": "...", "order": 0, "created_at": "..."}, ...]
        conn.execute(text(f"""
            UPDATE {schema}.products p
            SET images = subquery.images
            FROM (
                SELECT
                    product_id,
                    json_agg(
                        json_build_object(
                            'url', url,
                            'order', "order",
                            'created_at', created_at::text
                        )
                        ORDER BY "order"
                    ) as images
                FROM {schema}.product_images
                GROUP BY product_id
            ) subquery
            WHERE p.id = subquery.product_id
        """))

        print(f"✓ Restored {schema}.products.images with data from product_images table")
