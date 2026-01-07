"""rename plugin_tasks to marketplace_tasks

Revision ID: 9237e30dd08b
Revises: 384aeec75884
Create Date: 2026-01-07 09:22:28.979120+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '9237e30dd08b'
down_revision: Union[str, None] = '384aeec75884'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Rename plugin_tasks to marketplace_tasks and add new columns.
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
        # Check if plugin_tasks table exists
        table_exists = conn.execute(text(f"""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = '{schema}'
                AND table_name = 'plugin_tasks'
            )
        """)).scalar()

        if not table_exists:
            print(f"⚠ Skipping {schema} - plugin_tasks table not found")
            continue

        # 1. Rename table
        conn.execute(text(f"""
            ALTER TABLE {schema}.plugin_tasks RENAME TO marketplace_tasks;
        """))

        # 2. Create task_type enum
        conn.execute(text(f"""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'marketplace_task_type' AND typnamespace = '{schema}'::regnamespace) THEN
                    CREATE TYPE {schema}.marketplace_task_type AS ENUM (
                        'plugin_http', 'direct_http', 'db_operation', 'file_operation'
                    );
                END IF;
            END$$;
        """))

        # 3. Add task_type column (default 'plugin_http' for existing rows)
        conn.execute(text(f"""
            ALTER TABLE {schema}.marketplace_tasks
            ADD COLUMN IF NOT EXISTS task_type {schema}.marketplace_task_type DEFAULT 'plugin_http' NOT NULL;
        """))

        # 4. Add description column
        conn.execute(text(f"""
            ALTER TABLE {schema}.marketplace_tasks
            ADD COLUMN IF NOT EXISTS description VARCHAR(500);
        """))

        # 5. Populate description for existing tasks based on task_type
        conn.execute(text(f"""
            UPDATE {schema}.marketplace_tasks
            SET description = CASE
                WHEN http_method IS NOT NULL AND path IS NOT NULL
                    THEN http_method || ' ' || path
                WHEN task_type IS NOT NULL
                    THEN 'Plugin task'
                ELSE 'Task'
            END
            WHERE description IS NULL;
        """))

        # 6. Rename indexes to match new table name
        conn.execute(text(f"""
            DO $$
            DECLARE
                idx_name text;
            BEGIN
                FOR idx_name IN
                    SELECT indexname
                    FROM pg_indexes
                    WHERE schemaname = '{schema}'
                    AND indexname LIKE '%plugin_tasks%'
                LOOP
                    EXECUTE 'ALTER INDEX {schema}.' || idx_name || ' RENAME TO ' ||
                            replace(idx_name, 'plugin_tasks', 'marketplace_tasks');
                END LOOP;
            END$$;
        """))

        # 7. Rename constraints to match new table name
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
                    AND conname LIKE '%plugin_tasks%'
                LOOP
                    new_name := replace(const_name, 'plugin_tasks', 'marketplace_tasks');
                    EXECUTE 'ALTER TABLE {schema}.marketplace_tasks RENAME CONSTRAINT ' ||
                            const_name || ' TO ' || new_name;
                END LOOP;
            END$$;
        """))

        print(f"✓ Renamed plugin_tasks → marketplace_tasks in {schema}")


def downgrade() -> None:
    """
    Revert marketplace_tasks back to plugin_tasks.
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
        # Check if marketplace_tasks table exists
        table_exists = conn.execute(text(f"""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = '{schema}'
                AND table_name = 'marketplace_tasks'
            )
        """)).scalar()

        if not table_exists:
            print(f"⚠ Skipping {schema} - marketplace_tasks table not found")
            continue

        # 1. Drop new columns
        conn.execute(text(f"""
            ALTER TABLE {schema}.marketplace_tasks
            DROP COLUMN IF EXISTS task_type;
        """))

        conn.execute(text(f"""
            ALTER TABLE {schema}.marketplace_tasks
            DROP COLUMN IF EXISTS description;
        """))

        # 2. Rename table back
        conn.execute(text(f"""
            ALTER TABLE {schema}.marketplace_tasks RENAME TO plugin_tasks;
        """))

        # 3. Rename indexes back
        conn.execute(text(f"""
            DO $$
            DECLARE
                idx_name text;
            BEGIN
                FOR idx_name IN
                    SELECT indexname
                    FROM pg_indexes
                    WHERE schemaname = '{schema}'
                    AND indexname LIKE '%marketplace_tasks%'
                LOOP
                    EXECUTE 'ALTER INDEX {schema}.' || idx_name || ' RENAME TO ' ||
                            replace(idx_name, 'marketplace_tasks', 'plugin_tasks');
                END LOOP;
            END$$;
        """))

        # 4. Rename constraints back
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
                    AND conname LIKE '%marketplace_tasks%'
                LOOP
                    new_name := replace(const_name, 'marketplace_tasks', 'plugin_tasks');
                    EXECUTE 'ALTER TABLE {schema}.plugin_tasks RENAME CONSTRAINT ' ||
                            const_name || ' TO ' || new_name;
                END LOOP;
            END$$;
        """))

        # 5. Drop enum type
        conn.execute(text(f"""
            DROP TYPE IF EXISTS {schema}.marketplace_task_type;
        """))

        print(f"✓ Reverted marketplace_tasks → plugin_tasks in {schema}")
