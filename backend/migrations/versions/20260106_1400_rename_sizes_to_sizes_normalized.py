"""rename_sizes_to_sizes_normalized

Revision ID: 20260106_1400
Revises: 029b9f955564
Create Date: 2026-01-06 14:00:00.000000+01:00

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '20260106_1400'
down_revision: Union[str, None] = '029b9f955564'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Rename table sizes to sizes_normalized in product_attributes schema.
    """
    conn = op.get_bind()

    # Rename table
    op.execute(text("""
        ALTER TABLE product_attributes.sizes
        RENAME TO sizes_normalized;
    """))

    # Rename primary key constraint
    op.execute(text("""
        ALTER TABLE product_attributes.sizes_normalized
        RENAME CONSTRAINT sizes_pkey TO sizes_normalized_pkey;
    """))

    # Rename index (if exists)
    op.execute(text("""
        ALTER INDEX IF EXISTS product_attributes.ix_sizes_name_en
        RENAME TO ix_sizes_normalized_name_en;
    """))

    print("✅ Renamed sizes → sizes_normalized in product_attributes schema")


def downgrade() -> None:
    """
    Rollback: rename sizes_normalized back to sizes.
    """
    conn = op.get_bind()

    # Rename index back
    op.execute(text("""
        ALTER INDEX IF EXISTS product_attributes.ix_sizes_normalized_name_en
        RENAME TO ix_sizes_name_en;
    """))

    # Rename primary key constraint back
    op.execute(text("""
        ALTER TABLE product_attributes.sizes_normalized
        RENAME CONSTRAINT sizes_normalized_pkey TO sizes_pkey;
    """))

    # Rename table back
    op.execute(text("""
        ALTER TABLE product_attributes.sizes_normalized
        RENAME TO sizes;
    """))

    print("✅ Rolled back: sizes_normalized → sizes")
