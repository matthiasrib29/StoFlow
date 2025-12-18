"""add_all_missing_marketplace_columns

Revision ID: 0aefcf4d5daf
Revises: 182978057ce8
Create Date: 2025-12-08 15:38:26.188288+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0aefcf4d5daf'
down_revision: Union[str, None] = '182978057ce8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ===== ADD MISSING COLUMNS TO COLORS TABLE =====
    op.add_column('colors', sa.Column('name_nl', sa.String(100), nullable=True, comment='Nom de la couleur (NL)'), schema='product_attributes')
    op.add_column('colors', sa.Column('name_pl', sa.String(100), nullable=True, comment='Nom de la couleur (PL)'), schema='product_attributes')
    op.add_column('colors', sa.Column('etsy_2', sa.BigInteger(), nullable=True, comment='ID Etsy pour mapping couleurs'), schema='product_attributes')
    op.add_column('colors', sa.Column('vinted_id', sa.BigInteger(), nullable=True, comment='ID Vinted'), schema='product_attributes')
    op.add_column('colors', sa.Column('ebay_gb_color', sa.Text(), nullable=True, comment='Valeur couleur eBay UK'), schema='product_attributes')

    # ===== ADD MISSING COLUMNS TO CONDITIONS TABLE =====
    op.add_column('conditions', sa.Column('vinted_id', sa.BigInteger(), nullable=True, comment='ID Vinted'), schema='product_attributes')
    op.add_column('conditions', sa.Column('ebay_condition', sa.BigInteger(), nullable=True, comment='ID eBay condition'), schema='product_attributes')
    op.add_column('conditions', sa.Column('coefficient', sa.Numeric(5, 3), nullable=True, server_default='1.0', comment='Coefficient de pricing (0.8-1.0)'), schema='product_attributes')
    op.add_column('conditions', sa.Column('description_de', sa.String(50), nullable=True, comment='Description en allemand'), schema='product_attributes')
    op.add_column('conditions', sa.Column('description_it', sa.String(50), nullable=True, comment='Description en italien'), schema='product_attributes')
    op.add_column('conditions', sa.Column('description_es', sa.String(50), nullable=True, comment='Description en espagnol'), schema='product_attributes')
    op.add_column('conditions', sa.Column('description_nl', sa.String(50), nullable=True, comment='Description en néerlandais'), schema='product_attributes')
    op.add_column('conditions', sa.Column('description_pl', sa.String(50), nullable=True, comment='Description en polonais'), schema='product_attributes')

    # ===== ADD MISSING COLUMNS TO FITS TABLE =====
    op.add_column('fits', sa.Column('name_nl', sa.String(100), nullable=True, comment='Nom de la coupe (NL)'), schema='product_attributes')
    op.add_column('fits', sa.Column('name_pl', sa.String(100), nullable=True, comment='Nom de la coupe (PL)'), schema='product_attributes')
    op.add_column('fits', sa.Column('etsy_406', sa.String(100), nullable=True, comment='ID Etsy 406'), schema='product_attributes')
    op.add_column('fits', sa.Column('etsy_407', sa.String(100), nullable=True, comment='ID Etsy 407'), schema='product_attributes')
    op.add_column('fits', sa.Column('ebay_gb_fit', sa.String(100), nullable=True, comment='Valeur coupe eBay UK'), schema='product_attributes')
    op.add_column('fits', sa.Column('coefficient', sa.Numeric(5, 3), nullable=True, server_default='1.0', comment='Coefficient de pricing (0.9-1.2)'), schema='product_attributes')

    # ===== ADD MISSING COLUMNS TO GENDERS TABLE =====
    op.add_column('genders', sa.Column('name_nl', sa.String(100), nullable=True, comment='Nom du genre (NL)'), schema='product_attributes')
    op.add_column('genders', sa.Column('name_pl', sa.String(100), nullable=True, comment='Nom du genre (PL)'), schema='product_attributes')

    # ===== ADD MISSING COLUMNS TO MATERIALS TABLE =====
    op.add_column('materials', sa.Column('name_nl', sa.String(100), nullable=True, comment='Nom de la matière (NL)'), schema='product_attributes')
    op.add_column('materials', sa.Column('name_pl', sa.String(100), nullable=True, comment='Nom de la matière (PL)'), schema='product_attributes')
    op.add_column('materials', sa.Column('etsy_357', sa.BigInteger(), nullable=True, comment='ID Etsy pour mapping matières'), schema='product_attributes')
    op.add_column('materials', sa.Column('ebay_gb_material', sa.String(255), nullable=True, comment='Valeur matière eBay UK'), schema='product_attributes')

    # ===== ADD MISSING COLUMNS TO SEASONS TABLE =====
    op.add_column('seasons', sa.Column('name_nl', sa.String(100), nullable=True, comment='Nom de la saison (NL)'), schema='product_attributes')
    op.add_column('seasons', sa.Column('name_pl', sa.String(100), nullable=True, comment='Nom de la saison (PL)'), schema='product_attributes')

    # ===== ADD MISSING COLUMNS TO SIZES TABLE =====
    op.add_column('sizes', sa.Column('vinted_woman_title', sa.String(50), nullable=True, comment='Titre Vinted Women'), schema='product_attributes')
    op.add_column('sizes', sa.Column('vinted_woman_id', sa.Integer(), nullable=True, comment='ID Vinted Women'), schema='product_attributes')
    op.add_column('sizes', sa.Column('vinted_man_top_title', sa.String(50), nullable=True, comment='Titre Vinted Men Top'), schema='product_attributes')
    op.add_column('sizes', sa.Column('vinted_man_top_id', sa.Integer(), nullable=True, comment='ID Vinted Men Top'), schema='product_attributes')
    op.add_column('sizes', sa.Column('vinted_man_bottom_title', sa.String(50), nullable=True, comment='Titre Vinted Men Bottom'), schema='product_attributes')
    op.add_column('sizes', sa.Column('vinted_man_bottom_id', sa.Integer(), nullable=True, comment='ID Vinted Men Bottom'), schema='product_attributes')
    op.add_column('sizes', sa.Column('etsy_296', sa.BigInteger(), nullable=True, comment='ID Etsy 296 (category-specific)'), schema='product_attributes')
    op.add_column('sizes', sa.Column('etsy_454', sa.BigInteger(), nullable=True, comment='ID Etsy 454 (category-specific)'), schema='product_attributes')
    op.add_column('sizes', sa.Column('ebay_gb_size', sa.String(255), nullable=True, comment='Taille standard eBay UK'), schema='product_attributes')
    op.add_column('sizes', sa.Column('ebay_gb_waist_size', sa.String(255), nullable=True, comment='Tour de taille eBay UK'), schema='product_attributes')
    op.add_column('sizes', sa.Column('ebay_gb_inside_leg', sa.String(255), nullable=True, comment='Entrejambe eBay UK'), schema='product_attributes')


def downgrade() -> None:
    # ===== REMOVE ADDED COLUMNS FROM SIZES TABLE =====
    op.drop_column('sizes', 'ebay_gb_inside_leg', schema='product_attributes')
    op.drop_column('sizes', 'ebay_gb_waist_size', schema='product_attributes')
    op.drop_column('sizes', 'ebay_gb_size', schema='product_attributes')
    op.drop_column('sizes', 'etsy_454', schema='product_attributes')
    op.drop_column('sizes', 'etsy_296', schema='product_attributes')
    op.drop_column('sizes', 'vinted_man_bottom_id', schema='product_attributes')
    op.drop_column('sizes', 'vinted_man_bottom_title', schema='product_attributes')
    op.drop_column('sizes', 'vinted_man_top_id', schema='product_attributes')
    op.drop_column('sizes', 'vinted_man_top_title', schema='product_attributes')
    op.drop_column('sizes', 'vinted_woman_id', schema='product_attributes')
    op.drop_column('sizes', 'vinted_woman_title', schema='product_attributes')

    # ===== REMOVE ADDED COLUMNS FROM SEASONS TABLE =====
    op.drop_column('seasons', 'name_pl', schema='product_attributes')
    op.drop_column('seasons', 'name_nl', schema='product_attributes')

    # ===== REMOVE ADDED COLUMNS FROM MATERIALS TABLE =====
    op.drop_column('materials', 'ebay_gb_material', schema='product_attributes')
    op.drop_column('materials', 'etsy_357', schema='product_attributes')
    op.drop_column('materials', 'name_pl', schema='product_attributes')
    op.drop_column('materials', 'name_nl', schema='product_attributes')

    # ===== REMOVE ADDED COLUMNS FROM GENDERS TABLE =====
    op.drop_column('genders', 'name_pl', schema='product_attributes')
    op.drop_column('genders', 'name_nl', schema='product_attributes')

    # ===== REMOVE ADDED COLUMNS FROM FITS TABLE =====
    op.drop_column('fits', 'coefficient', schema='product_attributes')
    op.drop_column('fits', 'ebay_gb_fit', schema='product_attributes')
    op.drop_column('fits', 'etsy_407', schema='product_attributes')
    op.drop_column('fits', 'etsy_406', schema='product_attributes')
    op.drop_column('fits', 'name_pl', schema='product_attributes')
    op.drop_column('fits', 'name_nl', schema='product_attributes')

    # ===== REMOVE ADDED COLUMNS FROM CONDITIONS TABLE =====
    op.drop_column('conditions', 'description_pl', schema='product_attributes')
    op.drop_column('conditions', 'description_nl', schema='product_attributes')
    op.drop_column('conditions', 'description_es', schema='product_attributes')
    op.drop_column('conditions', 'description_it', schema='product_attributes')
    op.drop_column('conditions', 'description_de', schema='product_attributes')
    op.drop_column('conditions', 'coefficient', schema='product_attributes')
    op.drop_column('conditions', 'ebay_condition', schema='product_attributes')
    op.drop_column('conditions', 'vinted_id', schema='product_attributes')

    # ===== REMOVE ADDED COLUMNS FROM COLORS TABLE =====
    op.drop_column('colors', 'ebay_gb_color', schema='product_attributes')
    op.drop_column('colors', 'vinted_id', schema='product_attributes')
    op.drop_column('colors', 'etsy_2', schema='product_attributes')
    op.drop_column('colors', 'name_pl', schema='product_attributes')
    op.drop_column('colors', 'name_nl', schema='product_attributes')
