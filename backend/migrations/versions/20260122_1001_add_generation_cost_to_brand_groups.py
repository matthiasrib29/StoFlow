"""add_generation_cost_to_brand_groups

Revision ID: 6ab28e891928
Revises: b3c4d5e6f7a8
Create Date: 2026-01-22 10:01:11.356868+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6ab28e891928'
down_revision: Union[str, None] = 'b3c4d5e6f7a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'brand_groups',
        sa.Column('generation_cost', sa.DECIMAL(10, 6), nullable=True),
        schema='public'
    )


def downgrade() -> None:
    op.drop_column('brand_groups', 'generation_cost', schema='public')
