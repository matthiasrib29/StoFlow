"""merge_shipment_and_celery_heads

Revision ID: ed768f72d538
Revises: 97fb25ac9944, f9a0b1c2d3e4
Create Date: 2026-01-20 16:39:33.190103+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ed768f72d538'
down_revision: Union[str, None] = ('97fb25ac9944', 'f9a0b1c2d3e4')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
