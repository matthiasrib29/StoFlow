"""add_usage_counters_and_security_fields_to_users

Revision ID: 9ce74bed2321
Revises: 303159a94619
Create Date: 2026-01-07 11:01:02.599710+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9ce74bed2321'
down_revision: Union[str, None] = '83c5d2952134'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add usage counters and security fields to users table."""
    conn = op.get_bind()

    # Helper to check if column exists
    def column_exists(table: str, column: str, schema: str = 'public') -> bool:
        result = conn.execute(sa.text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = :schema AND table_name = :table AND column_name = :column
            )
        """), {"schema": schema, "table": table, "column": column})
        return result.scalar()

    # Add usage counter columns (if not exist)
    if not column_exists('users', 'current_products_count'):
        op.add_column(
            'users',
            sa.Column('current_products_count', sa.Integer(), nullable=False, server_default='0',
                      comment='Nombre actuel de produits actifs de l\'utilisateur'),
            schema='public'
        )

    if not column_exists('users', 'current_platforms_count'):
        op.add_column(
            'users',
            sa.Column('current_platforms_count', sa.Integer(), nullable=False, server_default='0',
                      comment='Nombre actuel de plateformes connectées'),
            schema='public'
        )

    # Add security tracking columns (if not exist)
    if not column_exists('users', 'last_failed_login'):
        op.add_column(
            'users',
            sa.Column('last_failed_login', sa.DateTime(timezone=True), nullable=True,
                      comment='Date de la dernière tentative de connexion échouée'),
            schema='public'
        )

    if not column_exists('users', 'password_changed_at'):
        op.add_column(
            'users',
            sa.Column('password_changed_at', sa.DateTime(timezone=True), nullable=True,
                      comment='Date du dernier changement de mot de passe'),
            schema='public'
        )

    # Rename email verification column (if old name exists)
    if column_exists('users', 'email_verification_sent_at') and not column_exists('users', 'email_verification_expires'):
        op.alter_column(
            'users',
            'email_verification_sent_at',
            new_column_name='email_verification_expires',
            schema='public'
        )


def downgrade() -> None:
    """Remove usage counters and security fields from users table."""
    # Restore original column name
    op.alter_column(
        'users',
        'email_verification_expires',
        new_column_name='email_verification_sent_at',
        schema='public'
    )

    # Drop security columns
    op.drop_column('users', 'password_changed_at', schema='public')
    op.drop_column('users', 'last_failed_login', schema='public')

    # Drop usage counter columns
    op.drop_column('users', 'current_platforms_count', schema='public')
    op.drop_column('users', 'current_products_count', schema='public')
