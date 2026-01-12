"""Simplify vinted_mapping and add attribute FKs

Revision ID: 20251217_1700
Revises: 20251217_1600
Create Date: 2025-12-17 17:00:00.000000

Changes:
- Remove redundant 'priority' column (is_default + attribute scoring is sufficient)
- Add FK constraints on attribute columns (my_fit, my_length, my_rise, my_material, my_pattern, my_neckline, my_sleeve_length)
- Update get_vinted_category function to remove priority from ORDER BY

Author: Claude
Date: 2025-12-17
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = '20251217_1700'
down_revision = '20251217_1600'
branch_labels = None
depends_on = None


def upgrade():
    """
    Simplify vinted_mapping and add FKs.
    """
    conn = op.get_bind()

    # =========================================================================
    # Step 1: Drop priority column (redundant - is_default + scoring is enough)
    # =========================================================================
    column_exists = conn.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name = 'vinted_mapping'
            AND column_name = 'priority'
        )
    """)).scalar()

    if column_exists:
        op.drop_column('vinted_mapping', 'priority', schema='public')
        print("  ✓ Dropped priority column from vinted_mapping")
    else:
        print("  ⏭️  priority column doesn't exist, skipping")

    # =========================================================================
    # Step 2: Add FK constraints on attribute columns
    # =========================================================================
    fk_definitions = [
        ('my_fit', 'product_attributes.fits', 'name_en', 'fk_vinted_mapping_fit'),
        ('my_length', 'product_attributes.lengths', 'name_en', 'fk_vinted_mapping_length'),
        ('my_rise', 'product_attributes.rises', 'name_en', 'fk_vinted_mapping_rise'),
        ('my_material', 'product_attributes.materials', 'name_en', 'fk_vinted_mapping_material'),
        ('my_pattern', 'product_attributes.patterns', 'name_en', 'fk_vinted_mapping_pattern'),
        ('my_neckline', 'product_attributes.necklines', 'name_en', 'fk_vinted_mapping_neckline'),
        ('my_sleeve_length', 'product_attributes.sleeve_lengths', 'name_en', 'fk_vinted_mapping_sleeve_length'),
    ]

    for col, ref_table, ref_col, fk_name in fk_definitions:
        # Check if FK already exists
        fk_exists = conn.execute(text(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_schema = 'public'
                AND tc.table_name = 'vinted_mapping'
                AND kcu.column_name = '{col}'
            )
        """)).scalar()

        if fk_exists:
            print(f"  ⏭️  FK on {col} already exists, skipping")
        else:
            op.create_foreign_key(
                fk_name,
                'vinted_mapping',
                ref_table.split('.')[1],  # Table name without schema
                [col],
                [ref_col],
                source_schema='public',
                referent_schema='product_attributes',
                onupdate='CASCADE',
                ondelete='SET NULL'
            )
            print(f"  ✓ Added FK on {col} -> {ref_table}.{ref_col}")

    # =========================================================================
    # Step 3: Update get_vinted_category function (remove priority)
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
            -- Score based on matching attributes (higher = better match)
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
    print("  ✓ Updated get_vinted_category function (removed priority)")


def downgrade():
    """
    Restore priority column and remove FKs.
    """
    conn = op.get_bind()

    # =========================================================================
    # Step 1: Drop FK constraints
    # =========================================================================
    fk_names = [
        'fk_vinted_mapping_fit',
        'fk_vinted_mapping_length',
        'fk_vinted_mapping_rise',
        'fk_vinted_mapping_material',
        'fk_vinted_mapping_pattern',
        'fk_vinted_mapping_neckline',
        'fk_vinted_mapping_sleeve_length',
    ]

    for fk_name in fk_names:
        # Check if FK exists
        fk_exists = conn.execute(text(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.table_constraints
                WHERE constraint_type = 'FOREIGN KEY'
                AND constraint_name = '{fk_name}'
                AND table_schema = 'public'
            )
        """)).scalar()

        if fk_exists:
            op.drop_constraint(fk_name, 'vinted_mapping', schema='public', type_='foreignkey')
            print(f"  ✓ Dropped FK {fk_name}")
        else:
            print(f"  ⏭️  FK {fk_name} doesn't exist, skipping")

    # =========================================================================
    # Step 2: Restore priority column
    # =========================================================================
    column_exists = conn.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name = 'vinted_mapping'
            AND column_name = 'priority'
        )
    """)).scalar()

    if column_exists:
        print("  ⏭️  priority column already exists, skipping")
    else:
        op.add_column(
            'vinted_mapping',
            sa.Column('priority', sa.Integer(), server_default='0', nullable=False),
            schema='public'
        )
        print("  ✓ Restored priority column")

    # =========================================================================
    # Step 3: Restore get_vinted_category function with priority
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
    print("  ✓ Restored get_vinted_category function with priority")
