"""rename vinted_jobs to marketplace_jobs

Revision ID: 00021459a310
Revises: 9237e30dd08b
Create Date: 2026-01-07 09:26:17.397009+01:00

"""
from typing import Sequence, Union


from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

from logging import getLogger

logger = getLogger(__name__)


# revision identifiers, used by Alembic.
revision: str = '00021459a310'
down_revision: Union[str, None] = '9237e30dd08b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Rename vinted_jobs to marketplace_jobs and add marketplace columns.
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

    # Also include template_tenant
    all_schemas = ['template_tenant'] + user_schemas

    for schema in all_schemas:
        # Check if vinted_jobs table exists
        table_exists = conn.execute(text(f"""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = '{schema}'
                AND table_name = 'vinted_jobs'
            )
        """)).scalar()

        if not table_exists:
            logger.info(f"⚠ Skipping {schema} - vinted_jobs table not found")
            continue

        # 1. Rename table
        conn.execute(text(f"""
            ALTER TABLE {schema}.vinted_jobs RENAME TO marketplace_jobs;
        """))

        # 2. Add marketplace column (default 'vinted' for existing rows)
        conn.execute(text(f"""
            ALTER TABLE {schema}.marketplace_jobs
            ADD COLUMN IF NOT EXISTS marketplace VARCHAR(50) DEFAULT 'vinted' NOT NULL;
        """))

        # 3. Add batch_job_id column (FK to batch_jobs)
        conn.execute(text(f"""
            ALTER TABLE {schema}.marketplace_jobs
            ADD COLUMN IF NOT EXISTS batch_job_id INTEGER;
        """))

        # 4. Add FK constraint to batch_jobs
        conn.execute(text(f"""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint
                    WHERE conname = 'fk_marketplace_jobs_batch_job'
                    AND connamespace = '{schema}'::regnamespace
                ) THEN
                    ALTER TABLE {schema}.marketplace_jobs
                    ADD CONSTRAINT fk_marketplace_jobs_batch_job
                    FOREIGN KEY (batch_job_id) REFERENCES {schema}.batch_jobs(id) ON DELETE SET NULL;
                END IF;
            END$$;
        """))

        # 5. Create index on marketplace and batch_job_id
        conn.execute(text(f"""
            CREATE INDEX IF NOT EXISTS idx_marketplace_jobs_marketplace ON {schema}.marketplace_jobs(marketplace);
            CREATE INDEX IF NOT EXISTS idx_marketplace_jobs_batch_job_id ON {schema}.marketplace_jobs(batch_job_id);
        """))

        # 6. Update FK in marketplace_tasks from vinted_jobs to marketplace_jobs
        conn.execute(text(f"""
            DO $$
            BEGIN
                -- Drop old FK constraint if exists
                IF EXISTS (
                    SELECT 1 FROM pg_constraint
                    WHERE conname LIKE '%vinted_jobs%'
                    AND connamespace = '{schema}'::regnamespace
                    AND conrelid = '{schema}.marketplace_tasks'::regclass
                ) THEN
                    ALTER TABLE {schema}.marketplace_tasks
                    DROP CONSTRAINT IF EXISTS marketplace_tasks_job_id_fkey;

                    ALTER TABLE {schema}.marketplace_tasks
                    DROP CONSTRAINT IF EXISTS plugin_tasks_job_id_fkey;
                END IF;

                -- Add new FK constraint
                ALTER TABLE {schema}.marketplace_tasks
                ADD CONSTRAINT fk_marketplace_tasks_job
                FOREIGN KEY (job_id) REFERENCES {schema}.marketplace_jobs(id) ON DELETE SET NULL;
            END$$;
        """))

        # 7. Rename indexes
        conn.execute(text(f"""
            DO $$
            DECLARE
                idx_name text;
            BEGIN
                FOR idx_name IN
                    SELECT indexname
                    FROM pg_indexes
                    WHERE schemaname = '{schema}'
                    AND tablename = 'marketplace_jobs'
                    AND indexname LIKE '%vinted_jobs%'
                LOOP
                    EXECUTE 'ALTER INDEX {schema}.' || idx_name || ' RENAME TO ' ||
                            replace(idx_name, 'vinted_jobs', 'marketplace_jobs');
                END LOOP;
            END$$;
        """))

        # 8. Rename remaining constraints
        conn.execute(text(f"""
            DO $$
            DECLARE
                const_name text;
                new_name text;
            BEGIN
                FOR const_name IN
                    SELECT conname
                    FROM pg_constraint
                    WHERE connamespace = '{schema}'::regnamespace
                    AND conrelid = '{schema}.marketplace_jobs'::regclass
                    AND conname LIKE '%vinted_jobs%'
                LOOP
                    new_name := replace(const_name, 'vinted_jobs', 'marketplace_jobs');
                    EXECUTE 'ALTER TABLE {schema}.marketplace_jobs RENAME CONSTRAINT ' ||
                            const_name || ' TO ' || new_name;
                END LOOP;
            END$$;
        """))

        logger.info(f"✓ Renamed vinted_jobs → marketplace_jobs in {schema}")


