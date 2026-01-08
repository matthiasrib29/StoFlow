"""Add vinted_women_id and vinted_men_id columns to sizes table

Revision ID: 8a3c5f1d2e4b
Revises: 151b3e941a9c
Create Date: 2026-01-05 09:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8a3c5f1d2e4b'
down_revision: Union[str, None] = '20260105_0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add vinted_women_id and vinted_men_id columns to sizes table.

    This replaces the single vinted_id column with gender-specific columns
    to properly support Vinted's size system where sizes have different IDs
    for women vs men.
    """
    # Add new columns
    op.add_column(
        'sizes',
        sa.Column('vinted_women_id', sa.Integer(), nullable=True),
        schema='product_attributes'
    )
    op.add_column(
        'sizes',
        sa.Column('vinted_men_id', sa.Integer(), nullable=True),
        schema='product_attributes'
    )

    # Drop old vinted_id column
    op.drop_column('sizes', 'vinted_id', schema='product_attributes')


def downgrade() -> None:
    """Restore single vinted_id column."""
    # Add back the old column
    op.add_column(
        'sizes',
        sa.Column('vinted_id', sa.Integer(), nullable=True),
        schema='product_attributes'
    )

    # Drop new columns
    op.drop_column('sizes', 'vinted_women_id', schema='product_attributes')
    op.drop_column('sizes', 'vinted_men_id', schema='product_attributes')
