"""move_vinted_orders_to_tenant

Migrate VintedOrder and VintedOrderProduct tables from vinted schema to tenant schema.
This provides proper multi-tenant isolation (one schema per user).

Steps:
1. Create tables in template_tenant (for new users)
2. Create tables in all existing user_X schemas
3. Migrate data from vinted.orders to user_X.orders based on user_id
4. Rename old tables as backup (vinted.orders_backup_YYYYMMDD)

Revision ID: d7e8f9a0b1c2
Revises: c8534674a69e
Create Date: 2026-01-20 15:30:00

"""
from typing import Sequence, Union
from datetime import datetime

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'd7e8f9a0b1c2'
down_revision: Union[str, None] = 'c8534674a69e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Backup suffix with today's date
BACKUP_DATE = datetime.now().strftime('%Y%m%d')


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


def schema_exists(conn, schema: str) -> bool:
    """Check if schema exists."""
    result = conn.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.schemata
            WHERE schema_name = :schema
        )
    """), {"schema": schema})
    return result.scalar()


def create_orders_table_ddl(schema: str) -> str:
    """Generate DDL for orders table."""
    return f"""
        CREATE TABLE IF NOT EXISTS {schema}.orders (
            transaction_id BIGINT PRIMARY KEY,
            conversation_id BIGINT,
            offer_id BIGINT,
            buyer_id BIGINT,
            buyer_login VARCHAR(255),
            buyer_photo_url TEXT,
            buyer_country_code VARCHAR(10),
            buyer_city VARCHAR(255),
            buyer_feedback_reputation NUMERIC(3,2),
            seller_id BIGINT,
            seller_login VARCHAR(255),
            status VARCHAR(50),
            vinted_status_code INTEGER,
            vinted_status_text VARCHAR(255),
            transaction_user_status VARCHAR(50),
            item_count INTEGER DEFAULT 1,
            total_price NUMERIC(10,2),
            currency VARCHAR(3) DEFAULT 'EUR',
            shipping_price NUMERIC(10,2),
            service_fee NUMERIC(10,2),
            buyer_protection_fee NUMERIC(10,2),
            seller_revenue NUMERIC(10,2),
            tracking_number VARCHAR(100),
            carrier VARCHAR(100),
            created_at_vinted TIMESTAMP WITH TIME ZONE,
            shipped_at TIMESTAMP WITH TIME ZONE,
            delivered_at TIMESTAMP WITH TIME ZONE,
            completed_at TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        )
    """


def create_order_products_table_ddl(schema: str) -> str:
    """Generate DDL for order_products table."""
    return f"""
        CREATE TABLE IF NOT EXISTS {schema}.order_products (
            id SERIAL PRIMARY KEY,
            transaction_id BIGINT NOT NULL REFERENCES {schema}.orders(transaction_id) ON DELETE CASCADE,
            vinted_item_id BIGINT,
            product_id BIGINT,
            title VARCHAR(255),
            price NUMERIC(10,2),
            size VARCHAR(100),
            brand VARCHAR(255),
            photo_url TEXT,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        )
    """


def create_indexes(conn, schema: str) -> None:
    """Create indexes for orders and order_products tables."""
    # Orders indexes
    conn.execute(text(f"""
        CREATE INDEX IF NOT EXISTS idx_orders_buyer_id ON {schema}.orders(buyer_id)
    """))
    conn.execute(text(f"""
        CREATE INDEX IF NOT EXISTS idx_orders_status ON {schema}.orders(status)
    """))
    conn.execute(text(f"""
        CREATE INDEX IF NOT EXISTS idx_orders_created_at_vinted ON {schema}.orders(created_at_vinted)
    """))

    # Order products indexes
    conn.execute(text(f"""
        CREATE INDEX IF NOT EXISTS idx_order_products_transaction_id ON {schema}.order_products(transaction_id)
    """))
    conn.execute(text(f"""
        CREATE INDEX IF NOT EXISTS idx_order_products_vinted_item_id ON {schema}.order_products(vinted_item_id)
    """))
    conn.execute(text(f"""
        CREATE INDEX IF NOT EXISTS idx_order_products_product_id ON {schema}.order_products(product_id)
    """))


def upgrade() -> None:
    """Migrate vinted.orders to tenant schema (multi-tenant)."""
    conn = op.get_bind()

    print("=" * 60)
    print("Migration: Move VintedOrder to tenant schema")
    print("=" * 60)

    # =========================================================================
    # Step 1: Create tables in template_tenant
    # =========================================================================
    print("\n[Step 1] Creating tables in template_tenant...")

    if not schema_exists(conn, "template_tenant"):
        conn.execute(text("CREATE SCHEMA template_tenant"))
        print("  Created schema template_tenant")

    if not table_exists(conn, "template_tenant", "orders"):
        conn.execute(text(create_orders_table_ddl("template_tenant")))
        print("  Created template_tenant.orders")
    else:
        print("  template_tenant.orders already exists")

    if not table_exists(conn, "template_tenant", "order_products"):
        conn.execute(text(create_order_products_table_ddl("template_tenant")))
        print("  Created template_tenant.order_products")
    else:
        print("  template_tenant.order_products already exists")

    create_indexes(conn, "template_tenant")
    print("  Indexes created/verified")

    # =========================================================================
    # Step 2: Create tables in all existing user_X schemas
    # =========================================================================
    print("\n[Step 2] Creating tables in user schemas...")

    user_schemas = get_user_schemas(conn)
    print(f"  Found {len(user_schemas)} user schemas: {user_schemas}")

    for schema in user_schemas:
        if not table_exists(conn, schema, "orders"):
            conn.execute(text(create_orders_table_ddl(schema)))
            print(f"  Created {schema}.orders")

        if not table_exists(conn, schema, "order_products"):
            conn.execute(text(create_order_products_table_ddl(schema)))
            print(f"  Created {schema}.order_products")

        create_indexes(conn, schema)

    # =========================================================================
    # Step 3: Migrate data from vinted.orders to user_X.orders
    # =========================================================================
    print("\n[Step 3] Migrating data from vinted schema...")

    if not table_exists(conn, "vinted", "orders"):
        print("  No vinted.orders table found, skipping data migration")
    else:
        # Get distinct user_ids from vinted.orders
        # Note: vinted.orders doesn't have user_id column, so we need to infer from seller_id
        # Actually, looking at the model, there's no user_id column.
        # We need to link via seller_id to users.vinted_user_id or similar

        # First, check if there's a user_id column (might have been added)
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'vinted'
                AND table_name = 'orders'
                AND column_name = 'user_id'
            )
        """))
        has_user_id = result.scalar()

        if has_user_id:
            # Migrate by user_id
            result = conn.execute(text("""
                SELECT DISTINCT user_id FROM vinted.orders WHERE user_id IS NOT NULL
            """))
            user_ids = [row[0] for row in result]

            print(f"  Found orders for {len(user_ids)} users")

            for user_id in user_ids:
                target_schema = f"user_{user_id}"

                if target_schema not in user_schemas:
                    print(f"  WARNING: Schema {target_schema} does not exist, skipping user {user_id}")
                    continue

                # Copy orders
                conn.execute(text(f"""
                    INSERT INTO {target_schema}.orders
                    SELECT transaction_id, conversation_id, offer_id, buyer_id, buyer_login,
                           buyer_photo_url, buyer_country_code, buyer_city, buyer_feedback_reputation,
                           seller_id, seller_login, status, vinted_status_code, vinted_status_text,
                           transaction_user_status, item_count, total_price, currency, shipping_price,
                           service_fee, buyer_protection_fee, seller_revenue, tracking_number, carrier,
                           created_at_vinted, shipped_at, delivered_at, completed_at, created_at, updated_at
                    FROM vinted.orders
                    WHERE user_id = :user_id
                    ON CONFLICT (transaction_id) DO NOTHING
                """), {"user_id": user_id})

                # Copy order_products
                conn.execute(text(f"""
                    INSERT INTO {target_schema}.order_products (transaction_id, vinted_item_id, product_id, title, price, size, brand, photo_url, created_at)
                    SELECT op.transaction_id, op.vinted_item_id, op.product_id, op.title, op.price, op.size, op.brand, op.photo_url, op.created_at
                    FROM vinted.order_products op
                    JOIN vinted.orders o ON o.transaction_id = op.transaction_id
                    WHERE o.user_id = :user_id
                    ON CONFLICT DO NOTHING
                """), {"user_id": user_id})

                # Count migrated
                result = conn.execute(text(f"""
                    SELECT COUNT(*) FROM {target_schema}.orders
                """))
                count = result.scalar()
                print(f"  Migrated to {target_schema}: {count} orders")

            # Check for orphan orders (user_id IS NULL)
            result = conn.execute(text("""
                SELECT COUNT(*) FROM vinted.orders WHERE user_id IS NULL
            """))
            orphan_count = result.scalar()
            if orphan_count > 0:
                print(f"  WARNING: {orphan_count} orders with NULL user_id (orphans)")

        else:
            # No user_id column - try to infer from seller_id matching users.vinted_user_id
            print("  No user_id column found in vinted.orders")
            print("  Attempting to match seller_id with users.vinted_user_id...")

            # Check if users table has vinted_user_id
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = 'public'
                    AND table_name = 'users'
                    AND column_name = 'vinted_user_id'
                )
            """))
            has_vinted_user_id = result.scalar()

            if has_vinted_user_id:
                # Get user mappings
                result = conn.execute(text("""
                    SELECT id, vinted_user_id FROM public.users WHERE vinted_user_id IS NOT NULL
                """))
                user_mappings = {row[1]: row[0] for row in result}

                print(f"  Found {len(user_mappings)} users with vinted_user_id")

                # For each user, migrate their orders
                for vinted_user_id, user_id in user_mappings.items():
                    target_schema = f"user_{user_id}"

                    if target_schema not in user_schemas:
                        print(f"  WARNING: Schema {target_schema} does not exist")
                        continue

                    # Copy orders where seller_id matches
                    conn.execute(text(f"""
                        INSERT INTO {target_schema}.orders
                        SELECT transaction_id, conversation_id, offer_id, buyer_id, buyer_login,
                               buyer_photo_url, buyer_country_code, buyer_city, buyer_feedback_reputation,
                               seller_id, seller_login, status, vinted_status_code, vinted_status_text,
                               transaction_user_status, item_count, total_price, currency, shipping_price,
                               service_fee, buyer_protection_fee, seller_revenue, tracking_number, carrier,
                               created_at_vinted, shipped_at, delivered_at, completed_at, created_at, updated_at
                        FROM vinted.orders
                        WHERE seller_id = :seller_id
                        ON CONFLICT (transaction_id) DO NOTHING
                    """), {"seller_id": vinted_user_id})

                    # Copy order_products
                    conn.execute(text(f"""
                        INSERT INTO {target_schema}.order_products (transaction_id, vinted_item_id, product_id, title, price, size, brand, photo_url, created_at)
                        SELECT op.transaction_id, op.vinted_item_id, op.product_id, op.title, op.price, op.size, op.brand, op.photo_url, op.created_at
                        FROM vinted.order_products op
                        JOIN vinted.orders o ON o.transaction_id = op.transaction_id
                        WHERE o.seller_id = :seller_id
                        ON CONFLICT DO NOTHING
                    """), {"seller_id": vinted_user_id})

                    result = conn.execute(text(f"""
                        SELECT COUNT(*) FROM {target_schema}.orders
                    """))
                    count = result.scalar()
                    print(f"  Migrated to {target_schema}: {count} orders (seller_id={vinted_user_id})")
            else:
                print("  WARNING: Cannot migrate data - no user_id column and no vinted_user_id in users table")
                print("  Orders will remain in vinted.orders_backup table")

    # =========================================================================
    # Step 4: Rename old tables as backup
    # =========================================================================
    print(f"\n[Step 4] Creating backup tables (suffix: {BACKUP_DATE})...")

    if table_exists(conn, "vinted", "orders"):
        backup_name = f"orders_backup_{BACKUP_DATE}"
        if not table_exists(conn, "vinted", backup_name):
            conn.execute(text(f"ALTER TABLE vinted.orders RENAME TO {backup_name}"))
            print(f"  Renamed vinted.orders -> vinted.{backup_name}")
        else:
            print(f"  Backup vinted.{backup_name} already exists")

    if table_exists(conn, "vinted", "order_products"):
        backup_name = f"order_products_backup_{BACKUP_DATE}"
        if not table_exists(conn, "vinted", backup_name):
            conn.execute(text(f"ALTER TABLE vinted.order_products RENAME TO {backup_name}"))
            print(f"  Renamed vinted.order_products -> vinted.{backup_name}")
        else:
            print(f"  Backup vinted.{backup_name} already exists")

    print("\n" + "=" * 60)
    print("Migration complete!")
    print("=" * 60)


def downgrade() -> None:
    """Revert migration - restore vinted schema tables from backup."""
    conn = op.get_bind()

    print("=" * 60)
    print("Downgrade: Restore VintedOrder to vinted schema")
    print("=" * 60)

    # Restore backup tables
    backup_orders = f"orders_backup_{BACKUP_DATE}"
    backup_products = f"order_products_backup_{BACKUP_DATE}"

    # Restore order_products first (has FK to orders)
    if table_exists(conn, "vinted", backup_products):
        if table_exists(conn, "vinted", "order_products"):
            conn.execute(text("DROP TABLE vinted.order_products"))
        conn.execute(text(f"ALTER TABLE vinted.{backup_products} RENAME TO order_products"))
        print(f"  Restored vinted.order_products from backup")

    if table_exists(conn, "vinted", backup_orders):
        if table_exists(conn, "vinted", "orders"):
            conn.execute(text("DROP TABLE vinted.orders"))
        conn.execute(text(f"ALTER TABLE vinted.{backup_orders} RENAME TO orders"))
        print(f"  Restored vinted.orders from backup")

    # Drop tables from user schemas
    user_schemas = get_user_schemas(conn)
    for schema in user_schemas:
        if table_exists(conn, schema, "order_products"):
            conn.execute(text(f"DROP TABLE {schema}.order_products"))
        if table_exists(conn, schema, "orders"):
            conn.execute(text(f"DROP TABLE {schema}.orders"))
        print(f"  Dropped {schema}.orders and {schema}.order_products")

    # Drop from template_tenant
    if table_exists(conn, "template_tenant", "order_products"):
        conn.execute(text("DROP TABLE template_tenant.order_products"))
    if table_exists(conn, "template_tenant", "orders"):
        conn.execute(text("DROP TABLE template_tenant.orders"))
    print("  Dropped template_tenant.orders and template_tenant.order_products")

    print("\nDowngrade complete!")
