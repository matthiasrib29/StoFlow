"""Add genders column to categories

Revision ID: 20251217_1300
Revises: 20251217_1250
Create Date: 2025-12-17 13:00:00.000000

Ajoute la colonne genders (ARRAY) a la table categories pour indiquer
quels genres sont disponibles pour chaque categorie.

Changes:
- Add genders column (TEXT[]) to product_attributes.categories
- Populate genders for all categories

Author: Claude
Date: 2025-12-17
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import ARRAY


# revision identifiers, used by Alembic.
revision = '20251217_1300'
down_revision = '20251217_1250'
branch_labels = None
depends_on = None


# Gender mappings by category (name_en -> genders array)
GENDER_MAPPINGS = {
    # Parents
    'clothing': ['men', 'women', 'boys', 'girls'],
    'tops': ['men', 'women', 'boys', 'girls'],
    'bottoms': ['men', 'women', 'boys', 'girls'],
    'outerwear': ['men', 'women', 'boys', 'girls'],
    'dresses-jumpsuits': ['women', 'girls'],
    'formalwear': ['men', 'women', 'boys', 'girls'],
    'sportswear': ['men', 'women', 'boys', 'girls'],

    # Tops (18)
    't-shirt': ['men', 'women', 'boys', 'girls'],
    'tank-top': ['men', 'women', 'boys', 'girls'],
    'shirt': ['men', 'women', 'boys', 'girls'],
    'blouse': ['women', 'girls'],
    'top': ['women', 'girls'],
    'bodysuit': ['women'],
    'corset': ['women'],
    'bustier': ['women'],
    'camisole': ['women'],
    'crop-top': ['women', 'girls'],
    'polo': ['men', 'women', 'boys', 'girls'],
    'sweater': ['men', 'women', 'boys', 'girls'],
    'cardigan': ['men', 'women', 'boys', 'girls'],
    'sweatshirt': ['men', 'women', 'boys', 'girls'],
    'hoodie': ['men', 'women', 'boys', 'girls'],
    'fleece': ['men', 'women', 'boys', 'girls'],
    'overshirt': ['men', 'women'],

    # Bottoms (12)
    'pants': ['men', 'women', 'boys', 'girls'],
    'jeans': ['men', 'women', 'boys', 'girls'],
    'chinos': ['men', 'women', 'boys', 'girls'],
    'joggers': ['men', 'women', 'boys', 'girls'],
    'cargo-pants': ['men', 'women', 'boys', 'girls'],
    'dress-pants': ['men', 'women', 'boys', 'girls'],
    'shorts': ['men', 'women', 'boys', 'girls'],
    'bermuda': ['men', 'women', 'boys', 'girls'],
    'skirt': ['women', 'girls'],
    'leggings': ['women', 'girls'],
    'culottes': ['women', 'girls'],

    # Outerwear (14)
    'jacket': ['men', 'women', 'boys', 'girls'],
    'bomber': ['men', 'women', 'boys', 'girls'],
    'puffer': ['men', 'women', 'boys', 'girls'],
    'coat': ['men', 'women', 'boys', 'girls'],
    'trench': ['men', 'women', 'boys', 'girls'],
    'parka': ['men', 'women', 'boys', 'girls'],
    'raincoat': ['men', 'women', 'boys', 'girls'],
    'windbreaker': ['men', 'women', 'boys', 'girls'],
    'blazer': ['men', 'women', 'boys', 'girls'],
    'vest': ['men', 'women', 'boys', 'girls'],
    'half-zip': ['men', 'women', 'boys', 'girls'],
    'cape': ['women', 'girls'],
    'poncho': ['men', 'women', 'boys', 'girls'],
    'kimono': ['women'],

    # Dresses & Jumpsuits (4)
    'dress': ['women', 'girls'],
    'jumpsuit': ['men', 'women', 'boys', 'girls'],
    'romper': ['women', 'girls'],
    'overalls': ['men', 'women', 'boys', 'girls'],

    # Formalwear (4)
    'suit': ['men', 'women'],
    'tuxedo': ['men'],
    'womens-suit': ['women'],
    'suit-vest': ['men', 'boys'],

    # Sportswear (8)
    'sports-bra': ['women', 'girls'],
    'sports-top': ['men', 'women', 'boys', 'girls'],
    'sports-shorts': ['men', 'women', 'boys', 'girls'],
    'sports-leggings': ['women', 'girls'],
    'tracksuit': ['men', 'women', 'boys', 'girls'],
    'swimsuit': ['men', 'women', 'boys', 'girls'],
    'bikini': ['women', 'girls'],
    'sports-jersey': ['men', 'women', 'boys', 'girls'],
}


def upgrade():
    """
    Add genders column to categories and populate values.
    """
    conn = op.get_bind()

    # 1. Check if column already exists
    column_exists = conn.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.columns
            WHERE table_schema = 'product_attributes'
            AND table_name = 'categories'
            AND column_name = 'genders'
        )
    """)).scalar()

    if column_exists:
        print("  ⏭️  genders column already exists, skipping creation")
    else:
        # 2. Add genders column (TEXT ARRAY)
        op.add_column(
            'categories',
            sa.Column(
                'genders',
                ARRAY(sa.String(20)),
                nullable=True,
                comment='Available genders for this category'
            ),
            schema='product_attributes'
        )
        print("  ✓ Added genders column to categories")

    # 3. Update genders for each category
    updated_count = 0
    for name_en, genders in GENDER_MAPPINGS.items():
        # Convert Python list to PostgreSQL array literal
        genders_array = '{' + ','.join(genders) + '}'

        result = conn.execute(
            text("""
                UPDATE product_attributes.categories
                SET genders = :genders
                WHERE name_en = :name_en
            """),
            {'genders': genders_array, 'name_en': name_en}
        )
        if result.rowcount > 0:
            updated_count += 1

    print(f"  ✓ Updated genders for {updated_count} categories")


def downgrade():
    """
    Remove genders column from categories.
    """
    conn = op.get_bind()

    # Check if column exists
    column_exists = conn.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.columns
            WHERE table_schema = 'product_attributes'
            AND table_name = 'categories'
            AND column_name = 'genders'
        )
    """)).scalar()

    if column_exists:
        op.drop_column('categories', 'genders', schema='product_attributes')
        print("  ✓ Dropped genders column from categories")
    else:
        print("  ⏭️  genders column doesn't exist, skipping")
