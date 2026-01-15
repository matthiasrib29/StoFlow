"""update_product_images_table_add_metadata_columns

Revision ID: eb1acc1555f1
Revises: 077dc55ef8d0
Create Date: 2026-01-15 10:56:06.804189+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eb1acc1555f1'
down_revision: Union[str, None] = '077dc55ef8d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Update product_images table structure to match new ProductImage model.

    Changes:
    - Rename image_path → url
    - Rename display_order → order
    - Add is_label (boolean, NOT NULL, default False, indexed)
    - Add metadata columns: alt_text, tags, mime_type, file_size, width, height
    - Add updated_at timestamp

    Applied to all tenant schemas.
    """
    from sqlalchemy import text

    conn = op.get_bind()

    # Get all tenant schemas (user_X and template_tenant)
    result = conn.execute(text("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%' OR schema_name = 'template_tenant'
        ORDER BY schema_name
    """))

    schemas = [row[0] for row in result]

    print(f"\n🔄 Updating product_images table in {len(schemas)} schemas...")

    for schema in schemas:
        print(f"   Migrating {schema}...")

        # 1. Rename columns
        op.alter_column(
            'product_images',
            'image_path',
            new_column_name='url',
            schema=schema
        )

        op.alter_column(
            'product_images',
            'display_order',
            new_column_name='order',
            schema=schema
        )

        # 2. Add new columns
        op.add_column(
            'product_images',
            sa.Column('is_label', sa.Boolean(), nullable=False, server_default='false'),
            schema=schema
        )

        op.add_column(
            'product_images',
            sa.Column('alt_text', sa.String(500), nullable=True),
            schema=schema
        )

        op.add_column(
            'product_images',
            sa.Column('tags', sa.ARRAY(sa.String()), nullable=True),
            schema=schema
        )

        op.add_column(
            'product_images',
            sa.Column('mime_type', sa.String(100), nullable=True),
            schema=schema
        )

        op.add_column(
            'product_images',
            sa.Column('file_size', sa.Integer(), nullable=True),
            schema=schema
        )

        op.add_column(
            'product_images',
            sa.Column('width', sa.Integer(), nullable=True),
            schema=schema
        )

        op.add_column(
            'product_images',
            sa.Column('height', sa.Integer(), nullable=True),
            schema=schema
        )

        op.add_column(
            'product_images',
            sa.Column(
                'updated_at',
                sa.TIMESTAMP(timezone=True),
                nullable=False,
                server_default=sa.text('now()')
            ),
            schema=schema
        )

        # 3. Create index on is_label
        op.create_index(
            f'ix_{schema}_product_images_is_label',
            'product_images',
            ['is_label'],
            schema=schema
        )

        print(f"   ✅ {schema} migrated")

    print(f"✅ Migration complete for {len(schemas)} schemas\n")


def downgrade() -> None:
    """
    Revert product_images table to original structure.
    """
    from sqlalchemy import text

    conn = op.get_bind()

    # Get all tenant schemas
    result = conn.execute(text("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%' OR schema_name = 'template_tenant'
        ORDER BY schema_name
    """))

    schemas = [row[0] for row in result]

    print(f"\n🔄 Reverting product_images table in {len(schemas)} schemas...")

    for schema in schemas:
        print(f"   Reverting {schema}...")

        # 1. Drop index
        op.drop_index(
            f'ix_{schema}_product_images_is_label',
            table_name='product_images',
            schema=schema
        )

        # 2. Drop new columns
        op.drop_column('product_images', 'updated_at', schema=schema)
        op.drop_column('product_images', 'height', schema=schema)
        op.drop_column('product_images', 'width', schema=schema)
        op.drop_column('product_images', 'file_size', schema=schema)
        op.drop_column('product_images', 'mime_type', schema=schema)
        op.drop_column('product_images', 'tags', schema=schema)
        op.drop_column('product_images', 'alt_text', schema=schema)
        op.drop_column('product_images', 'is_label', schema=schema)

        # 3. Rename columns back
        op.alter_column(
            'product_images',
            'order',
            new_column_name='display_order',
            schema=schema
        )

        op.alter_column(
            'product_images',
            'url',
            new_column_name='image_path',
            schema=schema
        )

        print(f"   ✅ {schema} reverted")

    print(f"✅ Downgrade complete for {len(schemas)} schemas\n")
