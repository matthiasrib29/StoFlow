"""add ebay_refunds table

Revision ID: 20260114_1100
Revises: 20260114_0800
Create Date: 2026-01-14 11:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy import text

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260114_1100"
down_revision: Union[str, None] = "20260114_0800"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def get_user_schemas(conn) -> list[str]:
    """Get all user schemas (user_*)."""
    result = conn.execute(
        text(
            """
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name LIKE 'user_%'
            ORDER BY schema_name
            """
        )
    )
    return [row[0] for row in result.fetchall()]


def table_exists(conn, schema: str, table: str) -> bool:
    """Check if a table exists in a schema."""
    result = conn.execute(
        text(
            """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = :schema
                AND table_name = :table
            )
            """
        ),
        {"schema": schema, "table": table},
    )
    return result.scalar()


def create_ebay_refunds_table(conn, schema: str) -> None:
    """Create ebay_refunds table in the given schema."""
    conn.execute(
        text(
            f"""
            CREATE TABLE IF NOT EXISTS {schema}.ebay_refunds (
                id BIGSERIAL PRIMARY KEY,
                refund_id TEXT NOT NULL UNIQUE,
                order_id TEXT REFERENCES {schema}.ebay_orders(order_id) ON DELETE SET NULL,

                -- Source
                refund_source TEXT,
                return_id TEXT,
                cancel_id TEXT,

                -- Status
                refund_status TEXT,

                -- Amount
                refund_amount FLOAT,
                refund_currency TEXT,
                original_amount FLOAT,

                -- Reason
                reason TEXT,
                comment TEXT,

                -- Buyer
                buyer_username TEXT,

                -- References
                refund_reference_id TEXT,
                transaction_id TEXT,
                line_item_id TEXT,

                -- Dates
                refund_date TIMESTAMPTZ,
                creation_date TIMESTAMPTZ,

                -- Raw data
                raw_data JSONB,

                -- Metadata
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
    )

    # Create indexes
    conn.execute(
        text(
            f"CREATE INDEX IF NOT EXISTS idx_{schema}_ebay_refunds_order_id "
            f"ON {schema}.ebay_refunds(order_id)"
        )
    )
    conn.execute(
        text(
            f"CREATE INDEX IF NOT EXISTS idx_{schema}_ebay_refunds_refund_status "
            f"ON {schema}.ebay_refunds(refund_status)"
        )
    )
    conn.execute(
        text(
            f"CREATE INDEX IF NOT EXISTS idx_{schema}_ebay_refunds_refund_source "
            f"ON {schema}.ebay_refunds(refund_source)"
        )
    )
    conn.execute(
        text(
            f"CREATE INDEX IF NOT EXISTS idx_{schema}_ebay_refunds_refund_date "
            f"ON {schema}.ebay_refunds(refund_date)"
        )
    )
    conn.execute(
        text(
            f"CREATE INDEX IF NOT EXISTS idx_{schema}_ebay_refunds_return_id "
            f"ON {schema}.ebay_refunds(return_id)"
        )
    )
    conn.execute(
        text(
            f"CREATE INDEX IF NOT EXISTS idx_{schema}_ebay_refunds_cancel_id "
            f"ON {schema}.ebay_refunds(cancel_id)"
        )
    )


def upgrade() -> None:
    """Create ebay_refunds table in template_tenant and all user schemas."""
    conn = op.get_bind()

    # 1. Create in template_tenant first
    if not table_exists(conn, "template_tenant", "ebay_refunds"):
        create_ebay_refunds_table(conn, "template_tenant")
        print("Created ebay_refunds in template_tenant")

    # 2. Create in all user schemas
    user_schemas = get_user_schemas(conn)
    for schema in user_schemas:
        if not table_exists(conn, schema, "ebay_refunds"):
            create_ebay_refunds_table(conn, schema)
            print(f"Created ebay_refunds in {schema}")
        else:
            print(f"Table ebay_refunds already exists in {schema}")


def downgrade() -> None:
    """Drop ebay_refunds table from all schemas."""
    conn = op.get_bind()

    # Drop from user schemas
    user_schemas = get_user_schemas(conn)
    for schema in user_schemas:
        if table_exists(conn, schema, "ebay_refunds"):
            conn.execute(text(f"DROP TABLE IF EXISTS {schema}.ebay_refunds CASCADE"))
            print(f"Dropped ebay_refunds from {schema}")

    # Drop from template_tenant
    if table_exists(conn, "template_tenant", "ebay_refunds"):
        conn.execute(
            text("DROP TABLE IF EXISTS template_tenant.ebay_refunds CASCADE")
        )
        print("Dropped ebay_refunds from template_tenant")
