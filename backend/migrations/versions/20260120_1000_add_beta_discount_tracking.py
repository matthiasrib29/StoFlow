"""add_beta_discount_tracking

Adds tracking fields for beta discount management:
- user_id: Link to converted user account
- discount_applied_at: When the -50% coupon was applied
- discount_revoked_at: When the discount was revoked (if applicable)
- discount_revoked_by: Admin who revoked the discount
- revocation_reason: Reason for revocation

Revision ID: 20260120_1000
Revises: 4269646f817b
Create Date: 2026-01-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260120_1000'
down_revision: Union[str, None] = 'ed768f72d538'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add beta discount tracking columns to beta_signups table."""
    from sqlalchemy import text

    conn = op.get_bind()

    # Check if columns already exist (idempotent)
    result = conn.execute(text("""
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'beta_signups'
    """))
    existing_columns = {row[0] for row in result.fetchall()}

    # Add user_id column (FK to users)
    if 'user_id' not in existing_columns:
        op.add_column(
            'beta_signups',
            sa.Column('user_id', sa.Integer(), nullable=True),
            schema='public'
        )
        # Add foreign key constraint
        op.create_foreign_key(
            'fk_beta_signups_user_id',
            'beta_signups', 'users',
            ['user_id'], ['id'],
            source_schema='public',
            referent_schema='public',
            ondelete='SET NULL'
        )
        # Add index for faster lookups
        op.create_index(
            'ix_beta_signups_user_id',
            'beta_signups',
            ['user_id'],
            schema='public'
        )

    # Add discount_applied_at column
    if 'discount_applied_at' not in existing_columns:
        op.add_column(
            'beta_signups',
            sa.Column('discount_applied_at', sa.DateTime(timezone=True), nullable=True),
            schema='public'
        )

    # Add discount_revoked_at column
    if 'discount_revoked_at' not in existing_columns:
        op.add_column(
            'beta_signups',
            sa.Column('discount_revoked_at', sa.DateTime(timezone=True), nullable=True),
            schema='public'
        )

    # Add discount_revoked_by column (FK to users - admin who revoked)
    if 'discount_revoked_by' not in existing_columns:
        op.add_column(
            'beta_signups',
            sa.Column('discount_revoked_by', sa.Integer(), nullable=True),
            schema='public'
        )
        # Add foreign key constraint
        op.create_foreign_key(
            'fk_beta_signups_revoked_by',
            'beta_signups', 'users',
            ['discount_revoked_by'], ['id'],
            source_schema='public',
            referent_schema='public',
            ondelete='SET NULL'
        )

    # Add revocation_reason column
    if 'revocation_reason' not in existing_columns:
        op.add_column(
            'beta_signups',
            sa.Column('revocation_reason', sa.String(500), nullable=True),
            schema='public'
        )

    # Add name column if missing (model uses 'name', migration had 'first_name')
    if 'name' not in existing_columns:
        op.add_column(
            'beta_signups',
            sa.Column('name', sa.String(255), nullable=True),
            schema='public'
        )
        # Copy first_name to name if first_name exists
        if 'first_name' in existing_columns:
            conn.execute(text("""
                UPDATE public.beta_signups SET name = first_name WHERE name IS NULL
            """))

    # Add updated_at column if missing
    if 'updated_at' not in existing_columns:
        op.add_column(
            'beta_signups',
            sa.Column(
                'updated_at',
                sa.DateTime(timezone=True),
                nullable=True,
                server_default=sa.text('NOW()')
            ),
            schema='public'
        )
        # Set initial value
        conn.execute(text("""
            UPDATE public.beta_signups SET updated_at = created_at WHERE updated_at IS NULL
        """))


def downgrade() -> None:
    """Remove beta discount tracking columns."""
    # Drop foreign keys first
    op.drop_constraint('fk_beta_signups_revoked_by', 'beta_signups', schema='public', type_='foreignkey')
    op.drop_constraint('fk_beta_signups_user_id', 'beta_signups', schema='public', type_='foreignkey')
    op.drop_index('ix_beta_signups_user_id', 'beta_signups', schema='public')

    # Drop columns
    op.drop_column('beta_signups', 'revocation_reason', schema='public')
    op.drop_column('beta_signups', 'discount_revoked_by', schema='public')
    op.drop_column('beta_signups', 'discount_revoked_at', schema='public')
    op.drop_column('beta_signups', 'discount_applied_at', schema='public')
    op.drop_column('beta_signups', 'user_id', schema='public')
    op.drop_column('beta_signups', 'name', schema='public')
    op.drop_column('beta_signups', 'updated_at', schema='public')
