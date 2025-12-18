"""add_pricing_and_descriptive_features_to_products

Revision ID: f07d95981520
Revises: 4f3b04388fe7
Create Date: 2025-12-08 11:09:45.988097+01:00

Ajoute 7 nouveaux champs au modèle Product pour compatibilité avec pythonApiWOO:
- 5 attributs de tarification (pricing_edit, pricing_rarity, pricing_quality, pricing_details, pricing_style)
- 2 features descriptifs (unique_feature, marking)

Business rationale (2025-12-08):
- Système de tarification dynamique basé sur rareté/qualité
- Tracking des features uniques et marquages pour vêtements vintage
- Compatibilité avec pythonApiWOO pour migration future

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f07d95981520'
down_revision: Union[str, None] = '4f3b04388fe7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Ajoute les attributs de tarification et features descriptifs aux produits.

    IMPORTANT: Cette migration doit être exécutée sur TOUS les schemas user_*
    car la table products est dans chaque schema tenant.
    """

    # Note: Les colonnes sont ajoutées dynamiquement à tous les schemas user_*
    # par la logique d'Alembic multi-tenant

    # Attributs de tarification
    op.add_column('products', sa.Column('pricing_edit', sa.String(length=100), nullable=True,
                  comment='Prix édité manuellement (indicateur)'))
    op.add_column('products', sa.Column('pricing_rarity', sa.String(length=100), nullable=True,
                  comment='Rareté pour calcul prix'))
    op.add_column('products', sa.Column('pricing_quality', sa.String(length=100), nullable=True,
                  comment='Qualité pour calcul prix'))
    op.add_column('products', sa.Column('pricing_details', sa.String(length=100), nullable=True,
                  comment='Détails spécifiques pour calcul prix'))
    op.add_column('products', sa.Column('pricing_style', sa.String(length=100), nullable=True,
                  comment='Style pour tarification'))

    # Features descriptifs
    op.add_column('products', sa.Column('unique_feature', sa.Text(), nullable=True,
                  comment='Features uniques séparées par virgules (ex: Vintage,Logo brodé,Pièce unique)'))
    op.add_column('products', sa.Column('marking', sa.Text(), nullable=True,
                  comment='Marquages/écritures visibles séparés par virgules (dates, codes, textes)'))


def downgrade() -> None:
    """
    Supprime les attributs de tarification et features descriptifs.
    """

    # Suppression dans l'ordre inverse
    op.drop_column('products', 'marking')
    op.drop_column('products', 'unique_feature')
    op.drop_column('products', 'pricing_style')
    op.drop_column('products', 'pricing_details')
    op.drop_column('products', 'pricing_quality')
    op.drop_column('products', 'pricing_rarity')
    op.drop_column('products', 'pricing_edit')
