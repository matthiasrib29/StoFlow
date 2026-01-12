"""Create vw_mapping_issues view for monitoring

Revision ID: 20251217_1800
Revises: 20251217_1700
Create Date: 2025-12-17 18:00:00.000000

Creates a comprehensive view to detect all mapping issues in real-time.

Author: Claude
Date: 2025-12-17
"""
from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = '20251217_1800'
down_revision = '20251217_1700'
branch_labels = None
depends_on = None


def upgrade():
    """
    Create vw_mapping_issues view for monitoring.
    """
    conn = op.get_bind()

    # Drop view if exists
    conn.execute(text("DROP VIEW IF EXISTS public.vw_mapping_issues"))

    conn.execute(text("""
        CREATE VIEW public.vw_mapping_issues AS

        -- 1. Catégories Vinted (feuilles) non mappées
        SELECT
            'VINTED_NOT_MAPPED' as issue_type,
            vc.id::text as identifier,
            vc.title || ' (' || vc.gender || ')' as description
        FROM public.vinted_categories vc
        LEFT JOIN public.vinted_mapping vm ON vc.id = vm.vinted_id
        WHERE vc.is_leaf = TRUE
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
        WHERE vm.vinted_gender != vc.gender

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
    print("  ✓ Created vw_mapping_issues view")


def downgrade():
    """
    Drop vw_mapping_issues view.
    """
    conn = op.get_bind()
    conn.execute(text("DROP VIEW IF EXISTS public.vw_mapping_issues"))
    print("  ✓ Dropped vw_mapping_issues view")
