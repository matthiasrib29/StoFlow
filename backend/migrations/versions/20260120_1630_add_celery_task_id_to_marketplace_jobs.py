"""add_celery_task_id_to_marketplace_jobs

Revision ID: 97fb25ac9944
Revises: 7a8b9c0d1e2f
Create Date: 2026-01-20 16:30:40.624489+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '97fb25ac9944'
down_revision: Union[str, None] = '7a8b9c0d1e2f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def get_user_schemas() -> list[str]:
    """Get all user schemas from database."""
    conn = op.get_bind()
    result = conn.execute(
        sa.text("SELECT schema_name FROM information_schema.schemata WHERE schema_name LIKE 'user_%'")
    )
    return [row[0] for row in result]


def upgrade() -> None:
    """Add celery_task_id column to marketplace_jobs for all user schemas."""
    schemas = get_user_schemas()

    for schema in schemas:
        op.add_column(
            'marketplace_jobs',
            sa.Column('celery_task_id', sa.String(36), nullable=True),
            schema=schema
        )
        # Add index for faster lookup during revoke operations
        op.create_index(
            f'ix_{schema}_marketplace_jobs_celery_task_id',
            'marketplace_jobs',
            ['celery_task_id'],
            schema=schema
        )


def downgrade() -> None:
    """Remove celery_task_id column from marketplace_jobs for all user schemas."""
    schemas = get_user_schemas()

    for schema in schemas:
        op.drop_index(
            f'ix_{schema}_marketplace_jobs_celery_task_id',
            table_name='marketplace_jobs',
            schema=schema
        )
        op.drop_column('marketplace_jobs', 'celery_task_id', schema=schema)
