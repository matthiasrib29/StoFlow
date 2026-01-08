"""add many-to-many product attributes

Revision ID: 3407fcb980ee
Revises: 4d2e58dae912
Create Date: 2026-01-07 17:05:47.029161+01:00

Create 3 Many-to-Many junction tables for product attributes:
- product_colors (product_id, color, is_primary)
- product_materials (product_id, material, percentage)
- product_condition_sups (product_id, condition_sup)

Migrate existing data:
- products.color (string) → product_colors (with is_primary=TRUE)
- products.material (string) → product_materials (no percentage)
- products.condition_sup (JSONB array) → product_condition_sups (explode array)

Note: Old columns are kept for backward compatibility (dual-write strategy).
They will be dropped in a future migration after validation period.
"""
from typing import Sequence, Union


from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

from logging import getLogger

logger = getLogger(__name__)


# revision identifiers, used by Alembic.
revision: str = '3407fcb980ee'
down_revision: Union[str, None] = 'd4d7725adb3a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def get_user_schemas(conn):
    """Get list of user schemas (template_tenant + user_X)."""
    result = conn.execute(text("""
        SELECT schema_name FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%'
        AND schema_name <> 'user_invalid'
        ORDER BY schema_name
    """))
    user_schemas = [row[0] for row in result.fetchall()]
    return ['template_tenant'] + user_schemas


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
    """Create M2M junction tables and migrate existing data."""
    conn = op.get_bind()

    logger.info("=" * 70)
    logger.info("🚀 CREATING MANY-TO-MANY JUNCTION TABLES")
    logger.info("=" * 70)

    schemas = get_user_schemas(conn)
    logger.info(f"\n✅ Found {len(schemas)} schemas to process\n")

    for schema in schemas:
        # Verify products table exists
        if not table_exists(conn, schema, 'products'):
            logger.info(f"⚠️  Skipping {schema} - products table not found")
            continue

        logger.info(f"📦 Processing {schema}...")

        # ===== 1. CREATE PRODUCT_COLORS TABLE =====
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS {schema}.product_colors (
                product_id INTEGER NOT NULL,
                color VARCHAR(100) NOT NULL,
                is_primary BOOLEAN NOT NULL DEFAULT FALSE,

                CONSTRAINT pk_product_colors PRIMARY KEY (product_id, color),
                CONSTRAINT fk_product_colors_product_id
                    FOREIGN KEY (product_id)
                    REFERENCES {schema}.products(id) ON DELETE CASCADE,
                CONSTRAINT fk_product_colors_color
                    FOREIGN KEY (color)
                    REFERENCES product_attributes.colors(name_en)
                    ON UPDATE CASCADE ON DELETE CASCADE
            );
        """))

        # Unique constraint: only one primary color per product
        conn.execute(text(f"""
            CREATE UNIQUE INDEX IF NOT EXISTS uq_product_colors_primary
            ON {schema}.product_colors(product_id)
            WHERE is_primary = TRUE;
        """))

        # Indexes for performance
        conn.execute(text(f"""
            CREATE INDEX IF NOT EXISTS idx_product_colors_product_id
            ON {schema}.product_colors(product_id);
        """))
        conn.execute(text(f"""
            CREATE INDEX IF NOT EXISTS idx_product_colors_color
            ON {schema}.product_colors(color);
        """))

        # ===== 2. CREATE PRODUCT_MATERIALS TABLE =====
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS {schema}.product_materials (
                product_id INTEGER NOT NULL,
                material VARCHAR(100) NOT NULL,
                percentage INTEGER NULL CHECK (percentage >= 0 AND percentage <= 100),

                CONSTRAINT pk_product_materials PRIMARY KEY (product_id, material),
                CONSTRAINT fk_product_materials_product_id
                    FOREIGN KEY (product_id)
                    REFERENCES {schema}.products(id) ON DELETE CASCADE,
                CONSTRAINT fk_product_materials_material
                    FOREIGN KEY (material)
                    REFERENCES product_attributes.materials(name_en)
                    ON UPDATE CASCADE ON DELETE CASCADE
            );
        """))

        # Indexes for performance
        conn.execute(text(f"""
            CREATE INDEX IF NOT EXISTS idx_product_materials_product_id
            ON {schema}.product_materials(product_id);
        """))
        conn.execute(text(f"""
            CREATE INDEX IF NOT EXISTS idx_product_materials_material
            ON {schema}.product_materials(material);
        """))

        # ===== 3. CREATE PRODUCT_CONDITION_SUPS TABLE =====
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS {schema}.product_condition_sups (
                product_id INTEGER NOT NULL,
                condition_sup VARCHAR(100) NOT NULL,

                CONSTRAINT pk_product_condition_sups PRIMARY KEY (product_id, condition_sup),
                CONSTRAINT fk_product_condition_sups_product_id
                    FOREIGN KEY (product_id)
                    REFERENCES {schema}.products(id) ON DELETE CASCADE,
                CONSTRAINT fk_product_condition_sups_condition_sup
                    FOREIGN KEY (condition_sup)
                    REFERENCES product_attributes.condition_sups(name_en)
                    ON UPDATE CASCADE ON DELETE CASCADE
            );
        """))

        # Indexes for performance
        conn.execute(text(f"""
            CREATE INDEX IF NOT EXISTS idx_product_condition_sups_product_id
            ON {schema}.product_condition_sups(product_id);
        """))
        conn.execute(text(f"""
            CREATE INDEX IF NOT EXISTS idx_product_condition_sups_condition_sup
            ON {schema}.product_condition_sups(condition_sup);
        """))

        logger.info(f"  ✅ Created 3 junction tables in {schema}")

    # ===== MIGRATE EXISTING DATA =====
    logger.info("\n" + "=" * 70)
    logger.info("📊 MIGRATING EXISTING DATA")
    logger.info("=" * 70 + "\n")

    total_colors_migrated = 0
    total_materials_migrated = 0
    total_condition_sups_migrated = 0
    total_colors_skipped = 0
    total_materials_skipped = 0
    total_condition_sups_skipped = 0

    for schema in schemas:
        if not table_exists(conn, schema, 'products'):
            continue

        logger.info(f"📦 Migrating data in {schema}...")

        # Migrate colors (String → product_colors with is_primary=TRUE)
        result = conn.execute(text(f"""
            INSERT INTO {schema}.product_colors (product_id, color, is_primary)
            SELECT id, color, TRUE
            FROM {schema}.products
            WHERE color IS NOT NULL
            AND color != ''
            AND color IN (SELECT name_en FROM product_attributes.colors)
            AND deleted_at IS NULL
            ON CONFLICT DO NOTHING;
        """))
        colors_count = result.rowcount
        total_colors_migrated += colors_count
        if colors_count > 0:
            logger.info(f"  ✅ Migrated {colors_count} colors")

        # Count skipped (invalid colors)
        result = conn.execute(text(f"""
            SELECT COUNT(*) FROM {schema}.products
            WHERE color IS NOT NULL
            AND color != ''
            AND color NOT IN (SELECT name_en FROM product_attributes.colors)
            AND deleted_at IS NULL
        """))
        colors_skipped = result.scalar()
        total_colors_skipped += colors_skipped
        if colors_skipped > 0:
            logger.info(f"  ⚠️  Skipped {colors_skipped} products with invalid color")

            # Log skipped products to migration_errors table
            conn.execute(text(f"""
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
            logger.info(f"     📝 Logged {colors_skipped} invalid colors to migration_errors table")

        # Migrate materials (String → product_materials, no percentage)
        result = conn.execute(text(f"""
            INSERT INTO {schema}.product_materials (product_id, material)
            SELECT id, material
            FROM {schema}.products
            WHERE material IS NOT NULL
            AND material != ''
            AND material IN (SELECT name_en FROM product_attributes.materials)
            AND deleted_at IS NULL
            ON CONFLICT DO NOTHING;
        """))
        materials_count = result.rowcount
        total_materials_migrated += materials_count
        if materials_count > 0:
            logger.info(f"  ✅ Migrated {materials_count} materials")

        # Count skipped (invalid materials)
        result = conn.execute(text(f"""
            SELECT COUNT(*) FROM {schema}.products
            WHERE material IS NOT NULL
            AND material != ''
            AND material NOT IN (SELECT name_en FROM product_attributes.materials)
            AND deleted_at IS NULL
        """))
        materials_skipped = result.scalar()
        total_materials_skipped += materials_skipped
        if materials_skipped > 0:
            logger.info(f"  ⚠️  Skipped {materials_skipped} products with invalid material")

            # Log skipped products to migration_errors table
            conn.execute(text(f"""
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
            logger.info(f"     📝 Logged {materials_skipped} invalid materials to migration_errors table")

        # Migrate condition_sup (JSONB array → product_condition_sups)
        # Use jsonb_array_elements_text to explode the array
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
        condition_sups_count = result.rowcount
        total_condition_sups_migrated += condition_sups_count
        if condition_sups_count > 0:
            logger.info(f"  ✅ Migrated {condition_sups_count} condition_sup entries")

        # Count skipped (invalid condition_sups)
        result = conn.execute(text(f"""
            SELECT COUNT(DISTINCT p.id) FROM {schema}.products p,
                   LATERAL jsonb_array_elements_text(p.condition_sup) AS elem
            WHERE p.condition_sup IS NOT NULL
            AND jsonb_typeof(p.condition_sup) = 'array'
            AND elem::text NOT IN (SELECT name_en FROM product_attributes.condition_sups)
            AND p.deleted_at IS NULL
        """))
        condition_sups_skipped = result.scalar()
        total_condition_sups_skipped += condition_sups_skipped
        if condition_sups_skipped > 0:
            logger.info(f"  ⚠️  Skipped {condition_sups_skipped} products with invalid condition_sup values")

            # Log skipped products to migration_errors table
            # Aggregate all invalid values per product into a comma-separated list
            conn.execute(text(f"""
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
            logger.info(f"     📝 Logged {condition_sups_skipped} invalid condition_sups to migration_errors table")

    logger.info("\n" + "=" * 70)
    logger.info("📊 MIGRATION SUMMARY")
    logger.info("=" * 70)
    logger.info(f"  Colors migrated: {total_colors_migrated}")
    logger.info(f"  Colors skipped (invalid): {total_colors_skipped}")
    logger.info(f"  Materials migrated: {total_materials_migrated}")
    logger.info(f"  Materials skipped (invalid): {total_materials_skipped}")
    logger.info(f"  Condition_sups migrated: {total_condition_sups_migrated}")
    logger.info(f"  Condition_sups skipped (invalid): {total_condition_sups_skipped}")
    logger.info("=" * 70)
    logger.info("✅ MIGRATION COMPLETE")
    logger.info("=" * 70)
    logger.info("\n⚠️  NOTE: Old columns (color, material, condition_sup) are kept")
    logger.info("   They will be dropped in a future migration after validation.")

    # Summary of skipped products logged to migration_errors
    total_skipped = total_colors_skipped + total_materials_skipped + total_condition_sups_skipped
    if total_skipped > 0:
        logger.info(f"\n📝 Data Quality Report:")
        logger.info(f"   {total_skipped} products with invalid data logged to public.migration_errors")
        logger.info(f"   Query to review: SELECT * FROM public.migration_errors")
        logger.info(f"   WHERE migration_name = 'add_many_to_many_product_attributes';")
        logger.info("=" * 70)


def downgrade() -> None:
    """Drop M2M junction tables."""
    conn = op.get_bind()

    logger.info("=" * 70)
    logger.info("🔙 ROLLING BACK MANY-TO-MANY JUNCTION TABLES")
    logger.info("=" * 70)

    schemas = get_user_schemas(conn)

    for schema in schemas:
        if not table_exists(conn, schema, 'products'):
            continue

        logger.info(f"📦 Dropping tables in {schema}...")

        # Drop tables (CASCADE to remove FKs)
        conn.execute(text(f"DROP TABLE IF EXISTS {schema}.product_colors CASCADE;"))
        conn.execute(text(f"DROP TABLE IF EXISTS {schema}.product_materials CASCADE;"))
        conn.execute(text(f"DROP TABLE IF EXISTS {schema}.product_condition_sups CASCADE;"))

        logger.info(f"  ✅ Dropped junction tables in {schema}")

    logger.info("=" * 70)
    logger.info("✅ ROLLBACK COMPLETE")
    logger.info("=" * 70)
