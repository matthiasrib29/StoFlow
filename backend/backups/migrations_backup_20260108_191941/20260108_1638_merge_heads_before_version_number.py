"""merge_heads_before_version_number

Revision ID: de2abccc91f9
Revises: 20260107_0001, 8df2f618afea
Create Date: 2026-01-08 16:38:28.796551+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'de2abccc91f9'
down_revision: Union[str, None] = ('20260107_0001', '8df2f618afea')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
