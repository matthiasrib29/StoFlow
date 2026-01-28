"""drop marketplace_jobs system tables

Revision ID: 8f711fbef16d
Revises: 31179c7ddf09
Create Date: 2026-01-27 19:12:55.885800+01:00

Drops the entire MarketplaceJob system (replaced by Temporal workflows):
- marketplace_tasks (user schemas)
- marketplace_jobs (user schemas)
- marketplace_batches (user schemas)
- marketplace_action_types (public schema)
- notify_marketplace_job() function and trigger
- create_marketplace_job_trigger() helper function
- Associated enum types

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '8f711fbef16d'
down_revision: Union[str, None] = '31179c7ddf09'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Tables to drop in FK-safe order (tasks references jobs, jobs references batches)
TENANT_TABLES = [
    'marketplace_task_stats',  # No FK dependencies
    'marketplace_tasks',       # References marketplace_jobs
    'marketplace_jobs',        # References marketplace_batches
    'marketplace_batches',     # Referenced by marketplace_jobs
]


def _get_tenant_schemas(conn) -> list[str]:
    """Get all user_X schemas + template_tenant."""
    result = conn.execute(text("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%'
           OR schema_name = 'template_tenant'
        ORDER BY schema_name
    """))
    return [row[0] for row in result.fetchall()]


