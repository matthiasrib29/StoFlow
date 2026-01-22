"""add_pricing_coefficient_to_product_attributes

Add pricing_coefficient column to decades, trends, and unique_features tables.
This allows pricing coefficients to be stored in the database instead of hardcoded.

Revision ID: 273375b81d83
Revises: 2226fa17a30c
Create Date: 2026-01-22 11:36:49.779024+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '273375b81d83'
down_revision: Union[str, None] = '2226fa17a30c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add pricing_coefficient to decades table
    op.add_column(
        'decades',
        sa.Column(
            'pricing_coefficient',
            sa.DECIMAL(precision=3, scale=2),
            nullable=False,
            server_default='0.00',
            comment='Pricing coefficient for vintage bonus (0.00 to 0.20)'
        ),
        schema='product_attributes'
    )

    # Add pricing_coefficient to trends table
    op.add_column(
        'trends',
        sa.Column(
            'pricing_coefficient',
            sa.DECIMAL(precision=3, scale=2),
            nullable=False,
            server_default='0.00',
            comment='Pricing coefficient for trend bonus (0.00 to 0.20)'
        ),
        schema='product_attributes'
    )

    # Add pricing_coefficient to unique_features table
    op.add_column(
        'unique_features',
        sa.Column(
            'pricing_coefficient',
            sa.DECIMAL(precision=3, scale=2),
            nullable=False,
            server_default='0.00',
            comment='Pricing coefficient for feature bonus (0.00 to 0.20)'
        ),
        schema='product_attributes'
    )


def downgrade() -> None:
    op.drop_column('unique_features', 'pricing_coefficient', schema='product_attributes')
    op.drop_column('trends', 'pricing_coefficient', schema='product_attributes')
    op.drop_column('decades', 'pricing_coefficient', schema='product_attributes')
