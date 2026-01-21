"""merge: unify beta security fixes with main branch

Revision ID: 3c57e3e4522b
Revises: 20260120_2330, 663b27621dca
Create Date: 2026-01-20 23:43:19.314079+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3c57e3e4522b'
down_revision: Union[str, None] = ('20260120_2330', '663b27621dca')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
