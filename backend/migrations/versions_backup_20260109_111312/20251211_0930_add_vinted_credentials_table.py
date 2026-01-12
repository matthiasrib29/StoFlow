"""add_vinted_credentials_table

Revision ID: 4a8b9c1d2e3f
Revises: 20251210_1306_add_pricing_columns_to_existing_user_
Create Date: 2025-12-11 09:30:00.000000+01:00

Cette migration ajoute la table vinted_credentials pour stocker les
credentials et infos du compte Vinted de chaque utilisateur.

Ces données sont extraites par le plugin navigateur depuis vinted.fr
et synchronisées vers le backend.

Author: Claude
Date: 2025-12-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4a8b9c1d2e3f'
down_revision: Union[str, None] = '89d945359837'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Ajoute la table vinted_credentials dans template_tenant et les schemas user existants.
    """

    # ===== 1. CRÉER LA TABLE DANS template_tenant =====
    op.create_table(
        'vinted_credentials',
        sa.Column('id', sa.Integer(), nullable=False),

        # Vinted IDs
        sa.Column('vinted_user_id', sa.BigInteger(), nullable=True, comment="ID utilisateur Vinted"),
        sa.Column('login', sa.String(length=255), nullable=True, comment="Username Vinted"),

        # API Tokens
        sa.Column('csrf_token', sa.String(length=100), nullable=True, comment="Token CSRF pour les requêtes Vinted"),
        sa.Column('anon_id', sa.String(length=100), nullable=True, comment="ID anonyme pour les requêtes Vinted"),

        # Identity
        sa.Column('email', sa.String(length=255), nullable=True, comment="Email du compte Vinted"),
        sa.Column('real_name', sa.String(length=255), nullable=True, comment="Nom complet"),
        sa.Column('birthday', sa.String(length=10), nullable=True, comment="Date de naissance (YYYY-MM-DD)"),
        sa.Column('gender', sa.String(length=20), nullable=True, comment="Genre"),

        # Location
        sa.Column('city', sa.String(length=255), nullable=True, comment="Ville"),
        sa.Column('country_code', sa.String(length=10), nullable=True, comment="Code pays (FR, BE, etc.)"),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='EUR', comment="Devise"),
        sa.Column('locale', sa.String(length=10), nullable=False, server_default='fr', comment="Locale"),

        # Profile
        sa.Column('profile_url', sa.Text(), nullable=True, comment="URL du profil Vinted"),
        sa.Column('photo_url', sa.Text(), nullable=True, comment="URL de la photo de profil"),

        # Statistics
        sa.Column('feedback_count', sa.Integer(), nullable=False, server_default='0', comment="Nombre total d'avis"),
        sa.Column('feedback_reputation', sa.Numeric(precision=3, scale=2), nullable=False, server_default='0.00', comment="Score de réputation (0.00-1.00)"),
        sa.Column('item_count', sa.Integer(), nullable=False, server_default='0', comment="Nombre d'articles en vente"),
        sa.Column('total_items_count', sa.Integer(), nullable=False, server_default='0', comment="Nombre total d'articles"),
        sa.Column('followers_count', sa.Integer(), nullable=False, server_default='0', comment="Nombre de followers"),
        sa.Column('following_count', sa.Integer(), nullable=False, server_default='0', comment="Nombre de following"),

        # Business (Pro account)
        sa.Column('is_business', sa.Boolean(), nullable=False, server_default='false', comment="True si compte professionnel"),
        sa.Column('business_legal_name', sa.String(length=255), nullable=True, comment="Nom légal de l'entreprise"),
        sa.Column('business_legal_code', sa.String(length=50), nullable=True, comment="SIRET ou équivalent"),
        sa.Column('business_vat', sa.String(length=50), nullable=True, comment="Numéro de TVA"),

        # Status
        sa.Column('is_connected', sa.Boolean(), nullable=False, server_default='false', comment="True si les credentials sont valides"),
        sa.Column('last_sync', sa.DateTime(timezone=True), nullable=True, comment="Dernière synchronisation réussie"),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),

        sa.PrimaryKeyConstraint('id'),
        schema='template_tenant'
    )

    # Index sur vinted_user_id
    op.create_index(
        'ix_template_tenant_vinted_credentials_vinted_user_id',
        'vinted_credentials',
        ['vinted_user_id'],
        unique=True,
        schema='template_tenant'
    )

    # ===== 2. CRÉER LA TABLE DANS LES SCHEMAS USER EXISTANTS =====
    connection = op.get_bind()
    result = connection.execute(sa.text(
        "SELECT schema_name FROM information_schema.schemata WHERE schema_name LIKE 'user_%'"
    ))
    user_schemas = [row[0] for row in result]

    for schema_name in user_schemas:
        # Créer la table en utilisant LIKE template_tenant
        op.execute(f"""
            CREATE TABLE IF NOT EXISTS {schema_name}.vinted_credentials
            (LIKE template_tenant.vinted_credentials INCLUDING ALL)
        """)
        print(f"  ✓ Created vinted_credentials in {schema_name}")


def downgrade() -> None:
    """
    Supprime la table vinted_credentials de tous les schemas.
    """

    # Supprimer des schemas user existants
    connection = op.get_bind()
    result = connection.execute(sa.text(
        "SELECT schema_name FROM information_schema.schemata WHERE schema_name LIKE 'user_%'"
    ))
    user_schemas = [row[0] for row in result]

    for schema_name in user_schemas:
        op.execute(f"DROP TABLE IF EXISTS {schema_name}.vinted_credentials CASCADE")

    # Supprimer de template_tenant
    op.drop_index(
        'ix_template_tenant_vinted_credentials_vinted_user_id',
        table_name='vinted_credentials',
        schema='template_tenant'
    )
    op.drop_table('vinted_credentials', schema='template_tenant')
