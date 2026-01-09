"""unify action types to public schema

Creates unified public.marketplace_action_types table and migrates
existing vinted.action_types data. This replaces the marketplace-specific
action_types tables with a single unified table.

Revision ID: 20260109_0200
Revises: 20260109_0100
Create Date: 2026-01-09

"""
from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = "20260109_0200"
down_revision = "20260109_0100"
branch_labels = None
depends_on = None


def upgrade():
    """
    Create public.marketplace_action_types and migrate vinted.action_types data.
    """
    connection = op.get_bind()

    # Step 1: Create unified table in public schema
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS public.marketplace_action_types (
            id SERIAL PRIMARY KEY,
            marketplace VARCHAR(50) NOT NULL,
            code VARCHAR(50) NOT NULL,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            priority INT DEFAULT 3 NOT NULL,
            is_batch BOOLEAN DEFAULT FALSE NOT NULL,
            rate_limit_ms INT DEFAULT 2000 NOT NULL,
            max_retries INT DEFAULT 3 NOT NULL,
            timeout_seconds INT DEFAULT 60 NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
            CONSTRAINT uq_marketplace_action_types_marketplace_code UNIQUE (marketplace, code)
        );

        CREATE INDEX IF NOT EXISTS idx_marketplace_action_types_marketplace
        ON public.marketplace_action_types(marketplace);

        CREATE INDEX IF NOT EXISTS idx_marketplace_action_types_code
        ON public.marketplace_action_types(code);
    """))

    print("✓ Created public.marketplace_action_types table")

    # Step 2: Check if vinted.action_types exists and migrate data
    vinted_schema_exists = connection.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.schemata
            WHERE schema_name = 'vinted'
        )
    """)).scalar()

    if vinted_schema_exists:
        vinted_table_exists = connection.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'vinted' AND table_name = 'action_types'
            )
        """)).scalar()

        if vinted_table_exists:
            # Migrate data from vinted.action_types to public.marketplace_action_types
            connection.execute(text("""
                INSERT INTO public.marketplace_action_types
                (marketplace, code, name, description, priority, is_batch, rate_limit_ms, max_retries, timeout_seconds, created_at)
                SELECT
                    'vinted' as marketplace,
                    code,
                    name,
                    description,
                    priority,
                    is_batch,
                    rate_limit_ms,
                    max_retries,
                    timeout_seconds,
                    created_at
                FROM vinted.action_types
                ON CONFLICT (marketplace, code) DO NOTHING
            """))

            print("✓ Migrated vinted.action_types data to public.marketplace_action_types")

            # Drop old vinted.action_types table
            connection.execute(text("DROP TABLE IF EXISTS vinted.action_types CASCADE"))
            print("✓ Dropped vinted.action_types table")
        else:
            print("ℹ vinted.action_types table not found (skipping migration)")
    else:
        print("ℹ vinted schema not found (skipping migration)")


def downgrade():
    """
    Rollback: Recreate vinted.action_types and restore data.

    NOTE: This is a destructive migration. Downgrade will lose any
    eBay/Etsy action_types data that was added after upgrade.
    """
    connection = op.get_bind()

    # Recreate vinted schema if needed
    connection.execute(text("CREATE SCHEMA IF NOT EXISTS vinted"))

    # Recreate vinted.action_types table
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS vinted.action_types (
            id SERIAL PRIMARY KEY,
            code VARCHAR(50) UNIQUE NOT NULL,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            priority INT DEFAULT 3 NOT NULL,
            is_batch BOOLEAN DEFAULT FALSE NOT NULL,
            rate_limit_ms INT DEFAULT 2000 NOT NULL,
            max_retries INT DEFAULT 3 NOT NULL,
            timeout_seconds INT DEFAULT 60 NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
        )
    """))

    # Restore vinted data only (lose ebay/etsy data)
    connection.execute(text("""
        INSERT INTO vinted.action_types
        (code, name, description, priority, is_batch, rate_limit_ms, max_retries, timeout_seconds, created_at)
        SELECT
            code,
            name,
            description,
            priority,
            is_batch,
            rate_limit_ms,
            max_retries,
            timeout_seconds,
            created_at
        FROM public.marketplace_action_types
        WHERE marketplace = 'vinted'
        ON CONFLICT (code) DO NOTHING
    """))

    # Drop unified table
    connection.execute(text("DROP TABLE IF EXISTS public.marketplace_action_types CASCADE"))

    print("✓ Downgrade complete - restored vinted.action_types (eBay/Etsy data lost)")
