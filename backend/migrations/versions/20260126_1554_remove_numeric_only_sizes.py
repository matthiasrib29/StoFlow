"""remove numeric-only sizes

Revision ID: b3ee8c6c03b9
Revises: 6e959ed396ab
Create Date: 2026-01-26 15:54:33.817106+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3ee8c6c03b9'
down_revision: Union[str, None] = '6e959ed396ab'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


NUMERIC_SIZES = ['36', '38', '40', '42', '44', '46', '48', '50']


def upgrade() -> None:
    conn = op.get_bind()
    for size in NUMERIC_SIZES:
        conn.execute(
            sa.text(
                "DELETE FROM product_attributes.sizes_normalized WHERE name_en = :name"
            ),
            {"name": size},
        )


def downgrade() -> None:
    conn = op.get_bind()
    for size in NUMERIC_SIZES:
        conn.execute(
            sa.text(
                "INSERT INTO product_attributes.sizes_normalized (name_en) "
                "VALUES (:name) ON CONFLICT DO NOTHING"
            ),
            {"name": size},
        )
