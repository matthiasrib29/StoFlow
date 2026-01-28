"""add category_group and equivalences to sizes_normalized

Phase 2 of size system refactoring:
- category_group: Classify sizes (letter, numeric_eu, waist, one_size)
- equivalent_fr/us/it: International size conversions

Revision ID: sz_catgrp_001
Revises: f2a3b4c5d6e7
Create Date: 2026-01-28
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = 'sz_catgrp_001'
down_revision: Union[str, None] = 'f2a3b4c5d6e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # Check if columns already exist (idempotent)
    columns_to_add = [
        ('category_group', 'VARCHAR(20)'),
        ('equivalent_fr', 'VARCHAR(20)'),
        ('equivalent_us', 'VARCHAR(20)'),
        ('equivalent_it', 'VARCHAR(20)'),
    ]

    for col_name, col_type in columns_to_add:
        col_exists = conn.execute(text(
            "SELECT EXISTS ("
            "  SELECT 1 FROM information_schema.columns "
            "  WHERE table_schema = 'product_attributes' "
            "    AND table_name = 'sizes_normalized' "
            "    AND column_name = :col_name"
            ")"
        ), {"col_name": col_name}).scalar()

        if not col_exists:
            conn.execute(text(
                f'ALTER TABLE product_attributes.sizes_normalized '
                f'ADD COLUMN {col_name} {col_type}'
            ))

    # Create index on category_group if not exists
    idx_exists = conn.execute(text(
        "SELECT EXISTS ("
        "  SELECT 1 FROM pg_indexes "
        "  WHERE schemaname = 'product_attributes' "
        "    AND tablename = 'sizes_normalized' "
        "    AND indexname = 'idx_sizes_normalized_category_group'"
        ")"
    )).scalar()

    if not idx_exists:
        conn.execute(text(
            "CREATE INDEX idx_sizes_normalized_category_group "
            "ON product_attributes.sizes_normalized(category_group)"
        ))


def downgrade() -> None:
    conn = op.get_bind()

    # Drop index
    conn.execute(text(
        "DROP INDEX IF EXISTS product_attributes.idx_sizes_normalized_category_group"
    ))

    # Drop columns
    columns_to_drop = ['category_group', 'equivalent_fr', 'equivalent_us', 'equivalent_it']

    for col_name in columns_to_drop:
        col_exists = conn.execute(text(
            "SELECT EXISTS ("
            "  SELECT 1 FROM information_schema.columns "
            "  WHERE table_schema = 'product_attributes' "
            "    AND table_name = 'sizes_normalized' "
            "    AND column_name = :col_name"
            ")"
        ), {"col_name": col_name}).scalar()

        if col_exists:
            conn.execute(text(
                f'ALTER TABLE product_attributes.sizes_normalized DROP COLUMN {col_name}'
            ))
