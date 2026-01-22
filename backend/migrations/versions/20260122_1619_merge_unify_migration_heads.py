"""merge: unify migration heads

Revision ID: ae033c2ade2a
Revises: 8a7c2e3f4d5b, d7af6191fc35
Create Date: 2026-01-22 16:19:55.054105+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ae033c2ade2a'
down_revision: Union[str, None] = ('8a7c2e3f4d5b', 'd7af6191fc35')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
