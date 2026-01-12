"""Create vinted_mapping system

Revision ID: 20251217_1500
Revises: 20251217_1400
Create Date: 2025-12-17 15:00:00.000000

Creates the bidirectional mapping system between our categories and Vinted categories:
- vinted_mapping: Main mapping table with attributes
- expected_mappings: Expected category/gender combinations
- mapping_validation: View to detect mapping issues
- get_vinted_category: Function to resolve category with attribute matching

Author: Claude
Date: 2025-12-17
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = '20251217_1500'
down_revision = '20251217_1400'
branch_labels = None
depends_on = None


def upgrade():
    """
    Create vinted_mapping system.
    """
    conn = op.get_bind()

    # =========================================================================
    # Step 2: Create vinted_mapping table
    # =========================================================================
    table_exists = conn.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = 'vinted_mapping'
        )
    """)).scalar()

    if table_exists:
        print("  ⏭️  vinted_mapping table already exists, skipping")
    else:
        op.create_table(
            'vinted_mapping',
            sa.Column('id', sa.Integer(), primary_key=True),
            # Vinted side
            sa.Column('vinted_id', sa.Integer(), sa.ForeignKey('public.vinted_categories.id'), nullable=False),
            sa.Column('vinted_gender', sa.String(20), nullable=False),
            # My App side
            sa.Column('my_category', sa.String(100), sa.ForeignKey('product_attributes.categories.name_en'), nullable=False),
            sa.Column('my_gender', sa.String(20), nullable=False),
            sa.Column('my_fit', sa.String(50), nullable=True),
            sa.Column('my_length', sa.String(50), nullable=True),
            sa.Column('my_rise', sa.String(50), nullable=True),
            sa.Column('my_material', sa.String(50), nullable=True),
            sa.Column('my_pattern', sa.String(50), nullable=True),
            sa.Column('my_neckline', sa.String(50), nullable=True),
            sa.Column('my_sleeve_length', sa.String(50), nullable=True),
            # For My App → Vinted direction
            sa.Column('is_default', sa.Boolean(), server_default='false', nullable=False),
            sa.Column('priority', sa.Integer(), server_default='0', nullable=False),
            # Note: No UNIQUE on vinted_id - same Vinted category can map to different my_gender
            schema='public'
        )

        # Create indexes
        op.create_index('idx_vinted_mapping_vinted', 'vinted_mapping', ['vinted_id'], schema='public')
        op.create_index('idx_vinted_mapping_my', 'vinted_mapping', ['my_category', 'my_gender'], schema='public')
        op.create_index('idx_vinted_mapping_default', 'vinted_mapping', ['my_category', 'my_gender', 'is_default'], schema='public')

        print("  ✓ Created vinted_mapping table with indexes")

    # =========================================================================
    # Step 3: Create expected_mappings table
    # =========================================================================
    table_exists = conn.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = 'expected_mappings'
        )
    """)).scalar()

    if table_exists:
        print("  ⏭️  expected_mappings table already exists, skipping")
    else:
        op.create_table(
            'expected_mappings',
            sa.Column('my_category', sa.String(100), sa.ForeignKey('product_attributes.categories.name_en'), nullable=False),
            sa.Column('my_gender', sa.String(20), nullable=False),
            sa.PrimaryKeyConstraint('my_category', 'my_gender'),
            schema='public'
        )
        print("  ✓ Created expected_mappings table")

        # Populate from categories.genders
        conn.execute(text("""
            INSERT INTO public.expected_mappings (my_category, my_gender)
            SELECT c.name_en, g.gender
            FROM product_attributes.categories c
            CROSS JOIN (VALUES ('men'), ('women'), ('boys'), ('girls')) AS g(gender)
            WHERE g.gender = ANY(c.genders)
            AND c.parent_category IS NOT NULL
            AND c.name_en NOT IN ('tops', 'bottoms', 'outerwear', 'dresses-jumpsuits', 'formalwear', 'sportswear')
            ON CONFLICT DO NOTHING
        """))
        print("  ✓ Populated expected_mappings from categories.genders")

    # =========================================================================
    # Step 4: Create mapping_validation view
    # =========================================================================
    view_exists = conn.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.views
            WHERE table_schema = 'public'
            AND table_name = 'mapping_validation'
        )
    """)).scalar()

    if view_exists:
        conn.execute(text("DROP VIEW IF EXISTS public.mapping_validation"))
        print("  ⏭️  Dropped existing mapping_validation view")

    conn.execute(text("""
        CREATE VIEW public.mapping_validation AS

        -- 1. Vinted leaf categories not mapped
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
    print("  ✓ Created mapping_validation view")

    # =========================================================================
    # Step 5: Create get_vinted_category function
    # =========================================================================
    conn.execute(text("DROP FUNCTION IF EXISTS public.get_vinted_category"))

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
            -- Try to find best match with attributes
            SELECT vinted_id INTO v_result
            FROM public.vinted_mapping
            WHERE my_category = p_category
              AND my_gender = p_gender
              AND (p_fit IS NULL OR my_fit IS NULL OR my_fit = p_fit)
              AND (p_length IS NULL OR my_length IS NULL OR my_length = p_length)
              AND (p_rise IS NULL OR my_rise IS NULL OR my_rise = p_rise)
              AND (p_material IS NULL OR my_material IS NULL OR my_material = p_material)
              AND (p_pattern IS NULL OR my_pattern IS NULL OR my_pattern = p_pattern)
              AND (p_neckline IS NULL OR my_neckline IS NULL OR my_neckline = p_neckline)
              AND (p_sleeve_length IS NULL OR my_sleeve_length IS NULL OR my_sleeve_length = p_sleeve_length)
            ORDER BY
                (CASE WHEN my_fit = p_fit THEN 10 ELSE 0 END) +
                (CASE WHEN my_length = p_length THEN 10 ELSE 0 END) +
                (CASE WHEN my_rise = p_rise THEN 10 ELSE 0 END) +
                (CASE WHEN my_material = p_material THEN 5 ELSE 0 END) +
                (CASE WHEN my_pattern = p_pattern THEN 3 ELSE 0 END) +
                (CASE WHEN my_neckline = p_neckline THEN 3 ELSE 0 END) +
                (CASE WHEN my_sleeve_length = p_sleeve_length THEN 2 ELSE 0 END) +
                priority DESC,
                is_default DESC
            LIMIT 1;

            -- Fallback to default if no specific match
            IF v_result IS NULL THEN
                SELECT vinted_id INTO v_result
                FROM public.vinted_mapping
                WHERE my_category = p_category
                  AND my_gender = p_gender
                  AND is_default = TRUE
                LIMIT 1;
            END IF;

            RETURN v_result;
        END;
        $$ LANGUAGE plpgsql
    """))
    print("  ✓ Created get_vinted_category function")


def downgrade():
    """
    Remove vinted_mapping system.
    """
    conn = op.get_bind()

    # Drop function
    conn.execute(text("DROP FUNCTION IF EXISTS public.get_vinted_category"))
    print("  ✓ Dropped get_vinted_category function")

    # Drop view
    conn.execute(text("DROP VIEW IF EXISTS public.mapping_validation"))
    print("  ✓ Dropped mapping_validation view")

    # Drop expected_mappings table
    table_exists = conn.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = 'expected_mappings'
        )
    """)).scalar()
    if table_exists:
        op.drop_table('expected_mappings', schema='public')
        print("  ✓ Dropped expected_mappings table")

    # Drop vinted_mapping table
    table_exists = conn.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = 'vinted_mapping'
        )
    """)).scalar()
    if table_exists:
        op.drop_index('idx_vinted_mapping_default', table_name='vinted_mapping', schema='public')
        op.drop_index('idx_vinted_mapping_my', table_name='vinted_mapping', schema='public')
        op.drop_index('idx_vinted_mapping_vinted', table_name='vinted_mapping', schema='public')
        op.drop_table('vinted_mapping', schema='public')
        print("  ✓ Dropped vinted_mapping table")
