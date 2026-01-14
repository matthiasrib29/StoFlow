"""Add ebay_payment_disputes table.

Revision ID: 20260114_1200
Revises: 20260114_1100
Create Date: 2026-01-14 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = "20260114_1200"
down_revision: Union[str, None] = "20260114_1100"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def get_user_schemas(conn) -> list[str]:
    """Get all user schemas (user_X pattern)."""
    result = conn.execute(
        text("""
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name LIKE 'user_%'
            ORDER BY schema_name
        """)
    )
    return [row[0] for row in result]


def table_exists(conn, schema: str, table: str) -> bool:
    """Check if table exists in schema."""
    result = conn.execute(
        text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = :schema
                AND table_name = :table
            )
        """),
        {"schema": schema, "table": table},
    )
    return result.scalar()


def upgrade() -> None:
    """Create ebay_payment_disputes table in all user schemas."""
    conn = op.get_bind()

    # Get all user schemas + template_tenant
    schemas = get_user_schemas(conn)
    schemas.append("template_tenant")

    for schema in schemas:
        # Skip if table already exists
        if table_exists(conn, schema, "ebay_payment_disputes"):
            print(f"Table {schema}.ebay_payment_disputes already exists, skipping")
            continue

        # Create table
        conn.execute(
            text(f"""
                CREATE TABLE {schema}.ebay_payment_disputes (
                    id SERIAL PRIMARY KEY,

                    -- eBay identifiers
                    payment_dispute_id VARCHAR(100) NOT NULL UNIQUE,
                    order_id VARCHAR(100),

                    -- Status fields
                    dispute_state VARCHAR(50),
                    reason VARCHAR(100),
                    reason_for_closure VARCHAR(100),

                    -- Seller response
                    seller_response VARCHAR(50),
                    note TEXT,

                    -- Amount
                    dispute_amount FLOAT,
                    dispute_currency VARCHAR(10),

                    -- Buyer info
                    buyer_username VARCHAR(100),

                    -- Revision (for API calls)
                    revision INTEGER,

                    -- Available choices (JSON array)
                    available_choices JSONB,

                    -- Evidence (JSON arrays)
                    evidence JSONB,
                    evidence_requests JSONB,

                    -- Line items (JSON array)
                    line_items JSONB,

                    -- Resolution (JSON object)
                    resolution JSONB,

                    -- Return address (JSON object)
                    return_address JSONB,

                    -- Dates
                    open_date TIMESTAMP,
                    respond_by_date TIMESTAMP,
                    closed_date TIMESTAMP,

                    -- Record timestamps
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
                )
            """)
        )

        # Create indexes
        conn.execute(
            text(f"""
                CREATE INDEX idx_{schema.replace('_', '')}_ebaypd_payment_dispute_id
                ON {schema}.ebay_payment_disputes (payment_dispute_id)
            """)
        )
        conn.execute(
            text(f"""
                CREATE INDEX idx_{schema.replace('_', '')}_ebaypd_order_id
                ON {schema}.ebay_payment_disputes (order_id)
            """)
        )
        conn.execute(
            text(f"""
                CREATE INDEX idx_{schema.replace('_', '')}_ebaypd_dispute_state
                ON {schema}.ebay_payment_disputes (dispute_state)
            """)
        )
        conn.execute(
            text(f"""
                CREATE INDEX idx_{schema.replace('_', '')}_ebaypd_reason
                ON {schema}.ebay_payment_disputes (reason)
            """)
        )
        conn.execute(
            text(f"""
                CREATE INDEX idx_{schema.replace('_', '')}_ebaypd_buyer_username
                ON {schema}.ebay_payment_disputes (buyer_username)
            """)
        )
        conn.execute(
            text(f"""
                CREATE INDEX idx_{schema.replace('_', '')}_ebaypd_respond_by_date
                ON {schema}.ebay_payment_disputes (respond_by_date)
            """)
        )

        print(f"Created table {schema}.ebay_payment_disputes")


def downgrade() -> None:
    """Drop ebay_payment_disputes table from all user schemas."""
    conn = op.get_bind()

    # Get all user schemas + template_tenant
    schemas = get_user_schemas(conn)
    schemas.append("template_tenant")

    for schema in schemas:
        if table_exists(conn, schema, "ebay_payment_disputes"):
            conn.execute(
                text(f"DROP TABLE IF EXISTS {schema}.ebay_payment_disputes CASCADE")
            )
            print(f"Dropped table {schema}.ebay_payment_disputes")
