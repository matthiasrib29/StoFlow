"""create_ebay_category_mapping_table

Revision ID: b58854908d67
Revises: 20251219_1500
Create Date: 2025-12-22 10:13:59.696864+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b58854908d67'
down_revision: Union[str, None] = '46909e0170ba'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create ebay_category_mapping table in public schema
    op.create_table(
        'ebay_category_mapping',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('my_category', sa.String(100), nullable=False, comment='StoFlow category name'),
        sa.Column('my_gender', sa.String(20), nullable=False, comment='Gender: men or women'),
        sa.Column('ebay_category_id', sa.Integer(), nullable=False, comment='eBay category ID (global for all EU marketplaces)'),
        sa.Column('ebay_name_en', sa.String(100), nullable=False, comment='eBay category name in English'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('my_category', 'my_gender', name='uq_ebay_category_mapping'),
        schema='public'
    )

    # Create index for lookup
    op.create_index(
        'idx_ebay_category_lookup',
        'ebay_category_mapping',
        ['my_category', 'my_gender'],
        schema='public'
    )

    # Insert mapping data
    ebay_mapping = sa.table(
        'ebay_category_mapping',
        sa.column('my_category', sa.String),
        sa.column('my_gender', sa.String),
        sa.column('ebay_category_id', sa.Integer),
        sa.column('ebay_name_en', sa.String),
        schema='public'
    )

    op.bulk_insert(ebay_mapping, [
        # T-shirts & Tops
        {'my_category': 't-shirt', 'my_gender': 'men', 'ebay_category_id': 15687, 'ebay_name_en': 'T-Shirts'},
        {'my_category': 't-shirt', 'my_gender': 'women', 'ebay_category_id': 53159, 'ebay_name_en': 'Tops & Shirts'},
        {'my_category': 'tank-top', 'my_gender': 'men', 'ebay_category_id': 15687, 'ebay_name_en': 'T-Shirts'},
        {'my_category': 'tank-top', 'my_gender': 'women', 'ebay_category_id': 53159, 'ebay_name_en': 'Tops & Shirts'},
        {'my_category': 'shirt', 'my_gender': 'men', 'ebay_category_id': 57990, 'ebay_name_en': 'Casual Shirts & Tops'},
        {'my_category': 'shirt', 'my_gender': 'women', 'ebay_category_id': 53159, 'ebay_name_en': 'Tops & Shirts'},
        {'my_category': 'blouse', 'my_gender': 'women', 'ebay_category_id': 53159, 'ebay_name_en': 'Tops & Shirts'},
        {'my_category': 'top', 'my_gender': 'women', 'ebay_category_id': 53159, 'ebay_name_en': 'Tops & Shirts'},
        {'my_category': 'bodysuit', 'my_gender': 'women', 'ebay_category_id': 53159, 'ebay_name_en': 'Tops & Shirts'},
        {'my_category': 'corset', 'my_gender': 'women', 'ebay_category_id': 53159, 'ebay_name_en': 'Tops & Shirts'},
        {'my_category': 'bustier', 'my_gender': 'women', 'ebay_category_id': 53159, 'ebay_name_en': 'Tops & Shirts'},
        {'my_category': 'camisole', 'my_gender': 'women', 'ebay_category_id': 53159, 'ebay_name_en': 'Tops & Shirts'},
        {'my_category': 'crop-top', 'my_gender': 'women', 'ebay_category_id': 53159, 'ebay_name_en': 'Tops & Shirts'},

        # Polos
        {'my_category': 'polo', 'my_gender': 'men', 'ebay_category_id': 185101, 'ebay_name_en': 'Polos'},
        {'my_category': 'polo', 'my_gender': 'women', 'ebay_category_id': 53159, 'ebay_name_en': 'Tops & Shirts'},

        # Sweaters & Cardigans
        {'my_category': 'sweater', 'my_gender': 'men', 'ebay_category_id': 11484, 'ebay_name_en': 'Jumpers & Cardigans'},
        {'my_category': 'sweater', 'my_gender': 'women', 'ebay_category_id': 63866, 'ebay_name_en': 'Jumpers & Cardigans'},
        {'my_category': 'cardigan', 'my_gender': 'men', 'ebay_category_id': 11484, 'ebay_name_en': 'Jumpers & Cardigans'},
        {'my_category': 'cardigan', 'my_gender': 'women', 'ebay_category_id': 63866, 'ebay_name_en': 'Jumpers & Cardigans'},

        # Hoodies & Sweatshirts
        {'my_category': 'sweatshirt', 'my_gender': 'men', 'ebay_category_id': 155183, 'ebay_name_en': 'Hoodies & Sweatshirts'},
        {'my_category': 'sweatshirt', 'my_gender': 'women', 'ebay_category_id': 155226, 'ebay_name_en': 'Hoodies & Sweatshirts'},
        {'my_category': 'hoodie', 'my_gender': 'men', 'ebay_category_id': 155183, 'ebay_name_en': 'Hoodies & Sweatshirts'},
        {'my_category': 'hoodie', 'my_gender': 'women', 'ebay_category_id': 155226, 'ebay_name_en': 'Hoodies & Sweatshirts'},
        {'my_category': 'fleece', 'my_gender': 'men', 'ebay_category_id': 155183, 'ebay_name_en': 'Hoodies & Sweatshirts'},
        {'my_category': 'fleece', 'my_gender': 'women', 'ebay_category_id': 155226, 'ebay_name_en': 'Hoodies & Sweatshirts'},
        {'my_category': 'half-zip', 'my_gender': 'men', 'ebay_category_id': 155183, 'ebay_name_en': 'Hoodies & Sweatshirts'},
        {'my_category': 'half-zip', 'my_gender': 'women', 'ebay_category_id': 155226, 'ebay_name_en': 'Hoodies & Sweatshirts'},

        # Overshirts
        {'my_category': 'overshirt', 'my_gender': 'men', 'ebay_category_id': 57990, 'ebay_name_en': 'Casual Shirts & Tops'},
        {'my_category': 'overshirt', 'my_gender': 'women', 'ebay_category_id': 53159, 'ebay_name_en': 'Tops & Shirts'},

        # Pants & Trousers
        {'my_category': 'pants', 'my_gender': 'men', 'ebay_category_id': 57989, 'ebay_name_en': 'Trousers'},
        {'my_category': 'pants', 'my_gender': 'women', 'ebay_category_id': 63863, 'ebay_name_en': 'Trousers'},
        {'my_category': 'chinos', 'my_gender': 'men', 'ebay_category_id': 57989, 'ebay_name_en': 'Trousers'},
        {'my_category': 'chinos', 'my_gender': 'women', 'ebay_category_id': 63863, 'ebay_name_en': 'Trousers'},
        {'my_category': 'cargo-pants', 'my_gender': 'men', 'ebay_category_id': 57989, 'ebay_name_en': 'Trousers'},
        {'my_category': 'cargo-pants', 'my_gender': 'women', 'ebay_category_id': 63863, 'ebay_name_en': 'Trousers'},
        {'my_category': 'dress-pants', 'my_gender': 'men', 'ebay_category_id': 57989, 'ebay_name_en': 'Trousers'},
        {'my_category': 'dress-pants', 'my_gender': 'women', 'ebay_category_id': 63863, 'ebay_name_en': 'Trousers'},
        {'my_category': 'culottes', 'my_gender': 'women', 'ebay_category_id': 63863, 'ebay_name_en': 'Trousers'},
        {'my_category': 'overalls', 'my_gender': 'men', 'ebay_category_id': 57989, 'ebay_name_en': 'Trousers'},

        # Jeans
        {'my_category': 'jeans', 'my_gender': 'men', 'ebay_category_id': 11483, 'ebay_name_en': 'Jeans'},
        {'my_category': 'jeans', 'my_gender': 'women', 'ebay_category_id': 11554, 'ebay_name_en': 'Jeans'},

        # Joggers (Activewear)
        {'my_category': 'joggers', 'my_gender': 'men', 'ebay_category_id': 260956, 'ebay_name_en': 'Activewear Trousers'},
        {'my_category': 'joggers', 'my_gender': 'women', 'ebay_category_id': 260954, 'ebay_name_en': 'Activewear Trousers'},

        # Shorts
        {'my_category': 'shorts', 'my_gender': 'men', 'ebay_category_id': 15689, 'ebay_name_en': 'Shorts'},
        {'my_category': 'shorts', 'my_gender': 'women', 'ebay_category_id': 11555, 'ebay_name_en': 'Shorts'},
        {'my_category': 'bermuda', 'my_gender': 'men', 'ebay_category_id': 15689, 'ebay_name_en': 'Shorts'},
        {'my_category': 'bermuda', 'my_gender': 'women', 'ebay_category_id': 11555, 'ebay_name_en': 'Shorts'},

        # Skirts & Leggings
        {'my_category': 'skirt', 'my_gender': 'women', 'ebay_category_id': 63864, 'ebay_name_en': 'Skirts'},
        {'my_category': 'leggings', 'my_gender': 'women', 'ebay_category_id': 169001, 'ebay_name_en': 'Leggings'},

        # Jackets & Coats
        {'my_category': 'jacket', 'my_gender': 'men', 'ebay_category_id': 57988, 'ebay_name_en': 'Coats Jackets & Waistcoats'},
        {'my_category': 'jacket', 'my_gender': 'women', 'ebay_category_id': 63862, 'ebay_name_en': 'Coats Jackets & Waistcoats'},
        {'my_category': 'bomber', 'my_gender': 'men', 'ebay_category_id': 57988, 'ebay_name_en': 'Coats Jackets & Waistcoats'},
        {'my_category': 'bomber', 'my_gender': 'women', 'ebay_category_id': 63862, 'ebay_name_en': 'Coats Jackets & Waistcoats'},
        {'my_category': 'puffer', 'my_gender': 'men', 'ebay_category_id': 57988, 'ebay_name_en': 'Coats Jackets & Waistcoats'},
        {'my_category': 'puffer', 'my_gender': 'women', 'ebay_category_id': 63862, 'ebay_name_en': 'Coats Jackets & Waistcoats'},
        {'my_category': 'coat', 'my_gender': 'men', 'ebay_category_id': 57988, 'ebay_name_en': 'Coats Jackets & Waistcoats'},
        {'my_category': 'coat', 'my_gender': 'women', 'ebay_category_id': 63862, 'ebay_name_en': 'Coats Jackets & Waistcoats'},
        {'my_category': 'trench', 'my_gender': 'men', 'ebay_category_id': 57988, 'ebay_name_en': 'Coats Jackets & Waistcoats'},
        {'my_category': 'trench', 'my_gender': 'women', 'ebay_category_id': 63862, 'ebay_name_en': 'Coats Jackets & Waistcoats'},
        {'my_category': 'parka', 'my_gender': 'men', 'ebay_category_id': 57988, 'ebay_name_en': 'Coats Jackets & Waistcoats'},
        {'my_category': 'parka', 'my_gender': 'women', 'ebay_category_id': 63862, 'ebay_name_en': 'Coats Jackets & Waistcoats'},
        {'my_category': 'raincoat', 'my_gender': 'men', 'ebay_category_id': 57988, 'ebay_name_en': 'Coats Jackets & Waistcoats'},
        {'my_category': 'raincoat', 'my_gender': 'women', 'ebay_category_id': 63862, 'ebay_name_en': 'Coats Jackets & Waistcoats'},
        {'my_category': 'windbreaker', 'my_gender': 'men', 'ebay_category_id': 57988, 'ebay_name_en': 'Coats Jackets & Waistcoats'},
        {'my_category': 'windbreaker', 'my_gender': 'women', 'ebay_category_id': 63862, 'ebay_name_en': 'Coats Jackets & Waistcoats'},
        {'my_category': 'blazer', 'my_gender': 'men', 'ebay_category_id': 57988, 'ebay_name_en': 'Coats Jackets & Waistcoats'},
        {'my_category': 'blazer', 'my_gender': 'women', 'ebay_category_id': 63862, 'ebay_name_en': 'Coats Jackets & Waistcoats'},
        {'my_category': 'vest', 'my_gender': 'men', 'ebay_category_id': 57988, 'ebay_name_en': 'Coats Jackets & Waistcoats'},
        {'my_category': 'vest', 'my_gender': 'women', 'ebay_category_id': 63862, 'ebay_name_en': 'Coats Jackets & Waistcoats'},
        {'my_category': 'cape', 'my_gender': 'women', 'ebay_category_id': 63862, 'ebay_name_en': 'Coats Jackets & Waistcoats'},
        {'my_category': 'poncho', 'my_gender': 'men', 'ebay_category_id': 57988, 'ebay_name_en': 'Coats Jackets & Waistcoats'},
        {'my_category': 'poncho', 'my_gender': 'women', 'ebay_category_id': 63862, 'ebay_name_en': 'Coats Jackets & Waistcoats'},
        {'my_category': 'kimono', 'my_gender': 'women', 'ebay_category_id': 63862, 'ebay_name_en': 'Coats Jackets & Waistcoats'},
        {'my_category': 'suit-vest', 'my_gender': 'men', 'ebay_category_id': 57988, 'ebay_name_en': 'Coats Jackets & Waistcoats'},

        # Dresses & Jumpsuits
        {'my_category': 'dress', 'my_gender': 'women', 'ebay_category_id': 63861, 'ebay_name_en': 'Dresses'},
        {'my_category': 'jumpsuit', 'my_gender': 'women', 'ebay_category_id': 3009, 'ebay_name_en': 'Jumpsuits & Playsuits'},
        {'my_category': 'romper', 'my_gender': 'women', 'ebay_category_id': 3009, 'ebay_name_en': 'Jumpsuits & Playsuits'},
        {'my_category': 'overalls', 'my_gender': 'women', 'ebay_category_id': 3009, 'ebay_name_en': 'Jumpsuits & Playsuits'},

        # Suits
        {'my_category': 'suit', 'my_gender': 'men', 'ebay_category_id': 3001, 'ebay_name_en': 'Suits & Tailoring'},
        {'my_category': 'suit', 'my_gender': 'women', 'ebay_category_id': 63865, 'ebay_name_en': 'Suits & Suit Separates'},
        {'my_category': 'tuxedo', 'my_gender': 'men', 'ebay_category_id': 3001, 'ebay_name_en': 'Suits & Tailoring'},
        {'my_category': 'womens-suit', 'my_gender': 'women', 'ebay_category_id': 63865, 'ebay_name_en': 'Suits & Suit Separates'},

        # Activewear / Sports
        {'my_category': 'sports-bra', 'my_gender': 'women', 'ebay_category_id': 185082, 'ebay_name_en': 'Activewear Tops'},
        {'my_category': 'sports-top', 'my_gender': 'men', 'ebay_category_id': 185076, 'ebay_name_en': 'Activewear Tops'},
        {'my_category': 'sports-top', 'my_gender': 'women', 'ebay_category_id': 185082, 'ebay_name_en': 'Activewear Tops'},
        {'my_category': 'sports-shorts', 'my_gender': 'men', 'ebay_category_id': 260957, 'ebay_name_en': 'Activewear Shorts'},
        {'my_category': 'sports-shorts', 'my_gender': 'women', 'ebay_category_id': 260955, 'ebay_name_en': 'Activewear Shorts'},
        {'my_category': 'sports-leggings', 'my_gender': 'women', 'ebay_category_id': 260954, 'ebay_name_en': 'Activewear Trousers'},
        {'my_category': 'sports-jersey', 'my_gender': 'men', 'ebay_category_id': 185076, 'ebay_name_en': 'Activewear Tops'},
        {'my_category': 'sports-jersey', 'my_gender': 'women', 'ebay_category_id': 185082, 'ebay_name_en': 'Activewear Tops'},
        {'my_category': 'tracksuit', 'my_gender': 'men', 'ebay_category_id': 185708, 'ebay_name_en': 'Tracksuits & Sets'},
        {'my_category': 'tracksuit', 'my_gender': 'women', 'ebay_category_id': 185084, 'ebay_name_en': 'Tracksuits & Sets'},

        # Swimwear
        {'my_category': 'swimsuit', 'my_gender': 'men', 'ebay_category_id': 15690, 'ebay_name_en': 'Swimwear'},
        {'my_category': 'swimsuit', 'my_gender': 'women', 'ebay_category_id': 63867, 'ebay_name_en': 'Swimwear'},
        {'my_category': 'bikini', 'my_gender': 'women', 'ebay_category_id': 63867, 'ebay_name_en': 'Swimwear'},
    ])


def downgrade() -> None:
    op.drop_index('idx_ebay_category_lookup', table_name='ebay_category_mapping', schema='public')
    op.drop_table('ebay_category_mapping', schema='public')
