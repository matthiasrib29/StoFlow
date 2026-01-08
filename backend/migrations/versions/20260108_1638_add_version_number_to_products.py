"""add_version_number_to_products

Revision ID: c8fad3791ba7
Revises: de2abccc91f9
Create Date: 2026-01-08 16:38:34.233277+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'c8fad3791ba7'
down_revision: Union[str, None] = 'de2abccc91f9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add version_number column to all user schema products tables."""
    conn = op.get_bind()

    # Get all user schemas
    result = conn.execute(text("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%'
    """))

    user_schemas = [row[0] for row in result]

    for schema in user_schemas:
        # Check if products table exists
        table_exists = conn.execute(text(f"""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = :schema AND table_name = 'products'
            )
        """), {"schema": schema}).scalar()

        if table_exists:
            # Add version_number with default 1
            conn.execute(text(f"""
                ALTER TABLE {schema}.products
                ADD COLUMN IF NOT EXISTS version_number INTEGER NOT NULL DEFAULT 1
            """))

    # Also template_tenant
    conn.execute(text("""
        ALTER TABLE template_tenant.products
        ADD COLUMN IF NOT EXISTS version_number INTEGER NOT NULL DEFAULT 1
    """))


def downgrade() -> None:
    """Remove version_number column."""
    conn = op.get_bind()

    result = conn.execute(text("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%'
    """))

    user_schemas = [row[0] for row in result]

    for schema in user_schemas:
        conn.execute(text(f"""
            ALTER TABLE {schema}.products
            DROP COLUMN IF EXISTS version_number
        """))

    conn.execute(text("""
        ALTER TABLE template_tenant.products
        DROP COLUMN IF EXISTS version_number
    """))
