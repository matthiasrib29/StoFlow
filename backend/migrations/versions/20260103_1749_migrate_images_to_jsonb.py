"""migrate_images_to_jsonb

Revision ID: 3b220416f60d
Revises: c49a23dbbae1
Create Date: 2026-01-03 17:49:22.866017+01:00

Migration: Replace product_images table with JSONB column in products.

Structure JSONB:
[
    {"url": "https://...", "order": 0, "created_at": "2025-01-03T10:00:00Z"},
    {"url": "https://...", "order": 1, "created_at": "2025-01-03T11:00:00Z"}
]

Phase 1: Migrate data (this migration)
Phase 2: Drop product_images table (separate migration after verification)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '3b220416f60d'
down_revision: Union[str, None] = 'c49a23dbbae1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def get_user_schemas():
    """Get all user schemas (user_1, user_2, etc.)"""
    connection = op.get_bind()
    result = connection.execute(sa.text(
        "SELECT schema_name FROM information_schema.schemata "
        "WHERE schema_name LIKE 'user_%' ORDER BY schema_name"
    ))
    return [row[0] for row in result]


def table_exists(connection, schema: str, table: str) -> bool:
    """Check if a table exists in a specific schema."""
    result = connection.execute(sa.text(
        "SELECT EXISTS ("
        "  SELECT 1 FROM information_schema.tables "
        "  WHERE table_schema = :schema AND table_name = :table"
        ")"
    ), {"schema": schema, "table": table})
    return result.scalar()


def upgrade() -> None:
    """
    1. Convert images column from Text to JSONB
    2. Migrate data from product_images to JSONB
    """
    user_schemas = get_user_schemas()
    connection = op.get_bind()

    for schema in user_schemas:
        print(f"Processing schema: {schema}")

        # Skip if products table doesn't exist
        if not table_exists(connection, schema, 'products'):
            print(f"  ⚠️  Skipping {schema} - products table does not exist")
            continue

        # Step 1: Drop old images column (Text, was deprecated/empty)
        op.drop_column('products', 'images', schema=schema)

        # Step 2: Add new images column as JSONB
        op.add_column('products', sa.Column(
            'images',
            postgresql.JSONB,
            nullable=True,
            server_default='[]',
            comment='Product images as JSONB array [{url, order, created_at}]'
        ), schema=schema)

        # Step 3: Migrate data from product_images table to JSONB column
        connection.execute(sa.text(f"""
            UPDATE {schema}.products p
            SET images = COALESCE(
                (
                    SELECT jsonb_agg(
                        jsonb_build_object(
                            'url', pi.image_path,
                            'order', pi.display_order,
                            'created_at', to_char(pi.created_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"')
                        ) ORDER BY pi.display_order
                    )
                    FROM {schema}.product_images pi
                    WHERE pi.product_id = p.id
                ),
                '[]'::jsonb
            )
        """))

        # Count migrated images
        result = connection.execute(sa.text(f"""
            SELECT
                COUNT(*) as products_with_images,
                SUM(jsonb_array_length(images)) as total_images
            FROM {schema}.products
            WHERE jsonb_array_length(images) > 0
        """))
        row = result.fetchone()
        print(f"  ✓ Migrated: {row[1] or 0} images across {row[0] or 0} products")


def downgrade() -> None:
    """
    1. Recreate images as Text column
    2. Note: Data in product_images table is preserved (not dropped in upgrade)
    """
    user_schemas = get_user_schemas()

    for schema in user_schemas:
        print(f"Downgrading schema: {schema}")

        # Drop JSONB column
        op.drop_column('products', 'images', schema=schema)

        # Recreate as Text (original deprecated column)
        op.add_column('products', sa.Column(
            'images',
            sa.Text,
            nullable=True,
            comment='DEPRECATED: JSON array URLs. Use product_images relationship'
        ), schema=schema)
