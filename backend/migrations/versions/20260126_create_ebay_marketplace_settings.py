"""create_ebay_marketplace_settings

Create ebay_marketplace_settings table in all tenant schemas.
Stores per-marketplace business policies, inventory location, and pricing config.

Revision ID: a3f7e1c2d4b6
Revises: b3ee8c6c03b9
Create Date: 2026-01-26
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'a3f7e1c2d4b6'
down_revision: Union[str, None] = 'b3ee8c6c03b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def get_user_schemas(conn) -> list[str]:
    """Get all user schemas (user_X pattern) + template_tenant."""
    result = conn.execute(text("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%' OR schema_name = 'template_tenant'
        ORDER BY schema_name
    """))
    return [row[0] for row in result]


def table_exists(conn, schema: str, table: str) -> bool:
    """Check if a table exists in a schema."""
    result = conn.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = :schema AND table_name = :table
        )
    """), {"schema": schema, "table": table})
    return result.scalar()


def create_ebay_marketplace_settings_ddl(schema: str) -> str:
    """Generate DDL for ebay_marketplace_settings table."""
    return f"""
        CREATE TABLE IF NOT EXISTS {schema}.ebay_marketplace_settings (
            id SERIAL PRIMARY KEY,
            marketplace_id VARCHAR(20) NOT NULL,
            payment_policy_id VARCHAR(50),
            fulfillment_policy_id VARCHAR(50),
            return_policy_id VARCHAR(50),
            inventory_location_key VARCHAR(50),
            price_coefficient NUMERIC(5, 2) NOT NULL DEFAULT 1.00,
            price_fee NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );

        CREATE UNIQUE INDEX IF NOT EXISTS uq_{schema}_ebay_mkt_settings_marketplace_id
            ON {schema}.ebay_marketplace_settings (marketplace_id);

        CREATE INDEX IF NOT EXISTS idx_{schema}_ebay_mkt_settings_marketplace_id
            ON {schema}.ebay_marketplace_settings (marketplace_id);
    """


def upgrade() -> None:
    conn = op.get_bind()

    schemas = get_user_schemas(conn)
    print(f"  Found {len(schemas)} schemas to update")

    for schema in schemas:
        if not table_exists(conn, schema, "ebay_marketplace_settings"):
            conn.execute(text(create_ebay_marketplace_settings_ddl(schema)))
            print(f"  Created {schema}.ebay_marketplace_settings")
        else:
            print(f"  {schema}.ebay_marketplace_settings already exists, skipping")


def downgrade() -> None:
    conn = op.get_bind()

    schemas = get_user_schemas(conn)
    for schema in schemas:
        if table_exists(conn, schema, "ebay_marketplace_settings"):
            conn.execute(text(
                f"DROP TABLE IF EXISTS {schema}.ebay_marketplace_settings CASCADE"
            ))
            print(f"  Dropped {schema}.ebay_marketplace_settings")
