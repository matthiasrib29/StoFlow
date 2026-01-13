"""add vinted order enrichment fields

Add new columns to vinted.orders for capturing more information:
- conversation_id, offer_id (Vinted IDs)
- vinted_status_code, vinted_status_text, transaction_user_status (status tracking)
- item_count (for bundles)
- buyer_photo_url, buyer_country_code, buyer_city, buyer_feedback_reputation (buyer info)

Revision ID: 20260113_1130
Revises: 20260112_1900_pricing
Create Date: 2026-01-13 11:30:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '20260113_1130'
down_revision: Union[str, None] = '20260112_1900_pricing'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def get_user_schemas(conn) -> list[str]:
    """Get all user schemas (user_X pattern)."""
    result = conn.execute(text("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%'
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


def column_exists(conn, schema: str, table: str, column: str) -> bool:
    """Check if column exists in table."""
    result = conn.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = :schema
            AND table_name = :table
            AND column_name = :column
        )
    """), {"schema": schema, "table": table, "column": column})
    return result.scalar()


def upgrade() -> None:
    """Add new columns to vinted.orders table."""
    conn = op.get_bind()

    # Columns to add with their SQL types
    new_columns = [
        ("conversation_id", "BIGINT", "Vinted conversation/thread ID (for messages)"),
        ("offer_id", "BIGINT", "Vinted offer ID"),
        ("vinted_status_code", "INTEGER", "Vinted status code (230=paid, 400+=completed)"),
        ("vinted_status_text", "VARCHAR(255)", "Vinted status text FR"),
        ("transaction_user_status", "VARCHAR(50)", "User action status (needs_action/waiting/completed/failed)"),
        ("item_count", "INTEGER DEFAULT 1", "Number of items in order"),
        ("buyer_photo_url", "TEXT", "Buyer profile photo URL"),
        ("buyer_country_code", "VARCHAR(10)", "Buyer country code (FR, DE, etc.)"),
        ("buyer_city", "VARCHAR(255)", "Buyer city"),
        ("buyer_feedback_reputation", "NUMERIC(3,2)", "Buyer reputation score (0-5)"),
    ]

    # Apply to vinted schema
    if table_exists(conn, "vinted", "orders"):
        for col_name, col_type, comment in new_columns:
            if not column_exists(conn, "vinted", "orders", col_name):
                conn.execute(text(f"""
                    ALTER TABLE vinted.orders
                    ADD COLUMN {col_name} {col_type}
                """))
                conn.execute(text(f"""
                    COMMENT ON COLUMN vinted.orders.{col_name} IS '{comment}'
                """))
                print(f"  Added vinted.orders.{col_name}")

    # Apply to template_tenant schema
    if table_exists(conn, "template_tenant", "orders"):
        for col_name, col_type, comment in new_columns:
            if not column_exists(conn, "template_tenant", "orders", col_name):
                conn.execute(text(f"""
                    ALTER TABLE template_tenant.orders
                    ADD COLUMN {col_name} {col_type}
                """))
                print(f"  Added template_tenant.orders.{col_name}")

    # Apply to all user schemas
    user_schemas = get_user_schemas(conn)
    for schema in user_schemas:
        if table_exists(conn, schema, "orders"):
            for col_name, col_type, _ in new_columns:
                if not column_exists(conn, schema, "orders", col_name):
                    conn.execute(text(f"""
                        ALTER TABLE {schema}.orders
                        ADD COLUMN {col_name} {col_type}
                    """))
            print(f"  Updated {schema}.orders")


def downgrade() -> None:
    """Remove added columns from vinted.orders table."""
    conn = op.get_bind()

    columns_to_remove = [
        "conversation_id",
        "offer_id",
        "vinted_status_code",
        "vinted_status_text",
        "transaction_user_status",
        "item_count",
        "buyer_photo_url",
        "buyer_country_code",
        "buyer_city",
        "buyer_feedback_reputation",
    ]

    # Remove from vinted schema
    if table_exists(conn, "vinted", "orders"):
        for col_name in columns_to_remove:
            if column_exists(conn, "vinted", "orders", col_name):
                conn.execute(text(f"""
                    ALTER TABLE vinted.orders
                    DROP COLUMN {col_name}
                """))

    # Remove from template_tenant schema
    if table_exists(conn, "template_tenant", "orders"):
        for col_name in columns_to_remove:
            if column_exists(conn, "template_tenant", "orders", col_name):
                conn.execute(text(f"""
                    ALTER TABLE template_tenant.orders
                    DROP COLUMN {col_name}
                """))

    # Remove from all user schemas
    user_schemas = get_user_schemas(conn)
    for schema in user_schemas:
        if table_exists(conn, schema, "orders"):
            for col_name in columns_to_remove:
                if column_exists(conn, schema, "orders", col_name):
                    conn.execute(text(f"""
                        ALTER TABLE {schema}.orders
                        DROP COLUMN {col_name}
                    """))
