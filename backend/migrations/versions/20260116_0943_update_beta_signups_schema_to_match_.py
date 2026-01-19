"""update beta_signups schema to match model

Revision ID: 4269646f817b
Revises: ab9f17f93147
Create Date: 2026-01-16 09:43:38.204637+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4269646f817b'
down_revision: Union[str, None] = 'ab9f17f93147'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def column_exists(conn, schema, table, column):
    """Check if column exists."""
    from sqlalchemy import text
    result = conn.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = :schema AND table_name = :table AND column_name = :column
        )
    """), {"schema": schema, "table": table, "column": column})
    return result.scalar()


def index_exists(conn, schema, index_name):
    """Check if index exists."""
    from sqlalchemy import text
    result = conn.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM pg_indexes
            WHERE schemaname = :schema AND indexname = :index_name
        )
    """), {"schema": schema, "index_name": index_name})
    return result.scalar()


def upgrade() -> None:
    """Update beta_signups table to match BetaSignup model."""
    from sqlalchemy import text
    conn = op.get_bind()

    # 1. Rename first_name to name (only if first_name exists and name doesn't)
    if column_exists(conn, 'public', 'beta_signups', 'first_name'):
        if not column_exists(conn, 'public', 'beta_signups', 'name'):
            op.alter_column('beta_signups', 'first_name',
                            new_column_name='name',
                            schema='public')
            print("  ✓ Renamed first_name to name")
        else:
            print("  - Both first_name and name exist, skipping rename")
    else:
        if column_exists(conn, 'public', 'beta_signups', 'name'):
            print("  - name column already exists, skipping rename")
        else:
            # Neither exists, add name column
            op.add_column('beta_signups',
                          sa.Column('name', sa.String(100), nullable=True),
                          schema='public')
            print("  ✓ Added name column")

    # 2. Add updated_at column (idempotent)
    if not column_exists(conn, 'public', 'beta_signups', 'updated_at'):
        op.add_column('beta_signups',
                      sa.Column('updated_at', sa.DateTime(timezone=True),
                               server_default=sa.text('now()'),
                               onupdate=sa.text('now()'),
                               nullable=False),
                      schema='public')
        print("  ✓ Added updated_at column")
    else:
        print("  - updated_at column already exists, skipping")

    # 3. Create index on status (idempotent)
    if not index_exists(conn, 'public', 'ix_public_beta_signups_status'):
        op.create_index(op.f('ix_public_beta_signups_status'),
                        'beta_signups', ['status'],
                        unique=False,
                        schema='public')
        print("  ✓ Created index on status")
    else:
        print("  - Index on status already exists, skipping")

    # 4. Create unique constraint on email (might already exist)
    result = conn.execute(text("""
        SELECT constraint_name
        FROM information_schema.table_constraints
        WHERE table_schema = 'public'
          AND table_name = 'beta_signups'
          AND constraint_type = 'UNIQUE'
          AND constraint_name = 'uq_beta_signups_email'
    """))
    if not result.scalar():
        op.create_unique_constraint('uq_beta_signups_email', 'beta_signups',
                                   ['email'], schema='public')
        print("  ✓ Created unique constraint on email")
    else:
        print("  - Unique constraint on email already exists, skipping")


def downgrade() -> None:
    """Revert beta_signups table changes."""
    # Drop unique constraint
    op.drop_constraint('uq_beta_signups_email', 'beta_signups',
                      schema='public', type_='unique')

    # Drop index
    op.drop_index(op.f('ix_public_beta_signups_status'),
                  table_name='beta_signups',
                  schema='public')

    # Drop updated_at column
    op.drop_column('beta_signups', 'updated_at', schema='public')

    # Rename name back to first_name
    op.alter_column('beta_signups', 'name',
                    new_column_name='first_name',
                    schema='public')
