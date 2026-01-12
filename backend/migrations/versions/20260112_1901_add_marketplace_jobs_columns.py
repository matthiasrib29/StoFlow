"""Add missing columns to marketplace_jobs table

This migration adds the following columns to marketplace_jobs:
- max_retries: Maximum number of retries (default 3)
- input_data: JSONB for job input parameters

Applied to: template_tenant and all user_X schemas

RECOVERED from lost commit c90899b (2026-01-12)

Revision ID: 20260112_1901
Revises: 20260112_1900
Create Date: 2026-01-12

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import JSONB
import logging

# revision identifiers, used by Alembic.
revision = '20260112_1901'
down_revision = '20260112_1900'
branch_labels = None
depends_on = None

logger = logging.getLogger(__name__)


def get_all_tenant_schemas(connection) -> list:
    """Get all tenant schemas (template_tenant + user_X)."""
    result = connection.execute(text("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name = 'template_tenant'
           OR schema_name ~ '^user_[0-9]+$'
        ORDER BY schema_name
    """))
    return [row[0] for row in result]


def table_exists(connection, schema: str, table: str) -> bool:
    """Check if a table exists in a schema."""
    result = connection.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = :schema AND table_name = :table
        )
    """), {"schema": schema, "table": table})
    return result.scalar()


def column_exists(connection, schema: str, table: str, column: str) -> bool:
    """Check if a column exists in a table."""
    result = connection.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = :schema
              AND table_name = :table
              AND column_name = :column
        )
    """), {"schema": schema, "table": table, "column": column})
    return result.scalar()


def upgrade() -> None:
    """Add missing columns to marketplace_jobs in all tenant schemas."""
    connection = op.get_bind()
    schemas = get_all_tenant_schemas(connection)

    logger.info(f"Upgrading marketplace_jobs in {len(schemas)} schemas...")

    for schema in schemas:
        if not table_exists(connection, schema, 'marketplace_jobs'):
            logger.info(f"  [{schema}] marketplace_jobs does not exist, skipping")
            continue

        logger.info(f"  [{schema}] Adding missing columns to marketplace_jobs...")

        # 1. Add max_retries column if not exists
        if not column_exists(connection, schema, 'marketplace_jobs', 'max_retries'):
            connection.execute(text(f"""
                ALTER TABLE {schema}.marketplace_jobs
                ADD COLUMN max_retries INTEGER NOT NULL DEFAULT 3
            """))
            logger.info(f"    + Added 'max_retries' column")

        # 2. Add input_data column if not exists
        if not column_exists(connection, schema, 'marketplace_jobs', 'input_data'):
            connection.execute(text(f"""
                ALTER TABLE {schema}.marketplace_jobs
                ADD COLUMN input_data JSONB
            """))
            logger.info(f"    + Added 'input_data' column")

        logger.info(f"  [{schema}] Done")

    logger.info("All schemas migrated successfully")


def downgrade() -> None:
    """Remove added columns from marketplace_jobs."""
    connection = op.get_bind()
    schemas = get_all_tenant_schemas(connection)

    logger.info(f"Downgrading marketplace_jobs in {len(schemas)} schemas...")

    for schema in schemas:
        if not table_exists(connection, schema, 'marketplace_jobs'):
            continue

        logger.info(f"  [{schema}] Removing columns from marketplace_jobs...")

        # 1. Drop max_retries column
        if column_exists(connection, schema, 'marketplace_jobs', 'max_retries'):
            connection.execute(text(f"""
                ALTER TABLE {schema}.marketplace_jobs
                DROP COLUMN max_retries
            """))
            logger.info(f"    - Dropped 'max_retries' column")

        # 2. Drop input_data column
        if column_exists(connection, schema, 'marketplace_jobs', 'input_data'):
            connection.execute(text(f"""
                ALTER TABLE {schema}.marketplace_jobs
                DROP COLUMN input_data
            """))
            logger.info(f"    - Dropped 'input_data' column")

        logger.info(f"  [{schema}] Done")

    logger.info("All schemas downgraded successfully")
