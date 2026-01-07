"""create batch_jobs table

Revision ID: 384aeec75884
Revises: 8650bc4ed14d
Create Date: 2026-01-07 09:20:17.524514+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '384aeec75884'
down_revision: Union[str, None] = '8650bc4ed14d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create batch_jobs table in all user schemas + template_tenant."""
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

    # Also include template_tenant
    all_schemas = ['template_tenant'] + user_schemas

    # Create enum type for batch_job_status
    batch_job_status_enum = postgresql.ENUM(
        'pending', 'running', 'completed', 'partially_failed', 'failed', 'cancelled',
        name='batch_job_status',
        create_type=False
    )

    for schema in all_schemas:
        # Create enum if not exists (in each schema)
        conn.execute(text(f"""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'batch_job_status' AND typnamespace = '{schema}'::regnamespace) THEN
                    CREATE TYPE {schema}.batch_job_status AS ENUM (
                        'pending', 'running', 'completed', 'partially_failed', 'failed', 'cancelled'
                    );
                END IF;
            END$$;
        """))

        # Create table
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS {schema}.batch_jobs (
                id SERIAL PRIMARY KEY,
                batch_id VARCHAR(100) NOT NULL UNIQUE,
                marketplace VARCHAR(50) NOT NULL,
                action_code VARCHAR(50) NOT NULL,
                total_count INTEGER NOT NULL DEFAULT 0,
                completed_count INTEGER NOT NULL DEFAULT 0,
                failed_count INTEGER NOT NULL DEFAULT 0,
                cancelled_count INTEGER NOT NULL DEFAULT 0,
                status {schema}.batch_job_status NOT NULL DEFAULT 'pending',
                priority INTEGER NOT NULL DEFAULT 3,
                created_by_user_id INTEGER,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                started_at TIMESTAMP WITH TIME ZONE,
                completed_at TIMESTAMP WITH TIME ZONE,

                CONSTRAINT fk_batch_jobs_user FOREIGN KEY (created_by_user_id)
                    REFERENCES public.users(id) ON DELETE SET NULL
            );
        """))

        # Create indexes
        conn.execute(text(f"""
            CREATE INDEX IF NOT EXISTS idx_batch_jobs_batch_id ON {schema}.batch_jobs(batch_id);
            CREATE INDEX IF NOT EXISTS idx_batch_jobs_marketplace ON {schema}.batch_jobs(marketplace, status);
            CREATE INDEX IF NOT EXISTS idx_batch_jobs_status ON {schema}.batch_jobs(status, created_at);
            CREATE INDEX IF NOT EXISTS idx_batch_jobs_created_at ON {schema}.batch_jobs(created_at);
        """))

        # Add comment
        conn.execute(text(f"""
            COMMENT ON TABLE {schema}.batch_jobs IS 'Groups multiple marketplace jobs into a single batch operation';
        """))

        print(f"✓ Created batch_jobs table in {schema}")


def downgrade() -> None:
    """Drop batch_jobs table from all user schemas + template_tenant."""
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

    # Also include template_tenant
    all_schemas = ['template_tenant'] + user_schemas

    for schema in all_schemas:
        # Drop table
        conn.execute(text(f"""
            DROP TABLE IF EXISTS {schema}.batch_jobs CASCADE;
        """))

        # Drop enum type
        conn.execute(text(f"""
            DROP TYPE IF EXISTS {schema}.batch_job_status;
        """))

        print(f"✓ Dropped batch_jobs table from {schema}")