def _table_exists(conn, schema: str, table: str) -> bool:
    """Check if a table exists in a given schema."""
    result = conn.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = :schema AND table_name = :table
        )
    """), {"schema": schema, "table": table})
    return result.scalar()


def upgrade() -> None:
    conn = op.get_bind()
    schemas = _get_tenant_schemas(conn)

    # 1. Drop triggers from all tenant schemas
    for schema in schemas:
        if _table_exists(conn, schema, 'marketplace_jobs'):
            conn.execute(text(f"""
                DROP TRIGGER IF EXISTS trg_marketplace_job_notify
                ON {schema}.marketplace_jobs
            """))

    # 2. Drop PostgreSQL functions
    conn.execute(text(
        "DROP FUNCTION IF EXISTS public.create_marketplace_job_trigger(text)"
    ))
    conn.execute(text(
        "DROP FUNCTION IF EXISTS public.notify_marketplace_job()"
    ))

    # 3. Drop tenant tables in FK-safe order
    for schema in schemas:
        for table in TENANT_TABLES:
            if _table_exists(conn, schema, table):
                conn.execute(text(f"DROP TABLE {schema}.{table} CASCADE"))

    # 4. Drop public table
    if _table_exists(conn, 'public', 'marketplace_action_types'):
        conn.execute(text("DROP TABLE public.marketplace_action_types CASCADE"))

    # 5. Drop enum types (created by SQLAlchemy)
    conn.execute(text("DROP TYPE IF EXISTS jobstatus CASCADE"))
    conn.execute(text("DROP TYPE IF EXISTS marketplacebatchstatus CASCADE"))
    conn.execute(text("DROP TYPE IF EXISTS marketplacetasktype CASCADE"))
    conn.execute(text("DROP TYPE IF EXISTS taskstatus CASCADE"))


def downgrade() -> None:
    """Recreate the MarketplaceJob system tables."""
    conn = op.get_bind()

    # 1. Recreate enum types
    conn.execute(text("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'jobstatus') THEN
                CREATE TYPE jobstatus AS ENUM (
                    'pending', 'running', 'paused', 'completed',
                    'failed', 'cancelled', 'expired'
                );
            END IF;
        END $$
    """))
    conn.execute(text("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'marketplacebatchstatus') THEN
                CREATE TYPE marketplacebatchstatus AS ENUM (
                    'pending', 'running', 'completed',
                    'partially_failed', 'failed', 'cancelled'
                );
            END IF;
        END $$
    """))
    conn.execute(text("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'marketplacetasktype') THEN
                CREATE TYPE marketplacetasktype AS ENUM (
                    'plugin_http', 'direct_http', 'db_operation', 'file_operation'
                );
            END IF;
        END $$
    """))
    conn.execute(text("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'taskstatus') THEN
                CREATE TYPE taskstatus AS ENUM (
                    'pending', 'processing', 'success',
                    'failed', 'timeout', 'cancelled'
                );
            END IF;
        END $$
    """))

    # 2. Recreate marketplace_action_types (public schema)
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS public.marketplace_action_types (
            id SERIAL PRIMARY KEY,
            marketplace VARCHAR(50) NOT NULL,
            code VARCHAR(50) NOT NULL,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            priority INTEGER NOT NULL DEFAULT 3,
            is_batch BOOLEAN NOT NULL DEFAULT FALSE,
            rate_limit_ms INTEGER NOT NULL DEFAULT 2000,
            max_retries INTEGER NOT NULL DEFAULT 3,
            timeout_seconds INTEGER NOT NULL DEFAULT 60,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (marketplace, code)
        )
    """))
    conn.execute(text("""
        CREATE INDEX IF NOT EXISTS ix_marketplace_action_types_marketplace
        ON public.marketplace_action_types (marketplace)
    """))
    conn.execute(text("""
        CREATE INDEX IF NOT EXISTS ix_marketplace_action_types_code
        ON public.marketplace_action_types (code)
    """))

    # 3. Recreate tenant tables in all schemas
    schemas = _get_tenant_schemas(conn)

    for schema in schemas:
        # marketplace_batches (referenced by marketplace_jobs)
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS {schema}.marketplace_batches (
                id SERIAL PRIMARY KEY,
                batch_id VARCHAR(100) NOT NULL UNIQUE,
                marketplace VARCHAR(50) NOT NULL,
                action_code VARCHAR(50) NOT NULL,
                total_count INTEGER NOT NULL DEFAULT 0,
                completed_count INTEGER NOT NULL DEFAULT 0,
                failed_count INTEGER NOT NULL DEFAULT 0,
                cancelled_count INTEGER NOT NULL DEFAULT 0,
                status marketplacebatchstatus NOT NULL DEFAULT 'pending',
                priority INTEGER NOT NULL DEFAULT 3,
                created_by_user_id INTEGER REFERENCES public.users(id) ON DELETE SET NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                started_at TIMESTAMPTZ,
                completed_at TIMESTAMPTZ
            )
        """))
        conn.execute(text(f"""
            CREATE INDEX IF NOT EXISTS ix_{schema}_mb_marketplace
            ON {schema}.marketplace_batches (marketplace)
        """))
        conn.execute(text(f"""
            CREATE INDEX IF NOT EXISTS ix_{schema}_mb_status
            ON {schema}.marketplace_batches (status)
        """))

        # marketplace_jobs (references marketplace_batches and marketplace_action_types)
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS {schema}.marketplace_jobs (
                id SERIAL PRIMARY KEY,
                marketplace VARCHAR(50) NOT NULL,
                marketplace_batch_id INTEGER REFERENCES {schema}.marketplace_batches(id) ON DELETE SET NULL,
                action_type_id INTEGER REFERENCES public.marketplace_action_types(id),
                product_id INTEGER REFERENCES {schema}.products(id) ON DELETE SET NULL,
                idempotency_key VARCHAR(64) UNIQUE,
                status jobstatus NOT NULL DEFAULT 'pending',
                cancel_requested BOOLEAN NOT NULL DEFAULT FALSE,
                priority INTEGER NOT NULL DEFAULT 3,
                input_data JSONB,
                result_data JSONB,
                failed_step VARCHAR(100),
                error_message TEXT,
                retry_count INTEGER NOT NULL DEFAULT 0,
                max_retries INTEGER NOT NULL DEFAULT 3,
                started_at TIMESTAMPTZ,
                completed_at TIMESTAMPTZ,
                expires_at TIMESTAMPTZ,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """))
        conn.execute(text(f"""
            CREATE INDEX IF NOT EXISTS ix_{schema}_mj_marketplace
            ON {schema}.marketplace_jobs (marketplace)
        """))
        conn.execute(text(f"""
            CREATE INDEX IF NOT EXISTS ix_{schema}_mj_status
            ON {schema}.marketplace_jobs (status)
        """))
        conn.execute(text(f"""
            CREATE INDEX IF NOT EXISTS ix_{schema}_mj_priority
            ON {schema}.marketplace_jobs (priority)
        """))
        conn.execute(text(f"""
            CREATE INDEX IF NOT EXISTS ix_{schema}_mj_processing
            ON {schema}.marketplace_jobs (marketplace, status, priority, created_at)
        """))

        # marketplace_tasks (references marketplace_jobs and products)
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS {schema}.marketplace_tasks (
                id SERIAL PRIMARY KEY,
                task_type marketplacetasktype NOT NULL,
                description VARCHAR(500),
                status taskstatus NOT NULL DEFAULT 'pending',
                payload JSON,
                result JSON,
                error_message TEXT,
                product_id INTEGER REFERENCES {schema}.products(id) ON DELETE CASCADE,
                job_id INTEGER REFERENCES {schema}.marketplace_jobs(id) ON DELETE SET NULL,
                platform VARCHAR(50),
                http_method VARCHAR(10),
                path VARCHAR(500),
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                started_at TIMESTAMPTZ,
                completed_at TIMESTAMPTZ,
                retry_count INTEGER NOT NULL DEFAULT 0
            )
        """))
        conn.execute(text(f"""
            CREATE INDEX IF NOT EXISTS ix_{schema}_mt_job_status
            ON {schema}.marketplace_tasks (job_id, status)
        """))

    # 4. Recreate notify function and triggers
    conn.execute(text("""
        CREATE OR REPLACE FUNCTION public.notify_marketplace_job()
        RETURNS TRIGGER AS $$
        BEGIN
            IF (TG_OP = 'INSERT') OR
               (TG_OP = 'UPDATE' AND NEW.status = 'pending' AND OLD.status != 'pending') THEN
                PERFORM pg_notify(
                    'marketplace_job_channel',
                    json_build_object(
                        'schema', TG_TABLE_SCHEMA,
                        'job_id', NEW.id,
                        'marketplace', NEW.marketplace,
                        'priority', NEW.priority,
                        'action_type_id', NEW.action_type_id
                    )::text
                );
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """))

    conn.execute(text("""
        CREATE OR REPLACE FUNCTION public.create_marketplace_job_trigger(schema_name text)
        RETURNS void AS $$
        BEGIN
            EXECUTE format(
                'CREATE TRIGGER trg_marketplace_job_notify
                 AFTER INSERT OR UPDATE ON %I.marketplace_jobs
                 FOR EACH ROW EXECUTE FUNCTION public.notify_marketplace_job()',
                schema_name
            );
        END;
        $$ LANGUAGE plpgsql
    """))

    # Apply trigger to all tenant schemas
    for schema in schemas:
        if _table_exists(conn, schema, 'marketplace_jobs'):
            conn.execute(text(f"""
                DROP TRIGGER IF EXISTS trg_marketplace_job_notify
                ON {schema}.marketplace_jobs
            """))
            conn.execute(text(f"""
                CREATE TRIGGER trg_marketplace_job_notify
                AFTER INSERT OR UPDATE ON {schema}.marketplace_jobs
                FOR EACH ROW EXECUTE FUNCTION public.notify_marketplace_job()
            """))
