"""remove_translations_from_decades

Revision ID: 4a281fb619e9
Revises: 4886bd185f07
Create Date: 2026-01-08 17:20:14.281995+01:00

Business Rules (2026-01-08):
- Remove translation columns from decades table
- Decade codes (1950s, 1960s, 1970s, etc.) are international standards
- No translation needed for decade codes
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4a281fb619e9'
down_revision: Union[str, None] = '4886bd185f07'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove translation columns from decades (codes are international)."""
    op.drop_column('decades', 'name_fr', schema='product_attributes')
    op.drop_column('decades', 'name_de', schema='product_attributes')
    op.drop_column('decades', 'name_it', schema='product_attributes')
    op.drop_column('decades', 'name_es', schema='product_attributes')
    op.drop_column('decades', 'name_nl', schema='product_attributes')
    op.drop_column('decades', 'name_pl', schema='product_attributes')


def downgrade() -> None:
    """Restore translation columns to decades."""
    op.add_column('decades',
        sa.Column('name_fr', sa.String(100), nullable=True, comment="Nom de la décennie (FR)"),
        schema='product_attributes')
    op.add_column('decades',
        sa.Column('name_de', sa.String(100), nullable=True, comment="Nom de la décennie (DE)"),
        schema='product_attributes')
    op.add_column('decades',
        sa.Column('name_it', sa.String(100), nullable=True, comment="Nom de la décennie (IT)"),
        schema='product_attributes')
    op.add_column('decades',
        sa.Column('name_es', sa.String(100), nullable=True, comment="Nom de la décennie (ES)"),
        schema='product_attributes')
    op.add_column('decades',
        sa.Column('name_nl', sa.String(100), nullable=True, comment="Nom de la décennie (NL)"),
        schema='product_attributes')
    op.add_column('decades',
        sa.Column('name_pl', sa.String(100), nullable=True, comment="Nom de la décennie (PL)"),
        schema='product_attributes')
