"""merge heads: vinted_prospects and link_ebay_products

Revision ID: c4ce5f067571
Revises: 3321c048edc7, d687e39bd2a0
Create Date: 2026-01-19 12:46:58.928819+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c4ce5f067571'
down_revision: Union[str, None] = ('3321c048edc7', 'd687e39bd2a0')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
