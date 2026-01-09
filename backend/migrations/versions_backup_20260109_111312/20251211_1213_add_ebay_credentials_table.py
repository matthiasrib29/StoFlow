"""add_ebay_credentials_table

Revision ID: 99f88e15be4a
Revises: 4a8b9c1d2e3f
Create Date: 2025-12-11 12:13:21.215723+01:00

Cette migration ajoute la table ebay_credentials pour stocker les
credentials OAuth2 du compte eBay de chaque utilisateur.

Author: Claude
Date: 2025-12-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '99f88e15be4a'
down_revision: Union[str, None] = '4a8b9c1d2e3f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Ajoute la table ebay_credentials dans template_tenant et les schemas user existants.
    """

    # ===== 1. CRÉER LA TABLE DANS template_tenant =====
    op.create_table(
        'ebay_credentials',
        sa.Column('id', sa.Integer(), nullable=False),

        # eBay User ID
        sa.Column('ebay_user_id', sa.String(length=255), nullable=True, comment="ID utilisateur eBay"),

        # OAuth2 Tokens
        sa.Column('access_token', sa.Text(), nullable=True, comment="OAuth2 Access Token (expire 2h)"),
        sa.Column('refresh_token', sa.Text(), nullable=True, comment="OAuth2 Refresh Token (expire 18 mois)"),

        # Token Expiration
        sa.Column('access_token_expires_at', sa.DateTime(timezone=True), nullable=True, comment="Date d'expiration du access_token"),
        sa.Column('refresh_token_expires_at', sa.DateTime(timezone=True), nullable=True, comment="Date d'expiration du refresh_token"),

        # Environment
        sa.Column('sandbox_mode', sa.Boolean(), nullable=False, server_default='false', comment="True si utilise eBay Sandbox"),

        # Status
        sa.Column('is_connected', sa.Boolean(), nullable=False, server_default='false', comment="True si les credentials sont valides"),
        sa.Column('last_sync', sa.DateTime(timezone=True), nullable=True, comment="Dernière synchronisation réussie"),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),

        sa.PrimaryKeyConstraint('id'),
        schema='template_tenant'
    )

    # Index sur ebay_user_id
    op.create_index(
        'ix_template_tenant_ebay_credentials_ebay_user_id',
        'ebay_credentials',
        ['ebay_user_id'],
        unique=False,
        schema='template_tenant'
    )

    # Index sur id
    op.create_index(
        'ix_template_tenant_ebay_credentials_id',
        'ebay_credentials',
        ['id'],
        unique=False,
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
            CREATE TABLE IF NOT EXISTS {schema_name}.ebay_credentials
            (LIKE template_tenant.ebay_credentials INCLUDING ALL)
        """)
        print(f"  ✓ Created ebay_credentials in {schema_name}")


def downgrade() -> None:
    """
    Supprime la table ebay_credentials de tous les schemas.
    """

    # Supprimer des schemas user existants
    connection = op.get_bind()
    result = connection.execute(sa.text(
        "SELECT schema_name FROM information_schema.schemata WHERE schema_name LIKE 'user_%'"
    ))
    user_schemas = [row[0] for row in result]

    for schema_name in user_schemas:
        op.execute(f"DROP TABLE IF EXISTS {schema_name}.ebay_credentials CASCADE")

    # Supprimer de template_tenant
    op.drop_index(
        'ix_template_tenant_ebay_credentials_id',
        table_name='ebay_credentials',
        schema='template_tenant'
    )
    op.drop_index(
        'ix_template_tenant_ebay_credentials_ebay_user_id',
        table_name='ebay_credentials',
        schema='template_tenant'
    )
    op.drop_table('ebay_credentials', schema='template_tenant')
