"""Add vinted_id column to materials table

Revision ID: 20251218_1400
Revises: 20251218_1300_add_security_columns_to_users
Create Date: 2025-12-18 14:00:00

Business Rules:
- Add vinted_id column to product_attributes.materials
- Populate with Vinted material IDs from Vinted API
- Mapping based on name_en → vinted_id
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251218_1400'
down_revision = '20251218_1300'
branch_labels = None
depends_on = None


# Vinted material mapping (name_en -> vinted_id)
# Source: Vinted API /api/v2/item_upload/items attributes
VINTED_MATERIAL_MAPPING = {
    # Common clothing materials
    'Cotton': 44,
    'Polyester': 45,
    'Wool': 46,
    'Viscose': 48,
    'Silk': 49,
    'Nylon': 52,
    'Elastane': 53,
    'Spandex': 53,  # Same as Elastane
    'Linen': 146,
    'Fleece': 120,
    'Merino': 121,
    'Alpaca': 122,
    'Cashmere': 123,
    'Acrylic': 149,
    'Mohair': 152,

    # Leather & synthetics
    'Leather': 43,
    'Faux Leather': 447,
    'Synthetic Leather': 447,
    'Patent Leather': 305,
    'Suede': 298,

    # Denim & canvas
    'Denim': 303,
    'Canvas': 441,

    # Special fabrics
    'Satin': 311,
    'Velvet': 466,
    'Corduroy': 299,
    'Tweed': 465,
    'Flannel': 451,
    'Lace': 455,
    'Tulle': 464,
    'Chiffon': 444,
    'Knit': 456,
    'Felt': 448,
    'Plush': 177,
    'Neoprene': 178,
    'Sequin': 226,

    # Natural materials
    'Down': 445,
    'Faux Fur': 446,
    'Bamboo': 440,
    'Jute': 454,

    # Other materials
    'Rubber': 301,
    'Latex': 302,
    'Plastic': 300,
    'Silicone': 470,

    # Metals & precious
    'Metal': 457,
    'Steel': 468,
    'Silver': 461,
    'Gold': 453,

    # Other
    'Wood': 467,
    'Ceramic': 443,
    'Glass': 452,
    'Porcelain': 459,
    'Paper': 458,
    'Cardboard': 442,
    'Foam': 449,
    'Rattan': 460,
    'Stone': 462,
    'Straw': 463,
}


def upgrade() -> None:
    connection = op.get_bind()

    # Check if column already exists
    result = connection.execute(sa.text("""
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = 'product_attributes'
        AND table_name = 'materials'
        AND column_name = 'vinted_id'
    """))
    column_exists = result.fetchone() is not None

    if not column_exists:
        # Add vinted_id column to materials table
        op.add_column(
            'materials',
            sa.Column('vinted_id', sa.Integer(), nullable=True, comment='Vinted material ID'),
            schema='product_attributes'
        )

        # Create index for faster lookups
        op.create_index(
            'ix_materials_vinted_id',
            'materials',
            ['vinted_id'],
            schema='product_attributes'
        )
    else:
        print("  ⏭️  vinted_id column already exists in materials, skipping")

    # Populate vinted_id based on name_en mapping
    connection = op.get_bind()

    for name_en, vinted_id in VINTED_MATERIAL_MAPPING.items():
        connection.execute(
            sa.text("""
                UPDATE product_attributes.materials
                SET vinted_id = :vinted_id
                WHERE LOWER(name_en) = LOWER(:name_en)
            """),
            {'vinted_id': vinted_id, 'name_en': name_en}
        )

    # Log unmapped materials
    result = connection.execute(
        sa.text("""
            SELECT name_en FROM product_attributes.materials
            WHERE vinted_id IS NULL
            ORDER BY name_en
        """)
    )
    unmapped = [row[0] for row in result]
    if unmapped:
        print(f"Materials without Vinted mapping: {unmapped}")


def downgrade() -> None:
    # Drop index
    op.drop_index(
        'ix_materials_vinted_id',
        table_name='materials',
        schema='product_attributes'
    )

    # Drop column
    op.drop_column('materials', 'vinted_id', schema='product_attributes')
