"""Drop vinted columns from users table

Revision ID: 20251217_1105
Revises: 20251217_1100
Create Date: 2025-12-17 11:05:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = '20251217_1105'
down_revision = '20251217_1100'
branch_labels = None
depends_on = None


def upgrade():
    """
    Drop vinted_user_id, vinted_username, vinted_cookies from public.users.

    Business Rules:
    - VintedConnection is now the single source of truth for Vinted connection state
    - These columns are redundant and have been migrated to VintedConnection
    - Data loss is acceptable as VintedConnection already contains all needed info
    """
    conn = op.get_bind()

    # Check if columns exist before dropping
    columns_to_drop = ['vinted_user_id', 'vinted_username', 'vinted_cookies']

    for column in columns_to_drop:
        column_exists = conn.execute(text(f"""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = 'users'
                AND column_name = '{column}'
            )
        """)).scalar()

        if column_exists:
            print(f"Dropping public.users.{column}")
            conn.execute(text(f"""
                ALTER TABLE public.users DROP COLUMN {column}
            """))
        else:
            print(f"Column public.users.{column} doesn't exist, skipping")


def downgrade():
    """
    Re-add vinted columns to public.users.

    Note: Data cannot be restored from this migration alone.
    Manual intervention needed to repopulate from VintedConnection if required.
    """
    conn = op.get_bind()

    # Add columns back (without data)
    columns_to_add = [
        ('vinted_user_id', 'INTEGER'),
        ('vinted_username', 'VARCHAR(255)'),
        ('vinted_cookies', 'TEXT'),
    ]

    for column_name, column_type in columns_to_add:
        column_exists = conn.execute(text(f"""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = 'users'
                AND column_name = '{column_name}'
            )
        """)).scalar()

        if not column_exists:
            print(f"Re-adding public.users.{column_name}")
            conn.execute(text(f"""
                ALTER TABLE public.users ADD COLUMN {column_name} {column_type}
            """))
