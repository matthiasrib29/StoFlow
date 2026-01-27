"""add_pending_actions_table

Add PENDING_DELETION status to product_status enum and create
pending_actions table in all tenant schemas.

Revision ID: 9b1ae5d09454
Revises: 733d8a9ac5b4
Create Date: 2026-01-22 22:05:47.927332+01:00

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '9b1ae5d09454'
down_revision: Union[str, None] = '733d8a9ac5b4'
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


def enum_value_exists(conn, enum_name: str, value: str) -> bool:
    """Check if an enum value already exists."""
    result = conn.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM pg_enum
            JOIN pg_type ON pg_enum.enumtypid = pg_type.oid
            WHERE pg_type.typname = :enum_name AND pg_enum.enumlabel = :value
        )
    """), {"enum_name": enum_name, "value": value})
    return result.scalar()


def create_pending_actions_ddl(schema: str) -> str:
    """Generate DDL for pending_actions table in a given schema."""
    return f"""
        CREATE TABLE IF NOT EXISTS {schema}.pending_actions (
            id SERIAL PRIMARY KEY,
            product_id INTEGER NOT NULL
                REFERENCES {schema}.products(id) ON DELETE CASCADE,
            action_type VARCHAR(20) NOT NULL,
            marketplace VARCHAR(20) NOT NULL,
            reason VARCHAR(500),
            context_data JSONB,
            previous_status VARCHAR(50),
            detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            confirmed_at TIMESTAMPTZ,
            confirmed_by VARCHAR(50),
            is_confirmed BOOLEAN
        );

        CREATE INDEX IF NOT EXISTS idx_pending_actions_product
            ON {schema}.pending_actions (product_id);
        CREATE INDEX IF NOT EXISTS idx_pending_actions_confirmed
            ON {schema}.pending_actions (confirmed_at);
        CREATE INDEX IF NOT EXISTS idx_pending_actions_marketplace
            ON {schema}.pending_actions (marketplace);
    """


def upgrade() -> None:
    conn = op.get_bind()

    # 1. Add PENDING_DELETION to product_status enum (uppercase to match existing values)
    if not enum_value_exists(conn, "product_status", "PENDING_DELETION"):
        conn.execute(text(
            "ALTER TYPE product_status ADD VALUE IF NOT EXISTS 'PENDING_DELETION'"
        ))
        conn.execute(text("COMMIT"))
        print("  Added 'PENDING_DELETION' to product_status enum")

    # 2. Create pending_actions table in all tenant schemas
    schemas = get_user_schemas(conn)
    print(f"  Found {len(schemas)} schemas to update")

    for schema in schemas:
        if not table_exists(conn, schema, "pending_actions"):
            conn.execute(text(create_pending_actions_ddl(schema)))
            print(f"  Created {schema}.pending_actions")
        else:
            print(f"  {schema}.pending_actions already exists, skipping")


def downgrade() -> None:
    conn = op.get_bind()

    # 1. Drop pending_actions table from all tenant schemas
    schemas = get_user_schemas(conn)
    for schema in schemas:
        if table_exists(conn, schema, "pending_actions"):
            conn.execute(text(f"DROP TABLE IF EXISTS {schema}.pending_actions CASCADE"))
            print(f"  Dropped {schema}.pending_actions")

    # 2. Note: Cannot remove enum value in PostgreSQL without recreating the type
    # pending_deletion value will remain but be unused
    print("  Note: 'pending_deletion' enum value cannot be removed (PostgreSQL limitation)")
