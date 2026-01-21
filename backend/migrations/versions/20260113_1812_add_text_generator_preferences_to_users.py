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
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '3796a01d0b82'
down_revision: Union[str, None] = '5533a6a37c28'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def column_exists(conn, schema: str, table: str, column: str) -> bool:
    """Check if a column exists in a table."""
    result = conn.execute(
        text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = :schema
                  AND table_name = :table
                  AND column_name = :column
            )
        """),
        {"schema": schema, "table": table, "column": column}
    )
    return result.scalar()


def constraint_exists(conn, schema: str, constraint_name: str) -> bool:
    """Check if a constraint exists."""
    result = conn.execute(
        text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.table_constraints
                WHERE constraint_schema = :schema
                  AND constraint_name = :constraint_name
            )
        """),
        {"schema": schema, "constraint_name": constraint_name}
    )
    return result.scalar()


def upgrade() -> None:
    conn = op.get_bind()

    # Add default_title_format column if not exists
    if not column_exists(conn, 'public', 'users', 'default_title_format'):
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

    # Add default_description_style column if not exists
    if not column_exists(conn, 'public', 'users', 'default_description_style'):
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

    # Add CHECK constraints for valid values (1-3 or NULL) if not exists
    if not constraint_exists(conn, 'public', 'ck_users_default_title_format_valid'):
        op.create_check_constraint(
            'ck_users_default_title_format_valid',
            'users',
            'default_title_format IS NULL OR (default_title_format >= 1 AND default_title_format <= 3)',
            schema='public'
        )

    if not constraint_exists(conn, 'public', 'ck_users_default_description_style_valid'):
        op.create_check_constraint(
            'ck_users_default_description_style_valid',
            'users',
            'default_description_style IS NULL OR (default_description_style >= 1 AND default_description_style <= 3)',
            schema='public'
        )


def downgrade() -> None:
    # Drop CHECK constraints first (ignore if not exists)
    try:
        op.drop_constraint('ck_users_default_description_style_valid', 'users', schema='public')
    except Exception:
        pass
    try:
        op.drop_constraint('ck_users_default_title_format_valid', 'users', schema='public')
    except Exception:
        pass

    # Drop columns (ignore if not exists)
    try:
        op.drop_column('users', 'default_description_style', schema='public')
    except Exception:
        pass
    try:
        op.drop_column('users', 'default_title_format', schema='public')
    except Exception:
        pass
