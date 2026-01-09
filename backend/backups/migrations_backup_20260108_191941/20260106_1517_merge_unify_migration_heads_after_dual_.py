"""merge: unify migration heads after dual-size-attributes

Revision ID: ef2af2d8a1c3
Revises: 20260106_1410, 2af3befa946a
Create Date: 2026-01-06 15:17:51.617475+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ef2af2d8a1c3'
down_revision: Union[str, None] = ('20260106_1410', '2af3befa946a')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
