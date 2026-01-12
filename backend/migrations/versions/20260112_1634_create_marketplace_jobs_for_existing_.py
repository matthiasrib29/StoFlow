"""create marketplace_jobs for existing user schemas

Revision ID: 94236e80c53d
Revises: 6bc865c4c841
Create Date: 2026-01-12 16:34:36.969318+01:00

This migration creates the marketplace_jobs table in existing user schemas
that don't have it yet. The table is cloned from template_tenant.marketplace_jobs.

"""
from typing import Sequence, Union
from logging import getLogger

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


logger = getLogger(__name__)

# revision identifiers, used by Alembic.
revision: str = '94236e80c53d'
down_revision: Union[str, None] = '20260112_1900'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create marketplace_jobs table in user schemas that don't have it.
    """
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

    for schema in user_schemas:
        # Check if marketplace_jobs already exists
        table_exists = conn.execute(text(f"""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = '{schema}'
                AND table_name = 'marketplace_jobs'
            )
        """)).scalar()

        if table_exists:
            logger.info(f"✓ {schema}.marketplace_jobs already exists, skipping")
            continue

        # Create table by cloning from template_tenant
        conn.execute(text(f"""
            CREATE TABLE {schema}.marketplace_jobs (
                LIKE template_tenant.marketplace_jobs INCLUDING ALL
            )
        """))

        logger.info(f"✓ Created marketplace_jobs in {schema}")


def downgrade() -> None:
    """
    Drop marketplace_jobs table from user schemas.
    This is destructive - only use if absolutely necessary.
    """
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

    for schema in user_schemas:
        # Check if marketplace_jobs exists
        table_exists = conn.execute(text(f"""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = '{schema}'
                AND table_name = 'marketplace_jobs'
            )
        """)).scalar()

        if not table_exists:
            logger.info(f"⚠ {schema}.marketplace_jobs doesn't exist, skipping")
            continue

        # Drop table
        conn.execute(text(f"""
            DROP TABLE IF EXISTS {schema}.marketplace_jobs CASCADE
        """))

        logger.info(f"✓ Dropped marketplace_jobs from {schema}")
