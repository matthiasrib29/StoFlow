"""move_attribute_tables_to_product_attributes_schema

Revision ID: 375ae2b4815c
Revises: 22e1178aebb9
Create Date: 2025-12-08 14:52:48.829782+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '375ae2b4815c'
down_revision: Union[str, None] = '22e1178aebb9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ===== CREATE SCHEMA product_attributes IF NOT EXISTS =====
    op.execute("CREATE SCHEMA IF NOT EXISTS product_attributes")

    # ===== MOVE TABLES FROM public TO product_attributes =====
    tables_to_move = [
        "condition_sups",
        "closures",
        "decades",
        "origins",
        "rises",
        "sleeve_lengths",
        "trends",
        "unique_features",
    ]

    for table_name in tables_to_move:
        op.execute(f"ALTER TABLE public.{table_name} SET SCHEMA product_attributes")


def downgrade() -> None:
    # ===== MOVE TABLES BACK FROM product_attributes TO public =====
    tables_to_move = [
        "condition_sups",
        "closures",
        "decades",
        "origins",
        "rises",
        "sleeve_lengths",
        "trends",
        "unique_features",
    ]

    for table_name in tables_to_move:
        op.execute(f"ALTER TABLE product_attributes.{table_name} SET SCHEMA public")
