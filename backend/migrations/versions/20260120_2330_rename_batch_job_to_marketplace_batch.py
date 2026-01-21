"""Rename BatchJob to MarketplaceBatch

Revision ID: c56f8e2a1b90
Revises: b34194fc47d0
Create Date: 2026-01-20 23:30:00

Renames for consistency with MarketplaceJob and MarketplaceTask:
- Table: batch_jobs → marketplace_batches
- Column: marketplace_jobs.batch_job_id → marketplace_jobs.marketplace_batch_id
- Enum: batch_job_status → marketplace_batch_status
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'c56f8e2a1b90'
down_revision = 'b34194fc47d0'
branch_labels = None
depends_on = None


def get_tenant_schemas(connection) -> list:
    """Get all tenant schemas (user_X and template_tenant)."""
    result = connection.execute(
        text("""
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name LIKE 'user_%'
            OR schema_name = 'template_tenant'
        """)
    )
    return [row[0] for row in result]


def table_exists(conn, schema: str, table: str) -> bool:
    """Check if a table exists in the given schema."""
    result = conn.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = :schema AND table_name = :table
        )
    """), {"schema": schema, "table": table})
    return result.scalar()


def column_exists(conn, schema: str, table: str, column: str) -> bool:
    """Check if a column exists in the given table."""
    result = conn.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = :schema AND table_name = :table AND column_name = :column
        )
    """), {"schema": schema, "table": table, "column": column})
    return result.scalar()


def constraint_exists(conn, schema: str, constraint: str) -> bool:
    """Check if a constraint exists in the given schema."""
    result = conn.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.table_constraints
            WHERE constraint_schema = :schema AND constraint_name = :constraint
        )
    """), {"schema": schema, "constraint": constraint})
    return result.scalar()


def index_exists(conn, schema: str, index: str) -> bool:
    """Check if an index exists in the given schema."""
    result = conn.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM pg_indexes
            WHERE schemaname = :schema AND indexname = :index
        )
    """), {"schema": schema, "index": index})
    return result.scalar()


def enum_exists(conn, enum_name: str) -> bool:
    """Check if an enum type exists."""
    result = conn.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM pg_type WHERE typname = :enum_name
        )
    """), {"enum_name": enum_name})
    return result.scalar()


