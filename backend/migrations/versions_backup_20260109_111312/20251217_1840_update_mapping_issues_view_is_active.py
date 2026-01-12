"""Update vw_mapping_issues view to use is_active

Revision ID: 20251217_1840
Revises: 20251217_1830
Create Date: 2025-12-17 18:40:00.000000

Updates the vw_mapping_issues view to only check active Vinted categories
instead of all leaf categories.

Author: Claude
Date: 2025-12-17
"""
from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = '20251217_1840'
down_revision = '20251217_1830'
branch_labels = None
depends_on = None


def upgrade():
    """
    Update vw_mapping_issues view to use is_active.
    """
    conn = op.get_bind()

    # Drop and recreate view
    conn.execute(text("DROP VIEW IF EXISTS public.vw_mapping_issues"))

    conn.execute(text("""
        CREATE VIEW public.vw_mapping_issues AS

        -- 1. Catégories Vinted ACTIVES non mappées
        SELECT
            'VINTED_NOT_MAPPED' as issue_type,
            vc.id::text as identifier,
            vc.title || ' (' || vc.gender || ')' as description
        FROM public.vinted_categories vc
        LEFT JOIN public.vinted_mapping vm ON vc.id = vm.vinted_id
        WHERE vc.is_active = TRUE
        AND vm.id IS NULL

        UNION ALL

        -- 2. Couples (category + gender) sans mapping
        SELECT
            'COUPLE_NOT_MAPPED' as issue_type,
            c.name_en || ' + ' || g.gender as identifier,
            'Aucun mapping pour ' || c.name_en || ' + ' || g.gender as description
        FROM product_attributes.categories c
        CROSS JOIN (VALUES ('men'), ('women'), ('boys'), ('girls')) AS g(gender)
        WHERE g.gender = ANY(c.genders)
        AND c.parent_category IS NOT NULL
        AND c.name_en NOT IN (
            'tops', 'bottoms', 'outerwear', 'dresses-jumpsuits',
            'formalwear', 'sportswear', 'clothing'
        )
        AND NOT EXISTS (
            SELECT 1 FROM public.vinted_mapping vm
            WHERE vm.my_category = c.name_en
            AND vm.my_gender = g.gender
        )

        UNION ALL

        -- 3. Couples sans défaut (0 défauts)
        SELECT
            'NO_DEFAULT' as issue_type,
            my_category || ' + ' || my_gender as identifier,
            'Aucun défaut défini pour ' || my_category || ' + ' || my_gender as description
        FROM public.vinted_mapping
        GROUP BY my_category, my_gender
        HAVING COUNT(*) FILTER (WHERE is_default = TRUE) = 0

        UNION ALL

        -- 4. Couples avec plusieurs défauts
        SELECT
            'MULTIPLE_DEFAULTS' as issue_type,
            my_category || ' + ' || my_gender as identifier,
            COUNT(*) FILTER (WHERE is_default = TRUE)::text ||
            ' défauts pour ' || my_category || ' + ' || my_gender as description
        FROM public.vinted_mapping
        GROUP BY my_category, my_gender
        HAVING COUNT(*) FILTER (WHERE is_default = TRUE) > 1

        UNION ALL

        -- 5. vinted_id orphelins (n'existent pas dans vinted_categories)
        SELECT
            'ORPHAN_VINTED_ID' as issue_type,
            vm.vinted_id::text as identifier,
            'vinted_id ' || vm.vinted_id || ' non trouvé dans vinted_categories '
            || '(' || vm.my_category || '/' || vm.my_gender || ')' as description
        FROM public.vinted_mapping vm
        LEFT JOIN public.vinted_categories vc ON vm.vinted_id = vc.id
        WHERE vc.id IS NULL

        UNION ALL

        -- 6. my_category orphelins (n'existent pas dans categories)
        SELECT
            'ORPHAN_MY_CATEGORY' as issue_type,
            vm.my_category as identifier,
            'my_category "' || vm.my_category || '" non trouvé dans categories' as description
        FROM public.vinted_mapping vm
        LEFT JOIN product_attributes.categories c ON vm.my_category = c.name_en
        WHERE c.name_en IS NULL
        GROUP BY vm.my_category

        UNION ALL

        -- 7. Gender incohérent entre vinted_mapping et vinted_categories
        SELECT
            'GENDER_MISMATCH' as issue_type,
            vm.vinted_id::text as identifier,
            'vinted_id ' || vm.vinted_id || ': mapping=' || vm.vinted_gender
            || ', actual=' || vc.gender as description
        FROM public.vinted_mapping vm
        JOIN public.vinted_categories vc ON vm.vinted_id = vc.id
        WHERE vm.vinted_gender <> vc.gender

        UNION ALL

        -- 8. my_gender non autorisé pour la catégorie
        SELECT
            'INVALID_MY_GENDER' as issue_type,
            vm.my_category || ' + ' || vm.my_gender as identifier,
            vm.my_gender || ' non autorisé pour ' || vm.my_category
            || ' (autorisés: ' || array_to_string(c.genders, ', ') || ')' as description
        FROM public.vinted_mapping vm
        JOIN product_attributes.categories c ON vm.my_category = c.name_en
        WHERE NOT (vm.my_gender = ANY(c.genders))
    """))
    print("  ✓ Updated vw_mapping_issues view (uses is_active instead of is_leaf)")

    # Also update mapping_validation view
    conn.execute(text("DROP VIEW IF EXISTS public.mapping_validation"))

    conn.execute(text("""
        CREATE VIEW public.mapping_validation AS

        -- 1. Vinted active categories not mapped
        SELECT
            'VINTED_NOT_MAPPED' as issue,
            vc.id::text as vinted_id,
            vc.title as vinted_title,
            vc.gender as vinted_gender,
            NULL as my_category,
            NULL as my_gender
        FROM public.vinted_categories vc
        LEFT JOIN public.vinted_mapping vm ON vc.id = vm.vinted_id
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
        FROM public.vinted_mapping
        GROUP BY my_category, my_gender
        HAVING SUM(CASE WHEN is_default THEN 1 ELSE 0 END) = 0

        UNION ALL

        -- 3. Expected couples not mapped
        SELECT
            'COUPLE_NOT_MAPPED' as issue,
            NULL as vinted_id,
            NULL as vinted_title,
            NULL as vinted_gender,
            em.my_category,
            em.my_gender
        FROM public.expected_mappings em
        LEFT JOIN public.vinted_mapping vm ON em.my_category = vm.my_category AND em.my_gender = vm.my_gender
        WHERE vm.id IS NULL
    """))
    print("  ✓ Updated mapping_validation view (uses is_active instead of is_leaf)")


