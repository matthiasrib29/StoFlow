"""remove deprecated marketplace_job.batch_id column

Revision ID: c2b2384bb910
Revises: 307a8e381a2b
Create Date: 2026-01-16 09:07:08.893831+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c2b2384bb910'
down_revision: Union[str, None] = '307a8e381a2b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Remove deprecated batch_id column from marketplace_jobs.

    All code now uses batch_job_id FK instead.

    Note: schema='tenant' handled by schema_translate_map in env.py
    """
    # Drop index first (if exists) - using raw SQL for IF EXISTS
    op.execute(
        'DROP INDEX IF EXISTS ix_marketplace_jobs_batch_id'
    )

    # Drop column
    op.drop_column(
        'marketplace_jobs',
        'batch_id'
    )


def downgrade() -> None:
    """
    Re-add batch_id column (for rollback only).

    WARNING: Data will be empty after rollback.
    """
    # Re-add column
    op.add_column(
        'marketplace_jobs',
        sa.Column('batch_id', sa.String(50), nullable=True)
    )

    # Re-create index
    op.create_index(
        'ix_marketplace_jobs_batch_id',
        'marketplace_jobs',
        ['batch_id']
    )