def upgrade() -> None:
    """
    Rename BatchJob to MarketplaceBatch:
    1. Rename enum type batch_job_status → marketplace_batch_status
    2. For each tenant schema:
       - Rename table batch_jobs → marketplace_batches
       - Rename column marketplace_jobs.batch_job_id → marketplace_batch_id
       - Update FK constraint and indexes
    """
    conn = op.get_bind()
    schemas = get_tenant_schemas(conn)

    # 1. Rename enum type (global, not per-schema)
    if enum_exists(conn, 'batch_job_status'):
        conn.execute(text("ALTER TYPE batch_job_status RENAME TO marketplace_batch_status"))

    for schema in schemas:
        batch_jobs_exists = table_exists(conn, schema, 'batch_jobs')
        marketplace_batches_exists = table_exists(conn, schema, 'marketplace_batches')

        # Case 1: Only batch_jobs exists - rename it
        if batch_jobs_exists and not marketplace_batches_exists:
            conn.execute(text(f'ALTER TABLE "{schema}".batch_jobs RENAME TO marketplace_batches'))

        # Case 2: Both tables exist (inconsistent state from model auto-creation)
        # Drop empty batch_jobs, keep marketplace_batches
        elif batch_jobs_exists and marketplace_batches_exists:
            batch_jobs_count = conn.execute(text(f'SELECT COUNT(*) FROM "{schema}".batch_jobs')).scalar()
            if batch_jobs_count == 0:
                conn.execute(text(f'DROP TABLE "{schema}".batch_jobs CASCADE'))
            else:
                # batch_jobs has data - this is unexpected, log and skip
                print(f'WARNING: {schema}.batch_jobs has {batch_jobs_count} rows - skipping table rename')

        # Case 3: Only marketplace_batches exists - already migrated (no action needed)
        # Case 4: Neither exists - nothing to do

        # 3. Rename column in marketplace_jobs (batch_job_id → marketplace_batch_id)
        if table_exists(conn, schema, 'marketplace_jobs'):
            if column_exists(conn, schema, 'marketplace_jobs', 'batch_job_id'):
                # Drop old FK constraint if exists
                if constraint_exists(conn, schema, 'marketplace_jobs_batch_job_id_fkey'):
                    conn.execute(text(f'ALTER TABLE "{schema}".marketplace_jobs DROP CONSTRAINT marketplace_jobs_batch_job_id_fkey'))

                # Drop old index if exists
                if index_exists(conn, schema, 'ix_marketplace_jobs_batch_job_id'):
                    conn.execute(text(f'DROP INDEX IF EXISTS "{schema}".ix_marketplace_jobs_batch_job_id'))

                # Rename the column
                conn.execute(text(f'ALTER TABLE "{schema}".marketplace_jobs RENAME COLUMN batch_job_id TO marketplace_batch_id'))

                # Create new FK constraint
                conn.execute(text(f'''
                    ALTER TABLE "{schema}".marketplace_jobs
                    ADD CONSTRAINT marketplace_jobs_marketplace_batch_id_fkey
                    FOREIGN KEY (marketplace_batch_id)
                    REFERENCES "{schema}".marketplace_batches(id)
                    ON DELETE SET NULL
                '''))

                # Create new index
                conn.execute(text(f'CREATE INDEX ix_marketplace_jobs_marketplace_batch_id ON "{schema}".marketplace_jobs(marketplace_batch_id)'))

        # 4. Rename indexes on marketplace_batches table
        # ix_batch_jobs_batch_id → ix_marketplace_batches_batch_id
        if index_exists(conn, schema, 'ix_batch_jobs_batch_id'):
            conn.execute(text(f'ALTER INDEX "{schema}".ix_batch_jobs_batch_id RENAME TO ix_marketplace_batches_batch_id'))

        # ix_batch_jobs_created_at → ix_marketplace_batches_created_at
        if index_exists(conn, schema, 'ix_batch_jobs_created_at'):
            conn.execute(text(f'ALTER INDEX "{schema}".ix_batch_jobs_created_at RENAME TO ix_marketplace_batches_created_at'))

        # ix_batch_jobs_marketplace → ix_marketplace_batches_marketplace
        if index_exists(conn, schema, 'ix_batch_jobs_marketplace'):
            conn.execute(text(f'ALTER INDEX "{schema}".ix_batch_jobs_marketplace RENAME TO ix_marketplace_batches_marketplace'))

        # ix_batch_jobs_action_code → ix_marketplace_batches_action_code
        if index_exists(conn, schema, 'ix_batch_jobs_action_code'):
            conn.execute(text(f'ALTER INDEX "{schema}".ix_batch_jobs_action_code RENAME TO ix_marketplace_batches_action_code'))

        # ix_batch_jobs_status → ix_marketplace_batches_status
        if index_exists(conn, schema, 'ix_batch_jobs_status'):
            conn.execute(text(f'ALTER INDEX "{schema}".ix_batch_jobs_status RENAME TO ix_marketplace_batches_status'))

        # ix_batch_jobs_priority → ix_marketplace_batches_priority
        if index_exists(conn, schema, 'ix_batch_jobs_priority'):
            conn.execute(text(f'ALTER INDEX "{schema}".ix_batch_jobs_priority RENAME TO ix_marketplace_batches_priority'))

        # Rename primary key constraint
        # batch_jobs_pkey → marketplace_batches_pkey
        if constraint_exists(conn, schema, 'batch_jobs_pkey'):
            conn.execute(text(f'ALTER TABLE "{schema}".marketplace_batches RENAME CONSTRAINT batch_jobs_pkey TO marketplace_batches_pkey'))


