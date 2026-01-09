"""add_vinted_connection_table

Revision ID: ea3f385f012e
Revises: c73cb6f31adb
Create Date: 2025-12-11 15:17:50.520148+01:00

Cette migration ajoute la table simplifiée vinted_connection qui remplace
la table vinted_credentials pour stocker uniquement userId + login.

Architecture:
- Table ultra-simple: vinted_user_id (PK), login, user_id (FK), timestamps
- Extraction depuis n'importe quelle page Vinted via parsing HTML
- Plus besoin de csrf_token, anon_id, etc.

Author: Claude
Date: 2025-12-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ea3f385f012e'
down_revision: Union[str, None] = 'c73cb6f31adb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Ajoute la table vinted_connection dans template_tenant et les schemas user existants.
    """

    # ===== 1. CRÉER LA TABLE DANS template_tenant =====
    op.create_table(
        'vinted_connection',
        # Primary key: Vinted User ID
        sa.Column('vinted_user_id', sa.Integer(), nullable=False, comment="ID utilisateur Vinted (PK)"),

        # Login/username
        sa.Column('login', sa.String(length=255), nullable=False, comment="Login/username Vinted"),

        # Foreign key vers public.users
        sa.Column('user_id', sa.Integer(), nullable=False, comment="FK vers public.users.id"),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_sync', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),

        sa.PrimaryKeyConstraint('vinted_user_id'),
        sa.ForeignKeyConstraint(['user_id'], ['public.users.id'], ondelete='CASCADE'),
        schema='template_tenant'
    )

    # Index sur user_id pour recherches fréquentes
    op.create_index(
        'ix_template_tenant_vinted_connection_user_id',
        'vinted_connection',
        ['user_id'],
        schema='template_tenant'
    )

    # Index sur login
    op.create_index(
        'ix_template_tenant_vinted_connection_login',
        'vinted_connection',
        ['login'],
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
            CREATE TABLE IF NOT EXISTS {schema_name}.vinted_connection
            (LIKE template_tenant.vinted_connection INCLUDING ALL)
        """)
        print(f"  ✓ Created vinted_connection in {schema_name}")


def downgrade() -> None:
    """
    Supprime la table vinted_connection de tous les schemas.
    """

    # Supprimer des schemas user existants
    connection = op.get_bind()
    result = connection.execute(sa.text(
        "SELECT schema_name FROM information_schema.schemata WHERE schema_name LIKE 'user_%'"
    ))
    user_schemas = [row[0] for row in result]

    for schema_name in user_schemas:
        op.execute(f"DROP TABLE IF EXISTS {schema_name}.vinted_connection CASCADE")

    # Supprimer de template_tenant
    op.drop_index(
        'ix_template_tenant_vinted_connection_login',
        table_name='vinted_connection',
        schema='template_tenant'
    )
    op.drop_index(
        'ix_template_tenant_vinted_connection_user_id',
        table_name='vinted_connection',
        schema='template_tenant'
    )
    op.drop_table('vinted_connection', schema='template_tenant')
