"""merge_alembic_cleanup_with_datadome

Revision ID: 342a43a97141
Revises: 20251219_1200, 41791f14505b
Create Date: 2025-12-19 17:05:26.771842+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '342a43a97141'
down_revision: Union[str, None] = ('20251219_1200', '41791f14505b')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
