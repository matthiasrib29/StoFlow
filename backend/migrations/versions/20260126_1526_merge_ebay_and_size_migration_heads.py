"""merge ebay and size migration heads

Revision ID: 6e959ed396ab
Revises: e9e9ed10290d, dafae8c50c01
Create Date: 2026-01-26 15:26:37.780249+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6e959ed396ab'
down_revision: Union[str, None] = ('e9e9ed10290d', 'dafae8c50c01')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
