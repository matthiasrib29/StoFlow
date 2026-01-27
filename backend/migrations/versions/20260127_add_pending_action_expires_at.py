"""add expires_at column to pending_actions

TTL for pending actions: auto-expire unconfirmed actions after 7 days.
Issue #3 - Business Logic Audit.

Revision ID: c9d2e3f4a5b6
Revises: b8c1d2e3f4a5
Create Date: 2026-01-27
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = 'c9d2e3f4a5b6'
down_revision: Union[str, None] = 'b8c1d2e3f4a5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _get_tenant_schemas(conn) -> list[str]:
    """Get all tenant schemas (user_X) + template_tenant."""
    result = conn.execute(text(
        "SELECT schema_name FROM information_schema.schemata "
        "WHERE schema_name LIKE 'user_%' OR schema_name = 'template_tenant' "
        "ORDER BY schema_name"
    ))
    return [row[0] for row in result]


def upgrade() -> None:
    conn = op.get_bind()
    schemas = _get_tenant_schemas(conn)

    for schema in schemas:
        # Check if pending_actions table exists
        exists = conn.execute(text(
            "SELECT EXISTS ("
            "  SELECT 1 FROM information_schema.tables "
            "  WHERE table_schema = :schema AND table_name = 'pending_actions'"
            ")"
        ), {"schema": schema}).scalar()

        if not exists:
            continue

        # Check if column already exists (idempotent)
        col_exists = conn.execute(text(
            "SELECT EXISTS ("
            "  SELECT 1 FROM information_schema.columns "
            "  WHERE table_schema = :schema "
            "    AND table_name = 'pending_actions' "
            "    AND column_name = 'expires_at'"
            ")"
        ), {"schema": schema}).scalar()

        if col_exists:
            continue

        conn.execute(text(
            f'ALTER TABLE "{schema}".pending_actions '
            f'ADD COLUMN expires_at TIMESTAMPTZ'
        ))


def downgrade() -> None:
    conn = op.get_bind()
    schemas = _get_tenant_schemas(conn)

    for schema in schemas:
        exists = conn.execute(text(
            "SELECT EXISTS ("
            "  SELECT 1 FROM information_schema.columns "
            "  WHERE table_schema = :schema "
            "    AND table_name = 'pending_actions' "
            "    AND column_name = 'expires_at'"
            ")"
        ), {"schema": schema}).scalar()

        if exists:
            conn.execute(text(
                f'ALTER TABLE "{schema}".pending_actions DROP COLUMN expires_at'
            ))
