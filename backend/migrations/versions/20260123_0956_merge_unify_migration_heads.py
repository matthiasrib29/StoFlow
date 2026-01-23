"""merge: unify migration heads

Revision ID: aaf52be15ebe
Revises: e7ca75754b9e, 9b1ae5d09454
Create Date: 2026-01-23 09:56:10.382159+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'aaf52be15ebe'
down_revision: Union[str, None] = ('e7ca75754b9e', '9b1ae5d09454')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
