"""add_ebay_account_info_columns

Revision ID: c837d967145c
Revises: 5o6p7q8r9s0t
Create Date: 2025-12-12 11:55:30.580853+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c837d967145c'
down_revision: Union[str, None] = '5o6p7q8r9s0t'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Ajoute les colonnes d'informations de compte eBay dans ebay_credentials.

    Ces colonnes seront remplies automatiquement lors de la connexion OAuth
    et permettent d'afficher les infos du compte sans appel API supplémentaire.

    Note: Cette migration s'applique uniquement aux schemas user_* (tenant-specific).
    La table ebay_credentials n'existe pas dans le schema public.
    """
    # Vérifier si la table existe avant de modifier (skip si schema public)
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # Si la table n'existe pas (cas du schema public), skip
    if 'ebay_credentials' not in inspector.get_table_names():
        return

    # Ajouter les colonnes d'informations du compte
    op.add_column('ebay_credentials', sa.Column('username', sa.String(255), nullable=True, comment='Username eBay (ex: shop.ton.outfit)'))
    op.add_column('ebay_credentials', sa.Column('email', sa.String(255), nullable=True, comment='Email du compte eBay'))
    op.add_column('ebay_credentials', sa.Column('account_type', sa.String(50), nullable=True, comment='Type de compte: BUSINESS ou INDIVIDUAL'))

    # Informations Business Account
    op.add_column('ebay_credentials', sa.Column('business_name', sa.String(255), nullable=True, comment='Nom de l\'entreprise (si BUSINESS)'))

    # Informations Individual Account
    op.add_column('ebay_credentials', sa.Column('first_name', sa.String(255), nullable=True, comment='Prénom (si INDIVIDUAL)'))
    op.add_column('ebay_credentials', sa.Column('last_name', sa.String(255), nullable=True, comment='Nom (si INDIVIDUAL)'))

    # Coordonnées
    op.add_column('ebay_credentials', sa.Column('phone', sa.String(50), nullable=True, comment='Numéro de téléphone'))
    op.add_column('ebay_credentials', sa.Column('address', sa.Text, nullable=True, comment='Adresse complète'))
    op.add_column('ebay_credentials', sa.Column('marketplace', sa.String(50), nullable=True, comment='Marketplace d\'inscription (EBAY_FR, EBAY_US, etc.)'))

    # Réputation vendeur
    op.add_column('ebay_credentials', sa.Column('feedback_score', sa.Integer, nullable=True, default=0, comment='Score de feedback'))
    op.add_column('ebay_credentials', sa.Column('feedback_percentage', sa.Float, nullable=True, default=0.0, comment='Pourcentage de feedback positif'))
    op.add_column('ebay_credentials', sa.Column('seller_level', sa.String(50), nullable=True, comment='Niveau vendeur (top_rated, above_standard, standard, below_standard)'))

    # Date d'inscription eBay
    op.add_column('ebay_credentials', sa.Column('registration_date', sa.String(50), nullable=True, comment='Date d\'inscription sur eBay'))


def downgrade() -> None:
    """Supprime les colonnes d'informations de compte eBay."""
    # Vérifier si la table existe avant de modifier (skip si schema public)
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # Si la table n'existe pas (cas du schema public), skip
    if 'ebay_credentials' not in inspector.get_table_names():
        return

    op.drop_column('ebay_credentials', 'registration_date')
    op.drop_column('ebay_credentials', 'seller_level')
    op.drop_column('ebay_credentials', 'feedback_percentage')
    op.drop_column('ebay_credentials', 'feedback_score')
    op.drop_column('ebay_credentials', 'marketplace')
    op.drop_column('ebay_credentials', 'address')
    op.drop_column('ebay_credentials', 'phone')
    op.drop_column('ebay_credentials', 'last_name')
    op.drop_column('ebay_credentials', 'first_name')
    op.drop_column('ebay_credentials', 'business_name')
    op.drop_column('ebay_credentials', 'account_type')
    op.drop_column('ebay_credentials', 'email')
    op.drop_column('ebay_credentials', 'username')
