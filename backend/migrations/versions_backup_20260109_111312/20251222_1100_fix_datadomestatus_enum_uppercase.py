"""Fix DataDomeStatus enum to use uppercase values

Revision ID: 20251222_1100
Revises: 20251222_1001
Create Date: 2025-12-22 11:00:00.000000

Problem: SQLAlchemy Enum() uses attribute NAMES (OK, FAILED, UNKNOWN) by default,
but the PostgreSQL enum was created with lowercase values (ok, failed, unknown).

Solution: Change PostgreSQL enum values to uppercase to match SQLAlchemy's default behavior.
"""
from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = '20251222_1100'
down_revision = '46909e0170ba'
branch_labels = None
depends_on = None


def upgrade():
    """Change datadomestatus enum values from lowercase to uppercase."""
    conn = op.get_bind()

    # PostgreSQL doesn't allow direct enum value modification.
    # We need to: create new type -> alter columns -> drop old type -> rename new type

    print("Fixing DataDomeStatus enum: lowercase -> UPPERCASE")

    # Step 1: Create new enum type with uppercase values
    conn.execute(text("""
        CREATE TYPE datadomestatus_new AS ENUM ('OK', 'FAILED', 'UNKNOWN');
    """))

    # Step 2: Get all schemas that have vinted_connection table
    result = conn.execute(text("""
        SELECT table_schema
        FROM information_schema.columns
        WHERE table_name = 'vinted_connection'
        AND column_name = 'datadome_status'
        ORDER BY table_schema
    """))
    schemas = [row[0] for row in result.fetchall()]

    print(f"Found {len(schemas)} schemas with datadome_status column: {schemas}")

    # Step 3: For each schema, alter the column to use new type
    for schema in schemas:
        print(f"  Updating {schema}.vinted_connection.datadome_status...")

        # First, drop the default (required before type change)
        conn.execute(text(f"""
            ALTER TABLE {schema}.vinted_connection
            ALTER COLUMN datadome_status DROP DEFAULT;
        """))

        # Alter column with type conversion (lowercase -> uppercase)
        conn.execute(text(f"""
            ALTER TABLE {schema}.vinted_connection
            ALTER COLUMN datadome_status TYPE datadomestatus_new
            USING (
                CASE datadome_status::text
                    WHEN 'ok' THEN 'OK'::datadomestatus_new
                    WHEN 'failed' THEN 'FAILED'::datadomestatus_new
                    WHEN 'unknown' THEN 'UNKNOWN'::datadomestatus_new
                    WHEN 'OK' THEN 'OK'::datadomestatus_new
                    WHEN 'FAILED' THEN 'FAILED'::datadomestatus_new
                    WHEN 'UNKNOWN' THEN 'UNKNOWN'::datadomestatus_new
                    ELSE 'UNKNOWN'::datadomestatus_new
                END
            );
        """))

        # Set the new default value
        conn.execute(text(f"""
            ALTER TABLE {schema}.vinted_connection
            ALTER COLUMN datadome_status SET DEFAULT 'UNKNOWN'::datadomestatus_new;
        """))

    # Step 4: Drop old enum type
    conn.execute(text("DROP TYPE datadomestatus;"))

    # Step 5: Rename new type to original name
    conn.execute(text("ALTER TYPE datadomestatus_new RENAME TO datadomestatus;"))

    print("DataDomeStatus enum fixed successfully!")


def downgrade():
    """Revert to lowercase enum values."""
    conn = op.get_bind()

    # Create old type with lowercase values
    conn.execute(text("""
        CREATE TYPE datadomestatus_old AS ENUM ('ok', 'failed', 'unknown');
    """))

    # Get all schemas
    result = conn.execute(text("""
        SELECT table_schema
        FROM information_schema.columns
        WHERE table_name = 'vinted_connection'
        AND column_name = 'datadome_status'
        ORDER BY table_schema
    """))
    schemas = [row[0] for row in result.fetchall()]

    # Alter columns back to lowercase
    for schema in schemas:
        conn.execute(text(f"""
            ALTER TABLE {schema}.vinted_connection
            ALTER COLUMN datadome_status TYPE datadomestatus_old
            USING (
                CASE datadome_status::text
                    WHEN 'OK' THEN 'ok'::datadomestatus_old
                    WHEN 'FAILED' THEN 'failed'::datadomestatus_old
                    WHEN 'UNKNOWN' THEN 'unknown'::datadomestatus_old
                    ELSE 'unknown'::datadomestatus_old
                END
            );
        """))

        conn.execute(text(f"""
            ALTER TABLE {schema}.vinted_connection
            ALTER COLUMN datadome_status SET DEFAULT 'unknown'::datadomestatus_old;
        """))

    # Drop and rename
    conn.execute(text("DROP TYPE datadomestatus;"))
    conn.execute(text("ALTER TYPE datadomestatus_old RENAME TO datadomestatus;"))
