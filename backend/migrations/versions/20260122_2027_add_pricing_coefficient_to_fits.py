"""add_pricing_coefficient_to_fits

Revision ID: 566f29854d44
Revises: 733d8a9ac5b4
Create Date: 2026-01-22 20:27:35.063719+01:00

Adds pricing_coefficient column to product_attributes.fits table.
This coefficient is used in the pricing algorithm to adjust prices
based on the fit type (e.g., bootcut, wide leg have different values).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '566f29854d44'
down_revision: Union[str, None] = '733d8a9ac5b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add pricing_coefficient column to fits table."""
    conn = op.get_bind()

    # Check if column already exists
    result = conn.execute(text("""
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = 'product_attributes'
        AND table_name = 'fits'
        AND column_name = 'pricing_coefficient'
    """))
    if result.fetchone():
        return  # Column already exists

    # Add pricing_coefficient column with default 0.00 (neutral)
    op.add_column(
        'fits',
        sa.Column('pricing_coefficient', sa.Numeric(4, 2), nullable=False, server_default='0.00'),
        schema='product_attributes'
    )

    # Initialize all fits with 0.00 (neutral - user will update with correct values)
    # Regular fit is the reference (0.00)
    conn.execute(text("""
        UPDATE product_attributes.fits
        SET pricing_coefficient = 0.00
    """))


def downgrade() -> None:
    """Remove pricing_coefficient column from fits table."""
    op.drop_column('fits', 'pricing_coefficient', schema='product_attributes')
