"""encrypt oauth tokens

Revision ID: 20260112_1800
Revises:
Create Date: 2026-01-12 18:00:00.000000

Add encrypted token columns for eBay and Etsy OAuth2 tokens.
Migration strategy:
1. Add new *_encrypted columns (nullable initially)
2. Data migration script will populate encrypted columns
3. Second migration will drop plaintext columns

Author: Claude
Date: 2026-01-12
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = '20260112_1800'
down_revision = '20260109_0400'
branch_labels = None
depends_on = None


def get_user_schemas(conn):
    """Get all user_* schemas."""
    result = conn.execute(text("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%'
        ORDER BY schema_name
    """))
    return [row[0] for row in result]


def upgrade() -> None:
    """Add encrypted token columns to eBay and Etsy credentials tables."""
    conn = op.get_bind()

    # Get all user schemas
    user_schemas = get_user_schemas(conn)

    for schema in user_schemas:
        # Check if ebay_credentials table exists
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = :schema
                AND table_name = 'ebay_credentials'
            )
        """), {"schema": schema})

        if result.scalar():
            # Add encrypted columns to ebay_credentials
            op.add_column(
                'ebay_credentials',
                sa.Column('access_token_encrypted', sa.LargeBinary, nullable=True,
                         comment='Encrypted OAuth2 Access Token (expire 2h)'),
                schema=schema
            )
            op.add_column(
                'ebay_credentials',
                sa.Column('refresh_token_encrypted', sa.LargeBinary, nullable=True,
                         comment='Encrypted OAuth2 Refresh Token (expire 18 mois)'),
                schema=schema
            )

        # Check if etsy_credentials table exists
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = :schema
                AND table_name = 'etsy_credentials'
            )
        """), {"schema": schema})

        if result.scalar():
            # Add encrypted columns to etsy_credentials
            op.add_column(
                'etsy_credentials',
                sa.Column('access_token_encrypted', sa.LargeBinary, nullable=True,
                         comment='Encrypted OAuth2 Access Token (expire 1h)'),
                schema=schema
            )
            op.add_column(
                'etsy_credentials',
                sa.Column('refresh_token_encrypted', sa.LargeBinary, nullable=True,
                         comment='Encrypted OAuth2 Refresh Token (expire 90 jours)'),
                schema=schema
            )


def downgrade() -> None:
    """Remove encrypted token columns."""
    conn = op.get_bind()

    # Get all user schemas
    user_schemas = get_user_schemas(conn)

    for schema in user_schemas:
        # Drop eBay encrypted columns
        try:
            op.drop_column('ebay_credentials', 'access_token_encrypted', schema=schema)
            op.drop_column('ebay_credentials', 'refresh_token_encrypted', schema=schema)
        except Exception:
            pass  # Table may not exist

        # Drop Etsy encrypted columns
        try:
            op.drop_column('etsy_credentials', 'access_token_encrypted', schema=schema)
            op.drop_column('etsy_credentials', 'refresh_token_encrypted', schema=schema)
        except Exception:
            pass  # Table may not exist
