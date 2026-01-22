"""drop_clothing_prices_table

Revision ID: 89a4d89ce1a8
Revises: d9da4b2acb30
Create Date: 2026-01-22 10:33:29.686917+01:00

Drops the unused clothing_prices table from public schema.
This table was intended for base pricing but was replaced by the new pricing algorithm
using brand_groups and models tables.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '89a4d89ce1a8'
down_revision: Union[str, None] = 'd9da4b2acb30'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table('clothing_prices', schema='public')


def downgrade() -> None:
    op.create_table(
        'clothing_prices',
        sa.Column('brand', sa.String(100), nullable=False, primary_key=True),
        sa.Column('category', sa.String(255), nullable=False, primary_key=True),
        sa.Column('base_price', sa.DECIMAL(10, 2), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('brand', 'category'),
        schema='public'
    )
