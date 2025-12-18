"""add_product_sku_sequence

Revision ID: a1b2c3d4e5f6
Revises: 92f651bd5381
Create Date: 2025-12-08 19:22:00.000000+01:00

Business Rules (2025-12-08):
- Créer séquence pour génération automatique de SKU
- Format simple : numérique auto-incrémenté (ex: 2726, 2727...)
- Séquence dans schema client_X (multi-tenant isolation)
- Start value: 1000 (éviter confusion avec IDs)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '92f651bd5381'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Créer séquence product_sku_seq dans le schema courant.

    Note: Cette séquence sera créée dans chaque schema client_X lors de la création du tenant.
    Cette migration crée le template pour les nouveaux schemas.
    """
    # La séquence sera créée dynamiquement dans chaque schema tenant
    # Cette migration documente la structure, la création réelle se fait dans user_schema_service
    pass


def downgrade() -> None:
    """Supprimer la séquence product_sku_seq."""
    # La séquence sera supprimée lors de la suppression du schema tenant
    pass
