"""add pending_instructions table

Créé la table pending_instructions dans tous les schémas user_X existants.
Cette table permet au backend d'orchestrer les actions plugin via des instructions
que le frontend récupère et exécute.

Revision ID: 2af3befa946a
Revises: 029b9f955564
Create Date: 2026-01-06 14:50:51.913672+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '2af3befa946a'
down_revision: Union[str, None] = '029b9f955564'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Crée la table pending_instructions dans tous les schémas user_X.
    """
    # Récupérer tous les schemas user_X
    conn = op.get_bind()
    result = conn.execute(sa.text("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%'
        ORDER BY schema_name
    """))
    user_schemas = [row[0] for row in result]

    print(f"Creating pending_instructions table in {len(user_schemas)} user schemas...")

    for schema in user_schemas:
        print(f"  - {schema}")
        op.execute(f'SET search_path TO {schema}, public')

        op.create_table(
            'pending_instructions',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('action', sa.String(100), nullable=False),
            sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
            sa.Column('result', postgresql.JSONB(), nullable=True),
            sa.Column('error', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
            schema=schema
        )

        op.create_index(
            f'idx_pending_instructions_user_status',
            'pending_instructions',
            ['user_id', 'status'],
            schema=schema
        )

    # Ajouter également au template_tenant pour les nouveaux users
    op.execute('SET search_path TO template_tenant, public')

    op.create_table(
        'pending_instructions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('result', postgresql.JSONB(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        schema='template_tenant'
    )

    op.create_index(
        'idx_pending_instructions_user_status',
        'pending_instructions',
        ['user_id', 'status'],
        schema='template_tenant'
    )

    print(f"✓ pending_instructions table created successfully")


def downgrade() -> None:
    """
    Supprime la table pending_instructions de tous les schémas user_X.
    """
    # Récupérer tous les schemas user_X
    conn = op.get_bind()
    result = conn.execute(sa.text("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%'
        ORDER BY schema_name
    """))
    user_schemas = [row[0] for row in result]

    print(f"Dropping pending_instructions table from {len(user_schemas)} user schemas...")

    for schema in user_schemas:
        print(f"  - {schema}")
        op.drop_index(f'idx_pending_instructions_user_status', 'pending_instructions', schema=schema)
        op.drop_table('pending_instructions', schema=schema)

    # Supprimer aussi du template_tenant
    op.drop_index('idx_pending_instructions_user_status', 'pending_instructions', schema='template_tenant')
    op.drop_table('pending_instructions', schema='template_tenant')

    print(f"✓ pending_instructions table dropped successfully")
