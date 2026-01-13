"""add_ebay_returns_table

Create ebay_returns table in all user schemas for storing eBay return requests.
Part of eBay order management improvement (Phase 2: Returns Backend Core).

Revision ID: d3a9c9036e1e
Revises: 3796a01d0b82
Create Date: 2026-01-13 19:44:50

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'd3a9c9036e1e'
down_revision: Union[str, None] = '3796a01d0b82'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def get_user_schemas(conn) -> list[str]:
    """Get all user schemas (user_X pattern) plus template_tenant."""
    result = conn.execute(text("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%'
           OR schema_name = 'template_tenant'
        ORDER BY schema_name
    """))
    return [row[0] for row in result]


def table_exists(conn, schema: str, table: str) -> bool:
    """Check if table exists in schema."""
    result = conn.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = :schema AND table_name = :table
        )
    """), {"schema": schema, "table": table})
    return result.scalar()


def upgrade() -> None:
    """Create ebay_returns table in all user schemas."""
    conn = op.get_bind()

    # Get all user schemas
    schemas = get_user_schemas(conn)
    print(f"Creating ebay_returns table in {len(schemas)} schemas...")

    for schema in schemas:
        # Skip if table already exists
        if table_exists(conn, schema, "ebay_returns"):
            print(f"  {schema}.ebay_returns already exists, skipping")
            continue

        # Check if ebay_orders table exists (for FK reference)
        has_orders = table_exists(conn, schema, "ebay_orders")

        # Create table
        conn.execute(text(f"""
            CREATE TABLE {schema}.ebay_returns (
                -- Primary Key
                id BIGSERIAL PRIMARY KEY,

                -- Return Identification
                return_id TEXT NOT NULL,
                order_id TEXT,

                -- Status
                status TEXT,
                state TEXT,
                return_type TEXT,

                -- Reason
                reason TEXT,
                reason_detail TEXT,

                -- Refund
                refund_amount FLOAT,
                refund_currency TEXT,
                refund_status TEXT,

                -- Buyer Info
                buyer_username TEXT,
                buyer_comments TEXT,

                -- Seller Info
                seller_comments TEXT,
                rma_number TEXT,

                -- Return Shipping
                return_tracking_number TEXT,
                return_carrier TEXT,

                -- Dates
                creation_date TIMESTAMP WITH TIME ZONE,
                deadline_date TIMESTAMP WITH TIME ZONE,
                closed_date TIMESTAMP WITH TIME ZONE,
                received_date TIMESTAMP WITH TIME ZONE,

                -- Raw eBay Data
                raw_data JSONB,

                -- Metadata
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,

                -- Constraints
                CONSTRAINT uq_{schema.replace('user_', 'u')}_returns_return_id UNIQUE (return_id)
            )
        """))

        # Create indexes
        conn.execute(text(f"""
            CREATE INDEX idx_{schema.replace('user_', 'u')}_returns_return_id
            ON {schema}.ebay_returns(return_id)
        """))

        conn.execute(text(f"""
            CREATE INDEX idx_{schema.replace('user_', 'u')}_returns_order_id
            ON {schema}.ebay_returns(order_id)
        """))

        conn.execute(text(f"""
            CREATE INDEX idx_{schema.replace('user_', 'u')}_returns_status
            ON {schema}.ebay_returns(status)
        """))

        conn.execute(text(f"""
            CREATE INDEX idx_{schema.replace('user_', 'u')}_returns_state
            ON {schema}.ebay_returns(state)
        """))

        conn.execute(text(f"""
            CREATE INDEX idx_{schema.replace('user_', 'u')}_returns_deadline
            ON {schema}.ebay_returns(deadline_date)
        """))

        # Add FK constraint only if ebay_orders exists
        if has_orders:
            conn.execute(text(f"""
                ALTER TABLE {schema}.ebay_returns
                ADD CONSTRAINT fk_{schema.replace('user_', 'u')}_returns_order
                FOREIGN KEY (order_id) REFERENCES {schema}.ebay_orders(order_id)
                ON DELETE SET NULL
            """))

        print(f"  Created {schema}.ebay_returns" + (" with FK" if has_orders else ""))

    print("Done!")


def downgrade() -> None:
    """Drop ebay_returns table from all user schemas."""
    conn = op.get_bind()

    schemas = get_user_schemas(conn)
    print(f"Dropping ebay_returns table from {len(schemas)} schemas...")

    for schema in schemas:
        if table_exists(conn, schema, "ebay_returns"):
            conn.execute(text(f"DROP TABLE IF EXISTS {schema}.ebay_returns CASCADE"))
            print(f"  Dropped {schema}.ebay_returns")

    print("Done!")
