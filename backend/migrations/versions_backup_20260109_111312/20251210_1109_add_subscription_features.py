"""add_subscription_features

Revision ID: 062469969708
Revises: e8f9a0b1c2d3
Create Date: 2025-12-10 11:09:54.960447+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '062469969708'
down_revision: Union[str, None] = 'e8f9a0b1c2d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add price column to subscription_quotas
    op.add_column(
        'subscription_quotas',
        sa.Column('price', sa.DECIMAL(precision=10, scale=2), nullable=False, server_default='0.00', comment="Prix mensuel de l'abonnement en euros"),
        schema='public'
    )

    # Create ai_credits table
    op.create_table(
        'ai_credits',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False, comment='Utilisateur propriétaire'),
        sa.Column('ai_credits_purchased', sa.Integer(), nullable=False, server_default='0', comment="Crédits IA achetés (cumulables, ne s'épuisent pas)"),
        sa.Column('ai_credits_used_this_month', sa.Integer(), nullable=False, server_default='0', comment='Crédits IA utilisés ce mois-ci'),
        sa.Column('last_reset_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Date du dernier reset mensuel'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['public.users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
        schema='public'
    )
    op.create_index(op.f('ix_public_ai_credits_id'), 'ai_credits', ['id'], unique=False, schema='public')
    op.create_index(op.f('ix_public_ai_credits_user_id'), 'ai_credits', ['user_id'], unique=True, schema='public')

    # Add usage counters to users table
    op.add_column(
        'users',
        sa.Column('current_products_count', sa.Integer(), nullable=False, server_default='0', comment="Nombre actuel de produits actifs de l'utilisateur"),
        schema='public'
    )
    op.add_column(
        'users',
        sa.Column('current_platforms_count', sa.Integer(), nullable=False, server_default='0', comment='Nombre actuel de plateformes connectées'),
        schema='public'
    )


def downgrade() -> None:
    # Remove usage counters from users table
    op.drop_column('users', 'current_platforms_count', schema='public')
    op.drop_column('users', 'current_products_count', schema='public')

    # Drop ai_credits table
    op.drop_index(op.f('ix_public_ai_credits_user_id'), table_name='ai_credits', schema='public')
    op.drop_index(op.f('ix_public_ai_credits_id'), table_name='ai_credits', schema='public')
    op.drop_table('ai_credits', schema='public')

    # Remove price column from subscription_quotas
    op.drop_column('subscription_quotas', 'price', schema='public')
