"""add_stripe_fields_to_user

Revision ID: 519b0731226b
Revises: 29170a73217f
Create Date: 2025-12-10 12:24:37.554503+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '519b0731226b'
down_revision: Union[str, None] = '29170a73217f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Ajouter les champs Stripe au modèle User
    op.add_column('users', sa.Column('stripe_customer_id', sa.String(length=255), nullable=True, comment='ID du customer Stripe (cus_xxx)'), schema='public')
    op.add_column('users', sa.Column('stripe_subscription_id', sa.String(length=255), nullable=True, comment='ID de la subscription Stripe active (sub_xxx)'), schema='public')

    # Créer un index unique sur stripe_customer_id
    op.create_index(op.f('ix_users_stripe_customer_id'), 'users', ['stripe_customer_id'], unique=True, schema='public')


def downgrade() -> None:
    # Supprimer l'index
    op.drop_index(op.f('ix_users_stripe_customer_id'), table_name='users', schema='public')

    # Supprimer les colonnes
    op.drop_column('users', 'stripe_subscription_id', schema='public')
    op.drop_column('users', 'stripe_customer_id', schema='public')
