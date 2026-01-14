"""Add ebay_inquiries table.

Revision ID: 20260114_1300
Revises: 20260114_1200
Create Date: 2026-01-14 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = "20260114_1300"
down_revision: Union[str, None] = "20260114_1200"
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
    """Create ebay_inquiries table in all user schemas."""
    conn = op.get_bind()

    # Get all user schemas + template_tenant
    schemas = get_user_schemas(conn)
    schemas.append("template_tenant")

    for schema in schemas:
        # Skip if table already exists
        if table_exists(conn, schema, "ebay_inquiries"):
            print(f"Table {schema}.ebay_inquiries already exists, skipping")
            continue

        # Create table
        conn.execute(
            text(f"""
                CREATE TABLE {schema}.ebay_inquiries (
                    id BIGSERIAL PRIMARY KEY,

                    -- eBay identifiers
                    inquiry_id VARCHAR(100) NOT NULL UNIQUE,
                    order_id VARCHAR(100),

                    -- Status fields
                    inquiry_state VARCHAR(50),
                    inquiry_status VARCHAR(100),
                    inquiry_type VARCHAR(50),

                    -- Claim amount
                    claim_amount FLOAT,
                    claim_currency VARCHAR(10),

                    -- Buyer info
                    buyer_username VARCHAR(100),
                    buyer_comments TEXT,

                    -- Seller response
                    seller_response VARCHAR(50),

                    -- Item info
                    item_id VARCHAR(100),
                    item_title TEXT,

                    -- Shipment info (if tracking provided)
                    shipment_tracking_number VARCHAR(200),
                    shipment_carrier VARCHAR(100),

                    -- Dates
                    creation_date TIMESTAMP WITH TIME ZONE,
                    respond_by_date TIMESTAMP WITH TIME ZONE,
                    closed_date TIMESTAMP WITH TIME ZONE,
                    escalation_date TIMESTAMP WITH TIME ZONE,

                    -- Raw data (for debugging)
                    raw_data JSONB,

                    -- Record timestamps
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
                )
            """)
        )

        # Create indexes
        conn.execute(
            text(f"""
                CREATE INDEX idx_{schema.replace('_', '')}_ebayinq_inquiry_id
                ON {schema}.ebay_inquiries (inquiry_id)
            """)
        )
        conn.execute(
            text(f"""
                CREATE INDEX idx_{schema.replace('_', '')}_ebayinq_order_id
                ON {schema}.ebay_inquiries (order_id)
            """)
        )
        conn.execute(
            text(f"""
                CREATE INDEX idx_{schema.replace('_', '')}_ebayinq_inquiry_state
                ON {schema}.ebay_inquiries (inquiry_state)
            """)
        )
        conn.execute(
            text(f"""
                CREATE INDEX idx_{schema.replace('_', '')}_ebayinq_inquiry_status
                ON {schema}.ebay_inquiries (inquiry_status)
            """)
        )
        conn.execute(
            text(f"""
                CREATE INDEX idx_{schema.replace('_', '')}_ebayinq_item_id
                ON {schema}.ebay_inquiries (item_id)
            """)
        )
        conn.execute(
            text(f"""
                CREATE INDEX idx_{schema.replace('_', '')}_ebayinq_respond_by_date
                ON {schema}.ebay_inquiries (respond_by_date)
            """)
        )

        print(f"Created table {schema}.ebay_inquiries")


def downgrade() -> None:
    """Drop ebay_inquiries table from all user schemas."""
    conn = op.get_bind()

    # Get all user schemas + template_tenant
    schemas = get_user_schemas(conn)
    schemas.append("template_tenant")

    for schema in schemas:
        if table_exists(conn, schema, "ebay_inquiries"):
            conn.execute(
                text(f"DROP TABLE IF EXISTS {schema}.ebay_inquiries CASCADE")
            )
            print(f"Dropped table {schema}.ebay_inquiries")
