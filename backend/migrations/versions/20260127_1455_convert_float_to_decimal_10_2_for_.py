"""convert Float to DECIMAL(10,2) for monetary columns in eBay models

Issue: Database Architecture Audit (Report 03)
Float columns cause precision loss for monetary values.
Convert to NUMERIC(10,2) for exact decimal representation.

Revision ID: 432b313a9d8f
Revises: d0e1f2a3b4c5
Create Date: 2026-01-27 14:55:27.371703+01:00

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '432b313a9d8f'
down_revision: Union[str, None] = 'd0e1f2a3b4c5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Columns to convert: (table_name, column_name)
MONETARY_COLUMNS = [
    ("ebay_orders", "total_price"),
    ("ebay_orders", "shipping_cost"),
    ("ebay_orders_products", "unit_price"),
    ("ebay_orders_products", "total_price"),
    ("ebay_returns", "refund_amount"),
    ("ebay_refunds", "refund_amount"),
    ("ebay_refunds", "original_amount"),
    ("ebay_payment_disputes", "dispute_amount"),
    ("ebay_inquiries", "claim_amount"),
    ("ebay_cancellations", "refund_amount"),
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
        for table, column in MONETARY_COLUMNS:
            if not _table_exists(conn, schema, table):
                continue

            conn.execute(text(
                f'ALTER TABLE "{schema}"."{table}" '
                f'ALTER COLUMN "{column}" TYPE NUMERIC(10,2) '
                f'USING "{column}"::NUMERIC(10,2)'
            ))


def downgrade() -> None:
    conn = op.get_bind()
    schemas = _get_tenant_schemas(conn)

    for schema in schemas:
        for table, column in MONETARY_COLUMNS:
            if not _table_exists(conn, schema, table):
                continue

            conn.execute(text(
                f'ALTER TABLE "{schema}"."{table}" '
                f'ALTER COLUMN "{column}" TYPE DOUBLE PRECISION '
                f'USING "{column}"::DOUBLE PRECISION'
            ))
