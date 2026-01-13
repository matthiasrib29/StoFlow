"""add_text_generator_preferences_to_users

Add default_title_format and default_description_style columns to public.users
for storing user preferences for text generation.

Values:
- default_title_format: 1=Ultra Complete, 2=Technical, 3=Style & Trend (nullable)
- default_description_style: 1=Professional, 2=Storytelling, 3=Minimalist (nullable)

Revision ID: 3796a01d0b82
Revises: 5533a6a37c28
Create Date: 2026-01-13 18:12:06.081539+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3796a01d0b82'
down_revision: Union[str, None] = '5533a6a37c28'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add default_title_format column
    op.add_column(
        'users',
        sa.Column(
            'default_title_format',
            sa.Integer(),
            nullable=True,
            comment='Default title format: 1=Ultra Complete, 2=Technical, 3=Style & Trend'
        ),
        schema='public'
    )

    # Add default_description_style column
    op.add_column(
        'users',
        sa.Column(
            'default_description_style',
            sa.Integer(),
            nullable=True,
            comment='Default description style: 1=Professional, 2=Storytelling, 3=Minimalist'
        ),
        schema='public'
    )

    # Add CHECK constraints for valid values (1-3 or NULL)
    op.create_check_constraint(
        'ck_users_default_title_format_valid',
        'users',
        'default_title_format IS NULL OR (default_title_format >= 1 AND default_title_format <= 3)',
        schema='public'
    )

    op.create_check_constraint(
        'ck_users_default_description_style_valid',
        'users',
        'default_description_style IS NULL OR (default_description_style >= 1 AND default_description_style <= 3)',
        schema='public'
    )


def downgrade() -> None:
    # Drop CHECK constraints first
    op.drop_constraint('ck_users_default_description_style_valid', 'users', schema='public')
    op.drop_constraint('ck_users_default_title_format_valid', 'users', schema='public')

    # Drop columns
    op.drop_column('users', 'default_description_style', schema='public')
    op.drop_column('users', 'default_title_format', schema='public')
