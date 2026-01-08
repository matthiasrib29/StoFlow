"""merge: unify migration heads after etsy integration

Revision ID: ef0a404372ff
Revises: 4fcb2f0387ba, be0703016e38
Create Date: 2026-01-07 12:23:55.896783+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ef0a404372ff'
down_revision: Union[str, None] = ('4fcb2f0387ba', 'be0703016e38')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
