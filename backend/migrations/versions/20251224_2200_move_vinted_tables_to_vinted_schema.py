"""Move Vinted tables from public to vinted schema

Revision ID: 20251224_2200
Revises: 20251224_2100
Create Date: 2024-12-24 22:00:00

This migration:
1. Creates the 'vinted' schema
2. Moves 6 tables from public to vinted schema:
   - vinted_action_types
   - vinted_categories
   - vinted_mapping
   - vinted_orders
   - vinted_order_products
   - vinted_deletions
3. Moves the get_vinted_category function to vinted schema
4. Updates foreign keys from template_tenant and user schemas
5. Recreates views with correct schema references

Author: Claude
Date: 2025-12-24
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic
revision = "20251224_2200"
down_revision = "20251224_2100"
branch_labels = None
depends_on = None


# Tables to move from public to vinted schema
TABLES_TO_MOVE = [
    "vinted_action_types",
    "vinted_categories",
    "vinted_mapping",
    "vinted_orders",
    "vinted_order_products",
    "vinted_deletions",
]


def upgrade() -> None:
    """Move Vinted tables to vinted schema."""
    conn = op.get_bind()

    # =========================================================================
    # 1. CREATE VINTED SCHEMA
    # =========================================================================
    print("  📦 Creating vinted schema...")
    conn.execute(text("CREATE SCHEMA IF NOT EXISTS vinted"))
    print("  ✅ Created vinted schema")

    # =========================================================================
    # 2. DROP VIEWS THAT REFERENCE THESE TABLES
    # =========================================================================
    print("  📦 Dropping dependent views...")
    conn.execute(text("DROP VIEW IF EXISTS public.vw_mapping_issues CASCADE"))
    conn.execute(text("DROP VIEW IF EXISTS public.mapping_validation CASCADE"))
    print("  ✅ Dropped dependent views")

    # =========================================================================
    # 3. DROP FOREIGN KEYS THAT REFERENCE THESE TABLES
    # =========================================================================
    print("  📦 Dropping foreign keys...")

    # FK from vinted_mapping to vinted_categories
    conn.execute(text("""
        ALTER TABLE public.vinted_mapping
        DROP CONSTRAINT IF EXISTS vinted_mapping_vinted_id_fkey
    """))

    # FK from vinted_order_products to vinted_orders
    conn.execute(text("""
        ALTER TABLE public.vinted_order_products
        DROP CONSTRAINT IF EXISTS vinted_order_products_transaction_id_fkey
    """))

    # FK from vinted_categories to itself (parent)
    conn.execute(text("""
        ALTER TABLE public.vinted_categories
        DROP CONSTRAINT IF EXISTS fk_vinted_categories_parent
    """))

    # FK from template_tenant.vinted_jobs to vinted_action_types
    conn.execute(text("""
        ALTER TABLE template_tenant.vinted_jobs
        DROP CONSTRAINT IF EXISTS vinted_jobs_action_type_id_fkey
    """))

    # FK from template_tenant.vinted_job_stats to vinted_action_types
    conn.execute(text("""
        ALTER TABLE template_tenant.vinted_job_stats
        DROP CONSTRAINT IF EXISTS vinted_job_stats_action_type_id_fkey
    """))

    # Drop FK from all user schemas
    result = conn.execute(text("""
        SELECT schema_name FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%'
    """))
    user_schemas = [row[0] for row in result]

    for schema in user_schemas:
        conn.execute(text(f"""
            ALTER TABLE {schema}.vinted_jobs
            DROP CONSTRAINT IF EXISTS vinted_jobs_action_type_id_fkey
        """))
        conn.execute(text(f"""
            ALTER TABLE {schema}.vinted_job_stats
            DROP CONSTRAINT IF EXISTS vinted_job_stats_action_type_id_fkey
        """))

    print("  ✅ Dropped all foreign keys")

    # =========================================================================
    # 4. MOVE TABLES TO VINTED SCHEMA
    # =========================================================================
    print("  📦 Moving tables to vinted schema...")
    for table in TABLES_TO_MOVE:
        conn.execute(text(f"ALTER TABLE public.{table} SET SCHEMA vinted"))
        print(f"    ✓ Moved {table}")
    print("  ✅ All tables moved")

    # =========================================================================
    # 5. RECREATE FOREIGN KEYS WITH NEW SCHEMA
    # =========================================================================
    print("  📦 Recreating foreign keys...")

    # FK from vinted.vinted_categories to itself (parent)
    conn.execute(text("""
        ALTER TABLE vinted.vinted_categories
        ADD CONSTRAINT fk_vinted_categories_parent
        FOREIGN KEY (parent_id) REFERENCES vinted.vinted_categories(id)
        ON DELETE CASCADE
    """))

    # FK from vinted.vinted_mapping to vinted.vinted_categories
    conn.execute(text("""
        ALTER TABLE vinted.vinted_mapping
        ADD CONSTRAINT vinted_mapping_vinted_id_fkey
        FOREIGN KEY (vinted_id) REFERENCES vinted.vinted_categories(id)
    """))

    # FK from vinted.vinted_order_products to vinted.vinted_orders
    conn.execute(text("""
        ALTER TABLE vinted.vinted_order_products
        ADD CONSTRAINT vinted_order_products_transaction_id_fkey
        FOREIGN KEY (transaction_id) REFERENCES vinted.vinted_orders(transaction_id)
        ON DELETE CASCADE
    """))

    # FK from template_tenant to vinted schema
    conn.execute(text("""
        ALTER TABLE template_tenant.vinted_jobs
        ADD CONSTRAINT vinted_jobs_action_type_id_fkey
        FOREIGN KEY (action_type_id) REFERENCES vinted.vinted_action_types(id)
    """))
    conn.execute(text("""
        ALTER TABLE template_tenant.vinted_job_stats
        ADD CONSTRAINT vinted_job_stats_action_type_id_fkey
        FOREIGN KEY (action_type_id) REFERENCES vinted.vinted_action_types(id)
    """))

    # FK from user schemas to vinted schema
    for schema in user_schemas:
        conn.execute(text(f"""
            ALTER TABLE {schema}.vinted_jobs
            ADD CONSTRAINT vinted_jobs_action_type_id_fkey
            FOREIGN KEY (action_type_id) REFERENCES vinted.vinted_action_types(id)
        """))
        conn.execute(text(f"""
            ALTER TABLE {schema}.vinted_job_stats
            ADD CONSTRAINT vinted_job_stats_action_type_id_fkey
            FOREIGN KEY (action_type_id) REFERENCES vinted.vinted_action_types(id)
        """))

    print("  ✅ All foreign keys recreated")

    # =========================================================================
    # 6. MOVE get_vinted_category FUNCTION TO VINTED SCHEMA
    # =========================================================================
    print("  📦 Moving get_vinted_category function...")

    # Get function definition
    result = conn.execute(text("""
        SELECT pg_get_functiondef(oid)
        FROM pg_proc
        WHERE proname = 'get_vinted_category'
        AND pronamespace = 'public'::regnamespace
    """))
    func_def = result.scalar()

    if func_def:
        # Drop old function
        conn.execute(text("DROP FUNCTION IF EXISTS public.get_vinted_category"))

        # Recreate in vinted schema with updated references
        new_func = func_def.replace(
            "public.get_vinted_category",
            "vinted.get_vinted_category"
        ).replace(
            "FROM vinted_mapping",
            "FROM vinted.vinted_mapping"
        ).replace(
            "FROM vinted_categories",
            "FROM vinted.vinted_categories"
        ).replace(
            "JOIN vinted_mapping",
            "JOIN vinted.vinted_mapping"
        ).replace(
            "JOIN vinted_categories",
            "JOIN vinted.vinted_categories"
        )
        conn.execute(text(new_func))
        print("  ✅ Moved get_vinted_category function")
    else:
        print("  ⚠️  get_vinted_category function not found, skipping")

    # =========================================================================
    # 7. RECREATE VIEWS WITH VINTED SCHEMA REFERENCES
    # =========================================================================
    print("  📦 Recreating views...")

    # Recreate vw_mapping_issues
    conn.execute(text("""
        CREATE OR REPLACE VIEW public.vw_mapping_issues AS
        -- VINTED_NOT_MAPPED: Catégories Vinted actives sans mapping
        SELECT
            'VINTED_NOT_MAPPED'::text AS issue_type,
            vc.id::text AS identifier,
            vc.title || ' (' || vc.gender || ')' AS description
        FROM vinted.vinted_categories vc
        LEFT JOIN vinted.vinted_mapping vm ON vc.id = vm.vinted_id
        WHERE vc.is_active = true AND vm.id IS NULL

        UNION ALL

        -- COUPLE_NOT_MAPPED: Paires category+gender sans mapping
        SELECT
            'COUPLE_NOT_MAPPED'::text AS issue_type,
            c.name_en || ' + ' || g.gender AS identifier,
            'Aucun mapping pour ' || c.name_en || ' + ' || g.gender AS description
        FROM product_attributes.categories c
        CROSS JOIN (VALUES ('men'), ('women'), ('boys'), ('girls')) AS g(gender)
        WHERE g.gender = ANY(c.genders::text[])
        AND c.parent_category IS NOT NULL
        AND c.name_en NOT IN ('tops', 'bottoms', 'outerwear', 'dresses-jumpsuits', 'formalwear', 'sportswear', 'clothing')
        AND NOT EXISTS (
            SELECT 1 FROM vinted.vinted_mapping vm
            WHERE vm.my_category = c.name_en AND vm.my_gender = g.gender
        )

        UNION ALL

        -- NO_DEFAULT: Groupes sans mapping par défaut
        SELECT
            'NO_DEFAULT'::text AS issue_type,
            my_category || ' + ' || my_gender AS identifier,
            'Aucun défaut défini pour ' || my_category || ' + ' || my_gender AS description
        FROM vinted.vinted_mapping
        GROUP BY my_category, my_gender
        HAVING COUNT(*) FILTER (WHERE is_default = true) = 0

        UNION ALL

        -- MULTIPLE_DEFAULTS: Groupes avec plusieurs défauts
        SELECT
            'MULTIPLE_DEFAULTS'::text AS issue_type,
            my_category || ' + ' || my_gender AS identifier,
            COUNT(*) FILTER (WHERE is_default = true)::text || ' défauts pour ' || my_category || ' + ' || my_gender AS description
        FROM vinted.vinted_mapping
        GROUP BY my_category, my_gender
        HAVING COUNT(*) FILTER (WHERE is_default = true) > 1

        UNION ALL

        -- ORPHAN_VINTED_ID: vinted_id non trouvé dans vinted_categories
        SELECT
            'ORPHAN_VINTED_ID'::text AS issue_type,
            vm.vinted_id::text AS identifier,
            'vinted_id ' || vm.vinted_id || ' non trouvé dans vinted_categories (' || vm.my_category || '/' || vm.my_gender || ')' AS description
        FROM vinted.vinted_mapping vm
        LEFT JOIN vinted.vinted_categories vc ON vm.vinted_id = vc.id
        WHERE vc.id IS NULL

        UNION ALL

        -- ORPHAN_MY_CATEGORY: my_category non trouvé dans categories
        SELECT
            'ORPHAN_MY_CATEGORY'::text AS issue_type,
            vm.my_category AS identifier,
            'my_category "' || vm.my_category || '" non trouvé dans categories' AS description
        FROM vinted.vinted_mapping vm
        LEFT JOIN product_attributes.categories c ON vm.my_category = c.name_en
        WHERE c.name_en IS NULL
        GROUP BY vm.my_category

        UNION ALL

        -- GENDER_MISMATCH: vinted_gender ne correspond pas au genre de la catégorie Vinted
        SELECT
            'GENDER_MISMATCH'::text AS issue_type,
            vm.vinted_id::text AS identifier,
            'vinted_id ' || vm.vinted_id || ': mapping=' || vm.vinted_gender || ', actual=' || vc.gender AS description
        FROM vinted.vinted_mapping vm
        JOIN vinted.vinted_categories vc ON vm.vinted_id = vc.id
        WHERE vm.vinted_gender <> vc.gender

        UNION ALL

        -- INVALID_MY_GENDER: my_gender non autorisé pour cette catégorie
        SELECT
            'INVALID_MY_GENDER'::text AS issue_type,
            vm.my_category || ' + ' || vm.my_gender AS identifier,
            vm.my_gender || ' non autorisé pour ' || vm.my_category || ' (autorisés: ' || array_to_string(c.genders, ', ') || ')' AS description
        FROM vinted.vinted_mapping vm
        JOIN product_attributes.categories c ON vm.my_category = c.name_en
        WHERE NOT (vm.my_gender = ANY(c.genders::text[]))
    """))
    print("  ✅ Recreated vw_mapping_issues view")

    # Summary
    print(f"\n  🎉 Successfully moved {len(TABLES_TO_MOVE)} tables to vinted schema")


def downgrade() -> None:
    """Move Vinted tables back to public schema."""
    conn = op.get_bind()

    print("  📦 Moving tables back to public schema...")

    # Drop views
    conn.execute(text("DROP VIEW IF EXISTS public.vw_mapping_issues CASCADE"))

    # Drop FKs from tenant schemas to vinted schema
    result = conn.execute(text("""
        SELECT schema_name FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%' OR schema_name = 'template_tenant'
    """))
    schemas = [row[0] for row in result]

    for schema in schemas:
        conn.execute(text(f"""
            ALTER TABLE {schema}.vinted_jobs
            DROP CONSTRAINT IF EXISTS vinted_jobs_action_type_id_fkey
        """))
        conn.execute(text(f"""
            ALTER TABLE {schema}.vinted_job_stats
            DROP CONSTRAINT IF EXISTS vinted_job_stats_action_type_id_fkey
        """))

    # Drop internal FKs
    conn.execute(text("""
        ALTER TABLE vinted.vinted_mapping
        DROP CONSTRAINT IF EXISTS vinted_mapping_vinted_id_fkey
    """))
    conn.execute(text("""
        ALTER TABLE vinted.vinted_order_products
        DROP CONSTRAINT IF EXISTS vinted_order_products_transaction_id_fkey
    """))
    conn.execute(text("""
        ALTER TABLE vinted.vinted_categories
        DROP CONSTRAINT IF EXISTS fk_vinted_categories_parent
    """))

    # Move tables back
    for table in TABLES_TO_MOVE:
        conn.execute(text(f"ALTER TABLE vinted.{table} SET SCHEMA public"))
        print(f"    ✓ Moved {table} back to public")

    # Recreate FKs in public schema
    conn.execute(text("""
        ALTER TABLE public.vinted_categories
        ADD CONSTRAINT fk_vinted_categories_parent
        FOREIGN KEY (parent_id) REFERENCES public.vinted_categories(id)
        ON DELETE CASCADE
    """))
    conn.execute(text("""
        ALTER TABLE public.vinted_mapping
        ADD CONSTRAINT vinted_mapping_vinted_id_fkey
        FOREIGN KEY (vinted_id) REFERENCES public.vinted_categories(id)
    """))
    conn.execute(text("""
        ALTER TABLE public.vinted_order_products
        ADD CONSTRAINT vinted_order_products_transaction_id_fkey
        FOREIGN KEY (transaction_id) REFERENCES public.vinted_orders(transaction_id)
        ON DELETE CASCADE
    """))

    # Recreate FKs from tenant schemas
    for schema in schemas:
        conn.execute(text(f"""
            ALTER TABLE {schema}.vinted_jobs
            ADD CONSTRAINT vinted_jobs_action_type_id_fkey
            FOREIGN KEY (action_type_id) REFERENCES public.vinted_action_types(id)
        """))
        conn.execute(text(f"""
            ALTER TABLE {schema}.vinted_job_stats
            ADD CONSTRAINT vinted_job_stats_action_type_id_fkey
            FOREIGN KEY (action_type_id) REFERENCES public.vinted_action_types(id)
        """))

    # Drop vinted schema
    conn.execute(text("DROP SCHEMA IF EXISTS vinted"))

    print("  ✅ Tables moved back to public schema")
