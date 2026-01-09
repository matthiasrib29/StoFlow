"""merge: unify migration heads after ai-implementation feature

Revision ID: fa1eb2c1d541
Revises: aae3bed742fd, 243e932d0557
Create Date: 2026-01-07 23:01:42.955612+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fa1eb2c1d541'
down_revision: Union[str, None] = ('aae3bed742fd', '243e932d0557')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
