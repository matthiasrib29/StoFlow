"""add_gender_to_categories

Revision ID: ba7bb9ecdbf4
Revises: 2e30e856c66d
Create Date: 2025-12-08 10:36:48.674402+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ba7bb9ecdbf4'
down_revision: Union[str, None] = '2e30e856c66d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create gender ENUM type
    op.execute("CREATE TYPE gender AS ENUM ('male', 'female', 'unisex')")

    # Add default_gender column to categories table
    op.add_column(
        'categories',
        sa.Column(
            'default_gender',
            sa.Enum('male', 'female', 'unisex', name='gender'),
            nullable=False,
            server_default='unisex',
            comment="Genre par défaut (male, female, unisex)"
        ),
        schema='public'
    )


def downgrade() -> None:
    # Remove default_gender column
    op.drop_column('categories', 'default_gender', schema='public')

    # Drop gender ENUM type
    op.execute("DROP TYPE gender")
