"""Add plugin_tasks table to template_tenant schema

Revision ID: fix_plugin_tasks_template
Revises: 062469969708
Create Date: 2025-12-10 13:59:00.000000

FIX: Creates plugin_tasks in template_tenant BEFORE the queue system migration
that tries to add columns to it.
"""
from alembic import op
import sqlalchemy as sa

revision = 'fix_plugin_tasks_template'
down_revision = '062469969708'
branch_labels = None
depends_on = None


def upgrade():
    """Create plugin_tasks table in template_tenant if not exists."""
    op.execute("""
        CREATE TABLE IF NOT EXISTS template_tenant.plugin_tasks (
            id SERIAL PRIMARY KEY,
            task_type VARCHAR(100),
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            payload JSONB NOT NULL DEFAULT '{}',
            result JSONB,
            error_message TEXT,
            product_id INTEGER,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
            started_at TIMESTAMP WITH TIME ZONE,
            completed_at TIMESTAMP WITH TIME ZONE,
            retry_count INTEGER DEFAULT 0 NOT NULL,
            max_retries INTEGER DEFAULT 3 NOT NULL
        )
    """)

    # Indexes
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_template_tenant_plugin_tasks_status
        ON template_tenant.plugin_tasks(status)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_template_tenant_plugin_tasks_product_id
        ON template_tenant.plugin_tasks(product_id)
    """)


def downgrade():
    """Drop plugin_tasks from template_tenant."""
    op.execute("DROP TABLE IF EXISTS template_tenant.plugin_tasks CASCADE")
