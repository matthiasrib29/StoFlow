"""add_name_fr_to_brand_and_size

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2025-12-08 19:25:00.000000+01:00

Business Rules (2025-12-08):
- Ajouter colonne name_fr à Brand et Size pour mapping FR/EN
- Permet affichage français dans l'UI tout en gardant stockage anglais
- Compatible avec PostEditFlet logic (affichage FR, stockage EN)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6g7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Ajouter colonnes name_fr pour mapping FR/EN.

    Business Rules:
    - Brand.name_fr: Nom français de la marque (optionnel)
    - Size.name_fr: Taille française (optionnel)
    - Permet affichage UI en français (ex: "Taille: L" → "Taille: Grand")
    """
    # Ajouter name_fr à brands
    op.add_column(
        'brands',
        sa.Column('name_fr', sa.String(100), nullable=True, comment="Nom de la marque (FR)"),
        schema='product_attributes'
    )

    # Ajouter name_fr à sizes
    op.add_column(
        'sizes',
        sa.Column('name_fr', sa.String(100), nullable=True, comment="Nom de la taille (FR)"),
        schema='product_attributes'
    )


def downgrade() -> None:
    """Supprimer les colonnes name_fr."""
    # Supprimer name_fr de sizes
    op.drop_column('sizes', 'name_fr', schema='product_attributes')

    # Supprimer name_fr de brands
    op.drop_column('brands', 'name_fr', schema='product_attributes')
