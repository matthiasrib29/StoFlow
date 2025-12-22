"""remove_alembic_version_from_user_schemas

Revision ID: 41791f14505b
Revises: dc56e044535f
Create Date: 2025-12-19 17:00:03.463749+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '41791f14505b'
down_revision: Union[str, None] = 'dc56e044535f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove alembic_version tables from user schemas and template_tenant.

    Only public schema should have alembic_version table.
    """
    connection = op.get_bind()

    # Find all schemas with alembic_version table (except public)
    result = connection.execute(sa.text("""
        SELECT schemaname
        FROM pg_tables
        WHERE tablename = 'alembic_version'
        AND schemaname != 'public'
        ORDER BY schemaname
    """))

    schemas_to_clean = [row[0] for row in result]

    for schema in schemas_to_clean:
        # Use quoted identifier to handle schema names safely
        connection.execute(sa.text(f'DROP TABLE IF EXISTS "{schema}".alembic_version CASCADE'))
        print(f"  Dropped alembic_version from {schema}")

    if schemas_to_clean:
        print(f"  Cleaned {len(schemas_to_clean)} schemas")
    else:
        print("  No alembic_version tables to clean")


def downgrade() -> None:
    # No downgrade - we don't want to recreate these tables
    pass
