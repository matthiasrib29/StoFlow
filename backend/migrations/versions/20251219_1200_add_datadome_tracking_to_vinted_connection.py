"""Add DataDome tracking columns to vinted_connection

Revision ID: 20251219_1200
Revises: 20251219_1100
Create Date: 2025-12-19 12:00:00.000000

Adds columns for tracking DataDome ping status:
- last_datadome_ping: Timestamp of last successful ping
- datadome_status: Enum (OK, FAILED, UNKNOWN)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = '20251219_1200'
down_revision = '20251219_1100'
branch_labels = None
depends_on = None


def upgrade():
    """Add DataDome tracking columns to vinted_connection in all user schemas."""
    conn = op.get_bind()

    # Create enum type in public schema (shared across all schemas)
    conn.execute(text("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'datadomestatus') THEN
                CREATE TYPE datadomestatus AS ENUM ('OK', 'FAILED', 'UNKNOWN');
            END IF;
        END$$;
    """))

    # Get all user schemas
    result = conn.execute(text("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%'
        AND schema_name <> 'user_invalid'
        ORDER BY schema_name
    """))
    user_schemas = [row[0] for row in result.fetchall()]

    for schema in user_schemas:
        # Check if vinted_connection table exists in this schema
        table_exists = conn.execute(text(f"""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = '{schema}'
                AND table_name = 'vinted_connection'
            )
        """)).scalar()

        if not table_exists:
            print(f"vinted_connection table doesn't exist in {schema}, skipping")
            continue

        # Check if last_datadome_ping column already exists
        column_exists = conn.execute(text(f"""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = '{schema}'
                AND table_name = 'vinted_connection'
                AND column_name = 'last_datadome_ping'
            )
        """)).scalar()

        if column_exists:
            print(f"DataDome columns already exist in {schema}.vinted_connection, skipping")
            continue

        print(f"Adding DataDome columns to {schema}.vinted_connection")

        # Add last_datadome_ping column
        conn.execute(text(f"""
            ALTER TABLE {schema}.vinted_connection
            ADD COLUMN last_datadome_ping TIMESTAMP WITH TIME ZONE DEFAULT NULL
        """))

        # Add datadome_status column with default 'UNKNOWN'
        conn.execute(text(f"""
            ALTER TABLE {schema}.vinted_connection
            ADD COLUMN datadome_status datadomestatus NOT NULL DEFAULT 'UNKNOWN'
        """))

        print(f"  -> Added last_datadome_ping, datadome_status to {schema}.vinted_connection")

    # Also update template_tenant if it exists
    template_exists = conn.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'template_tenant'
            AND table_name = 'vinted_connection'
        )
    """)).scalar()

    if template_exists:
        column_exists = conn.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'template_tenant'
                AND table_name = 'vinted_connection'
                AND column_name = 'last_datadome_ping'
            )
        """)).scalar()

        if not column_exists:
            print("Adding DataDome columns to template_tenant.vinted_connection")
            conn.execute(text("""
                ALTER TABLE template_tenant.vinted_connection
                ADD COLUMN last_datadome_ping TIMESTAMP WITH TIME ZONE DEFAULT NULL
            """))
            conn.execute(text("""
                ALTER TABLE template_tenant.vinted_connection
                ADD COLUMN datadome_status datadomestatus NOT NULL DEFAULT 'UNKNOWN'
            """))
            print("  -> Added columns to template_tenant.vinted_connection")


def downgrade():
    """Remove DataDome tracking columns from vinted_connection."""
    conn = op.get_bind()

    # Get all user schemas
    result = conn.execute(text("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%'
        AND schema_name <> 'user_invalid'
        ORDER BY schema_name
    """))
    user_schemas = [row[0] for row in result.fetchall()]

    for schema in user_schemas:
        table_exists = conn.execute(text(f"""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = '{schema}'
                AND table_name = 'vinted_connection'
            )
        """)).scalar()

        if table_exists:
            conn.execute(text(f"""
                ALTER TABLE {schema}.vinted_connection
                DROP COLUMN IF EXISTS last_datadome_ping,
                DROP COLUMN IF EXISTS datadome_status
            """))
            print(f"Removed DataDome columns from {schema}.vinted_connection")

    # Also update template_tenant
    template_exists = conn.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'template_tenant'
            AND table_name = 'vinted_connection'
        )
    """)).scalar()

    if template_exists:
        conn.execute(text("""
            ALTER TABLE template_tenant.vinted_connection
            DROP COLUMN IF EXISTS last_datadome_ping,
            DROP COLUMN IF EXISTS datadome_status
        """))
        print("Removed DataDome columns from template_tenant.vinted_connection")

    # Drop the enum type
    conn.execute(text("""
        DROP TYPE IF EXISTS datadomestatus
    """))
