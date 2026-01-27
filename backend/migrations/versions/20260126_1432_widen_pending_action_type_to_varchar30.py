"""widen pending_action_type to varchar30

Widen pending_actions.action_type from varchar(20) to varchar(30)
to support the new DELETE_VINTED_LISTING action type (22 chars).

Applied to template_tenant and all user_X schemas.

Revision ID: e9e9ed10290d
Revises: 8df28affd5e2
Create Date: 2026-01-26 14:32:20.128284+01:00

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'e9e9ed10290d'
down_revision: Union[str, None] = '8df28affd5e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _get_tenant_schemas(conn) -> list[str]:
    """Get all tenant schemas (template + user_X)."""
    result = conn.execute(text(
        "SELECT schema_name FROM information_schema.schemata "
        "WHERE schema_name = 'template_tenant' OR schema_name LIKE 'user_%'"
    ))
    return [row[0] for row in result]


def upgrade() -> None:
    conn = op.get_bind()
    schemas = _get_tenant_schemas(conn)

    for schema in schemas:
        # Check if table exists in this schema
        exists = conn.execute(text(
            "SELECT 1 FROM information_schema.tables "
            "WHERE table_schema = :schema AND table_name = 'pending_actions'"
        ), {"schema": schema}).scalar()

        if exists:
            conn.execute(text(
                f"ALTER TABLE {schema}.pending_actions "
                f"ALTER COLUMN action_type TYPE varchar(30)"
            ))


def downgrade() -> None:
    conn = op.get_bind()
    schemas = _get_tenant_schemas(conn)

    for schema in schemas:
        exists = conn.execute(text(
            "SELECT 1 FROM information_schema.tables "
            "WHERE table_schema = :schema AND table_name = 'pending_actions'"
        ), {"schema": schema}).scalar()

        if exists:
            conn.execute(text(
                f"ALTER TABLE {schema}.pending_actions "
                f"ALTER COLUMN action_type TYPE varchar(20)"
            ))
