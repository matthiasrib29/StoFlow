"""add_missing_beta_signups_columns

Add missing columns to beta_signups table:
- user_id (FK to users)
- discount_applied_at
- discount_revoked_at
- discount_revoked_by
- revocation_reason

These columns are needed for discount tracking when beta users convert.

Revision ID: 20260121_1100
Revises: 3c57e3e4522b
Create Date: 2026-01-21 11:00:00.000000+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '20260121_1100'
down_revision: Union[str, None] = '3c57e3e4522b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def column_exists(conn, schema: str, table: str, column: str) -> bool:
    """Check if a column exists."""
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


def index_exists(conn, schema: str, index_name: str) -> bool:
    """Check if an index exists."""
    result = conn.execute(
        text("""
            SELECT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE schemaname = :schema AND indexname = :index_name
            )
        """),
        {"schema": schema, "index_name": index_name}
    )
    return result.scalar()


def upgrade() -> None:
    """Add missing columns to beta_signups table."""
    conn = op.get_bind()

    # Add user_id column if not exists
    if not column_exists(conn, 'public', 'beta_signups', 'user_id'):
        op.add_column(
            'beta_signups',
            sa.Column('user_id', sa.Integer(), nullable=True),
            schema='public'
        )
        # Add foreign key constraint
        op.create_foreign_key(
            'fk_beta_signups_user_id',
            'beta_signups',
            'users',
            ['user_id'],
            ['id'],
            source_schema='public',
            referent_schema='public',
            ondelete='SET NULL'
        )

    # Add index on user_id if not exists
    if not index_exists(conn, 'public', 'ix_beta_signups_user_id'):
        op.create_index(
            'ix_beta_signups_user_id',
            'beta_signups',
            ['user_id'],
            schema='public'
        )

    # Add discount_applied_at column if not exists
    if not column_exists(conn, 'public', 'beta_signups', 'discount_applied_at'):
        op.add_column(
            'beta_signups',
            sa.Column('discount_applied_at', sa.DateTime(timezone=True), nullable=True),
            schema='public'
        )

    # Add discount_revoked_at column if not exists
    if not column_exists(conn, 'public', 'beta_signups', 'discount_revoked_at'):
        op.add_column(
            'beta_signups',
            sa.Column('discount_revoked_at', sa.DateTime(timezone=True), nullable=True),
            schema='public'
        )

    # Add discount_revoked_by column if not exists
    if not column_exists(conn, 'public', 'beta_signups', 'discount_revoked_by'):
        op.add_column(
            'beta_signups',
            sa.Column('discount_revoked_by', sa.Integer(), nullable=True),
            schema='public'
        )
        # Add foreign key constraint
        op.create_foreign_key(
            'fk_beta_signups_discount_revoked_by',
            'beta_signups',
            'users',
            ['discount_revoked_by'],
            ['id'],
            source_schema='public',
            referent_schema='public',
            ondelete='SET NULL'
        )

    # Add revocation_reason column if not exists
    if not column_exists(conn, 'public', 'beta_signups', 'revocation_reason'):
        op.add_column(
            'beta_signups',
            sa.Column('revocation_reason', sa.String(500), nullable=True),
            schema='public'
        )


def downgrade() -> None:
    """Remove added columns from beta_signups table."""
    # Drop foreign keys first
    try:
        op.drop_constraint('fk_beta_signups_discount_revoked_by', 'beta_signups', schema='public', type_='foreignkey')
    except Exception:
        pass
    try:
        op.drop_constraint('fk_beta_signups_user_id', 'beta_signups', schema='public', type_='foreignkey')
    except Exception:
        pass

    # Drop index
    try:
        op.drop_index('ix_beta_signups_user_id', table_name='beta_signups', schema='public')
    except Exception:
        pass

    # Drop columns
    try:
        op.drop_column('beta_signups', 'revocation_reason', schema='public')
    except Exception:
        pass
    try:
        op.drop_column('beta_signups', 'discount_revoked_by', schema='public')
    except Exception:
        pass
    try:
        op.drop_column('beta_signups', 'discount_revoked_at', schema='public')
    except Exception:
        pass
    try:
        op.drop_column('beta_signups', 'discount_applied_at', schema='public')
    except Exception:
        pass
    try:
        op.drop_column('beta_signups', 'user_id', schema='public')
    except Exception:
        pass
