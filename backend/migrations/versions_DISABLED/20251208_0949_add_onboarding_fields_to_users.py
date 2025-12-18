"""add_onboarding_fields_to_users

Revision ID: 2e30e856c66d
Revises: 46aad9f85d14
Create Date: 2025-12-08 09:49:33.437953+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2e30e856c66d'
down_revision: Union[str, None] = '46aad9f85d14'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create ENUM types (already exist, so skip if present)
    # Note: These should match the values in Python enums (lowercase)

    # Add columns to public.users
    op.add_column('users', sa.Column('business_name', sa.String(255), nullable=True, comment="Nom de l'entreprise ou de la boutique"), schema='public')
    op.add_column('users', sa.Column('account_type', sa.Enum('individual', 'professional', name='account_type'), nullable=False, server_default='individual', comment="Type de compte: individual (particulier) ou professional (entreprise)"), schema='public')
    op.add_column('users', sa.Column('business_type', sa.Enum('resale', 'dropshipping', 'artisan', 'retail', 'other', name='business_type'), nullable=True, comment="Type d'activité: resale, dropshipping, artisan, retail, other"), schema='public')
    op.add_column('users', sa.Column('estimated_products', sa.Enum('0-50', '50-200', '200-500', '500+', name='estimated_products'), nullable=True, comment="Nombre de produits estimé: 0-50, 50-200, 200-500, 500+"), schema='public')
    op.add_column('users', sa.Column('siret', sa.String(14), nullable=True, comment="Numéro SIRET (France) - uniquement pour les professionnels"), schema='public')
    op.add_column('users', sa.Column('vat_number', sa.String(20), nullable=True, comment="Numéro de TVA intracommunautaire - uniquement pour les professionnels"), schema='public')
    op.add_column('users', sa.Column('phone', sa.String(20), nullable=True, comment="Numéro de téléphone"), schema='public')
    op.add_column('users', sa.Column('country', sa.String(2), nullable=False, server_default='FR', comment="Code pays ISO 3166-1 alpha-2 (FR, BE, CH, etc.)"), schema='public')
    op.add_column('users', sa.Column('language', sa.String(2), nullable=False, server_default='fr', comment="Code langue ISO 639-1 (fr, en, etc.)"), schema='public')


def downgrade() -> None:
    # Remove columns from public.users
    op.drop_column('users', 'language', schema='public')
    op.drop_column('users', 'country', schema='public')
    op.drop_column('users', 'phone', schema='public')
    op.drop_column('users', 'vat_number', schema='public')
    op.drop_column('users', 'siret', schema='public')
    op.drop_column('users', 'estimated_products', schema='public')
    op.drop_column('users', 'business_type', schema='public')
    op.drop_column('users', 'account_type', schema='public')
    op.drop_column('users', 'business_name', schema='public')

    # Drop ENUM types
    op.execute("DROP TYPE estimated_products")
    op.execute("DROP TYPE business_type")
    op.execute("DROP TYPE account_type")
