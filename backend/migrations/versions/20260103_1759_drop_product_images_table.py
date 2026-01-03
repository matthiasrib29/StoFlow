"""drop_product_images_table

Revision ID: 9183cce67eb2
Revises: 3b220416f60d
Create Date: 2026-01-03 17:59:54.733384+01:00

Migration: Drop the product_images table after successful JSONB migration.

IMPORTANT: This migration should only be run AFTER verifying that:
1. migrate_images_to_jsonb migration ran successfully
2. All images are accessible via Product.images JSONB column
3. No code references ProductImage model anymore
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9183cce67eb2'
down_revision: Union[str, None] = '3b220416f60d'
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


def table_exists(schema: str, table: str) -> bool:
    """Check if a table exists in a specific schema."""
    connection = op.get_bind()
    result = connection.execute(sa.text(
        "SELECT EXISTS ("
        "  SELECT 1 FROM information_schema.tables "
        "  WHERE table_schema = :schema AND table_name = :table"
        ")"
    ), {"schema": schema, "table": table})
    return result.scalar()


def upgrade() -> None:
    """
    Drop product_images table from all user schemas.

    The data has been migrated to products.images JSONB column.
    """
    user_schemas = get_user_schemas()

    for schema in user_schemas:
        # Skip if product_images table doesn't exist
        if not table_exists(schema, 'product_images'):
            print(f"  ⚠️  Skipping {schema} - product_images table does not exist")
            continue

        print(f"Dropping product_images table from schema: {schema}")

        # Drop the index first
        op.drop_index(
            'idx_product_image_product_id_order',
            table_name='product_images',
            schema=schema,
            if_exists=True
        )

        # Drop the table
        op.drop_table('product_images', schema=schema)

        print(f"  ✓ product_images table dropped from {schema}")


def downgrade() -> None:
    """
    Recreate product_images table in all user schemas.

    NOTE: This does NOT restore the data, only the table structure.
    Data would need to be manually migrated from products.images JSONB.
    """
    user_schemas = get_user_schemas()

    for schema in user_schemas:
        print(f"Recreating product_images table in schema: {schema}")

        op.create_table(
            'product_images',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('product_id', sa.Integer(), nullable=False),
            sa.Column('image_path', sa.String(1000), nullable=False),
            sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(
                ['product_id'], [f'{schema}.products.id'],
                ondelete='CASCADE'
            ),
            sa.PrimaryKeyConstraint('id'),
            schema=schema
        )

        # Create index
        op.create_index(
            'idx_product_image_product_id_order',
            'product_images',
            ['product_id', 'display_order'],
            schema=schema
        )

        print(f"  ✓ product_images table recreated in {schema}")
