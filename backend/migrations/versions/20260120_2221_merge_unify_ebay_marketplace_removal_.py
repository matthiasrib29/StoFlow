"""merge: unify ebay_marketplace_removal and beta_discount heads

Revision ID: f5ac88970130
Revises: 20260120_1000, 5c0d1e2f3a4b
Create Date: 2026-01-20 22:21:03.016346+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f5ac88970130'
down_revision: Union[str, None] = ('20260120_1000', '5c0d1e2f3a4b')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
