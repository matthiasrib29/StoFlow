"""add_ebay_cancellations_table

Create ebay_cancellations table in all user schemas for storing eBay cancellation requests.
Part of eBay order management improvement (Phase 6: Cancellations Backend).

Revision ID: e4b0d0147f2f
Revises: d3a9c9036e1e
Create Date: 2026-01-14 08:00:00

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'e4b0d0147f2f'
down_revision: Union[str, None] = 'd3a9c9036e1e'
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
    """Create ebay_cancellations table in all user schemas."""
    conn = op.get_bind()

    # Get all user schemas
    schemas = get_user_schemas(conn)
    print(f"Creating ebay_cancellations table in {len(schemas)} schemas...")

    for schema in schemas:
        # Skip if table already exists
        if table_exists(conn, schema, "ebay_cancellations"):
            print(f"  {schema}.ebay_cancellations already exists, skipping")
            continue

        # Check if ebay_orders table exists (for FK reference)
        has_orders = table_exists(conn, schema, "ebay_orders")

        # Create table
        conn.execute(text(f"""
            CREATE TABLE {schema}.ebay_cancellations (
                -- Primary Key
                id BIGSERIAL PRIMARY KEY,

                -- Cancellation Identification
                cancel_id TEXT NOT NULL,
                order_id TEXT,

                -- Status
                cancel_status TEXT,
                cancel_state TEXT,
                cancel_reason TEXT,

                -- Request Info
                requestor_role TEXT,
                request_date TIMESTAMP WITH TIME ZONE,
                response_due_date TIMESTAMP WITH TIME ZONE,

                -- Refund
                refund_amount FLOAT,
                refund_currency TEXT,
                refund_status TEXT,

                -- Buyer Info
                buyer_username TEXT,
                buyer_comments TEXT,

                -- Seller Info
                seller_comments TEXT,
                reject_reason TEXT,

                -- Shipping Info (for rejection)
                tracking_number TEXT,
                carrier TEXT,
                shipped_date TIMESTAMP WITH TIME ZONE,

                -- Dates
                creation_date TIMESTAMP WITH TIME ZONE,
                closed_date TIMESTAMP WITH TIME ZONE,

                -- Raw eBay Data
                raw_data JSONB,

                -- Metadata
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,

                -- Constraints
                CONSTRAINT uq_{schema.replace('user_', 'u')}_cancels_cancel_id UNIQUE (cancel_id)
            )
        """))

        # Create indexes
        conn.execute(text(f"""
            CREATE INDEX idx_{schema.replace('user_', 'u')}_cancels_cancel_id
            ON {schema}.ebay_cancellations(cancel_id)
        """))

        conn.execute(text(f"""
            CREATE INDEX idx_{schema.replace('user_', 'u')}_cancels_order_id
            ON {schema}.ebay_cancellations(order_id)
        """))

        conn.execute(text(f"""
            CREATE INDEX idx_{schema.replace('user_', 'u')}_cancels_status
            ON {schema}.ebay_cancellations(cancel_status)
        """))

        conn.execute(text(f"""
            CREATE INDEX idx_{schema.replace('user_', 'u')}_cancels_state
            ON {schema}.ebay_cancellations(cancel_state)
        """))

        conn.execute(text(f"""
            CREATE INDEX idx_{schema.replace('user_', 'u')}_cancels_response_due
            ON {schema}.ebay_cancellations(response_due_date)
        """))

        # Add FK constraint only if ebay_orders exists
        if has_orders:
            conn.execute(text(f"""
                ALTER TABLE {schema}.ebay_cancellations
                ADD CONSTRAINT fk_{schema.replace('user_', 'u')}_cancels_order
                FOREIGN KEY (order_id) REFERENCES {schema}.ebay_orders(order_id)
                ON DELETE SET NULL
            """))

        print(f"  Created {schema}.ebay_cancellations" + (" with FK" if has_orders else ""))

    print("Done!")


def downgrade() -> None:
    """Drop ebay_cancellations table from all user schemas."""
    conn = op.get_bind()

    schemas = get_user_schemas(conn)
    print(f"Dropping ebay_cancellations table from {len(schemas)} schemas...")

    for schema in schemas:
        if table_exists(conn, schema, "ebay_cancellations"):
            conn.execute(text(f"DROP TABLE IF EXISTS {schema}.ebay_cancellations CASCADE"))
            print(f"  Dropped {schema}.ebay_cancellations")

    print("Done!")
