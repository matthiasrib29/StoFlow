"""add odd W and L sizes for precision

Revision ID: dafae8c50c01
Revises: e7ca75754b9e
Create Date: 2026-01-26 14:54:34.710547+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dafae8c50c01'
down_revision: Union[str, None] = 'e7ca75754b9e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Generate all sizes to add (standalone odd W + all W/L combinations including odd)
    sizes_to_add = []

    # 1. Standalone odd W sizes (W25, W27, ..., W45)
    for w in range(25, 46, 2):
        sizes_to_add.append(f"W{w}")

    # 2. All W/L combinations: W24-W46 × L26-L38 (odd + even)
    for w in range(24, 47):
        for l in range(26, 39):
            sizes_to_add.append(f"W{w}/L{l}")

    # Bulk insert with ON CONFLICT DO NOTHING to skip existing
    conn = op.get_bind()
    for size in sizes_to_add:
        conn.execute(
            sa.text(
                "INSERT INTO product_attributes.sizes_normalized (name_en) "
                "VALUES (:name) ON CONFLICT DO NOTHING"
            ),
            {"name": size},
        )


def downgrade() -> None:
    # Remove only the sizes added by this migration (odd standalone W + odd W/L combos)
    sizes_to_remove = []

    for w in range(25, 46, 2):
        sizes_to_remove.append(f"W{w}")

    for w in range(24, 47):
        for l in range(26, 39):
            # Only remove odd combinations (at least one odd number)
            if w % 2 != 0 or l % 2 != 0:
                sizes_to_remove.append(f"W{w}/L{l}")

    conn = op.get_bind()
    for size in sizes_to_remove:
        conn.execute(
            sa.text(
                "DELETE FROM product_attributes.sizes_normalized WHERE name_en = :name"
            ),
            {"name": size},
        )
