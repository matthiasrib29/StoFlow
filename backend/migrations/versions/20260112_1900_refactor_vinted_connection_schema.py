"""Refactor vinted_connection table schema

This migration aligns the vinted_connection table with the new model structure:
- Add `id` as new auto-increment primary key
- Rename `login` → `username`
- Rename `last_sync` → `last_synced_at`
- Make `vinted_user_id` nullable (BigInteger for large Vinted IDs)
- Add missing columns: session_id, csrf_token, datadome_cookie, updated_at
- Remove `disconnected_at` column
- Add UNIQUE constraint on `user_id`

Applied to: template_tenant and all user_X schemas

RECOVERED from lost commit c90899b (2026-01-12)

Revision ID: 20260112_1900
Revises: 6bc865c4c841
Create Date: 2026-01-12

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
import logging

# revision identifiers, used by Alembic.
revision = '20260112_1900'
down_revision = '94236e80c53d'
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


def constraint_exists(connection, schema: str, constraint_name: str) -> bool:
    """Check if a constraint exists."""
    result = connection.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.table_constraints
            WHERE constraint_schema = :schema
              AND constraint_name = :constraint_name
        )
    """), {"schema": schema, "constraint_name": constraint_name})
    return result.scalar()


def upgrade() -> None:
    """Upgrade vinted_connection table in all tenant schemas."""
    connection = op.get_bind()
    schemas = get_all_tenant_schemas(connection)

    logger.info(f"Upgrading vinted_connection in {len(schemas)} schemas...")

    for schema in schemas:
        if not table_exists(connection, schema, 'vinted_connection'):
            logger.info(f"  [{schema}] Table does not exist, skipping")
            continue

        logger.info(f"  [{schema}] Migrating vinted_connection...")

        # 1. Add `id` column if not exists (will become new PK)
        if not column_exists(connection, schema, 'vinted_connection', 'id'):
            # First, drop the existing PK constraint on vinted_user_id
            connection.execute(text(f"""
                ALTER TABLE {schema}.vinted_connection
                DROP CONSTRAINT IF EXISTS vinted_connection_pkey
            """))

            # Add id column with SERIAL (auto-increment)
            connection.execute(text(f"""
                ALTER TABLE {schema}.vinted_connection
                ADD COLUMN id SERIAL
            """))

            # Make id the new primary key
            connection.execute(text(f"""
                ALTER TABLE {schema}.vinted_connection
                ADD PRIMARY KEY (id)
            """))
            logger.info(f"    + Added 'id' column as new PK")

        # 2. Rename login → username if needed
        if column_exists(connection, schema, 'vinted_connection', 'login'):
            if not column_exists(connection, schema, 'vinted_connection', 'username'):
                connection.execute(text(f"""
                    ALTER TABLE {schema}.vinted_connection
                    RENAME COLUMN login TO username
                """))
                logger.info(f"    ~ Renamed 'login' → 'username'")

        # 3. Rename last_sync → last_synced_at if needed
        if column_exists(connection, schema, 'vinted_connection', 'last_sync'):
            if not column_exists(connection, schema, 'vinted_connection', 'last_synced_at'):
                connection.execute(text(f"""
                    ALTER TABLE {schema}.vinted_connection
                    RENAME COLUMN last_sync TO last_synced_at
                """))
                logger.info(f"    ~ Renamed 'last_sync' → 'last_synced_at'")

        # 4. Make vinted_user_id nullable and change to BIGINT
        # First check if it's already nullable
        result = connection.execute(text("""
            SELECT is_nullable, data_type
            FROM information_schema.columns
            WHERE table_schema = :schema
              AND table_name = 'vinted_connection'
              AND column_name = 'vinted_user_id'
        """), {"schema": schema})
        row = result.fetchone()

        if row:
            is_nullable, data_type = row
            if is_nullable == 'NO':
                connection.execute(text(f"""
                    ALTER TABLE {schema}.vinted_connection
                    ALTER COLUMN vinted_user_id DROP NOT NULL
                """))
                logger.info(f"    ~ Made 'vinted_user_id' nullable")

            if data_type == 'integer':
                connection.execute(text(f"""
                    ALTER TABLE {schema}.vinted_connection
                    ALTER COLUMN vinted_user_id TYPE BIGINT
                """))
                logger.info(f"    ~ Changed 'vinted_user_id' to BIGINT")

        # 5. Make username nullable (was login NOT NULL before)
        result = connection.execute(text("""
            SELECT is_nullable
            FROM information_schema.columns
            WHERE table_schema = :schema
              AND table_name = 'vinted_connection'
              AND column_name = 'username'
        """), {"schema": schema})
        row = result.fetchone()
        if row and row[0] == 'NO':
            connection.execute(text(f"""
                ALTER TABLE {schema}.vinted_connection
                ALTER COLUMN username DROP NOT NULL
            """))
            logger.info(f"    ~ Made 'username' nullable")

        # 6. Add missing columns
        new_columns = [
            ('session_id', 'TEXT'),
            ('csrf_token', 'TEXT'),
            ('datadome_cookie', 'TEXT'),
            ('updated_at', "TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL"),
        ]

        for col_name, col_type in new_columns:
            if not column_exists(connection, schema, 'vinted_connection', col_name):
                connection.execute(text(f"""
                    ALTER TABLE {schema}.vinted_connection
                    ADD COLUMN {col_name} {col_type}
                """))
                logger.info(f"    + Added '{col_name}' column")

        # 7. Drop disconnected_at column if exists
        if column_exists(connection, schema, 'vinted_connection', 'disconnected_at'):
            connection.execute(text(f"""
                ALTER TABLE {schema}.vinted_connection
                DROP COLUMN disconnected_at
            """))
            logger.info(f"    - Dropped 'disconnected_at' column")

        # 8. Add UNIQUE constraint on user_id if not exists
        constraint_name = f"{schema}_vinted_connection_user_id_key"
        if not constraint_exists(connection, schema, constraint_name):
            # Check if there's an existing unique constraint
            existing = connection.execute(text("""
                SELECT constraint_name
                FROM information_schema.table_constraints
                WHERE table_schema = :schema
                  AND table_name = 'vinted_connection'
                  AND constraint_type = 'UNIQUE'
            """), {"schema": schema}).fetchall()

            if not any('user_id' in str(c) for c in existing):
                connection.execute(text(f"""
                    ALTER TABLE {schema}.vinted_connection
                    ADD CONSTRAINT {constraint_name} UNIQUE (user_id)
                """))
                logger.info(f"    + Added UNIQUE constraint on 'user_id'")

        # 9. Update indexes - drop old login index if exists
        connection.execute(text(f"""
            DROP INDEX IF EXISTS {schema}.ix_{schema}_vinted_connection_login
        """))
        connection.execute(text(f"""
            DROP INDEX IF EXISTS ix_{schema}_vinted_connection_login
        """))

        # Create new username index if not exists
        connection.execute(text(f"""
            CREATE INDEX IF NOT EXISTS ix_{schema}_vinted_connection_username
            ON {schema}.vinted_connection (username)
        """))

        logger.info(f"  [{schema}] ✓ Migration complete")

    logger.info("✅ All schemas migrated successfully")


