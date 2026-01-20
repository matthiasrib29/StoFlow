"""Add LISTEN/NOTIFY trigger for marketplace jobs

Revision ID: 3a8b9c0d1e2f
Revises: ed768f72d538
Create Date: 2026-01-20 20:35:00

This migration adds a PostgreSQL trigger that sends NOTIFY events
when marketplace jobs are created or updated to PENDING status.

The worker uses LISTEN to receive instant notifications instead of polling.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '3a8b9c0d1e2f'
down_revision = 'ed768f72d538'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create NOTIFY trigger for marketplace jobs.

    The trigger fires on:
    - INSERT (new job created)
    - UPDATE when status changes to 'pending' (job reset for retry)

    Notification payload contains:
    - job_id: Job ID
    - marketplace: Target marketplace (ebay, etsy, vinted)
    - action_type_id: Action type for routing
    - priority: Job priority (1=CRITICAL to 4=LOW)
    - schema: Tenant schema name
    """
    # Create the notify function in public schema
    op.execute("""
        CREATE OR REPLACE FUNCTION public.notify_marketplace_job()
        RETURNS TRIGGER AS $$
        BEGIN
            -- Only notify on INSERT or status change to PENDING
            IF (TG_OP = 'INSERT') OR
               (TG_OP = 'UPDATE' AND NEW.status = 'pending' AND OLD.status != 'pending') THEN
                PERFORM pg_notify(
                    'marketplace_job',
                    json_build_object(
                        'job_id', NEW.id,
                        'marketplace', NEW.marketplace,
                        'action_type_id', NEW.action_type_id,
                        'priority', NEW.priority,
                        'schema', current_schema()
                    )::text
                );
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Create helper function to add trigger to a schema
    # This will be called for each user schema
    op.execute("""
        CREATE OR REPLACE FUNCTION public.create_marketplace_job_trigger(schema_name text)
        RETURNS void AS $$
        BEGIN
            EXECUTE format(
                'CREATE TRIGGER IF NOT EXISTS trg_marketplace_job_notify
                    AFTER INSERT OR UPDATE ON %I.marketplace_jobs
                    FOR EACH ROW
                    EXECUTE FUNCTION public.notify_marketplace_job()',
                schema_name
            );
        EXCEPTION
            WHEN duplicate_object THEN
                -- Trigger already exists, ignore
                NULL;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Add triggers to all existing user schemas
    op.execute("""
        DO $$
        DECLARE
            schema_rec RECORD;
        BEGIN
            FOR schema_rec IN
                SELECT schema_name
                FROM information_schema.schemata
                WHERE schema_name LIKE 'user_%'
            LOOP
                -- Check if marketplace_jobs table exists in this schema
                IF EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = schema_rec.schema_name
                    AND table_name = 'marketplace_jobs'
                ) THEN
                    EXECUTE format(
                        'DROP TRIGGER IF EXISTS trg_marketplace_job_notify ON %I.marketplace_jobs',
                        schema_rec.schema_name
                    );
                    EXECUTE format(
                        'CREATE TRIGGER trg_marketplace_job_notify
                            AFTER INSERT OR UPDATE ON %I.marketplace_jobs
                            FOR EACH ROW
                            EXECUTE FUNCTION public.notify_marketplace_job()',
                        schema_rec.schema_name
                    );
                    RAISE NOTICE 'Created trigger for schema: %', schema_rec.schema_name;
                END IF;
            END LOOP;
        END;
        $$;
    """)


def downgrade() -> None:
    """Remove NOTIFY trigger and functions."""
    # Remove triggers from all user schemas
    op.execute("""
        DO $$
        DECLARE
            schema_rec RECORD;
        BEGIN
            FOR schema_rec IN
                SELECT schema_name
                FROM information_schema.schemata
                WHERE schema_name LIKE 'user_%'
            LOOP
                EXECUTE format(
                    'DROP TRIGGER IF EXISTS trg_marketplace_job_notify ON %I.marketplace_jobs',
                    schema_rec.schema_name
                );
            END LOOP;
        END;
        $$;
    """)

    # Drop helper function
    op.execute("DROP FUNCTION IF EXISTS public.create_marketplace_job_trigger(text);")

    # Drop notify function
    op.execute("DROP FUNCTION IF EXISTS public.notify_marketplace_job();")
