"""remove_translations_from_sizes_normalized

Revision ID: ec223113457e
Revises: f9g3d7e6b8c5
Create Date: 2026-01-08 17:15:50.859770+01:00

Business Rules (2026-01-08):
- Remove translation columns from sizes_normalized table
- Size codes (XS, S, M, L, 28, 30, etc.) are international standards
- No translation needed for size codes
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ec223113457e'
down_revision: Union[str, None] = 'f9g3d7e6b8c5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove translation columns from sizes_normalized (codes are international)."""
    op.drop_column('sizes_normalized', 'name_fr', schema='product_attributes')
    op.drop_column('sizes_normalized', 'name_de', schema='product_attributes')
    op.drop_column('sizes_normalized', 'name_it', schema='product_attributes')
    op.drop_column('sizes_normalized', 'name_es', schema='product_attributes')
    op.drop_column('sizes_normalized', 'name_nl', schema='product_attributes')
    op.drop_column('sizes_normalized', 'name_pl', schema='product_attributes')


def downgrade() -> None:
    """Restore translation columns to sizes_normalized."""
    op.add_column('sizes_normalized',
        sa.Column('name_fr', sa.String(100), nullable=True, comment="Code de la taille (FR)"),
        schema='product_attributes')
    op.add_column('sizes_normalized',
        sa.Column('name_de', sa.String(100), nullable=True, comment="Code de la taille (DE)"),
        schema='product_attributes')
    op.add_column('sizes_normalized',
        sa.Column('name_it', sa.String(100), nullable=True, comment="Code de la taille (IT)"),
        schema='product_attributes')
    op.add_column('sizes_normalized',
        sa.Column('name_es', sa.String(100), nullable=True, comment="Code de la taille (ES)"),
        schema='product_attributes')
    op.add_column('sizes_normalized',
        sa.Column('name_nl', sa.String(100), nullable=True, comment="Code de la taille (NL)"),
        schema='product_attributes')
    op.add_column('sizes_normalized',
        sa.Column('name_pl', sa.String(100), nullable=True, comment="Code de la taille (PL)"),
        schema='product_attributes')
