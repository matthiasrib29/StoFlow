"""merge: unify migration heads after product-attribut hotfix

Revision ID: 8df2f618afea
Revises: 0d178c306708, fa1eb2c1d541
Create Date: 2026-01-07 23:02:58.802151+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8df2f618afea'
down_revision: Union[str, None] = ('0d178c306708', 'fa1eb2c1d541')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
