"""remove marketplace_tasks table

Removes the marketplace_tasks table (formerly marketplace_tasks) from all user schemas.
This table was used for the old polling-based plugin communication system,
which has been replaced by WebSocket real-time communication.

Note: marketplace_tasks was renamed to marketplace_tasks on 2026-01-07.

Revision ID: 20260109_0100
Revises: 53a8b38c9737
Create Date: 2026-01-09

"""
from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = "20260109_0100"
down_revision = "53a8b38c9737"
branch_labels = None
depends_on = None


def get_user_schemas(connection):
    """Get list of user schemas."""
    result = connection.execute(
        text(
            """
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%'
    """
        )
    )
    return [row[0] for row in result]


def table_exists(conn, schema, table):
    """Check if table exists in schema."""
    result = conn.execute(
        text(
            """
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = :schema AND table_name = :table
        )
    """
        ),
        {"schema": schema, "table": table},
    )
    return result.scalar()


def upgrade():
    """Drop marketplace_tasks table from all user schemas."""
    connection = op.get_bind()
    user_schemas = get_user_schemas(connection)

    dropped_count = 0
    for schema in user_schemas:
        # Check if table exists
        if table_exists(connection, schema, "marketplace_tasks"):
            # Drop table
            connection.execute(
                text(f'DROP TABLE IF EXISTS "{schema}".marketplace_tasks CASCADE')
            )
            print(f"✓ Dropped marketplace_tasks in {schema}")
            dropped_count += 1

    if dropped_count == 0:
        print("No marketplace_tasks tables found (already removed or never created)")
    else:
        print(f"✓ Dropped marketplace_tasks from {dropped_count} user schemas")


def downgrade():
    """
    Recreate marketplace_tasks table (for rollback).

    NOTE: This is a destructive migration. Downgrade will recreate the table structure
    but all data will be lost. This is acceptable since we're migrating to a new system.
    """
    connection = op.get_bind()
    user_schemas = get_user_schemas(connection)

    for schema in user_schemas:
        # Recreate table structure
        connection.execute(
            text(
                f"""
            CREATE TABLE IF NOT EXISTS "{schema}".marketplace_tasks (
                id SERIAL PRIMARY KEY,
                status VARCHAR(20) NOT NULL DEFAULT 'pending',
                http_method VARCHAR(10) NOT NULL,
                path TEXT NOT NULL,
                payload JSONB,
                platform VARCHAR(50) NOT NULL,
                product_id INTEGER,
                job_id INTEGER,
                result JSONB,
                error_message TEXT,
                timeout INTEGER DEFAULT 60,
                description TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP WITH TIME ZONE,
                CONSTRAINT marketplace_tasks_status_check CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'timeout'))
            )
        """
            )
        )
        print(f"✓ Recreated marketplace_tasks in {schema} (empty)")
