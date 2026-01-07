"""add migration_errors table for data quality tracking

Revision ID: 50071b8d3b21
Revises: 3407fcb980ee
Create Date: 2026-01-07 18:05:04.004678+01:00

Purpose:
    Create a persistent log table for tracking data quality issues encountered
    during migrations (e.g., invalid FK references, skipped records).

    This table lives in the 'public' schema and is used by migrations to record
    products with invalid data that cannot be migrated automatically.

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '50071b8d3b21'
down_revision: Union[str, None] = '3407fcb980ee'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create migration_errors table in public schema."""
    conn = op.get_bind()

    print("\n" + "=" * 70)
    print("📊 CREATING MIGRATION_ERRORS TABLE")
    print("=" * 70 + "\n")

    # Create migration_errors table in public schema
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS public.migration_errors (
            id SERIAL PRIMARY KEY,
            schema_name VARCHAR(100) NOT NULL,
            product_id INTEGER NOT NULL,
            migration_name VARCHAR(255) NOT NULL,
            error_type VARCHAR(100) NOT NULL,
            error_details TEXT,
            migrated_at TIMESTAMP NOT NULL DEFAULT NOW(),

            -- Indexes for querying
            CONSTRAINT idx_migration_errors_schema_product
                UNIQUE (schema_name, product_id, migration_name, error_type)
        );
    """))

    # Create indexes
    conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_migration_errors_schema_name
            ON public.migration_errors(schema_name);
    """))

    conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_migration_errors_error_type
            ON public.migration_errors(error_type);
    """))

    conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_migration_errors_migrated_at
            ON public.migration_errors(migrated_at DESC);
    """))

    print("✅ Created migration_errors table in public schema")
    print("=" * 70)
    print("\nTable Structure:")
    print("  - schema_name: Schema where the error occurred (user_X)")
    print("  - product_id: ID of the affected product")
    print("  - migration_name: Name of the migration that detected the error")
    print("  - error_type: Type of error (e.g., 'invalid_color', 'invalid_material')")
    print("  - error_details: Details about the invalid value")
    print("  - migrated_at: Timestamp when the error was logged")
    print("=" * 70 + "\n")


def downgrade() -> None:
    """Drop migration_errors table."""
    conn = op.get_bind()

    print("\n⚠️  Dropping migration_errors table...")
    conn.execute(text("DROP TABLE IF EXISTS public.migration_errors CASCADE;"))
    print("✅ Dropped migration_errors table")
