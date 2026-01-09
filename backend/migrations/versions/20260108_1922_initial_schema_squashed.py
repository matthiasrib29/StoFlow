"""initial_schema_squashed

Squashed migration combining 81 previous migrations into a single base.

Revision ID: 9e1b5d86d3ec
Revises: None
Create Date: 2026-01-08 19:22:57.930609+01:00

Business Context:
- Squashed 81 migrations (from project inception to 2026-01-08)
- Includes all product_attributes tables with multilingual support (EN, FR, DE, IT, ES, NL, PL)
- Multi-tenant architecture with user schemas
- Marketplace integrations (Vinted, eBay, Etsy)

This migration is IDEMPOTENT:
- For NEW installations: Creates full schema from squashed_schema.sql
- For EXISTING installations: Detects existing schema and does nothing (no-op)

Safe to run on production: `alembic upgrade head`

"""
from typing import Sequence, Union
from pathlib import Path

from alembic import op
from sqlalchemy import text
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9e1b5d86d3ec'
down_revision: Union[str, None] = None  # This is now the base migration
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Apply squashed schema if database is empty, otherwise skip (idempotent).

    This allows running `alembic upgrade head` on both:
    - Fresh databases (creates everything)
    - Existing databases (does nothing, already migrated)
    """
    conn = op.get_bind()

    # Check if product_attributes schema exists (indicator of existing installation)
    result = conn.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.schemata
            WHERE schema_name = 'product_attributes'
        )
    """))
    schema_exists = result.scalar()

    if schema_exists:
        # Existing installation - schema already applied via old migrations
        # This is a no-op to maintain Alembic version tracking
        print("✅ Existing installation detected - skipping schema creation (already applied)")
        return

    # New installation - apply full schema from SQL file
    print("🆕 New installation detected - applying squashed schema...")

    sql_file = Path(__file__).parent.parent / 'squashed_schema.sql'

    if not sql_file.exists():
        raise FileNotFoundError(
            f"Squashed schema file not found: {sql_file}\n"
            f"Cannot proceed with fresh installation."
        )

    # Read and execute the SQL file
    with open(sql_file, 'r') as f:
        sql_content = f.read()

    # Execute the SQL (will create all schemas, tables, and seed data)
    conn.execute(text(sql_content))

    print("✅ Squashed schema applied successfully")


def downgrade() -> None:
    """
    Rollback by dropping all schemas.

    WARNING: This will DELETE ALL DATA!
    Only use in development/test environments.
    """
    conn = op.get_bind()

    print("⚠️  WARNING: Dropping all schemas - this will DELETE ALL DATA!")

    # Drop all custom schemas
    conn.execute(text("DROP SCHEMA IF EXISTS product_attributes CASCADE"))
    conn.execute(text("DROP SCHEMA IF EXISTS template_tenant CASCADE"))
    conn.execute(text("DROP SCHEMA IF EXISTS ebay CASCADE"))
    conn.execute(text("DROP SCHEMA IF EXISTS vinted CASCADE"))

    # Recreate public schema
    conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
    conn.execute(text("CREATE SCHEMA public"))
    conn.execute(text("COMMENT ON SCHEMA public IS 'standard public schema'"))

    print("✅ All schemas dropped - database reset to empty state")
