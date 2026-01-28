"""merge: unify migration heads

Revision ID: 92d0dba977cb
Revises: 654a38c4df6d, c54480463cd1
Create Date: 2026-01-27 18:34:46.915444+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '92d0dba977cb'
down_revision: Union[str, None] = ('654a38c4df6d', 'c54480463cd1')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
