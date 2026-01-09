"""merge: unify migration heads after plugin-task hotfix

Revision ID: 46909e0170ba
Revises: fix_plugin_tasks_template, 20251219_1500, 342a43a97141
Create Date: 2025-12-22 10:01:44.146441+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '46909e0170ba'
down_revision: Union[str, None] = ('fix_plugin_tasks_template', '20251219_1500', '342a43a97141')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
