"""add registrar_name and photo_url to vinted_pro_sellers

Revision ID: 62f78011361f
Revises: c54480463cd1
Create Date: 2026-01-27 16:27:53.103858+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '62f78011361f'
down_revision: Union[str, None] = 'c54480463cd1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "vinted_pro_sellers",
        sa.Column("registrar_name", sa.String(255), nullable=True, comment="Registrar name (e.g. RCS Aubenas)"),
        schema="vinted",
    )
    op.add_column(
        "vinted_pro_sellers",
        sa.Column("photo_url", sa.String(500), nullable=True, comment="Profile photo URL"),
        schema="vinted",
    )


def downgrade() -> None:
    op.drop_column("vinted_pro_sellers", "photo_url", schema="vinted")
    op.drop_column("vinted_pro_sellers", "registrar_name", schema="vinted")
