"""create_ebay_categories_table

Revision ID: 953e068d8e94
Revises: aaf52be15ebe
Create Date: 2026-01-23 10:47:28.924997+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '953e068d8e94'
down_revision: Union[str, None] = 'aaf52be15ebe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("category_id", sa.String(20), primary_key=True, comment="eBay category ID (natural key)"),
        sa.Column("category_name", sa.String(255), nullable=False, comment="Category name (English, EBAY_GB)"),
        sa.Column("parent_id", sa.String(20), sa.ForeignKey("ebay.categories.category_id", ondelete="CASCADE"), nullable=True, comment="Parent category ID"),
        sa.Column("level", sa.SmallInteger(), nullable=False, comment="Level in the category tree (0 = root)"),
        sa.Column("is_leaf", sa.Boolean(), server_default="false", nullable=False, comment="True if category is a leaf (can be used for listing)"),
        sa.Column("path", sa.String(1000), nullable=True, comment="Full breadcrumb path"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False, comment="Record creation timestamp"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False, comment="Record last update timestamp"),
        schema="ebay",
    )

    op.create_index("ix_ebay_categories_parent_id", "categories", ["parent_id"], schema="ebay")
    op.create_index("ix_ebay_categories_level", "categories", ["level"], schema="ebay")
    op.create_index("ix_ebay_categories_is_leaf", "categories", ["is_leaf"], schema="ebay")
    op.create_index("ix_ebay_categories_category_name", "categories", ["category_name"], schema="ebay")


def downgrade() -> None:
    op.drop_index("ix_ebay_categories_category_name", table_name="categories", schema="ebay")
    op.drop_index("ix_ebay_categories_is_leaf", table_name="categories", schema="ebay")
    op.drop_index("ix_ebay_categories_level", table_name="categories", schema="ebay")
    op.drop_index("ix_ebay_categories_parent_id", table_name="categories", schema="ebay")
    op.drop_table("categories", schema="ebay")
