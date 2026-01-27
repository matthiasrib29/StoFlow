"""add missing indexes on marketplace_jobs started_at and expires_at

Issue: Database Architecture Audit (Report 03)
These columns are used in cleanup queries (started_at) and expiration
queries (expires_at) but were missing indexes.

Revision ID: 654a38c4df6d
Revises: 432b313a9d8f
Create Date: 2026-01-27 14:59:18.734657+01:00

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '654a38c4df6d'
down_revision: Union[str, None] = '432b313a9d8f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

INDEXES = [
    ("idx_marketplace_jobs_started_at", "marketplace_jobs", "started_at"),
    ("idx_marketplace_jobs_expires_at", "marketplace_jobs", "expires_at"),
]


def _get_tenant_schemas(conn) -> list[str]:
    """Get all tenant schemas (user_X) + template_tenant."""
    result = conn.execute(text(
        "SELECT schema_name FROM information_schema.schemata "
        "WHERE schema_name LIKE 'user_%' OR schema_name = 'template_tenant' "
        "ORDER BY schema_name"
    ))
    return [row[0] for row in result]


def _table_exists(conn, schema: str, table: str) -> bool:
    """Check if a table exists in the given schema."""
    return conn.execute(text(
        "SELECT EXISTS ("
        "  SELECT 1 FROM information_schema.tables "
        "  WHERE table_schema = :schema AND table_name = :table"
        ")"
    ), {"schema": schema, "table": table}).scalar()


def upgrade() -> None:
    conn = op.get_bind()
    schemas = _get_tenant_schemas(conn)

    for schema in schemas:
        for idx_name, table, column in INDEXES:
            if not _table_exists(conn, schema, table):
                continue

            conn.execute(text(
                f'CREATE INDEX IF NOT EXISTS {idx_name} '
                f'ON "{schema}"."{table}" ("{column}")'
            ))


def downgrade() -> None:
    conn = op.get_bind()
    schemas = _get_tenant_schemas(conn)

    for schema in schemas:
        for idx_name, table, column in INDEXES:
            if not _table_exists(conn, schema, table):
                continue

            conn.execute(text(
                f'DROP INDEX IF EXISTS "{schema}".{idx_name}'
            ))
