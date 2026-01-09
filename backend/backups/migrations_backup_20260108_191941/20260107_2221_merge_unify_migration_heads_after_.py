"""merge: unify migration heads after improve-attributes

Revision ID: 243e932d0557
Revises: 6a3214ecae07, a9b8c7d6e5f4
Create Date: 2026-01-07 22:21:04.040266+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '243e932d0557'
down_revision: Union[str, None] = ('6a3214ecae07', 'a9b8c7d6e5f4')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
