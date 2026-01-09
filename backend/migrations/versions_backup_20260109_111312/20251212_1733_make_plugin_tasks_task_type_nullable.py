"""make_plugin_tasks_task_type_nullable

Rend la colonne task_type nullable dans plugin_tasks.

On n'utilise plus task_type - le backend garde le contexte via async/await.
Chaque tâche est juste une requête HTTP simple (http_method + path).

Revision ID: e055fbcc7557
Revises: d948e068256d
Create Date: 2025-12-12 17:33:10.796126+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e055fbcc7557'
down_revision: Union[str, None] = 'd948e068256d'
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
        # Vérifier si la table existe dans ce schema
        table_exists = connection.execute(sa.text(f"""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = '{schema}' AND table_name = 'plugin_tasks'
            )
        """)).scalar()

        if table_exists:
            # Rendre task_type nullable
            op.alter_column(
                'plugin_tasks',
                'task_type',
                existing_type=sa.String(100),
                nullable=True,
                schema=schema
            )
            print(f"  ✅ {schema}.plugin_tasks.task_type → nullable=True")


def downgrade() -> None:
    connection = op.get_bind()
    schemas = get_user_schemas(connection)

    for schema in schemas:
        table_exists = connection.execute(sa.text(f"""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = '{schema}' AND table_name = 'plugin_tasks'
            )
        """)).scalar()

        if table_exists:
            # Remettre NOT NULL (avec valeur par défaut pour les NULL existants)
            connection.execute(sa.text(f"""
                UPDATE {schema}.plugin_tasks
                SET task_type = 'HTTP_REQUEST'
                WHERE task_type IS NULL
            """))

            op.alter_column(
                'plugin_tasks',
                'task_type',
                existing_type=sa.String(100),
                nullable=False,
                schema=schema
            )
            print(f"  ✅ {schema}.plugin_tasks.task_type → nullable=False")
