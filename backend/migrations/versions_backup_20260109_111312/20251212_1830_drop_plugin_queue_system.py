"""drop_plugin_queue_system

Supprime le système de Queue pour les plugin tasks.
Architecture simplifiée: le backend orchestre step-by-step avec async/await,
pas besoin de queue.

Revision ID: f1a2b3c4d5e6
Revises: e055fbcc7557
Create Date: 2025-12-12 18:30:00.000000+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, None] = 'e055fbcc7557'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def get_user_schemas(connection) -> list[str]:
    """Récupère tous les schemas user_X existants."""
    result = connection.execute(sa.text(
        "SELECT schema_name FROM information_schema.schemata "
        "WHERE schema_name LIKE 'user_%' OR schema_name = 'template_tenant'"
    ))
    return [row[0] for row in result]


def upgrade() -> None:
    connection = op.get_bind()
    schemas = get_user_schemas(connection)

    for schema in schemas:
        # 1. Vérifier si la colonne queue_id existe dans plugin_tasks
        column_exists = connection.execute(sa.text(f"""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = '{schema}'
                AND table_name = 'plugin_tasks'
                AND column_name = 'queue_id'
            )
        """)).scalar()

        if column_exists:
            # Supprimer la contrainte FK et la colonne avec SQL brut (plus fiable)
            # D'abord trouver le nom exact de la contrainte
            fk_name = connection.execute(sa.text(f"""
                SELECT constraint_name FROM information_schema.table_constraints
                WHERE table_schema = '{schema}'
                AND table_name = 'plugin_tasks'
                AND constraint_type = 'FOREIGN KEY'
                AND constraint_name LIKE '%queue%'
            """)).scalar()

            if fk_name:
                connection.execute(sa.text(f'ALTER TABLE {schema}.plugin_tasks DROP CONSTRAINT "{fk_name}"'))
                print(f"  ✅ {schema}.plugin_tasks: FK constraint '{fk_name}' dropped")

            # Supprimer la colonne queue_id
            connection.execute(sa.text(f'ALTER TABLE {schema}.plugin_tasks DROP COLUMN IF EXISTS queue_id'))
            print(f"  ✅ {schema}.plugin_tasks.queue_id dropped")

        # 2. Supprimer la table plugin_queue si elle existe
        connection.execute(sa.text(f'DROP TABLE IF EXISTS {schema}.plugin_queue CASCADE'))
        print(f"  ✅ {schema}.plugin_queue table dropped (if existed)")


def downgrade() -> None:
    """
    Restaure le système de Queue (non recommandé).
    """
    connection = op.get_bind()
    schemas = get_user_schemas(connection)

    for schema in schemas:
        # 1. Recréer la table plugin_queue
        table_exists = connection.execute(sa.text(f"""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = '{schema}' AND table_name = 'plugin_queue'
            )
        """)).scalar()

        if not table_exists:
            op.create_table(
                'plugin_queue',
                sa.Column('id', sa.Integer(), primary_key=True),
                sa.Column('platform', sa.String(50), nullable=False, index=True),
                sa.Column('operation', sa.String(100), nullable=False),
                sa.Column('product_id', sa.Integer(), nullable=True, index=True),
                sa.Column('status', sa.String(20), nullable=False, default='queued', index=True),
                sa.Column('current_step', sa.String(100), nullable=True),
                sa.Column('accumulated_data', sa.JSON(), default=dict),
                sa.Column('context_data', sa.JSON(), default=dict),
                sa.Column('error_message', sa.Text(), nullable=True),
                sa.Column('retry_count', sa.Integer(), default=0),
                sa.Column('created_at', sa.DateTime(), nullable=False),
                sa.Column('updated_at', sa.DateTime(), nullable=False),
                schema=schema
            )
            print(f"  ✅ {schema}.plugin_queue table created")

        # 2. Ajouter la colonne queue_id à plugin_tasks
        column_exists = connection.execute(sa.text(f"""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = '{schema}'
                AND table_name = 'plugin_tasks'
                AND column_name = 'queue_id'
            )
        """)).scalar()

        if not column_exists:
            op.add_column(
                'plugin_tasks',
                sa.Column('queue_id', sa.Integer(), nullable=True),
                schema=schema
            )

            # Ajouter la FK constraint
            op.create_foreign_key(
                'plugin_tasks_queue_id_fkey',
                'plugin_tasks',
                'plugin_queue',
                ['queue_id'],
                ['id'],
                ondelete='CASCADE',
                source_schema=schema,
                referent_schema=schema
            )
            print(f"  ✅ {schema}.plugin_tasks.queue_id restored")