def downgrade() -> None:
    """Revert vinted_connection table changes."""
    connection = op.get_bind()
    schemas = get_all_tenant_schemas(connection)

    logger.info(f"Downgrading vinted_connection in {len(schemas)} schemas...")

    for schema in schemas:
        if not table_exists(connection, schema, 'vinted_connection'):
            continue

        logger.info(f"  [{schema}] Reverting vinted_connection...")

        # 1. Add back disconnected_at
        if not column_exists(connection, schema, 'vinted_connection', 'disconnected_at'):
            connection.execute(text(f"""
                ALTER TABLE {schema}.vinted_connection
                ADD COLUMN disconnected_at TIMESTAMP WITH TIME ZONE
            """))

        # 2. Drop new columns
        for col in ['session_id', 'csrf_token', 'datadome_cookie', 'updated_at']:
            if column_exists(connection, schema, 'vinted_connection', col):
                connection.execute(text(f"""
                    ALTER TABLE {schema}.vinted_connection
                    DROP COLUMN {col}
                """))

        # 3. Rename username → login
        if column_exists(connection, schema, 'vinted_connection', 'username'):
            if not column_exists(connection, schema, 'vinted_connection', 'login'):
                connection.execute(text(f"""
                    ALTER TABLE {schema}.vinted_connection
                    RENAME COLUMN username TO login
                """))

        # 4. Rename last_synced_at → last_sync
        if column_exists(connection, schema, 'vinted_connection', 'last_synced_at'):
            if not column_exists(connection, schema, 'vinted_connection', 'last_sync'):
                connection.execute(text(f"""
                    ALTER TABLE {schema}.vinted_connection
                    RENAME COLUMN last_synced_at TO last_sync
                """))

        # 5. Drop id column and restore vinted_user_id as PK
        if column_exists(connection, schema, 'vinted_connection', 'id'):
            # Drop PK on id
            connection.execute(text(f"""
                ALTER TABLE {schema}.vinted_connection
                DROP CONSTRAINT IF EXISTS vinted_connection_pkey
            """))

            # Drop id column
            connection.execute(text(f"""
                ALTER TABLE {schema}.vinted_connection
                DROP COLUMN id
            """))

            # Make vinted_user_id NOT NULL
            connection.execute(text(f"""
                ALTER TABLE {schema}.vinted_connection
                ALTER COLUMN vinted_user_id SET NOT NULL
            """))

            # Restore vinted_user_id as PK
            connection.execute(text(f"""
                ALTER TABLE {schema}.vinted_connection
                ADD PRIMARY KEY (vinted_user_id)
            """))

        # 6. Make login NOT NULL
        if column_exists(connection, schema, 'vinted_connection', 'login'):
            connection.execute(text(f"""
                ALTER TABLE {schema}.vinted_connection
                ALTER COLUMN login SET NOT NULL
            """))

        # 7. Drop UNIQUE constraint on user_id
        constraint_name = f"{schema}_vinted_connection_user_id_key"
        connection.execute(text(f"""
            ALTER TABLE {schema}.vinted_connection
            DROP CONSTRAINT IF EXISTS {constraint_name}
        """))

        logger.info(f"  [{schema}] ✓ Downgrade complete")

    logger.info("✅ All schemas downgraded successfully")
