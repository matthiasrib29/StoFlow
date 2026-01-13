"""merge: unify migration heads

Revision ID: 16637868e60c
Revises: 20260113_1130, 20260113_1200
Create Date: 2026-01-13 12:51:47.075948+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '16637868e60c'
down_revision: Union[str, None] = ('20260113_1130', '20260113_1200')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
