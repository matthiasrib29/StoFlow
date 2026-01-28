"""add FK sizes_original to sizes_normalized

Phase 2 of size system refactoring:
- Add size_normalized_id column to sizes_original
- FK to sizes_normalized.name_en for auto-resolution

Revision ID: sz_catgrp_003
Revises: sz_catgrp_002
Create Date: 2026-01-28
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = 'sz_catgrp_003'
down_revision: Union[str, None] = 'sz_catgrp_002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # Check if column already exists (idempotent)
    col_exists = conn.execute(text(
        "SELECT EXISTS ("
        "  SELECT 1 FROM information_schema.columns "
        "  WHERE table_schema = 'product_attributes' "
        "    AND table_name = 'sizes_original' "
        "    AND column_name = 'size_normalized_id'"
        ")"
    )).scalar()

    if not col_exists:
        # Add column
        conn.execute(text(
            "ALTER TABLE product_attributes.sizes_original "
            "ADD COLUMN size_normalized_id VARCHAR(100)"
        ))

        # Add FK constraint
        conn.execute(text(
            "ALTER TABLE product_attributes.sizes_original "
            "ADD CONSTRAINT fk_sizes_original_size_normalized "
            "FOREIGN KEY (size_normalized_id) "
            "REFERENCES product_attributes.sizes_normalized(name_en) "
            "ON UPDATE CASCADE ON DELETE SET NULL"
        ))

        # Add index
        conn.execute(text(
            "CREATE INDEX idx_sizes_original_size_normalized_id "
            "ON product_attributes.sizes_original(size_normalized_id)"
        ))


def downgrade() -> None:
    conn = op.get_bind()

    col_exists = conn.execute(text(
        "SELECT EXISTS ("
        "  SELECT 1 FROM information_schema.columns "
        "  WHERE table_schema = 'product_attributes' "
        "    AND table_name = 'sizes_original' "
        "    AND column_name = 'size_normalized_id'"
        ")"
    )).scalar()

    if col_exists:
        # Drop index
        conn.execute(text(
            "DROP INDEX IF EXISTS product_attributes.idx_sizes_original_size_normalized_id"
        ))

        # Drop FK constraint
        conn.execute(text(
            "ALTER TABLE product_attributes.sizes_original "
            "DROP CONSTRAINT IF EXISTS fk_sizes_original_size_normalized"
        ))

        # Drop column
        conn.execute(text(
            "ALTER TABLE product_attributes.sizes_original "
            "DROP COLUMN size_normalized_id"
        ))
