"""add_queue_id_to_plugin_tasks

Revision ID: c73cb6f31adb
Revises: 99f88e15be4a
Create Date: 2025-12-11 13:04:53.431405+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c73cb6f31adb'
down_revision: Union[str, None] = '99f88e15be4a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add queue_id column to plugin_tasks (skip if already exists from earlier migration)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'plugin_tasks'
                AND column_name = 'queue_id'
            ) THEN
                ALTER TABLE plugin_tasks ADD COLUMN queue_id INTEGER;
                CREATE INDEX ix_plugin_tasks_queue_id ON plugin_tasks(queue_id);
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM information_schema.table_constraints
                WHERE table_name = 'plugin_tasks'
                AND constraint_name = 'fk_plugin_tasks_queue_id'
            ) THEN
                ALTER TABLE plugin_tasks
                ADD CONSTRAINT fk_plugin_tasks_queue_id
                FOREIGN KEY (queue_id) REFERENCES plugin_queue(id) ON DELETE CASCADE;
            END IF;
        END $$;
    """)


def downgrade() -> None:
    # Remove queue_id column from plugin_tasks
    op.drop_constraint('fk_plugin_tasks_queue_id', 'plugin_tasks', type_='foreignkey')
    op.drop_index(op.f('ix_plugin_tasks_queue_id'), table_name='plugin_tasks')
    op.drop_column('plugin_tasks', 'queue_id')
