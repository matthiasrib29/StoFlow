"""remigrate condition_sup to m2m table

Revision ID: dd7f6b1ded75
Revises: 9b12d3d8f4c4
Create Date: 2026-01-07 18:16:07.248574+01:00

Purpose:
    Re-migrate condition_sup data from JSONB column to M2M table.

    After fixing case issues, all condition_sup values now match the reference
    table, so we can properly migrate them to product_condition_sups M2M table.

    Strategy:
    1. Clear existing product_condition_sups entries (from failed first migration)
    2. Re-migrate with correct Title Case values
    3. Clear migration_errors for condition_sup (issues are now fixed)

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'dd7f6b1ded75'
down_revision: Union[str, None] = '9b12d3d8f4c4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def get_user_schemas(conn):
    """Get all user schemas (template_tenant + user_X)."""
    result = conn.execute(text("""
        SELECT schema_name FROM information_schema.schemata
        WHERE schema_name = 'template_tenant'
        OR schema_name LIKE 'user_%'
        ORDER BY schema_name
    """))
    return [row[0] for row in result.fetchall()]


def table_exists(conn, schema, table):
    """Check if a table exists in a schema."""
    result = conn.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = :schema AND table_name = :table
        )
    """), {"schema": schema, "table": table})
    return result.scalar()


def upgrade() -> None:
    """Re-migrate condition_sup from JSONB to M2M table."""
    conn = op.get_bind()

    print("\n" + "=" * 70)
    print("📊 RE-MIGRATING CONDITION_SUP TO M2M TABLE")
    print("=" * 70 + "\n")

    schemas = get_user_schemas(conn)
    total_migrated = 0
    total_cleared = 0

    for schema in schemas:
        if not table_exists(conn, schema, 'products'):
            continue

        print(f"📦 Processing {schema}...")

        # Step 1: Clear existing entries in product_condition_sups for this schema
        result = conn.execute(text(f"""
            DELETE FROM {schema}.product_condition_sups;
        """))
        cleared = result.rowcount
        if cleared > 0:
            print(f"  🧹 Cleared {cleared} old entries from product_condition_sups")
            total_cleared += cleared

        # Step 2: Re-migrate with corrected Title Case values
        result = conn.execute(text(f"""
            INSERT INTO {schema}.product_condition_sups (product_id, condition_sup)
            SELECT p.id, elem::text
            FROM {schema}.products p,
                 LATERAL jsonb_array_elements_text(p.condition_sup) AS elem
            WHERE p.condition_sup IS NOT NULL
            AND jsonb_typeof(p.condition_sup) = 'array'
            AND elem::text IN (SELECT name_en FROM product_attributes.condition_sups)
            AND p.deleted_at IS NULL
            ON CONFLICT DO NOTHING;
        """))
        migrated = result.rowcount
        if migrated > 0:
            print(f"  ✅ Migrated {migrated} condition_sup entries to M2M table")
            total_migrated += migrated

    print("\n" + "=" * 70)
    print("📊 RE-MIGRATION SUMMARY")
    print("=" * 70)
    print(f"  Old entries cleared: {total_cleared}")
    print(f"  New entries migrated: {total_migrated}")
    print("=" * 70)

    # Step 3: Clear migration_errors for condition_sup (issues now fixed)
    print("\n🧹 Clearing migration_errors for condition_sup...")
    result = conn.execute(text("""
        DELETE FROM public.migration_errors
        WHERE migration_name = 'add_many_to_many_product_attributes'
        AND error_type = 'invalid_condition_sup';
    """))
    errors_cleared = result.rowcount
    print(f"  ✅ Cleared {errors_cleared} error logs (issues resolved)")

    print("\n" + "=" * 70)
    print("✅ RE-MIGRATION COMPLETE")
    print("=" * 70)


def downgrade() -> None:
    """Clear M2M table (revert to JSONB only)."""
    conn = op.get_bind()

    print("\n⚠️  Clearing product_condition_sups M2M table...")

    schemas = get_user_schemas(conn)
    total_cleared = 0

    for schema in schemas:
        if not table_exists(conn, schema, 'product_condition_sups'):
            continue

        result = conn.execute(text(f"""
            DELETE FROM {schema}.product_condition_sups;
        """))
        total_cleared += result.rowcount

    print(f"✅ Cleared {total_cleared} M2M entries (reverted to JSONB only)")