def downgrade() -> None:
    """
    Revert marketplace_jobs back to vinted_jobs.
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

    # Also include template_tenant
    all_schemas = ['template_tenant'] + user_schemas

    for schema in all_schemas:
        # Check if marketplace_jobs table exists
        table_exists = conn.execute(text(f"""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = '{schema}'
                AND table_name = 'marketplace_jobs'
            )
        """)).scalar()

        if not table_exists:
            logger.info(f"⚠ Skipping {schema} - marketplace_jobs table not found")
            continue

        # 1. Drop new columns
        conn.execute(text(f"""
            ALTER TABLE {schema}.marketplace_jobs
            DROP COLUMN IF EXISTS marketplace CASCADE;
        """))

        conn.execute(text(f"""
            ALTER TABLE {schema}.marketplace_jobs
            DROP COLUMN IF EXISTS batch_job_id CASCADE;
        """))

        # 2. Rename table back
        conn.execute(text(f"""
            ALTER TABLE {schema}.marketplace_jobs RENAME TO vinted_jobs;
        """))

        # 3. Restore FK in marketplace_tasks
        conn.execute(text(f"""
            DO $$
            BEGIN
                ALTER TABLE {schema}.marketplace_tasks
                DROP CONSTRAINT IF EXISTS fk_marketplace_tasks_job;

                ALTER TABLE {schema}.marketplace_tasks
                ADD CONSTRAINT plugin_tasks_job_id_fkey
                FOREIGN KEY (job_id) REFERENCES {schema}.vinted_jobs(id) ON DELETE SET NULL;
            END$$;
        """))

        # 4. Rename indexes back
        conn.execute(text(f"""
            DO $$
            DECLARE
                idx_name text;
            BEGIN
                FOR idx_name IN
                    SELECT indexname
                    FROM pg_indexes
                    WHERE schemaname = '{schema}'
                    AND tablename = 'vinted_jobs'
                    AND indexname LIKE '%marketplace_jobs%'
                LOOP
                    EXECUTE 'ALTER INDEX {schema}.' || idx_name || ' RENAME TO ' ||
                            replace(idx_name, 'marketplace_jobs', 'vinted_jobs');
                END LOOP;
            END$$;
        """))

        # 5. Rename constraints back
        conn.execute(text(f"""
            DO $$
            DECLARE
                const_name text;
                new_name text;
            BEGIN
                FOR const_name IN
                    SELECT conname
                    FROM pg_constraint
                    WHERE connamespace = '{schema}'::regnamespace
                    AND conrelid = '{schema}.vinted_jobs'::regclass
                    AND conname LIKE '%marketplace_jobs%'
                LOOP
                    new_name := replace(const_name, 'marketplace_jobs', 'vinted_jobs');
                    EXECUTE 'ALTER TABLE {schema}.vinted_jobs RENAME CONSTRAINT ' ||
                            const_name || ' TO ' || new_name;
                END LOOP;
            END$$;
        """))

        logger.info(f"✓ Reverted marketplace_jobs → vinted_jobs in {schema}")
