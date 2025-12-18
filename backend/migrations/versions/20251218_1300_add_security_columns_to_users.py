"""Add security columns to users table (failed login tracking, email verification)

Revision ID: 20251218_1300
Revises: 20251218_1200
Create Date: 2025-12-18 13:00:00.000000

Security Features Added:
- failed_login_attempts: Track consecutive failed login attempts
- last_failed_login: Timestamp of last failed attempt
- locked_until: Account lockout timestamp (after 5 failed attempts)
- email_verified: Email verification status
- email_verification_token: Token for email verification
- email_verification_expires: Token expiration timestamp
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = '20251218_1300'
down_revision = '20251218_1200'
branch_labels = None
depends_on = None


def column_exists(conn, schema, table, column):
    """Check if a column exists in a table."""
    result = conn.execute(text(f"""
        SELECT EXISTS (
            SELECT FROM information_schema.columns
            WHERE table_schema = '{schema}'
            AND table_name = '{table}'
            AND column_name = '{column}'
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
    Add security columns to public.users table.

    Business Rules (2025-12-18):
    - Failed login tracking: Block account after 5 consecutive failed attempts for 30 minutes
    - Email verification: Require email verification for certain actions
    """
    conn = op.get_bind()

    columns_to_add = [
        ('failed_login_attempts', sa.Integer(), False, '0', 'Nombre de tentatives de connexion échouées consécutives'),
        ('last_failed_login', sa.DateTime(timezone=True), True, None, 'Date de la dernière tentative de connexion échouée'),
        ('locked_until', sa.DateTime(timezone=True), True, None, "Date jusqu'à laquelle le compte est verrouillé"),
        ('email_verified', sa.Boolean(), False, 'false', "Email vérifié par l'utilisateur"),
        ('email_verification_token', sa.String(64), True, None, "Token de vérification d'email"),
        ('email_verification_expires', sa.DateTime(timezone=True), True, None, "Date d'expiration du token de vérification"),
    ]

    for col_name, col_type, nullable, default, comment in columns_to_add:
        if column_exists(conn, 'public', 'users', col_name):
            print(f"  ⏭️  Column {col_name} already exists, skipping")
        else:
            op.add_column('users', sa.Column(
                col_name,
                col_type,
                nullable=nullable,
                server_default=default,
                comment=comment
            ), schema='public')
            print(f"  ✓ Added column {col_name}")

    # Create index on locked_until for efficient lookup of locked accounts
    if not index_exists(conn, 'public', 'ix_users_locked_until'):
        op.create_index(
            'ix_users_locked_until',
            'users',
            ['locked_until'],
            schema='public',
            postgresql_where=sa.text('locked_until IS NOT NULL')
        )
        print("  ✓ Created index ix_users_locked_until")
    else:
        print("  ⏭️  Index ix_users_locked_until already exists, skipping")

    # Create index on email_verification_token for token lookup
    if not index_exists(conn, 'public', 'ix_users_email_verification_token'):
        op.create_index(
            'ix_users_email_verification_token',
            'users',
            ['email_verification_token'],
            schema='public',
            postgresql_where=sa.text('email_verification_token IS NOT NULL')
        )
        print("  ✓ Created index ix_users_email_verification_token")
    else:
        print("  ⏭️  Index ix_users_email_verification_token already exists, skipping")

    print("\n=== Security columns migration complete ===")


def downgrade():
    """Remove security columns from public.users table."""
    # Drop indexes first
    op.drop_index('ix_users_email_verification_token', table_name='users', schema='public')
    op.drop_index('ix_users_locked_until', table_name='users', schema='public')

    # Drop columns
    op.drop_column('users', 'email_verification_expires', schema='public')
    op.drop_column('users', 'email_verification_token', schema='public')
    op.drop_column('users', 'email_verified', schema='public')
    op.drop_column('users', 'locked_until', schema='public')
    op.drop_column('users', 'last_failed_login', schema='public')
    op.drop_column('users', 'failed_login_attempts', schema='public')

    print("Removed security columns from public.users")
