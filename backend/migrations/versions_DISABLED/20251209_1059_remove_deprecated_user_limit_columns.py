"""remove_deprecated_user_limit_columns

Revision ID: 7c235d5f635c
Revises: a6d4f61329de
Create Date: 2025-12-09 10:59:14.602919+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7c235d5f635c'
down_revision: Union[str, None] = 'a6d4f61329de'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Supprime les colonnes deprecated de User (max_products, max_platforms, ai_credits_monthly)."""

    # Supprimer les colonnes deprecated (maintenant dans subscription_quotas)
    op.drop_column('users', 'max_products', schema='public')
    op.drop_column('users', 'max_platforms', schema='public')
    op.drop_column('users', 'ai_credits_monthly', schema='public')


def downgrade() -> None:
    """Restaure les colonnes deprecated."""

    # Ajouter les colonnes avec valeurs par défaut
    op.add_column('users', sa.Column('max_products', sa.Integer(), nullable=False, server_default='30'), schema='public')
    op.add_column('users', sa.Column('max_platforms', sa.Integer(), nullable=False, server_default='2'), schema='public')
    op.add_column('users', sa.Column('ai_credits_monthly', sa.Integer(), nullable=False, server_default='15'), schema='public')

    # Peupler avec les valeurs depuis subscription_quotas
    op.execute("""
        UPDATE public.users u
        SET
            max_products = sq.max_products,
            max_platforms = sq.max_platforms,
            ai_credits_monthly = sq.ai_credits_monthly
        FROM public.subscription_quotas sq
        WHERE u.subscription_tier_id = sq.id
    """)
