"""Remove legacy orders and order_products tables

Revision ID: d56316he69f2
Revises: 663b27621dca
Create Date: 2026-01-21 00:01:00

Removes old orders and order_products tables that were replaced by
vinted_orders and vinted_order_products.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'd56316he69f2'
down_revision = '663b27621dca'
branch_labels = None
depends_on = None


def get_tenant_schemas(connection) -> list:
    """Get all tenant schemas (user_X and template_tenant)."""
    result = connection.execute(
        text("""
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name LIKE 'user_%'
               OR schema_name = 'template_tenant'
        """)
    )
    return [row[0] for row in result]


def table_exists(connection, schema: str, table: str) -> bool:
    """Check if a table exists in a schema."""
    result = connection.execute(
        text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = :schema AND table_name = :table
            )
        """),
        {"schema": schema, "table": table}
    )
    return result.scalar()


def upgrade() -> None:
    """Drop legacy orders and order_products tables."""
    connection = op.get_bind()
    schemas = get_tenant_schemas(connection)

    for schema in schemas:
        # Drop order_products first (has FK to orders)
        if table_exists(connection, schema, "order_products"):
            connection.execute(text(f"DROP TABLE IF EXISTS {schema}.order_products CASCADE"))

        # Then drop orders
        if table_exists(connection, schema, "orders"):
            connection.execute(text(f"DROP TABLE IF EXISTS {schema}.orders CASCADE"))


def downgrade() -> None:
    """Recreate legacy orders and order_products tables."""
    connection = op.get_bind()
    schemas = get_tenant_schemas(connection)

    for schema in schemas:
        # Create orders table
        if not table_exists(connection, schema, "orders"):
            connection.execute(text(f"""
                CREATE TABLE {schema}.orders (
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
                    created_at_vinted TIMESTAMPTZ,
                    shipped_at TIMESTAMPTZ,
                    delivered_at TIMESTAMPTZ,
                    completed_at TIMESTAMPTZ,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
                )
            """))
            connection.execute(text(f"CREATE INDEX idx_{schema}_orders_buyer_id ON {schema}.orders(buyer_id)"))
            connection.execute(text(f"CREATE INDEX idx_{schema}_orders_status ON {schema}.orders(status)"))
            connection.execute(text(f"CREATE INDEX idx_{schema}_orders_created_at_vinted ON {schema}.orders(created_at_vinted)"))

        # Create order_products table
        if not table_exists(connection, schema, "order_products"):
            connection.execute(text(f"""
                CREATE TABLE {schema}.order_products (
                    id SERIAL PRIMARY KEY,
                    transaction_id BIGINT NOT NULL REFERENCES {schema}.orders(transaction_id) ON DELETE CASCADE,
                    vinted_item_id BIGINT,
                    product_id BIGINT,
                    title VARCHAR(255),
                    price NUMERIC(10,2),
                    size VARCHAR(100),
                    brand VARCHAR(255),
                    photo_url TEXT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
                )
            """))
            connection.execute(text(f"CREATE INDEX idx_{schema}_order_products_transaction_id ON {schema}.order_products(transaction_id)"))
            connection.execute(text(f"CREATE INDEX idx_{schema}_order_products_vinted_item_id ON {schema}.order_products(vinted_item_id)"))
            connection.execute(text(f"CREATE INDEX idx_{schema}_order_products_product_id ON {schema}.order_products(product_id)"))
