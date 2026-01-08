"""remove_name_fr_from_brands

Revision ID: 3b9cddbe6380
Revises: c8fad3791ba7
Create Date: 2026-01-08 16:57:55.295999+01:00

Business Rules (2026-01-08):
- Remove name_fr column from brands table
- Brand names don't need translation (Nike, Adidas, etc. remain the same)
- Column is nullable so safe to drop without data migration
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3b9cddbe6380'
down_revision: Union[str, None] = 'c8fad3791ba7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove name_fr column from brands table."""
    op.drop_column('brands', 'name_fr', schema='product_attributes')


def downgrade() -> None:
    """Restore name_fr column to brands table."""
    op.add_column(
        'brands',
        sa.Column('name_fr', sa.String(100), nullable=True, comment="Nom de la marque (FR)"),
        schema='product_attributes'
    )
