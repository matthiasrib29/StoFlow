"""merge_permissions_and_conversations

Revision ID: dc56e044535f
Revises: 20251219_1000, 20251219_1100
Create Date: 2025-12-19 11:29:46.923335+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dc56e044535f'
down_revision: Union[str, None] = ('20251219_1000', '20251219_1100')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
