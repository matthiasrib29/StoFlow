"""add beta_signups table

Revision ID: a031dc90f6d0
Revises: 39282d822e9c
Create Date: 2026-01-16 09:32:01.256319+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a031dc90f6d0'
down_revision: Union[str, None] = '39282d822e9c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create beta_signups table in public schema."""
    op.create_table(
        'beta_signups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('vendor_type', sa.String(length=50), nullable=False),
        sa.Column('monthly_volume', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email', name='uq_beta_signups_email'),
        schema='public'
    )
    op.create_index(op.f('ix_public_beta_signups_id'), 'beta_signups', ['id'], unique=False, schema='public')
    op.create_index(op.f('ix_public_beta_signups_email'), 'beta_signups', ['email'], unique=True, schema='public')
    op.create_index(op.f('ix_public_beta_signups_status'), 'beta_signups', ['status'], unique=False, schema='public')


def downgrade() -> None:
    """Drop beta_signups table from public schema."""
    op.drop_index(op.f('ix_public_beta_signups_status'), table_name='beta_signups', schema='public')
    op.drop_index(op.f('ix_public_beta_signups_email'), table_name='beta_signups', schema='public')
    op.drop_index(op.f('ix_public_beta_signups_id'), table_name='beta_signups', schema='public')
    op.drop_table('beta_signups', schema='public')
