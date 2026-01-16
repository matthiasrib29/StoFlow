"""merge: unify migration heads

Revision ID: ab9f17f93147
Revises: 9de98e91cd03, 39282d822e9c
Create Date: 2026-01-16 09:43:24.939570+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ab9f17f93147'
down_revision: Union[str, None] = ('9de98e91cd03', '39282d822e9c')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
