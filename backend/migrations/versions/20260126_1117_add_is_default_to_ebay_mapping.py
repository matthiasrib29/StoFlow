"""add_is_default_to_ebay_mapping

Revision ID: 8df28affd5e2
Revises: 4e4ac6402b10
Create Date: 2026-01-26 11:17:54.111092+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8df28affd5e2'
down_revision: Union[str, None] = '4e4ac6402b10'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "mapping",
        sa.Column("is_default", sa.Boolean(), server_default="false", nullable=False,
                  comment="True = default for reverse mapping (eBay -> StoFlow)"),
        schema="ebay",
    )


def downgrade() -> None:
    op.drop_column("mapping", "is_default", schema="ebay")
