"""Add is_connected and disconnected_at to vinted_connection

Revision ID: 20251217_1100
Revises: 20251217_1017
Create Date: 2025-12-17 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = '20251217_1100'
down_revision = '20251217_1017'
branch_labels = None
depends_on = None


def upgrade():
    """
    Add is_connected and disconnected_at columns to vinted_connection in all user schemas.

    Business Rules:
    - is_connected: Boolean flag indicating if user is currently connected to Vinted
    - disconnected_at: Timestamp of last disconnection (NULL if connected)
    - Default is_connected to TRUE for existing records (they were connected)
    """
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

        # Check if is_connected column already exists
        column_exists = conn.execute(text(f"""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = '{schema}'
                AND table_name = 'vinted_connection'
                AND column_name = 'is_connected'
            )
        """)).scalar()

        if column_exists:
            print(f"is_connected already exists in {schema}.vinted_connection, skipping")
            continue

        print(f"Adding columns to {schema}.vinted_connection")

        # Add is_connected column (default TRUE for existing records)
        conn.execute(text(f"""
            ALTER TABLE {schema}.vinted_connection
            ADD COLUMN is_connected BOOLEAN NOT NULL DEFAULT TRUE
        """))

        # Add disconnected_at column
        conn.execute(text(f"""
            ALTER TABLE {schema}.vinted_connection
            ADD COLUMN disconnected_at TIMESTAMP WITH TIME ZONE DEFAULT NULL
        """))

        # Create index on is_connected for faster queries
        conn.execute(text(f"""
            CREATE INDEX IF NOT EXISTS ix_{schema.replace('user_', 'u')}_vinted_conn_is_connected
            ON {schema}.vinted_connection(is_connected)
        """))

        print(f"  -> Added is_connected, disconnected_at to {schema}.vinted_connection")

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
                AND column_name = 'is_connected'
            )
        """)).scalar()

        if not column_exists:
            print("Adding columns to template_tenant.vinted_connection")
            conn.execute(text("""
                ALTER TABLE template_tenant.vinted_connection
                ADD COLUMN is_connected BOOLEAN NOT NULL DEFAULT TRUE
            """))
            conn.execute(text("""
                ALTER TABLE template_tenant.vinted_connection
                ADD COLUMN disconnected_at TIMESTAMP WITH TIME ZONE DEFAULT NULL
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_template_vinted_conn_is_connected
                ON template_tenant.vinted_connection(is_connected)
            """))
            print("  -> Added columns to template_tenant.vinted_connection")


def downgrade():
    """Remove is_connected and disconnected_at columns from vinted_connection."""
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
            # Drop index first
            conn.execute(text(f"""
                DROP INDEX IF EXISTS {schema}.ix_{schema.replace('user_', 'u')}_vinted_conn_is_connected
            """))
            # Drop columns
            conn.execute(text(f"""
                ALTER TABLE {schema}.vinted_connection
                DROP COLUMN IF EXISTS is_connected,
                DROP COLUMN IF EXISTS disconnected_at
            """))
            print(f"Removed columns from {schema}.vinted_connection")

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
            DROP INDEX IF EXISTS template_tenant.ix_template_vinted_conn_is_connected
        """))
        conn.execute(text("""
            ALTER TABLE template_tenant.vinted_connection
            DROP COLUMN IF EXISTS is_connected,
            DROP COLUMN IF EXISTS disconnected_at
        """))
        print("Removed columns from template_tenant.vinted_connection")
