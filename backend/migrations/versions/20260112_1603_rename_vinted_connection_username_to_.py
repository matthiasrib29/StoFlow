"""rename vinted_connection username to login

Revision ID: 3837a9aa2009
Revises: 6bc865c4c841
Create Date: 2026-01-12 16:03:07.186030+01:00

The SQLAlchemy model uses 'login' but the DB has 'username'.
This migration renames the column to match the model.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from logging import getLogger

logger = getLogger(__name__)

# revision identifiers, used by Alembic.
revision: str = '3837a9aa2009'
down_revision: Union[str, None] = '6bc865c4c841'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def get_user_schemas(connection) -> list[str]:
    """Get all user_X schemas."""
    result = connection.execute(text("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%'
        ORDER BY schema_name
    """))
    return [row[0] for row in result.fetchall()]


def column_exists(connection, schema: str, table: str, column: str) -> bool:
    """Check if a column exists in a table."""
    result = connection.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = :schema
            AND table_name = :table
            AND column_name = :column
        )
    """), {"schema": schema, "table": table, "column": column})
    return result.scalar()


def upgrade() -> None:
    connection = op.get_bind()

    # Rename in template_tenant
    if column_exists(connection, 'template_tenant', 'vinted_connection', 'username'):
        op.alter_column(
            'vinted_connection',
            'username',
            new_column_name='login',
            schema='template_tenant'
        )
        logger.info("  + Renamed username -> login in template_tenant.vinted_connection")

    # Rename in all user schemas
    user_schemas = get_user_schemas(connection)
    for schema in user_schemas:
        if column_exists(connection, schema, 'vinted_connection', 'username'):
            op.alter_column(
                'vinted_connection',
                'username',
                new_column_name='login',
                schema=schema
            )
            logger.info(f"  + Renamed username -> login in {schema}.vinted_connection")


def downgrade() -> None:
    connection = op.get_bind()

    # Rename back in template_tenant
    if column_exists(connection, 'template_tenant', 'vinted_connection', 'login'):
        op.alter_column(
            'vinted_connection',
            'login',
            new_column_name='username',
            schema='template_tenant'
        )

    # Rename back in all user schemas
    user_schemas = get_user_schemas(connection)
    for schema in user_schemas:
        if column_exists(connection, schema, 'vinted_connection', 'login'):
            op.alter_column(
                'vinted_connection',
                'login',
                new_column_name='username',
                schema=schema
            )
