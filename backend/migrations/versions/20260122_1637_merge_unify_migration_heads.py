"""merge: unify migration heads

Revision ID: 733d8a9ac5b4
Revises: 4c9523cb4029, ae033c2ade2a
Create Date: 2026-01-22 16:37:22.867164+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '733d8a9ac5b4'
down_revision: Union[str, None] = ('4c9523cb4029', 'ae033c2ade2a')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
