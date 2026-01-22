"""add_pricing_coefficient_to_origins

Add pricing_coefficient and is_premium columns to origins table.
Premium origins (Italy, France, Japan, USA, UK, Germany) get +0.15 bonus.

Revision ID: 219f1f322a89
Revises: f424dde129a1
Create Date: 2026-01-22 12:11:22.646380+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '219f1f322a89'
down_revision: Union[str, None] = 'f424dde129a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Premium origins with +0.15 coefficient
PREMIUM_ORIGINS = ["Italy", "France", "Japan", "Usa", "United kingdom", "Germany"]


def upgrade() -> None:
    # Add columns to origins table
    op.add_column(
        'origins',
        sa.Column('pricing_coefficient', sa.DECIMAL(precision=3, scale=2),
                  nullable=False, server_default='0.00'),
        schema='product_attributes'
    )
    op.add_column(
        'origins',
        sa.Column('is_premium', sa.Boolean(),
                  nullable=False, server_default='false'),
        schema='product_attributes'
    )

    # Populate premium origins
    conn = op.get_bind()
    for origin in PREMIUM_ORIGINS:
        conn.execute(
            text("""
                UPDATE product_attributes.origins
                SET pricing_coefficient = 0.15, is_premium = true
                WHERE name_en = :name
            """),
            {"name": origin}
        )


def downgrade() -> None:
    op.drop_column('origins', 'is_premium', schema='product_attributes')
    op.drop_column('origins', 'pricing_coefficient', schema='product_attributes')
