"""Create admin_audit_logs table for tracking admin actions

Revision ID: 20251224_3000
Revises: 20251224_2900
Create Date: 2025-12-24 15:00:00.000000

Admin Audit Logging System:
- Tracks all admin actions (CREATE, UPDATE, DELETE, TOGGLE, UNLOCK)
- Records resource type, ID, and name
- Stores changed fields and before/after values in JSON
- Captures IP address for security auditing
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '20251224_3000'
down_revision = '20251224_2900'
branch_labels = None
depends_on = None


def table_exists(conn, schema, table):
    """Check if a table exists."""
    result = conn.execute(text(f"""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = '{schema}'
            AND table_name = '{table}'
        )
    """))
    return result.scalar()


def index_exists(conn, schema, index_name):
    """Check if an index exists."""
    result = conn.execute(text(f"""
        SELECT EXISTS (
            SELECT FROM pg_indexes
            WHERE schemaname = '{schema}'
            AND indexname = '{index_name}'
        )
    """))
    return result.scalar()


def upgrade():
    """
    Create admin_audit_logs table in public schema.

    This table tracks all admin actions for auditing purposes:
    - Who performed the action (admin_id)
    - What action was performed (action)
    - On which resource (resource_type, resource_id, resource_name)
    - What changed (details JSON)
    - When and from where (created_at, ip_address)
    """
    conn = op.get_bind()

    if table_exists(conn, 'public', 'admin_audit_logs'):
        print("  ⏭️  Table admin_audit_logs already exists, skipping")
        return

    op.create_table(
        'admin_audit_logs',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('admin_id', sa.Integer(), sa.ForeignKey('public.users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('action', sa.String(50), nullable=False, comment='Action type: CREATE, UPDATE, DELETE, TOGGLE_ACTIVE, UNLOCK'),
        sa.Column('resource_type', sa.String(50), nullable=False, comment='Resource type: user, brand, category, color, material'),
        sa.Column('resource_id', sa.String(100), nullable=True, comment='Primary key of the affected resource'),
        sa.Column('resource_name', sa.String(255), nullable=True, comment='Human-readable name of the resource'),
        sa.Column('details', postgresql.JSON(), nullable=True, comment='Changed fields, before/after values'),
        sa.Column('ip_address', sa.String(45), nullable=True, comment='IP address of the admin'),
        sa.Column('user_agent', sa.String(500), nullable=True, comment='User agent of the admin browser'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema='public'
    )
    print("  ✓ Created table admin_audit_logs")

    # Create indexes for efficient filtering
    indexes = [
        ('ix_audit_admin_id', 'admin_audit_logs', ['admin_id']),
        ('ix_audit_action', 'admin_audit_logs', ['action']),
        ('ix_audit_resource_type', 'admin_audit_logs', ['resource_type']),
        ('ix_audit_created_at', 'admin_audit_logs', ['created_at']),
    ]

    for idx_name, table_name, columns in indexes:
        if not index_exists(conn, 'public', idx_name):
            op.create_index(idx_name, table_name, columns, schema='public')
            print(f"  ✓ Created index {idx_name}")
        else:
            print(f"  ⏭️  Index {idx_name} already exists, skipping")

    print("\n=== Admin audit logs table created ===")


def downgrade():
    """Remove admin_audit_logs table."""
    # Drop indexes first
    op.drop_index('ix_audit_created_at', table_name='admin_audit_logs', schema='public')
    op.drop_index('ix_audit_resource_type', table_name='admin_audit_logs', schema='public')
    op.drop_index('ix_audit_action', table_name='admin_audit_logs', schema='public')
    op.drop_index('ix_audit_admin_id', table_name='admin_audit_logs', schema='public')

    # Drop table
    op.drop_table('admin_audit_logs', schema='public')

    print("Removed admin_audit_logs table")
