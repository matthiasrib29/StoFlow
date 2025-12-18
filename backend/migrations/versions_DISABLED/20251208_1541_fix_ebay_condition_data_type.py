"""fix_ebay_condition_data_type

Revision ID: 92f651bd5381
Revises: 0aefcf4d5daf
Create Date: 2025-12-08 15:41:41.767120+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '92f651bd5381'
down_revision: Union[str, None] = '0aefcf4d5daf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Change ebay_condition from BigInteger to Text in conditions table
    op.alter_column(
        'conditions',
        'ebay_condition',
        type_=sa.Text(),
        existing_type=sa.BigInteger(),
        existing_nullable=True,
        schema='product_attributes'
    )


def downgrade() -> None:
    # Revert ebay_condition from Text back to BigInteger
    op.alter_column(
        'conditions',
        'ebay_condition',
        type_=sa.BigInteger(),
        existing_type=sa.Text(),
        existing_nullable=True,
        schema='product_attributes'
    )
