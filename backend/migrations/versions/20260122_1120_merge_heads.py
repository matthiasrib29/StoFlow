"""merge_heads

Revision ID: d6d39a258be5
Revises: 6ab28e891928, 922bd876f757
Create Date: 2026-01-22 11:20:17.976635+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd6d39a258be5'
down_revision: Union[str, None] = ('6ab28e891928', '922bd876f757')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
