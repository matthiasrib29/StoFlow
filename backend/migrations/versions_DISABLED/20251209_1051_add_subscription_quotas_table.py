"""add_subscription_quotas_table

Revision ID: a6d4f61329de
Revises: 08484e0176eb
Create Date: 2025-12-09 10:51:31.897497+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a6d4f61329de'
down_revision: Union[str, None] = '08484e0176eb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Crée la table subscription_quotas et seed les quotas par défaut."""

    # Créer la table subscription_quotas
    op.create_table(
        'subscription_quotas',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tier', sa.Enum('FREE', 'STARTER', 'PRO', 'ENTERPRISE', name='subscriptiontier', schema='public'), nullable=False),
        sa.Column('max_products', sa.Integer(), nullable=False, comment='Nombre maximum de produits actifs'),
        sa.Column('max_platforms', sa.Integer(), nullable=False, comment='Nombre maximum de plateformes connectées'),
        sa.Column('ai_credits_monthly', sa.Integer(), nullable=False, comment='Crédits IA mensuels'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tier'),
        schema='public'
    )

    # Créer les index
    op.create_index('ix_subscription_quotas_id', 'subscription_quotas', ['id'], unique=False, schema='public')
    op.create_index('ix_subscription_quotas_tier', 'subscription_quotas', ['tier'], unique=False, schema='public')

    # Seed les quotas par défaut
    op.execute("""
        INSERT INTO public.subscription_quotas (tier, max_products, max_platforms, ai_credits_monthly)
        VALUES
            ('FREE', 30, 2, 15),
            ('STARTER', 150, 3, 75),
            ('PRO', 500, 5, 250),
            ('ENTERPRISE', 999999, 999999, 999999)
    """)

    # Migrer l'ancien enum subscription_tier vers le nouveau format
    # Mapping: STANDARD -> STARTER, PREMIUM -> PRO, BUSINESS -> PRO, tout le reste reste identique
    op.execute("""
        ALTER TABLE public.users
        ALTER COLUMN subscription_tier TYPE text
    """)

    op.execute("""
        UPDATE public.users
        SET subscription_tier = CASE
            WHEN subscription_tier = 'STANDARD' THEN 'STARTER'
            WHEN subscription_tier = 'PREMIUM' THEN 'PRO'
            WHEN subscription_tier = 'BUSINESS' THEN 'PRO'
            ELSE subscription_tier
        END
    """)

    # Supprimer l'ancien type enum subscription_tier
    op.execute("DROP TYPE IF EXISTS public.subscription_tier CASCADE")

    # Recréer le type enum avec les nouvelles valeurs
    op.execute("CREATE TYPE public.subscription_tier AS ENUM ('FREE', 'STARTER', 'PRO', 'ENTERPRISE')")

    # Reconvertir la colonne en enum
    op.execute("""
        ALTER TABLE public.users
        ALTER COLUMN subscription_tier TYPE public.subscription_tier
        USING subscription_tier::public.subscription_tier
    """)

    # Ajouter la colonne subscription_tier_id à users (foreign key vers subscription_quotas)
    op.add_column('users', sa.Column('subscription_tier_id', sa.Integer(), nullable=True), schema='public')
    op.create_foreign_key(
        'fk_users_subscription_tier_id',
        'users', 'subscription_quotas',
        ['subscription_tier_id'], ['id'],
        source_schema='public',
        referent_schema='public'
    )

    # Peupler subscription_tier_id pour les utilisateurs existants
    op.execute("""
        UPDATE public.users u
        SET subscription_tier_id = sq.id
        FROM public.subscription_quotas sq
        WHERE u.subscription_tier::text = sq.tier::text
    """)

    # Rendre subscription_tier_id NOT NULL maintenant qu'il est peuplé
    op.alter_column('users', 'subscription_tier_id', nullable=False, schema='public')


def downgrade() -> None:
    """Supprime la table subscription_quotas et la foreign key."""

    # Supprimer la foreign key et la colonne subscription_tier_id
    op.drop_constraint('fk_users_subscription_tier_id', 'users', schema='public', type_='foreignkey')
    op.drop_column('users', 'subscription_tier_id', schema='public')

    # Supprimer les index
    op.drop_index('ix_subscription_quotas_tier', table_name='subscription_quotas', schema='public')
    op.drop_index('ix_subscription_quotas_id', table_name='subscription_quotas', schema='public')

    # Supprimer la table
    op.drop_table('subscription_quotas', schema='public')
