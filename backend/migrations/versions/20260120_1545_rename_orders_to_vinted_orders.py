"""rename_orders_to_vinted_orders

Rename tables to add vinted_ prefix for clarity:
- orders -> vinted_orders
- order_products -> vinted_order_products

Revision ID: e8f9a0b1c2d3
Revises: d7e8f9a0b1c2
Create Date: 2026-01-20 15:45:00

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'e8f9a0b1c2d3'
down_revision: Union[str, None] = 'd7e8f9a0b1c2'
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


def rename_tables_in_schema(conn, schema: str, to_vinted_prefix: bool = True) -> None:
    """Rename tables in a schema."""
    if to_vinted_prefix:
        # orders -> vinted_orders
        if table_exists(conn, schema, "orders") and not table_exists(conn, schema, "vinted_orders"):
            # Drop FK constraint first (order_products -> orders)
            if table_exists(conn, schema, "order_products"):
                conn.execute(text(f"""
                    ALTER TABLE {schema}.order_products
                    DROP CONSTRAINT IF EXISTS order_products_transaction_id_fkey
                """))

            conn.execute(text(f"ALTER TABLE {schema}.orders RENAME TO vinted_orders"))

            # Rename indexes
            conn.execute(text(f"ALTER INDEX IF EXISTS {schema}.idx_orders_buyer_id RENAME TO idx_vinted_orders_buyer_id"))
            conn.execute(text(f"ALTER INDEX IF EXISTS {schema}.idx_orders_status RENAME TO idx_vinted_orders_status"))
            conn.execute(text(f"ALTER INDEX IF EXISTS {schema}.idx_orders_created_at_vinted RENAME TO idx_vinted_orders_created_at_vinted"))

            print(f"  Renamed {schema}.orders -> {schema}.vinted_orders")

        # order_products -> vinted_order_products
        if table_exists(conn, schema, "order_products") and not table_exists(conn, schema, "vinted_order_products"):
            conn.execute(text(f"ALTER TABLE {schema}.order_products RENAME TO vinted_order_products"))

            # Re-add FK constraint with new table name
            conn.execute(text(f"""
                ALTER TABLE {schema}.vinted_order_products
                ADD CONSTRAINT vinted_order_products_transaction_id_fkey
                FOREIGN KEY (transaction_id) REFERENCES {schema}.vinted_orders(transaction_id) ON DELETE CASCADE
            """))

            # Rename indexes
            conn.execute(text(f"ALTER INDEX IF EXISTS {schema}.idx_order_products_transaction_id RENAME TO idx_vinted_order_products_transaction_id"))
            conn.execute(text(f"ALTER INDEX IF EXISTS {schema}.idx_order_products_vinted_item_id RENAME TO idx_vinted_order_products_vinted_item_id"))
            conn.execute(text(f"ALTER INDEX IF EXISTS {schema}.idx_order_products_product_id RENAME TO idx_vinted_order_products_product_id"))

            print(f"  Renamed {schema}.order_products -> {schema}.vinted_order_products")
    else:
        # Reverse: vinted_orders -> orders
        if table_exists(conn, schema, "vinted_orders") and not table_exists(conn, schema, "orders"):
            if table_exists(conn, schema, "vinted_order_products"):
                conn.execute(text(f"""
                    ALTER TABLE {schema}.vinted_order_products
                    DROP CONSTRAINT IF EXISTS vinted_order_products_transaction_id_fkey
                """))

            conn.execute(text(f"ALTER TABLE {schema}.vinted_orders RENAME TO orders"))

            conn.execute(text(f"ALTER INDEX IF EXISTS {schema}.idx_vinted_orders_buyer_id RENAME TO idx_orders_buyer_id"))
            conn.execute(text(f"ALTER INDEX IF EXISTS {schema}.idx_vinted_orders_status RENAME TO idx_orders_status"))
            conn.execute(text(f"ALTER INDEX IF EXISTS {schema}.idx_vinted_orders_created_at_vinted RENAME TO idx_orders_created_at_vinted"))

            print(f"  Renamed {schema}.vinted_orders -> {schema}.orders")

        if table_exists(conn, schema, "vinted_order_products") and not table_exists(conn, schema, "order_products"):
            conn.execute(text(f"ALTER TABLE {schema}.vinted_order_products RENAME TO order_products"))

            conn.execute(text(f"""
                ALTER TABLE {schema}.order_products
                ADD CONSTRAINT order_products_transaction_id_fkey
                FOREIGN KEY (transaction_id) REFERENCES {schema}.orders(transaction_id) ON DELETE CASCADE
            """))

            conn.execute(text(f"ALTER INDEX IF EXISTS {schema}.idx_vinted_order_products_transaction_id RENAME TO idx_order_products_transaction_id"))
            conn.execute(text(f"ALTER INDEX IF EXISTS {schema}.idx_vinted_order_products_vinted_item_id RENAME TO idx_order_products_vinted_item_id"))
            conn.execute(text(f"ALTER INDEX IF EXISTS {schema}.idx_vinted_order_products_product_id RENAME TO idx_order_products_product_id"))

            print(f"  Renamed {schema}.vinted_order_products -> {schema}.order_products")


def upgrade() -> None:
    """Rename tables to add vinted_ prefix."""
    conn = op.get_bind()

    print("=" * 60)
    print("Renaming tables: orders -> vinted_orders")
    print("=" * 60)

    # Rename in template_tenant
    print("\n[template_tenant]")
    rename_tables_in_schema(conn, "template_tenant", to_vinted_prefix=True)

    # Rename in all user schemas
    user_schemas = get_user_schemas(conn)
    for schema in user_schemas:
        print(f"\n[{schema}]")
        rename_tables_in_schema(conn, schema, to_vinted_prefix=True)

    print("\n" + "=" * 60)
    print("Rename complete!")
    print("=" * 60)


def downgrade() -> None:
    """Revert: remove vinted_ prefix from table names."""
    conn = op.get_bind()

    print("=" * 60)
    print("Reverting: vinted_orders -> orders")
    print("=" * 60)

    # Revert in template_tenant
    print("\n[template_tenant]")
    rename_tables_in_schema(conn, "template_tenant", to_vinted_prefix=False)

    # Revert in all user schemas
    user_schemas = get_user_schemas(conn)
    for schema in user_schemas:
        print(f"\n[{schema}]")
        rename_tables_in_schema(conn, schema, to_vinted_prefix=False)

    print("\nDowngrade complete!")
