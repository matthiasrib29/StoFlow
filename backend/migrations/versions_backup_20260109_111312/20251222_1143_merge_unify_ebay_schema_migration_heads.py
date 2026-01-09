"""merge: unify ebay schema migration heads

Revision ID: 9a0b65decb46
Revises: c7a9b3d8e5f2, 20251222_1100
Create Date: 2025-12-22 11:43:16.391269+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9a0b65decb46'
down_revision: Union[str, None] = ('c7a9b3d8e5f2', '20251222_1100')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
