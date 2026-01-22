"""populate_unique_features_pricing_coefficients

Revision ID: 9bb2236304c8
Revises: 273375b81d83
Create Date: 2026-01-22 11:56:06.067990+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9bb2236304c8'
down_revision: Union[str, None] = '273375b81d83'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
