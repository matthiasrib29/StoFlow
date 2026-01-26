"""create_ebay_mapping_table

Revision ID: 4e4ac6402b10
Revises: 953e068d8e94
Create Date: 2026-01-23 11:48:56.977503+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4e4ac6402b10'
down_revision: Union[str, None] = '953e068d8e94'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "mapping",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("my_category", sa.String(100), nullable=False, comment="StoFlow category (name_en)"),
        sa.Column("my_gender", sa.String(20), nullable=False, comment="Gender: men, women, boys, girls"),
        sa.Column("ebay_category_id", sa.String(20), nullable=False, comment="FK to ebay.categories.category_id"),
        sa.UniqueConstraint("my_category", "my_gender", name="uq_ebay_mapping_category_gender"),
        schema="ebay",
    )

    op.create_index("ix_ebay_mapping_category_gender", "mapping", ["my_category", "my_gender"], schema="ebay")
    op.create_index("ix_ebay_mapping_ebay_category_id", "mapping", ["ebay_category_id"], schema="ebay")


def downgrade() -> None:
    op.drop_index("ix_ebay_mapping_ebay_category_id", table_name="mapping", schema="ebay")
    op.drop_index("ix_ebay_mapping_category_gender", table_name="mapping", schema="ebay")
    op.drop_table("mapping", schema="ebay")
