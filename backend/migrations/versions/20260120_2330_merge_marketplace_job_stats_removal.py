"""merge_marketplace_job_stats_removal

Revision ID: 663b27621dca
Revises: c45205gd58e1, c56f8e2a1b90
Create Date: 2026-01-20 23:30:07.503878+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '663b27621dca'
down_revision: Union[str, None] = ('c45205gd58e1', 'c56f8e2a1b90')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
