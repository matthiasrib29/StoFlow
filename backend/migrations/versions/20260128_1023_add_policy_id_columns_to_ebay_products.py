"""add policy_id columns to ebay_products

Revision ID: efafc37b381d
Revises: 0e1eae92f46a
Create Date: 2026-01-28 10:23:34.473304+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'efafc37b381d'
down_revision: Union[str, None] = '0e1eae92f46a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _get_user_schemas(conn) -> list[str]:
    """Get all user schemas."""
    result = conn.execute(
        sa.text("SELECT schema_name FROM information_schema.schemata WHERE schema_name LIKE 'user_%' ORDER BY schema_name")
    )
    return [row[0] for row in result]


def _table_exists(conn, schema: str, table: str) -> bool:
    """Check if table exists in schema."""
    result = conn.execute(
        sa.text("SELECT 1 FROM information_schema.tables WHERE table_schema = :schema AND table_name = :table"),
        {"schema": schema, "table": table},
    )
    return result.fetchone() is not None


def _column_exists(conn, schema: str, table: str, column: str) -> bool:
    """Check if column exists in table."""
    result = conn.execute(
        sa.text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_schema = :schema AND table_name = :table AND column_name = :column"
        ),
        {"schema": schema, "table": table, "column": column},
    )
    return result.fetchone() is not None


COLUMNS = [
    ("payment_policy_id", sa.String(50), "eBay payment policy ID"),
    ("fulfillment_policy_id", sa.String(50), "eBay fulfillment (shipping) policy ID"),
    ("return_policy_id", sa.String(50), "eBay return policy ID"),
]


def upgrade() -> None:
    conn = op.get_bind()
    schemas = _get_user_schemas(conn)

    for schema in schemas:
        if not _table_exists(conn, schema, "ebay_products"):
            continue

        for col_name, col_type, comment in COLUMNS:
            if not _column_exists(conn, schema, "ebay_products", col_name):
                op.add_column(
                    "ebay_products",
                    sa.Column(col_name, col_type, nullable=True, comment=comment),
                    schema=schema,
                )


def downgrade() -> None:
    conn = op.get_bind()
    schemas = _get_user_schemas(conn)

    for schema in schemas:
        if not _table_exists(conn, schema, "ebay_products"):
            continue

        for col_name, _, _ in COLUMNS:
            if _column_exists(conn, schema, "ebay_products", col_name):
                op.drop_column("ebay_products", col_name, schema=schema)
