"""merge translations branch with idempotency branch

Revision ID: 53a8b38c9737
Revises: 156564a2f2c7, 115b8afdd149
Create Date: 2026-01-08 19:05:13.616808+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '53a8b38c9737'
down_revision: Union[str, None] = ('156564a2f2c7', '115b8afdd149')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