def downgrade() -> None:
    """
    Revert MarketplaceBatch to BatchJob:
    1. Rename enum type marketplace_batch_status → batch_job_status
    2. For each tenant schema:
       - Rename table marketplace_batches → batch_jobs
       - Rename column marketplace_jobs.marketplace_batch_id → batch_job_id
       - Update FK constraint and indexes
    """
    conn = op.get_bind()
    schemas = get_tenant_schemas(conn)

    # 1. Rename enum type back
    if enum_exists(conn, 'marketplace_batch_status'):
        conn.execute(text("ALTER TYPE marketplace_batch_status RENAME TO batch_job_status"))

    for schema in schemas:
        # Skip if marketplace_batches doesn't exist
        if not table_exists(conn, schema, 'marketplace_batches'):
            continue

        # 2. Rename column in marketplace_jobs (marketplace_batch_id → batch_job_id)
        if table_exists(conn, schema, 'marketplace_jobs'):
            if column_exists(conn, schema, 'marketplace_jobs', 'marketplace_batch_id'):
                # Drop new FK constraint if exists
                if constraint_exists(conn, schema, 'marketplace_jobs_marketplace_batch_id_fkey'):
                    conn.execute(text(f'ALTER TABLE "{schema}".marketplace_jobs DROP CONSTRAINT marketplace_jobs_marketplace_batch_id_fkey'))

                # Drop new index if exists
                if index_exists(conn, schema, 'ix_marketplace_jobs_marketplace_batch_id'):
                    conn.execute(text(f'DROP INDEX IF EXISTS "{schema}".ix_marketplace_jobs_marketplace_batch_id'))

                # Rename the column back
                conn.execute(text(f'ALTER TABLE "{schema}".marketplace_jobs RENAME COLUMN marketplace_batch_id TO batch_job_id'))

        # 3. Rename the marketplace_batches table back to batch_jobs
        conn.execute(text(f'ALTER TABLE "{schema}".marketplace_batches RENAME TO batch_jobs'))

        # 4. Recreate old FK constraint
        if table_exists(conn, schema, 'marketplace_jobs'):
            if column_exists(conn, schema, 'marketplace_jobs', 'batch_job_id'):
                conn.execute(text(f'''
                    ALTER TABLE "{schema}".marketplace_jobs
                    ADD CONSTRAINT marketplace_jobs_batch_job_id_fkey
                    FOREIGN KEY (batch_job_id)
                    REFERENCES "{schema}".batch_jobs(id)
                    ON DELETE SET NULL
                '''))

                # Recreate old index
                conn.execute(text(f'CREATE INDEX ix_marketplace_jobs_batch_job_id ON "{schema}".marketplace_jobs(batch_job_id)'))

        # 5. Rename indexes back
        if index_exists(conn, schema, 'ix_marketplace_batches_batch_id'):
            conn.execute(text(f'ALTER INDEX "{schema}".ix_marketplace_batches_batch_id RENAME TO ix_batch_jobs_batch_id'))

        if index_exists(conn, schema, 'ix_marketplace_batches_created_at'):
            conn.execute(text(f'ALTER INDEX "{schema}".ix_marketplace_batches_created_at RENAME TO ix_batch_jobs_created_at'))

        if index_exists(conn, schema, 'ix_marketplace_batches_marketplace'):
            conn.execute(text(f'ALTER INDEX "{schema}".ix_marketplace_batches_marketplace RENAME TO ix_batch_jobs_marketplace'))

        if index_exists(conn, schema, 'ix_marketplace_batches_action_code'):
            conn.execute(text(f'ALTER INDEX "{schema}".ix_marketplace_batches_action_code RENAME TO ix_batch_jobs_action_code'))

        if index_exists(conn, schema, 'ix_marketplace_batches_status'):
            conn.execute(text(f'ALTER INDEX "{schema}".ix_marketplace_batches_status RENAME TO ix_batch_jobs_status'))

        if index_exists(conn, schema, 'ix_marketplace_batches_priority'):
            conn.execute(text(f'ALTER INDEX "{schema}".ix_marketplace_batches_priority RENAME TO ix_batch_jobs_priority'))

        # Rename primary key constraint back
        if constraint_exists(conn, schema, 'marketplace_batches_pkey'):
            conn.execute(text(f'ALTER TABLE "{schema}".batch_jobs RENAME CONSTRAINT marketplace_batches_pkey TO batch_jobs_pkey'))
