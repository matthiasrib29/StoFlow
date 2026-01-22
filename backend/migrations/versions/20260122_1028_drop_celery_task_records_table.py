"""drop_celery_task_records_table

Revision ID: d9da4b2acb30
Revises: 9b5d3f2e4c6a
Create Date: 2026-01-22 10:28:11.247502+01:00

Drops the unused celery_task_records table from public schema.
This table was created for Celery task tracking but is no longer used.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'd9da4b2acb30'
down_revision: Union[str, None] = '9b5d3f2e4c6a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table('celery_task_records', schema='public')


def downgrade() -> None:
    op.create_table(
        'celery_task_records',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('marketplace', sa.String(), nullable=True),
        sa.Column('action_code', sa.String(), nullable=True),
        sa.Column('product_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('args', postgresql.JSONB(), nullable=True),
        sa.Column('kwargs', postgresql.JSONB(), nullable=True),
        sa.Column('result', postgresql.JSONB(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('traceback', sa.Text(), nullable=True),
        sa.Column('retries', sa.Integer(), nullable=True),
        sa.Column('max_retries', sa.Integer(), nullable=True),
        sa.Column('eta', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('expires', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('worker', sa.String(), nullable=True),
        sa.Column('queue', sa.String(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('started_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('completed_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('runtime_seconds', sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        schema='public'
    )
