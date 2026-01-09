"""Add vinted_id column to colors table

Revision ID: 9b4d6e2f3a5c
Revises: 8a3c5f1d2e4b
Create Date: 2026-01-05 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9b4d6e2f3a5c'
down_revision: Union[str, None] = '8a3c5f1d2e4b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add vinted_id column to colors table."""
    op.add_column(
        'colors',
        sa.Column('vinted_id', sa.Integer(), nullable=True),
        schema='product_attributes'
    )


def downgrade() -> None:
    """Remove vinted_id column from colors table."""
    op.drop_column('colors', 'vinted_id', schema='product_attributes')
