"""add_plugin_tasks_table

Revision ID: 20251207_0023
Revises:
Create Date: 2025-12-07

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '20251207_0023'
down_revision: Union[str, None] = '05ab399d382a'
depends_on: Union[str, None] = None


def upgrade() -> None:
    """
    Create plugin_tasks table in all tenant schemas.

    Business Rules (2025-12-06):
    - Table tenant-specific (client_{id}.plugin_tasks)
    - Gere la queue de taches pour le plugin browser
    - Le plugin poll GET /api/plugin/tasks toutes les 5s
    """
    conn = op.get_bind()

    # Recuperer tous les tenants existants
    tenants = conn.execute(text("SELECT id FROM public.tenants")).fetchall()

    for tenant in tenants:
        schema_name = f"client_{tenant.id}"

        # Check if table already exists
        table_exists = conn.execute(text(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = '{schema_name}' AND table_name = 'plugin_tasks'
            )
        """)).scalar()

        if table_exists:
            print(f"⚠️  Table plugin_tasks already exists in {schema_name}, skipping...")
            continue

        # Creer la table plugin_tasks dans le schema tenant
        op.create_table(
            'plugin_tasks',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('task_type', sa.String(50), nullable=False),
            sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
            sa.Column('payload', sa.JSON(), nullable=False),
            sa.Column('result', sa.JSON(), nullable=True),
            sa.Column('error_message', sa.Text(), nullable=True),
            sa.Column('product_id', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('max_retries', sa.Integer(), nullable=False, server_default='3'),
            sa.PrimaryKeyConstraint('id'),
            schema=schema_name
        )

        # Ajouter FK vers products si la table existe
        products_exists = conn.execute(text(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = '{schema_name}' AND table_name = 'products'
            )
        """)).scalar()

        if products_exists:
            op.create_foreign_key(
                f'fk_{schema_name}_plugin_tasks_product_id',
                'plugin_tasks', 'products',
                ['product_id'], ['id'],
                source_schema=schema_name,
                referent_schema=schema_name,
                ondelete='CASCADE'
            )

        # Creer les indexes
        op.create_index(
            f'ix_{schema_name}_plugin_tasks_id',
            'plugin_tasks',
            ['id'],
            unique=False,
            schema=schema_name
        )

        op.create_index(
            f'ix_{schema_name}_plugin_tasks_task_type',
            'plugin_tasks',
            ['task_type'],
            unique=False,
            schema=schema_name
        )

        op.create_index(
            f'ix_{schema_name}_plugin_tasks_status',
            'plugin_tasks',
            ['status'],
            unique=False,
            schema=schema_name
        )

        op.create_index(
            f'ix_{schema_name}_plugin_tasks_product_id',
            'plugin_tasks',
            ['product_id'],
            unique=False,
            schema=schema_name
        )

        # Index composite pour polling efficace (status + created_at)
        op.create_index(
            f'ix_{schema_name}_plugin_tasks_status_created',
            'plugin_tasks',
            ['status', 'created_at'],
            unique=False,
            schema=schema_name
        )


def downgrade() -> None:
    """Drop plugin_tasks table from all tenant schemas."""
    conn = op.get_bind()
    tenants = conn.execute(text("SELECT id FROM public.tenants")).fetchall()

    for tenant in tenants:
        schema_name = f"client_{tenant.id}"

        # Check if table exists before dropping
        table_exists = conn.execute(text(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = '{schema_name}' AND table_name = 'plugin_tasks'
            )
        """)).scalar()

        if table_exists:
            op.drop_table('plugin_tasks', schema=schema_name)
