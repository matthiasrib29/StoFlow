"""merge: unify migration heads after product-model feature

Revision ID: 151b3e941a9c
Revises: 20260103_0100, 9183cce67eb2
Create Date: 2026-01-03 18:08:10.202625+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '151b3e941a9c'
down_revision: Union[str, None] = ('20260103_0100', '9183cce67eb2')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
