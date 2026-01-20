"""add_celery_task_records_table

Revision ID: c8534674a69e
Revises: 7a8b9c0d1e2f
Create Date: 2026-01-20 13:21:47.883534+01:00

Creates a table to track Celery task execution metadata.
This allows monitoring task history from the StoFlow UI.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c8534674a69e'
down_revision: Union[str, None] = '7a8b9c0d1e2f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create celery_task_records table in public schema
    op.create_table(
        'celery_task_records',
        sa.Column('id', sa.String(36), primary_key=True, comment="Celery task UUID"),
        sa.Column('name', sa.String(255), nullable=False, comment="Task name (e.g., tasks.marketplace_tasks.publish_product)"),
        sa.Column('status', sa.String(50), nullable=False, default='PENDING', comment="Task status: PENDING, STARTED, SUCCESS, FAILURE, RETRY, REVOKED"),
        sa.Column('marketplace', sa.String(50), nullable=True, comment="Marketplace: vinted, ebay, etsy"),
        sa.Column('action_code', sa.String(50), nullable=True, comment="Action: publish, update, delete, sync, sync_orders"),
        sa.Column('product_id', sa.Integer, nullable=True, comment="Product ID if applicable"),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, comment="User who initiated the task"),
        sa.Column('args', postgresql.JSONB, nullable=True, comment="Task arguments (JSON)"),
        sa.Column('kwargs', postgresql.JSONB, nullable=True, comment="Task keyword arguments (JSON)"),
        sa.Column('result', postgresql.JSONB, nullable=True, comment="Task result (JSON)"),
        sa.Column('error', sa.Text, nullable=True, comment="Error message if failed"),
        sa.Column('traceback', sa.Text, nullable=True, comment="Error traceback if failed"),
        sa.Column('retries', sa.Integer, default=0, comment="Number of retry attempts"),
        sa.Column('max_retries', sa.Integer, default=3, comment="Maximum retry attempts"),
        sa.Column('eta', sa.DateTime(timezone=True), nullable=True, comment="Scheduled execution time"),
        sa.Column('expires', sa.DateTime(timezone=True), nullable=True, comment="Task expiration time"),
        sa.Column('worker', sa.String(255), nullable=True, comment="Worker hostname that processed the task"),
        sa.Column('queue', sa.String(255), nullable=True, comment="Queue name"),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('runtime_seconds', sa.Float, nullable=True, comment="Task execution time in seconds"),
        schema='public',
    )

    # Create indexes for common queries
    op.create_index(
        'ix_celery_task_records_user_id',
        'celery_task_records',
        ['user_id'],
        schema='public',
    )
    op.create_index(
        'ix_celery_task_records_status',
        'celery_task_records',
        ['status'],
        schema='public',
    )
    op.create_index(
        'ix_celery_task_records_marketplace',
        'celery_task_records',
        ['marketplace'],
        schema='public',
    )
    op.create_index(
        'ix_celery_task_records_created_at',
        'celery_task_records',
        ['created_at'],
        schema='public',
    )
    op.create_index(
        'ix_celery_task_records_user_status',
        'celery_task_records',
        ['user_id', 'status'],
        schema='public',
    )
    op.create_index(
        'ix_celery_task_records_user_marketplace',
        'celery_task_records',
        ['user_id', 'marketplace'],
        schema='public',
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_celery_task_records_user_marketplace', table_name='celery_task_records', schema='public')
    op.drop_index('ix_celery_task_records_user_status', table_name='celery_task_records', schema='public')
    op.drop_index('ix_celery_task_records_created_at', table_name='celery_task_records', schema='public')
    op.drop_index('ix_celery_task_records_marketplace', table_name='celery_task_records', schema='public')
    op.drop_index('ix_celery_task_records_status', table_name='celery_task_records', schema='public')
    op.drop_index('ix_celery_task_records_user_id', table_name='celery_task_records', schema='public')

    # Drop table
    op.drop_table('celery_task_records', schema='public')
