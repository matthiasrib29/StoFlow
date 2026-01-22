"""drop_migration_errors_table

Revision ID: a526b508fa0e
Revises: 89a4d89ce1a8
Create Date: 2026-01-22 10:39:52.132454+01:00

Drops the migration_errors table from public schema.
This table was only used for tracking data migration errors and is no longer needed.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a526b508fa0e'
down_revision: Union[str, None] = '89a4d89ce1a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table('migration_errors', schema='public')


def downgrade() -> None:
    op.create_table(
        'migration_errors',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('schema_name', sa.String(100), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('migration_name', sa.String(200), nullable=False),
        sa.Column('error_type', sa.String(100), nullable=False),
        sa.Column('error_details', sa.Text(), nullable=True),
        sa.Column('migrated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        schema='public'
    )
    op.create_index('idx_migration_errors_schema_name', 'migration_errors', ['schema_name'], schema='public')
    op.create_index('idx_migration_errors_error_type', 'migration_errors', ['error_type'], schema='public')
    op.create_index('idx_migration_errors_migrated_at', 'migration_errors', ['migrated_at'], schema='public')
