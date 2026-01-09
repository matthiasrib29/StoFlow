"""Add revoked_tokens table for token revocation during logout.

Revision ID: 20260107_0001
Revises: [previous revision]
Create Date: 2026-01-07

This migration adds the revoked_tokens table to track logout/revoked tokens.
Used by JWT refresh token strategy for invalidating sessions.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260107_0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create revoked_tokens table in public schema."""
    op.create_table(
        'revoked_tokens',
        sa.Column('token_hash', sa.String(255), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('token_hash'),
        schema='public'
    )

    # Create indexes for performance
    op.create_index('idx_revoked_tokens_token_hash', 'revoked_tokens', ['token_hash'], schema='public')
    op.create_index('idx_revoked_tokens_expires_at', 'revoked_tokens', ['expires_at'], schema='public')


def downgrade() -> None:
    """Drop revoked_tokens table."""
    op.drop_index('idx_revoked_tokens_expires_at', schema='public', table_name='revoked_tokens')
    op.drop_index('idx_revoked_tokens_token_hash', schema='public', table_name='revoked_tokens')
    op.drop_table('revoked_tokens', schema='public')
