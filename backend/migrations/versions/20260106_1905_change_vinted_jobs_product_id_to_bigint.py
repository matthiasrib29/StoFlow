"""change vinted_jobs product_id to bigint

Revision ID: 8650bc4ed14d
Revises: 7d1dc0b3f83e
Create Date: 2026-01-06 19:05:55.699675+01:00

"""
from typing import Sequence, Union


from alembic import op
from sqlalchemy import text

from logging import getLogger

logger = getLogger(__name__)


# revision identifiers, used by Alembic.
revision: str = '8650bc4ed14d'
down_revision: Union[str, None] = '7d1dc0b3f83e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Change vinted_jobs.product_id from INTEGER to BIGINT in all user schemas."""
    conn = op.get_bind()

    # Get all user schemas
    result = conn.execute(text("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%'
        AND schema_name <> 'user_invalid'
        ORDER BY schema_name
    """))
    user_schemas = [row[0] for row in result.fetchall()]

    # Also update template_tenant schema
    all_schemas = ['template_tenant'] + user_schemas

    for schema in all_schemas:
        # Check if vinted_jobs table exists in this schema
        table_exists = conn.execute(text(f"""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = '{schema}'
                AND table_name = 'vinted_jobs'
            )
        """)).scalar()

        if table_exists:
            # Alter column type to BIGINT
            conn.execute(text(f"""
                ALTER TABLE {schema}.vinted_jobs
                ALTER COLUMN product_id TYPE BIGINT;
            """))
            logger.info(f"✓ Updated {schema}.vinted_jobs.product_id to BIGINT")


def downgrade() -> None:
    """Revert vinted_jobs.product_id from BIGINT to INTEGER in all user schemas."""
    conn = op.get_bind()

    # Get all user schemas
    result = conn.execute(text("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%'
        AND schema_name <> 'user_invalid'
        ORDER BY schema_name
    """))
    user_schemas = [row[0] for row in result.fetchall()]

    # Also update template_tenant schema
    all_schemas = ['template_tenant'] + user_schemas

    for schema in all_schemas:
        # Check if vinted_jobs table exists in this schema
        table_exists = conn.execute(text(f"""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = '{schema}'
                AND table_name = 'vinted_jobs'
            )
        """)).scalar()

        if table_exists:
            # Alter column type back to INTEGER
            # WARNING: This may fail if values exceed INTEGER max (2147483647)
            conn.execute(text(f"""
                ALTER TABLE {schema}.vinted_jobs
                ALTER COLUMN product_id TYPE INTEGER;
            """))
            logger.info(f"✓ Reverted {schema}.vinted_jobs.product_id to INTEGER")
