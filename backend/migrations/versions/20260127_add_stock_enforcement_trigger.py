"""add stock enforcement trigger

Defense-in-depth: PL/pgSQL trigger that prevents stock_quantity from going
negative on UPDATE. The CheckConstraint already exists on the model, but this
trigger also blocks raw SQL bypasses.

Issue #28 - Business Logic Audit.

Revision ID: b8c1d2e3f4a5
Revises: a3f7e1c2d4b6
Create Date: 2026-01-27
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = 'b8c1d2e3f4a5'
down_revision: Union[str, None] = 'a3f7e1c2d4b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# PL/pgSQL function that raises an exception if stock goes negative
CREATE_FUNCTION_SQL = """
CREATE OR REPLACE FUNCTION enforce_non_negative_stock()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.stock_quantity < 0 THEN
        RAISE EXCEPTION 'stock_quantity cannot be negative (got %)', NEW.stock_quantity
            USING ERRCODE = 'check_violation';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

DROP_FUNCTION_SQL = "DROP FUNCTION IF EXISTS enforce_non_negative_stock();"

TRIGGER_NAME = "trg_enforce_non_negative_stock"


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

    # 1. Create the function in public schema (shared)
    conn.execute(text(CREATE_FUNCTION_SQL))

    # 2. Fan-out: create trigger on products table in each tenant schema
    schemas = _get_tenant_schemas(conn)
    for schema in schemas:
        # Check if products table exists in this schema
        exists = conn.execute(text(
            "SELECT EXISTS ("
            "  SELECT 1 FROM information_schema.tables "
            "  WHERE table_schema = :schema AND table_name = 'products'"
            ")"
        ), {"schema": schema}).scalar()

        if not exists:
            continue

        # Drop trigger if it already exists (idempotent)
        conn.execute(text(
            f'DROP TRIGGER IF EXISTS {TRIGGER_NAME} ON "{schema}".products'
        ))

        # Create trigger
        conn.execute(text(
            f'CREATE TRIGGER {TRIGGER_NAME} '
            f'BEFORE UPDATE ON "{schema}".products '
            f'FOR EACH ROW EXECUTE FUNCTION enforce_non_negative_stock()'
        ))


def downgrade() -> None:
    conn = op.get_bind()

    # 1. Drop triggers from all tenant schemas
    schemas = _get_tenant_schemas(conn)
    for schema in schemas:
        conn.execute(text(
            f'DROP TRIGGER IF EXISTS {TRIGGER_NAME} ON "{schema}".products'
        ))

    # 2. Drop the function
    conn.execute(text(DROP_FUNCTION_SQL))
