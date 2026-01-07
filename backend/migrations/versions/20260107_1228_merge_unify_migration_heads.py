"""merge: unify migration heads

Revision ID: 4d2e58dae912
Revises: 303159a94619, ef0a404372ff
Create Date: 2026-01-07 12:28:50.902655+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4d2e58dae912'
down_revision: Union[str, None] = ('303159a94619', 'ef0a404372ff')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
