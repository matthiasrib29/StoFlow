"""merge: unify migration heads

Revision ID: 6bc865c4c841
Revises: 68a6d6ef6f65, 20260112_1800
Create Date: 2026-01-12 15:32:03.690396+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6bc865c4c841'
down_revision: Union[str, None] = ('68a6d6ef6f65', '20260112_1800')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
