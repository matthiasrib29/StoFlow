"""merge: unify migration heads after ebay orders feature

Revision ID: 6a3214ecae07
Revises: f8a4a4d3ec7e, 9c7c0b878bb4
Create Date: 2026-01-07 19:21:04.440520+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6a3214ecae07'
down_revision: Union[str, None] = ('f8a4a4d3ec7e', '9c7c0b878bb4')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