def downgrade():
    """
    Restore views to use is_leaf.
    """
    conn = op.get_bind()

    # Restore vw_mapping_issues with is_leaf
    conn.execute(text("DROP VIEW IF EXISTS public.vw_mapping_issues"))

    conn.execute(text("""
        CREATE VIEW public.vw_mapping_issues AS

        SELECT
            'VINTED_NOT_MAPPED' as issue_type,
            vc.id::text as identifier,
            vc.title || ' (' || vc.gender || ')' as description
        FROM public.vinted_categories vc
        LEFT JOIN public.vinted_mapping vm ON vc.id = vm.vinted_id
        WHERE vc.is_leaf = TRUE
        AND vm.id IS NULL

        UNION ALL

        SELECT
            'COUPLE_NOT_MAPPED' as issue_type,
            c.name_en || ' + ' || g.gender as identifier,
            'Aucun mapping pour ' || c.name_en || ' + ' || g.gender as description
        FROM product_attributes.categories c
        CROSS JOIN (VALUES ('men'), ('women'), ('boys'), ('girls')) AS g(gender)
        WHERE g.gender = ANY(c.genders)
        AND c.parent_category IS NOT NULL
        AND c.name_en NOT IN (
            'tops', 'bottoms', 'outerwear', 'dresses-jumpsuits',
            'formalwear', 'sportswear', 'clothing'
        )
        AND NOT EXISTS (
            SELECT 1 FROM public.vinted_mapping vm
            WHERE vm.my_category = c.name_en
            AND vm.my_gender = g.gender
        )

        UNION ALL

        SELECT
            'NO_DEFAULT' as issue_type,
            my_category || ' + ' || my_gender as identifier,
            'Aucun défaut défini' as description
        FROM public.vinted_mapping
        GROUP BY my_category, my_gender
        HAVING COUNT(*) FILTER (WHERE is_default = TRUE) = 0

        UNION ALL

        SELECT
            'MULTIPLE_DEFAULTS' as issue_type,
            my_category || ' + ' || my_gender as identifier,
            COUNT(*) FILTER (WHERE is_default = TRUE)::text || ' défauts' as description
        FROM public.vinted_mapping
        GROUP BY my_category, my_gender
        HAVING COUNT(*) FILTER (WHERE is_default = TRUE) > 1

        UNION ALL

        SELECT
            'ORPHAN_VINTED_ID' as issue_type,
            vm.vinted_id::text as identifier,
            'vinted_id orphelin' as description
        FROM public.vinted_mapping vm
        LEFT JOIN public.vinted_categories vc ON vm.vinted_id = vc.id
        WHERE vc.id IS NULL

        UNION ALL

        SELECT
            'ORPHAN_MY_CATEGORY' as issue_type,
            vm.my_category as identifier,
            'my_category orphelin' as description
        FROM public.vinted_mapping vm
        LEFT JOIN product_attributes.categories c ON vm.my_category = c.name_en
        WHERE c.name_en IS NULL
        GROUP BY vm.my_category

        UNION ALL

        SELECT
            'GENDER_MISMATCH' as issue_type,
            vm.vinted_id::text as identifier,
            'Gender incohérent' as description
        FROM public.vinted_mapping vm
        JOIN public.vinted_categories vc ON vm.vinted_id = vc.id
        WHERE vm.vinted_gender <> vc.gender

        UNION ALL

        SELECT
            'INVALID_MY_GENDER' as issue_type,
            vm.my_category || ' + ' || vm.my_gender as identifier,
            'Gender non autorisé' as description
        FROM public.vinted_mapping vm
        JOIN product_attributes.categories c ON vm.my_category = c.name_en
        WHERE NOT (vm.my_gender = ANY(c.genders))
    """))
    print("  ✓ Restored vw_mapping_issues view (uses is_leaf)")

    # Restore mapping_validation with is_leaf
    conn.execute(text("DROP VIEW IF EXISTS public.mapping_validation"))

    conn.execute(text("""
        CREATE VIEW public.mapping_validation AS

        SELECT
            'VINTED_NOT_MAPPED' as issue,
            vc.id::text as vinted_id,
            vc.title as vinted_title,
            vc.gender as vinted_gender,
            NULL as my_category,
            NULL as my_gender
        FROM public.vinted_categories vc
        LEFT JOIN public.vinted_mapping vm ON vc.id = vm.vinted_id
        WHERE vc.is_leaf = TRUE
        AND vm.id IS NULL

        UNION ALL

        SELECT
            'NO_DEFAULT' as issue,
            NULL as vinted_id,
            NULL as vinted_title,
            NULL as vinted_gender,
            my_category,
            my_gender
        FROM public.vinted_mapping
        GROUP BY my_category, my_gender
        HAVING SUM(CASE WHEN is_default THEN 1 ELSE 0 END) = 0

        UNION ALL

        SELECT
            'COUPLE_NOT_MAPPED' as issue,
            NULL as vinted_id,
            NULL as vinted_title,
            NULL as vinted_gender,
            em.my_category,
            em.my_gender
        FROM public.expected_mappings em
        LEFT JOIN public.vinted_mapping vm ON em.my_category = vm.my_category AND em.my_gender = vm.my_gender
        WHERE vm.id IS NULL
    """))
    print("  ✓ Restored mapping_validation view (uses is_leaf)")
