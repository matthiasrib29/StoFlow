"""create_clothing_prices_table

Revision ID: c3d4e5f6g7h8
Revises: b2c3d4e5f6g7
Create Date: 2025-12-08 19:26:00.000000+01:00

Business Rules (2025-12-08):
- Table pour pricing automatique (calcul prix selon brand + category + condition + rarity + quality)
- Formule: prix_final = base_price × coeff_condition × coeff_rarity × coeff_quality
- Prix minimum: 5€, arrondi: 0.50€
- Compatible avec PostEditFlet logic (adjust_price)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import DECIMAL


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6g7h8'
down_revision: Union[str, None] = 'b2c3d4e5f6g7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Créer table clothing_prices pour pricing automatique.

    Business Rules:
    - base_price: Prix de base pour une combinaison brand + category
    - Clé primaire composite: (brand, category)
    - FK vers product_attributes.brands et product_attributes.categories
    - Prix en euros (DECIMAL 10,2)
    """
    op.create_table(
        'clothing_prices',
        sa.Column(
            'brand',
            sa.String(100),
            nullable=False,
            comment="Marque (FK product_attributes.brands.name)"
        ),
        sa.Column(
            'category',
            sa.String(255),
            nullable=False,
            comment="Catégorie (FK product_attributes.categories.name_en)"
        ),
        sa.Column(
            'base_price',
            DECIMAL(10, 2),
            nullable=False,
            comment="Prix de base en euros"
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            comment="Date de dernière mise à jour du prix"
        ),
        sa.PrimaryKeyConstraint('brand', 'category', name='pk_clothing_prices'),
        sa.ForeignKeyConstraint(
            ['brand'],
            ['product_attributes.brands.name'],
            onupdate='CASCADE',
            ondelete='CASCADE',
            name='fk_clothing_prices_brand'
        ),
        sa.ForeignKeyConstraint(
            ['category'],
            ['product_attributes.categories.name_en'],
            onupdate='CASCADE',
            ondelete='CASCADE',
            name='fk_clothing_prices_category'
        ),
        sa.CheckConstraint('base_price >= 0', name='check_base_price_positive'),
        schema='public',
        comment='Prix de base par brand/category pour calcul automatique'
    )

    # Indexes pour performance
    op.create_index(
        'ix_clothing_prices_brand',
        'clothing_prices',
        ['brand'],
        schema='public'
    )
    op.create_index(
        'ix_clothing_prices_category',
        'clothing_prices',
        ['category'],
        schema='public'
    )

    # Note: Le seed de données a été retiré car il nécessite que les tables
    # brands et categories soient peuplées au préalable.
    # Utiliser le script scripts/seed_product_attributes.py pour peupler cette table.


def downgrade() -> None:
    """Supprimer la table clothing_prices."""
    op.drop_index('ix_clothing_prices_category', table_name='clothing_prices', schema='public')
    op.drop_index('ix_clothing_prices_brand', table_name='clothing_prices', schema='public')
    op.drop_table('clothing_prices', schema='public')
