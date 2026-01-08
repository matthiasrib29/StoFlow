"""populate migration_errors with existing invalid data

Revision ID: 6e32427bc9b3
Revises: 50071b8d3b21
Create Date: 2026-01-07 18:07:39.870781+01:00

Purpose:
    Retroactively populate the migration_errors table with products that have
    invalid attribute values (colors, materials, condition_sups that don't exist
    in product_attributes schema).

    This migration identifies all existing data quality issues and logs them for
    manual review and correction.

"""
from typing import Sequence, Union


from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

from logging import getLogger

logger = getLogger(__name__)


# revision identifiers, used by Alembic.
revision: str = '6e32427bc9b3'
down_revision: Union[str, None] = '50071b8d3b21'
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
    """Populate migration_errors with existing invalid data."""
    conn = op.get_bind()

    logger.info("\n" + "=" * 70)
    logger.info("📊 POPULATING MIGRATION_ERRORS WITH EXISTING INVALID DATA")
    logger.info("=" * 70 + "\n")

    schemas = get_user_schemas(conn)
    total_errors_logged = 0

    for schema in schemas:
        if not table_exists(conn, schema, 'products'):
            continue

        logger.info(f"📦 Scanning {schema}...")

        # Log products with invalid colors
        result = conn.execute(text(f"""
            INSERT INTO public.migration_errors
                (schema_name, product_id, migration_name, error_type, error_details)
            SELECT
                '{schema}' AS schema_name,
                id AS product_id,
                'add_many_to_many_product_attributes' AS migration_name,
                'invalid_color' AS error_type,
                'Color: ' || color AS error_details
            FROM {schema}.products
            WHERE color IS NOT NULL
            AND color != ''
            AND color NOT IN (SELECT name_en FROM product_attributes.colors)
            AND deleted_at IS NULL
            ON CONFLICT (schema_name, product_id, migration_name, error_type) DO NOTHING;
        """))
        colors_logged = result.rowcount
        if colors_logged > 0:
            logger.info(f"  📝 Logged {colors_logged} products with invalid color")
            total_errors_logged += colors_logged

        # Log products with invalid materials
        result = conn.execute(text(f"""
            INSERT INTO public.migration_errors
                (schema_name, product_id, migration_name, error_type, error_details)
            SELECT
                '{schema}' AS schema_name,
                id AS product_id,
                'add_many_to_many_product_attributes' AS migration_name,
                'invalid_material' AS error_type,
                'Material: ' || material AS error_details
            FROM {schema}.products
            WHERE material IS NOT NULL
            AND material != ''
            AND material NOT IN (SELECT name_en FROM product_attributes.materials)
            AND deleted_at IS NULL
            ON CONFLICT (schema_name, product_id, migration_name, error_type) DO NOTHING;
        """))
        materials_logged = result.rowcount
        if materials_logged > 0:
            logger.info(f"  📝 Logged {materials_logged} products with invalid material")
            total_errors_logged += materials_logged

        # Log products with invalid condition_sups
        result = conn.execute(text(f"""
            INSERT INTO public.migration_errors
                (schema_name, product_id, migration_name, error_type, error_details)
            SELECT
                '{schema}' AS schema_name,
                p.id AS product_id,
                'add_many_to_many_product_attributes' AS migration_name,
                'invalid_condition_sup' AS error_type,
                'Invalid values: ' || string_agg(elem::text, ', ') AS error_details
            FROM {schema}.products p,
                 LATERAL jsonb_array_elements_text(p.condition_sup) AS elem
            WHERE p.condition_sup IS NOT NULL
            AND jsonb_typeof(p.condition_sup) = 'array'
            AND elem::text NOT IN (SELECT name_en FROM product_attributes.condition_sups)
            AND p.deleted_at IS NULL
            GROUP BY p.id
            ON CONFLICT (schema_name, product_id, migration_name, error_type) DO NOTHING;
        """))
        condition_sups_logged = result.rowcount
        if condition_sups_logged > 0:
            logger.info(f"  📝 Logged {condition_sups_logged} products with invalid condition_sup")
            total_errors_logged += condition_sups_logged

    logger.info("\n" + "=" * 70)
    logger.info("📊 POPULATION SUMMARY")
    logger.info("=" * 70)
    logger.info(f"  Total errors logged: {total_errors_logged}")
    logger.info("=" * 70)
    logger.info("✅ POPULATION COMPLETE")
    logger.info("=" * 70)

    if total_errors_logged > 0:
        logger.info(f"\n📝 Data Quality Report:")
        logger.info(f"   {total_errors_logged} products with invalid data logged to public.migration_errors")
        logger.info(f"   Query to review:")
        logger.info(f"   SELECT * FROM public.migration_errors")
        logger.info(f"   WHERE migration_name = 'add_many_to_many_product_attributes'")
        logger.info(f"   ORDER BY schema_name, product_id;")
        logger.info("=" * 70)


def downgrade() -> None:
    """Remove logged errors from migration_errors table."""
    conn = op.get_bind()

    logger.info("\n⚠️  Removing logged errors from migration_errors...")
    result = conn.execute(text("""
        DELETE FROM public.migration_errors
        WHERE migration_name = 'add_many_to_many_product_attributes';
    """))
    logger.info(f"✅ Removed {result.rowcount} error logs")
