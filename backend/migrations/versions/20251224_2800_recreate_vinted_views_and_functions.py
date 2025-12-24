"""recreate vinted views and functions in vinted schema

Revision ID: 20251224_2800
Revises: 20251224_2700
Create Date: 2025-12-24

Recreates the mapping_validation view and get_vinted_category function
in the vinted schema with updated table references.
"""

from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic
revision = "20251224_2800"
down_revision = "20251224_2700"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Recreate views and functions in vinted schema.
    """
    conn = op.get_bind()

    # =========================================================================
    # Step 1: Recreate get_vinted_category function in vinted schema
    # =========================================================================
    conn.execute(text("DROP FUNCTION IF EXISTS public.get_vinted_category"))
    conn.execute(text("DROP FUNCTION IF EXISTS vinted.get_vinted_category"))

    conn.execute(text("""
        CREATE OR REPLACE FUNCTION vinted.get_vinted_category(
            p_category VARCHAR,
            p_gender VARCHAR,
            p_fit VARCHAR DEFAULT NULL,
            p_length VARCHAR DEFAULT NULL,
            p_rise VARCHAR DEFAULT NULL,
            p_material VARCHAR DEFAULT NULL,
            p_pattern VARCHAR DEFAULT NULL,
            p_neckline VARCHAR DEFAULT NULL,
            p_sleeve_length VARCHAR DEFAULT NULL
        ) RETURNS INTEGER AS $$
        DECLARE
            v_result INTEGER;
        BEGIN
            -- Try to find best match with attributes
            -- Score based on matching attributes (higher = better match)
            SELECT vinted_id INTO v_result
            FROM vinted.mapping
            WHERE my_category = p_category
              AND my_gender = p_gender
              AND (p_fit IS NULL OR my_fit IS NULL OR my_fit = p_fit)
              AND (p_length IS NULL OR my_length IS NULL OR my_length = p_length)
              AND (p_rise IS NULL OR my_rise IS NULL OR my_rise = p_rise)
              AND (p_material IS NULL OR my_material IS NULL OR my_material = p_material)
              AND (p_pattern IS NULL OR my_pattern IS NULL OR my_pattern = p_pattern)
              AND (p_neckline IS NULL OR my_neckline IS NULL || my_neckline = p_neckline)
              AND (p_sleeve_length IS NULL OR my_sleeve_length IS NULL OR my_sleeve_length = p_sleeve_length)
            ORDER BY
                -- Calculate match score: higher weight for more important attributes
                (CASE WHEN my_fit = p_fit THEN 10 ELSE 0 END) +
                (CASE WHEN my_length = p_length THEN 10 ELSE 0 END) +
                (CASE WHEN my_rise = p_rise THEN 10 ELSE 0 END) +
                (CASE WHEN my_material = p_material THEN 5 ELSE 0 END) +
                (CASE WHEN my_pattern = p_pattern THEN 3 ELSE 0 END) +
                (CASE WHEN my_neckline = p_neckline THEN 3 ELSE 0 END) +
                (CASE WHEN my_sleeve_length = p_sleeve_length THEN 2 ELSE 0 END) DESC,
                -- Prefer default mapping as tiebreaker
                is_default DESC
            LIMIT 1;

            -- Fallback to default if no specific match
            IF v_result IS NULL THEN
                SELECT vinted_id INTO v_result
                FROM vinted.mapping
                WHERE my_category = p_category
                  AND my_gender = p_gender
                  AND is_default = TRUE
                LIMIT 1;
            END IF;

            RETURN v_result;
        END;
        $$ LANGUAGE plpgsql
    """))
    print("  ✓ Created vinted.get_vinted_category function")

    # Also create in public schema for backward compatibility
    conn.execute(text("""
        CREATE OR REPLACE FUNCTION public.get_vinted_category(
            p_category VARCHAR,
            p_gender VARCHAR,
            p_fit VARCHAR DEFAULT NULL,
            p_length VARCHAR DEFAULT NULL,
            p_rise VARCHAR DEFAULT NULL,
            p_material VARCHAR DEFAULT NULL,
            p_pattern VARCHAR DEFAULT NULL,
            p_neckline VARCHAR DEFAULT NULL,
            p_sleeve_length VARCHAR DEFAULT NULL
        ) RETURNS INTEGER AS $$
        BEGIN
            RETURN vinted.get_vinted_category(
                p_category, p_gender, p_fit, p_length, p_rise,
                p_material, p_pattern, p_neckline, p_sleeve_length
            );
        END;
        $$ LANGUAGE plpgsql
    """))
    print("  ✓ Created public.get_vinted_category wrapper for backward compatibility")

    # =========================================================================
    # Step 2: Recreate mapping_validation view in vinted schema
    # =========================================================================
    conn.execute(text("DROP VIEW IF EXISTS public.mapping_validation"))
    conn.execute(text("DROP VIEW IF EXISTS vinted.mapping_validation"))

    conn.execute(text("""
        CREATE VIEW vinted.mapping_validation AS

        -- 1. Vinted active categories not mapped
        SELECT
            'VINTED_NOT_MAPPED' as issue,
            vc.id::text as vinted_id,
            vc.title as vinted_title,
            vc.gender as vinted_gender,
            NULL as my_category,
            NULL as my_gender
        FROM vinted.categories vc
        LEFT JOIN vinted.mapping vm ON vc.id = vm.vinted_id
        WHERE vc.is_active = TRUE
        AND vm.id IS NULL

        UNION ALL

        -- 2. Category/gender couples without default
        SELECT
            'NO_DEFAULT' as issue,
            NULL as vinted_id,
            NULL as vinted_title,
            NULL as vinted_gender,
            my_category,
            my_gender
        FROM vinted.mapping
        GROUP BY my_category, my_gender
        HAVING SUM(CASE WHEN is_default THEN 1 ELSE 0 END) = 0

        UNION ALL

        -- 3. Expected couples not mapped (based on categories with genders)
        SELECT
            'COUPLE_NOT_MAPPED' as issue,
            NULL as vinted_id,
            NULL as vinted_title,
            NULL as vinted_gender,
            c.name_en as my_category,
            g.gender as my_gender
        FROM product_attributes.categories c
        CROSS JOIN (VALUES ('men'), ('women'), ('boys'), ('girls')) AS g(gender)
        WHERE g.gender = ANY(c.genders)
        AND c.parent_category IS NOT NULL
        AND c.name_en NOT IN (
            'tops', 'bottoms', 'outerwear', 'dresses-jumpsuits',
            'formalwear', 'sportswear', 'clothing'
        )
        AND NOT EXISTS (
            SELECT 1 FROM vinted.mapping vm
            WHERE vm.my_category = c.name_en
            AND vm.my_gender = g.gender
        )
    """))
    print("  ✓ Created vinted.mapping_validation view")


def downgrade() -> None:
    """
    Restore views and functions in public schema.
    """
    conn = op.get_bind()

    # Drop vinted schema objects
    conn.execute(text("DROP VIEW IF EXISTS vinted.mapping_validation"))
    conn.execute(text("DROP FUNCTION IF EXISTS vinted.get_vinted_category"))
    conn.execute(text("DROP FUNCTION IF EXISTS public.get_vinted_category"))

    # Recreate function in public schema with old table names
    conn.execute(text("""
        CREATE OR REPLACE FUNCTION public.get_vinted_category(
            p_category VARCHAR,
            p_gender VARCHAR,
            p_fit VARCHAR DEFAULT NULL,
            p_length VARCHAR DEFAULT NULL,
            p_rise VARCHAR DEFAULT NULL,
            p_material VARCHAR DEFAULT NULL,
            p_pattern VARCHAR DEFAULT NULL,
            p_neckline VARCHAR DEFAULT NULL,
            p_sleeve_length VARCHAR DEFAULT NULL
        ) RETURNS INTEGER AS $$
        DECLARE
            v_result INTEGER;
        BEGIN
            SELECT vinted_id INTO v_result
            FROM vinted.mapping
            WHERE my_category = p_category
              AND my_gender = p_gender
              AND (p_fit IS NULL OR my_fit IS NULL OR my_fit = p_fit)
              AND (p_length IS NULL OR my_length IS NULL OR my_length = p_length)
              AND (p_rise IS NULL OR my_rise IS NULL OR my_rise = p_rise)
              AND (p_material IS NULL OR my_material IS NULL OR my_material = p_material)
              AND (p_pattern IS NULL OR my_pattern IS NULL OR my_pattern = p_pattern)
              AND (p_neckline IS NULL OR my_neckline IS NULL || my_neckline = p_neckline)
              AND (p_sleeve_length IS NULL OR my_sleeve_length IS NULL OR my_sleeve_length = p_sleeve_length)
            ORDER BY
                (CASE WHEN my_fit = p_fit THEN 10 ELSE 0 END) +
                (CASE WHEN my_length = p_length THEN 10 ELSE 0 END) +
                (CASE WHEN my_rise = p_rise THEN 10 ELSE 0 END) +
                (CASE WHEN my_material = p_material THEN 5 ELSE 0 END) +
                (CASE WHEN my_pattern = p_pattern THEN 3 ELSE 0 END) +
                (CASE WHEN my_neckline = p_neckline THEN 3 ELSE 0 END) +
                (CASE WHEN my_sleeve_length = p_sleeve_length THEN 2 ELSE 0 END) DESC,
                is_default DESC
            LIMIT 1;

            IF v_result IS NULL THEN
                SELECT vinted_id INTO v_result
                FROM vinted.mapping
                WHERE my_category = p_category
                  AND my_gender = p_gender
                  AND is_default = TRUE
                LIMIT 1;
            END IF;

            RETURN v_result;
        END;
        $$ LANGUAGE plpgsql
    """))

    # Recreate view in public schema
    conn.execute(text("""
        CREATE VIEW public.mapping_validation AS

        SELECT
            'VINTED_NOT_MAPPED' as issue,
            vc.id::text as vinted_id,
            vc.title as vinted_title,
            vc.gender as vinted_gender,
            NULL as my_category,
            NULL as my_gender
        FROM vinted.categories vc
        LEFT JOIN vinted.mapping vm ON vc.id = vm.vinted_id
        WHERE vc.is_active = TRUE
        AND vm.id IS NULL

        UNION ALL

        SELECT
            'NO_DEFAULT' as issue,
            NULL as vinted_id,
            NULL as vinted_title,
            NULL as vinted_gender,
            my_category,
            my_gender
        FROM vinted.mapping
        GROUP BY my_category, my_gender
        HAVING SUM(CASE WHEN is_default THEN 1 ELSE 0 END) = 0

        UNION ALL

        SELECT
            'COUPLE_NOT_MAPPED' as issue,
            NULL as vinted_id,
            NULL as vinted_title,
            NULL as vinted_gender,
            c.name_en as my_category,
            g.gender as my_gender
        FROM product_attributes.categories c
        CROSS JOIN (VALUES ('men'), ('women'), ('boys'), ('girls')) AS g(gender)
        WHERE g.gender = ANY(c.genders)
        AND c.parent_category IS NOT NULL
        AND c.name_en NOT IN (
            'tops', 'bottoms', 'outerwear', 'dresses-jumpsuits',
            'formalwear', 'sportswear', 'clothing'
        )
        AND NOT EXISTS (
            SELECT 1 FROM vinted.mapping vm
            WHERE vm.my_category = c.name_en
            AND vm.my_gender = g.gender
        )
    """))
    print("  ✓ Restored public.mapping_validation view and function")
