"""add etsy_credentials table

Revision ID: be0703016e38
Revises: 83c5d2952134
Create Date: 2026-01-07 12:00:00.000000+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'be0703016e38'
down_revision: Union[str, None] = '83c5d2952134'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create etsy_credentials table in template_tenant schema."""
    # Create table in template_tenant
    op.execute("""
        CREATE TABLE IF NOT EXISTS template_tenant.etsy_credentials (
            id SERIAL PRIMARY KEY,
            access_token TEXT,
            refresh_token TEXT,
            access_token_expires_at TIMESTAMPTZ,
            refresh_token_expires_at TIMESTAMPTZ,
            shop_id VARCHAR(255),
            shop_name VARCHAR(255),
            shop_url VARCHAR(500),
            user_id_etsy VARCHAR(255),
            email VARCHAR(255),
            is_connected BOOLEAN NOT NULL DEFAULT FALSE,
            last_sync TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    # Create indexes
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_etsy_credentials_id
        ON template_tenant.etsy_credentials (id)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_etsy_credentials_shop_id
        ON template_tenant.etsy_credentials (shop_id)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_etsy_credentials_user_id_etsy
        ON template_tenant.etsy_credentials (user_id_etsy)
    """)

    # Find all existing user schemas and create the table in each
    from sqlalchemy import text

    connection = op.get_bind()
    result = connection.execute(text("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%'
    """))

    user_schemas = [row[0] for row in result]

    for schema in user_schemas:
        op.execute(f"""
            CREATE TABLE IF NOT EXISTS {schema}.etsy_credentials (
                id SERIAL PRIMARY KEY,
                access_token TEXT,
                refresh_token TEXT,
                access_token_expires_at TIMESTAMPTZ,
                refresh_token_expires_at TIMESTAMPTZ,
                shop_id VARCHAR(255),
                shop_name VARCHAR(255),
                shop_url VARCHAR(500),
                user_id_etsy VARCHAR(255),
                email VARCHAR(255),
                is_connected BOOLEAN NOT NULL DEFAULT FALSE,
                last_sync TIMESTAMPTZ,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)

        op.execute(f"""
            CREATE INDEX IF NOT EXISTS ix_etsy_credentials_id
            ON {schema}.etsy_credentials (id)
        """)
        op.execute(f"""
            CREATE INDEX IF NOT EXISTS ix_etsy_credentials_shop_id
            ON {schema}.etsy_credentials (shop_id)
        """)
        op.execute(f"""
            CREATE INDEX IF NOT EXISTS ix_etsy_credentials_user_id_etsy
            ON {schema}.etsy_credentials (user_id_etsy)
        """)


def downgrade() -> None:
    """Drop etsy_credentials table from all schemas."""
    from sqlalchemy import text

    connection = op.get_bind()

    # Drop from template_tenant
    op.execute("DROP TABLE IF EXISTS template_tenant.etsy_credentials CASCADE")

    # Find all user schemas and drop the table
    result = connection.execute(text("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%'
    """))

    user_schemas = [row[0] for row in result]

    for schema in user_schemas:
        op.execute(f"DROP TABLE IF EXISTS {schema}.etsy_credentials CASCADE")
