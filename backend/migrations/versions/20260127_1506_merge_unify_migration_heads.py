"""merge: unify migration heads

Revision ID: c54480463cd1
Revises: 31179c7ddf09, 20260127_0100
Create Date: 2026-01-27 15:06:24.217710+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c54480463cd1'
down_revision: Union[str, None] = ('31179c7ddf09', '20260127_0100')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
