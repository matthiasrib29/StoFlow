"""add_shipment_id_to_vinted_orders

Add shipment_id column to vinted_orders table.
This is needed to fetch the shipping label via /shipments/{id}/label_url

Revision ID: f9a0b1c2d3e4
Revises: e8f9a0b1c2d3
Create Date: 2026-01-20 16:30:00

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'f9a0b1c2d3e4'
down_revision: Union[str, None] = 'c8534674a69e'
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
    """Add shipment_id column to vinted_orders tables."""
    conn = op.get_bind()

    print("Adding shipment_id to vinted_orders tables...")

    # Add to template_tenant
    if table_exists(conn, "template_tenant", "vinted_orders"):
        if not column_exists(conn, "template_tenant", "vinted_orders", "shipment_id"):
            conn.execute(text("""
                ALTER TABLE template_tenant.vinted_orders
                ADD COLUMN shipment_id BIGINT
            """))
            conn.execute(text("""
                COMMENT ON COLUMN template_tenant.vinted_orders.shipment_id
                IS 'Vinted shipment ID (for label_url)'
            """))
            print("  Added to template_tenant.vinted_orders")

    # Add to all user schemas
    user_schemas = get_user_schemas(conn)
    for schema in user_schemas:
        if table_exists(conn, schema, "vinted_orders"):
            if not column_exists(conn, schema, "vinted_orders", "shipment_id"):
                conn.execute(text(f"""
                    ALTER TABLE {schema}.vinted_orders
                    ADD COLUMN shipment_id BIGINT
                """))
                print(f"  Added to {schema}.vinted_orders")

    print("Done!")


def downgrade() -> None:
    """Remove shipment_id column from vinted_orders tables."""
    conn = op.get_bind()

    print("Removing shipment_id from vinted_orders tables...")

    # Remove from template_tenant
    if table_exists(conn, "template_tenant", "vinted_orders"):
        if column_exists(conn, "template_tenant", "vinted_orders", "shipment_id"):
            conn.execute(text("""
                ALTER TABLE template_tenant.vinted_orders
                DROP COLUMN shipment_id
            """))
            print("  Removed from template_tenant.vinted_orders")

    # Remove from all user schemas
    user_schemas = get_user_schemas(conn)
    for schema in user_schemas:
        if table_exists(conn, schema, "vinted_orders"):
            if column_exists(conn, schema, "vinted_orders", "shipment_id"):
                conn.execute(text(f"""
                    ALTER TABLE {schema}.vinted_orders
                    DROP COLUMN shipment_id
                """))
                print(f"  Removed from {schema}.vinted_orders")

    print("Done!")
