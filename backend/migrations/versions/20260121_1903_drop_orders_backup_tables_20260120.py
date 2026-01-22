"""drop orders backup tables 20260120

Revision ID: b7af373f1ff0
Revises: b3c4d5e6f7a8
Create Date: 2026-01-21 19:03:10.247160+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7af373f1ff0'
down_revision: Union[str, None] = 'b3c4d5e6f7a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop backup tables created on 2026-01-20
    op.drop_table('order_products_backup_20260120', schema='vinted')
    op.drop_table('orders_backup_20260120', schema='vinted')


def downgrade() -> None:
    # Cannot restore backup tables - data would be lost
    # These were temporary backup tables, no need to recreate
    pass
