"""add CHECK constraints on product dimensions (dim1-dim6)

Defense-in-depth: ensure dimensions are within valid range (0-500 cm).
Issue #27 - Business Logic Audit.

Revision ID: d0e1f2a3b4c5
Revises: c9d2e3f4a5b6
Create Date: 2026-01-27
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = 'd0e1f2a3b4c5'
down_revision: Union[str, None] = 'c9d2e3f4a5b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DIMENSION_COLUMNS = ['dim1', 'dim2', 'dim3', 'dim4', 'dim5', 'dim6']
MAX_DIMENSION = 500


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
        # Check if products table exists
        exists = conn.execute(text(
            "SELECT EXISTS ("
            "  SELECT 1 FROM information_schema.tables "
            "  WHERE table_schema = :schema AND table_name = 'products'"
            ")"
        ), {"schema": schema}).scalar()

        if not exists:
            continue

        for col in DIMENSION_COLUMNS:
            constraint_name = f"check_{col}_range"

            # Check if constraint already exists (idempotent)
            constraint_exists = conn.execute(text(
                "SELECT EXISTS ("
                "  SELECT 1 FROM information_schema.check_constraints cc "
                "  JOIN information_schema.table_constraints tc "
                "    ON cc.constraint_name = tc.constraint_name "
                "    AND cc.constraint_schema = tc.constraint_schema "
                "  WHERE tc.table_schema = :schema "
                "    AND tc.table_name = 'products' "
                "    AND tc.constraint_name = :constraint_name"
                ")"
            ), {"schema": schema, "constraint_name": constraint_name}).scalar()

            if constraint_exists:
                continue

            conn.execute(text(
                f'ALTER TABLE "{schema}".products '
                f'ADD CONSTRAINT {constraint_name} '
                f'CHECK ({col} IS NULL OR ({col} >= 0 AND {col} <= {MAX_DIMENSION}))'
            ))


def downgrade() -> None:
    conn = op.get_bind()
    schemas = _get_tenant_schemas(conn)

    for schema in schemas:
        for col in DIMENSION_COLUMNS:
            constraint_name = f"check_{col}_range"

            # Check if constraint exists before dropping
            constraint_exists = conn.execute(text(
                "SELECT EXISTS ("
                "  SELECT 1 FROM information_schema.check_constraints cc "
                "  JOIN information_schema.table_constraints tc "
                "    ON cc.constraint_name = tc.constraint_name "
                "    AND cc.constraint_schema = tc.constraint_schema "
                "  WHERE tc.table_schema = :schema "
                "    AND tc.table_name = 'products' "
                "    AND tc.constraint_name = :constraint_name"
                ")"
            ), {"schema": schema, "constraint_name": constraint_name}).scalar()

            if constraint_exists:
                conn.execute(text(
                    f'ALTER TABLE "{schema}".products '
                    f'DROP CONSTRAINT {constraint_name}'
                ))
