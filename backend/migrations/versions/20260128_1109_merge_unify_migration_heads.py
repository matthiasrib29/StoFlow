"""merge: unify migration heads

Revision ID: dd45dbbb6368
Revises: efafc37b381d, 19c2a4d0c9b8
Create Date: 2026-01-28 11:09:29.073172+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dd45dbbb6368'
down_revision: Union[str, None] = ('efafc37b381d', '19c2a4d0c9b8')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
