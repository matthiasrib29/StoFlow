"""merge: unify migration heads

Revision ID: 0e1eae92f46a
Revises: f491f40d8758, 8f711fbef16d
Create Date: 2026-01-28 09:13:18.881593+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0e1eae92f46a'
down_revision: Union[str, None] = ('f491f40d8758', '8f711fbef16d')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
