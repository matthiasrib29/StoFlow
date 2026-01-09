"""Add plugin_tasks table to all user schemas

Revision ID: 20251217_1017
Revises: ba45bfe5128a
Create Date: 2025-12-17 10:17:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = '20251217_1017'
down_revision = 'ba45bfe5128a'
branch_labels = None
depends_on = None


def upgrade():
    """
    Add plugin_tasks table to all user schemas that don't have it.

    Business Rules:
    - Each user schema needs a plugin_tasks table for the task queue system
    - Schema isolation: each user has their own task queue
    - Columns match the PluginTask model in models/user/plugin_task.py
    """
    conn = op.get_bind()

    # Get all user schemas
    result = conn.execute(text("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%'
        AND schema_name != 'user_invalid'
        ORDER BY schema_name
    """))
    user_schemas = [row[0] for row in result.fetchall()]

    for schema in user_schemas:
        # Check if table already exists
        table_exists = conn.execute(text(f"""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = '{schema}'
                AND table_name = 'plugin_tasks'
            )
        """)).scalar()

        if not table_exists:
            print(f"Creating plugin_tasks in {schema}")

            # Create the table with all columns
            conn.execute(text(f"""
                CREATE TABLE {schema}.plugin_tasks (
                    id SERIAL PRIMARY KEY,
                    task_type VARCHAR(100),
                    status VARCHAR(20) NOT NULL DEFAULT 'pending',
                    payload JSONB NOT NULL DEFAULT '{{}}',
                    result JSONB,
                    error_message TEXT,
                    product_id INTEGER,
                    platform VARCHAR(50),
                    http_method VARCHAR(10),
                    path VARCHAR(500),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
                    started_at TIMESTAMP WITH TIME ZONE,
                    completed_at TIMESTAMP WITH TIME ZONE,
                    retry_count INTEGER DEFAULT 0 NOT NULL,
                    max_retries INTEGER DEFAULT 3 NOT NULL
                )
            """))

            # Create indexes
            conn.execute(text(f"""
                CREATE INDEX IF NOT EXISTS idx_{schema.replace('user_', 'u')}_plugin_tasks_status
                ON {schema}.plugin_tasks(status)
            """))
            conn.execute(text(f"""
                CREATE INDEX IF NOT EXISTS idx_{schema.replace('user_', 'u')}_plugin_tasks_platform
                ON {schema}.plugin_tasks(platform)
            """))
            conn.execute(text(f"""
                CREATE INDEX IF NOT EXISTS idx_{schema.replace('user_', 'u')}_plugin_tasks_task_type
                ON {schema}.plugin_tasks(task_type)
            """))
            conn.execute(text(f"""
                CREATE INDEX IF NOT EXISTS idx_{schema.replace('user_', 'u')}_plugin_tasks_product_id
                ON {schema}.plugin_tasks(product_id)
            """))

            print(f"  -> plugin_tasks created in {schema}")
        else:
            print(f"plugin_tasks already exists in {schema}")


def downgrade():
    """Drop plugin_tasks from user schemas that were created by this migration."""
    conn = op.get_bind()

    # Get all user schemas
    result = conn.execute(text("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%'
        AND schema_name != 'user_invalid'
        ORDER BY schema_name
    """))
    user_schemas = [row[0] for row in result.fetchall()]

    for schema in user_schemas:
        # Note: This will drop the table even if it existed before
        # In production, you might want to be more careful here
        conn.execute(text(f"DROP TABLE IF EXISTS {schema}.plugin_tasks CASCADE"))
        print(f"Dropped plugin_tasks from {schema}")
