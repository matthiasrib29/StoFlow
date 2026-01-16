"""merge: unify migration heads (beta_signups + remove_jsonb_column)

Revision ID: 9de98e91cd03
Revises: 07f059f11992, e6514e0300aa
Create Date: 2026-01-15 16:32:00.947545+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9de98e91cd03'
down_revision: Union[str, None] = ('07f059f11992', 'e6514e0300aa')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
