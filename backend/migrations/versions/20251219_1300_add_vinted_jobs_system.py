"""
Add Vinted Jobs System

Creates tables for job orchestration:
- vinted_action_types: Reference table for action types (publish, sync, etc.)
- vinted_jobs: Job instances with status tracking
- vinted_job_stats: Daily analytics per action type
- Adds job_id FK to plugin_tasks

Revision ID: 20251219_1300
Revises: 20251219_1200
Create Date: 2025-12-19 13:00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "20251219_1300"
down_revision = "20251219_1200"
branch_labels = None
depends_on = None


def get_user_schemas(connection) -> list[str]:
    """Get all user schemas that have the products table (complete schemas only)."""
    result = connection.execute(
        sa.text(
            """
            SELECT DISTINCT s.schema_name
            FROM information_schema.schemata s
            INNER JOIN information_schema.tables t
                ON t.table_schema = s.schema_name AND t.table_name = 'products'
            WHERE s.schema_name LIKE 'user_%' OR s.schema_name = 'template_tenant'
            """
        )
    )
    return [row[0] for row in result]


def upgrade() -> None:
    connection = op.get_bind()

    # =========================================================================
    # 1. Create vinted_action_types in PUBLIC schema (shared reference table)
    # =========================================================================
    op.create_table(
        "vinted_action_types",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(50), unique=True, nullable=False, comment="Unique code: publish, sync, orders, message, update, delete"),
        sa.Column("name", sa.String(100), nullable=False, comment="Display name"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("priority", sa.Integer(), default=3, nullable=False, comment="1=CRITICAL, 2=HIGH, 3=NORMAL, 4=LOW"),
        sa.Column("is_batch", sa.Boolean(), default=False, nullable=False, comment="True if action processes multiple items"),
        sa.Column("rate_limit_ms", sa.Integer(), default=2000, nullable=False, comment="Delay between requests in ms"),
        sa.Column("max_retries", sa.Integer(), default=3, nullable=False),
        sa.Column("timeout_seconds", sa.Integer(), default=60, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema="public"
    )

    # Seed initial action types
    op.execute("""
        INSERT INTO public.vinted_action_types (code, name, description, priority, is_batch, rate_limit_ms, max_retries, timeout_seconds) VALUES
        ('message', 'Respond to message', 'Reply to Vinted buyer messages', 1, false, 1000, 3, 30),
        ('orders', 'Fetch orders', 'Retrieve new orders/sales from Vinted', 3, true, 1500, 3, 60),
        ('publish', 'Publish product', 'Create a new listing on Vinted', 3, false, 2500, 3, 120),
        ('update', 'Update product', 'Modify price, description, photos', 3, false, 2000, 3, 60),
        ('delete', 'Delete product', 'Remove listing from Vinted', 4, false, 2000, 3, 30),
        ('sync', 'Sync products', 'Synchronize all products with Vinted', 4, true, 1500, 3, 300)
    """)

    # =========================================================================
    # 2. Create vinted_jobs in USER schemas (tenant-specific)
    # =========================================================================
    user_schemas = get_user_schemas(connection)

    for schema_name in user_schemas:
        # Create vinted_jobs table
        op.execute(f"""
            CREATE TABLE IF NOT EXISTS {schema_name}.vinted_jobs (
                id SERIAL PRIMARY KEY,
                batch_id VARCHAR(50),
                action_type_id INTEGER NOT NULL REFERENCES public.vinted_action_types(id),
                product_id INTEGER REFERENCES {schema_name}.products(id) ON DELETE SET NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'pending',
                priority INTEGER NOT NULL DEFAULT 3,
                error_message TEXT,
                retry_count INTEGER NOT NULL DEFAULT 0,
                started_at TIMESTAMP WITH TIME ZONE,
                completed_at TIMESTAMP WITH TIME ZONE,
                expires_at TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

                CONSTRAINT valid_status CHECK (status IN ('pending', 'running', 'paused', 'completed', 'failed', 'cancelled', 'expired'))
            )
        """)

        # Create indexes
        op.execute(f"CREATE INDEX IF NOT EXISTS ix_{schema_name.replace('_', '')}_vinted_jobs_status ON {schema_name}.vinted_jobs(status)")
        op.execute(f"CREATE INDEX IF NOT EXISTS ix_{schema_name.replace('_', '')}_vinted_jobs_batch_id ON {schema_name}.vinted_jobs(batch_id)")
        op.execute(f"CREATE INDEX IF NOT EXISTS ix_{schema_name.replace('_', '')}_vinted_jobs_priority ON {schema_name}.vinted_jobs(priority)")
        op.execute(f"CREATE INDEX IF NOT EXISTS ix_{schema_name.replace('_', '')}_vinted_jobs_created_at ON {schema_name}.vinted_jobs(created_at)")

        # Create vinted_job_stats table
        op.execute(f"""
            CREATE TABLE IF NOT EXISTS {schema_name}.vinted_job_stats (
                id SERIAL PRIMARY KEY,
                action_type_id INTEGER NOT NULL REFERENCES public.vinted_action_types(id),
                date DATE NOT NULL,
                total_jobs INTEGER NOT NULL DEFAULT 0,
                success_count INTEGER NOT NULL DEFAULT 0,
                failure_count INTEGER NOT NULL DEFAULT 0,
                avg_duration_ms INTEGER,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

                UNIQUE(action_type_id, date)
            )
        """)

        # Add job_id column to plugin_tasks
        # Check if column exists first
        result = connection.execute(sa.text(f"""
            SELECT column_name FROM information_schema.columns
            WHERE table_schema = '{schema_name}'
            AND table_name = 'plugin_tasks'
            AND column_name = 'job_id'
        """))
        if result.fetchone() is None:
            op.execute(f"""
                ALTER TABLE {schema_name}.plugin_tasks
                ADD COLUMN job_id INTEGER REFERENCES {schema_name}.vinted_jobs(id) ON DELETE SET NULL
            """)
            op.execute(f"CREATE INDEX IF NOT EXISTS ix_{schema_name.replace('_', '')}_plugin_tasks_job_id ON {schema_name}.plugin_tasks(job_id)")


def downgrade() -> None:
    connection = op.get_bind()
    user_schemas = get_user_schemas(connection)

    for schema_name in user_schemas:
        # Remove job_id from plugin_tasks
        op.execute(f"ALTER TABLE {schema_name}.plugin_tasks DROP COLUMN IF EXISTS job_id")

        # Drop vinted_job_stats
        op.execute(f"DROP TABLE IF EXISTS {schema_name}.vinted_job_stats")

        # Drop vinted_jobs
        op.execute(f"DROP TABLE IF EXISTS {schema_name}.vinted_jobs")

    # Drop vinted_action_types from public
    op.execute("DROP TABLE IF EXISTS public.vinted_action_types")
