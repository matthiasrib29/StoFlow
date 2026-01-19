"""add_beta_signups_table

Revision ID: 07f059f11992
Revises: 20260115_1730
Create Date: 2026-01-15 16:26:23.196547+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '07f059f11992'
down_revision: Union[str, None] = '20260115_1730'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def table_exists(conn, schema, table):
    """Check if table exists."""
    result = conn.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = :schema AND table_name = :table
        )
    """), {"schema": schema, "table": table})
    return result.scalar()


def upgrade() -> None:
    """Create beta_signups table in public schema."""
    conn = op.get_bind()

    if table_exists(conn, 'public', 'beta_signups'):
        print("  - beta_signups table already exists, skipping")
        return

    op.create_table(
        'beta_signups',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('first_name', sa.String(100), nullable=True),
        sa.Column('vendor_type', sa.String(50), nullable=True),
        sa.Column('monthly_volume', sa.String(50), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        schema='public'
    )
    print("  ✓ Created beta_signups table")


def downgrade() -> None:
    """Drop beta_signups table."""
    op.drop_table('beta_signups', schema='public')
