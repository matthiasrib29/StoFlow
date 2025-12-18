"""add_missing_columns_to_attribute_tables

Revision ID: 182978057ce8
Revises: a17332e07bb1
Create Date: 2025-12-08 14:59:55.825217+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '182978057ce8'
down_revision: Union[str, None] = 'a17332e07bb1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ===== ADD MISSING COLUMNS TO BRANDS TABLE =====
    op.add_column('brands', sa.Column('vinted_id', sa.Text(), nullable=True, comment='ID Vinted pour intégration marketplace'), schema='product_attributes')
    op.add_column('brands', sa.Column('monitoring', sa.Boolean(), nullable=False, server_default='false', comment='Marque surveillée (tracking spécial)'), schema='product_attributes')
    op.add_column('brands', sa.Column('sector_jeans', sa.String(20), nullable=True, comment='Segment de marché pour les jeans'), schema='product_attributes')
    op.add_column('brands', sa.Column('sector_jacket', sa.String(20), nullable=True, comment='Segment de marché pour les vestes'), schema='product_attributes')


def downgrade() -> None:
    # ===== REMOVE ADDED COLUMNS FROM BRANDS TABLE =====
    op.drop_column('brands', 'sector_jacket', schema='product_attributes')
    op.drop_column('brands', 'sector_jeans', schema='product_attributes')
    op.drop_column('brands', 'monitoring', schema='product_attributes')
    op.drop_column('brands', 'vinted_id', schema='product_attributes')
