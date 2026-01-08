"""add_idempotency_key_to_marketplace_jobs

Revision ID: 156564a2f2c7
Revises: c8fad3791ba7
Create Date: 2026-01-08 16:40:31.449242+01:00

Security Audit 2 - Add idempotency_key to marketplace_jobs
to prevent duplicate publications across all marketplaces (Vinted, eBay, Etsy).

"""
from typing import Sequence, Union
import logging

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


logger = logging.getLogger("alembic")

# revision identifiers, used by Alembic.
revision: str = '156564a2f2c7'
down_revision: Union[str, None] = 'c8fad3791ba7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add idempotency_key column to marketplace_jobs in all user schemas."""
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

    logger.info(f"Found {len(user_schemas)} user schemas to migrate")

    for schema in user_schemas:
        # Check if marketplace_jobs table exists in this schema
        table_exists_result = conn.execute(text(f"""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = '{schema}'
                AND table_name = 'marketplace_jobs'
            )
        """))
        table_exists = table_exists_result.scalar()

        if not table_exists:
            logger.warning(f"Schema {schema}: marketplace_jobs table not found, skipping")
            continue

        # Check if column already exists
        column_exists_result = conn.execute(text(f"""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = '{schema}'
                AND table_name = 'marketplace_jobs'
                AND column_name = 'idempotency_key'
            )
        """))
        column_exists = column_exists_result.scalar()

        if column_exists:
            logger.info(f"Schema {schema}: idempotency_key column already exists, skipping")
            continue

        logger.info(f"Schema {schema}: Adding idempotency_key column")

        # Add idempotency_key column
        conn.execute(text(f"""
            ALTER TABLE {schema}.marketplace_jobs
            ADD COLUMN idempotency_key VARCHAR(64)
        """))

        # Add comment
        conn.execute(text(f"""
            COMMENT ON COLUMN {schema}.marketplace_jobs.idempotency_key IS
            'Unique key to prevent duplicate publications (format: pub_<product_id>_<uuid>)'
        """))

        # Create unique index (with WHERE clause for partial index on non-null values)
        conn.execute(text(f"""
            CREATE UNIQUE INDEX idx_{schema.replace('user_', '')}_marketplace_jobs_idempotency_key
            ON {schema}.marketplace_jobs(idempotency_key)
            WHERE idempotency_key IS NOT NULL
        """))

        logger.info(f"Schema {schema}: ✅ Migration completed")

    # Also add to template_tenant for new users
    template_table_exists = conn.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'template_tenant'
            AND table_name = 'marketplace_jobs'
        )
    """)).scalar()

    if template_table_exists:
        logger.info("Updating template_tenant schema")

        # Check if column already exists in template
        template_column_exists = conn.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'template_tenant'
                AND table_name = 'marketplace_jobs'
                AND column_name = 'idempotency_key'
            )
        """)).scalar()

        if not template_column_exists:
            conn.execute(text("""
                ALTER TABLE template_tenant.marketplace_jobs
                ADD COLUMN idempotency_key VARCHAR(64)
            """))

            conn.execute(text("""
                COMMENT ON COLUMN template_tenant.marketplace_jobs.idempotency_key IS
                'Unique key to prevent duplicate publications (format: pub_<product_id>_<uuid>)'
            """))

            conn.execute(text("""
                CREATE UNIQUE INDEX idx_template_marketplace_jobs_idempotency_key
                ON template_tenant.marketplace_jobs(idempotency_key)
                WHERE idempotency_key IS NOT NULL
            """))

            logger.info("template_tenant: ✅ Migration completed")
        else:
            logger.info("template_tenant: idempotency_key column already exists")

    logger.info("✅ All schemas migrated successfully")


def downgrade() -> None:
    """Remove idempotency_key column from marketplace_jobs in all user schemas."""
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

    logger.info(f"Rolling back {len(user_schemas)} user schemas")

    for schema in user_schemas:
        # Check if table exists
        table_exists_result = conn.execute(text(f"""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = '{schema}'
                AND table_name = 'marketplace_jobs'
            )
        """))
        table_exists = table_exists_result.scalar()

        if not table_exists:
            continue

        # Drop index if exists
        index_exists_result = conn.execute(text(f"""
            SELECT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE schemaname = '{schema}'
                AND indexname = 'idx_{schema.replace('user_', '')}_marketplace_jobs_idempotency_key'
            )
        """))
        index_exists = index_exists_result.scalar()

        if index_exists:
            conn.execute(text(f"""
                DROP INDEX {schema}.idx_{schema.replace('user_', '')}_marketplace_jobs_idempotency_key
            """))

        # Drop column if exists
        column_exists_result = conn.execute(text(f"""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = '{schema}'
                AND table_name = 'marketplace_jobs'
                AND column_name = 'idempotency_key'
            )
        """))
        column_exists = column_exists_result.scalar()

        if column_exists:
            conn.execute(text(f"""
                ALTER TABLE {schema}.marketplace_jobs
                DROP COLUMN idempotency_key
            """))

        logger.info(f"Schema {schema}: ✅ Rollback completed")

    # Rollback template_tenant
    template_table_exists = conn.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'template_tenant'
            AND table_name = 'marketplace_jobs'
        )
    """)).scalar()

    if template_table_exists:
        # Drop index
        template_index_exists = conn.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE schemaname = 'template_tenant'
                AND indexname = 'idx_template_marketplace_jobs_idempotency_key'
            )
        """)).scalar()

        if template_index_exists:
            conn.execute(text("""
                DROP INDEX template_tenant.idx_template_marketplace_jobs_idempotency_key
            """))

        # Drop column
        template_column_exists = conn.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'template_tenant'
                AND table_name = 'marketplace_jobs'
                AND column_name = 'idempotency_key'
            )
        """)).scalar()

        if template_column_exists:
            conn.execute(text("""
                ALTER TABLE template_tenant.marketplace_jobs
                DROP COLUMN idempotency_key
            """))

        logger.info("template_tenant: ✅ Rollback completed")

    logger.info("✅ All schemas rolled back successfully")
