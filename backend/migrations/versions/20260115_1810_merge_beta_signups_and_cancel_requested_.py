"""merge: beta_signups and cancel_requested heads

Revision ID: 39282d822e9c
Revises: 07f059f11992, 381503c3aa77
Create Date: 2026-01-15 18:10:35.512442+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '39282d822e9c'
down_revision: Union[str, None] = ('07f059f11992', '381503c3aa77')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
