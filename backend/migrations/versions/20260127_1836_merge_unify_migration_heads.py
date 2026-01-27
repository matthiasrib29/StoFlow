"""merge: unify migration heads

Revision ID: f491f40d8758
Revises: 62f78011361f, 92d0dba977cb
Create Date: 2026-01-27 18:36:25.419211+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f491f40d8758'
down_revision: Union[str, None] = ('62f78011361f', '92d0dba977cb')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
