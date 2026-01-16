"""merge: unify migration heads for test dump generation

Revision ID: ff06af3092db
Revises: c2b2384bb910, 4269646f817b
Create Date: 2026-01-16 13:42:27.123878+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ff06af3092db'
down_revision: Union[str, None] = ('c2b2384bb910', '4269646f817b')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
