"""Add 1:1 relationship between Product and VintedProduct

Revision ID: 20251218_1200
Revises: 20251218_1100
Create Date: 2025-12-18 12:00:00.000000

Adds product_id FK to vinted_products table to create a 1:1 relationship
with products. This links Stoflow products to their Vinted counterparts.

Author: Claude
Date: 2025-12-18
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = '20251218_1200'
down_revision = '20251218_1100'
branch_labels = None
depends_on = None


def upgrade():
    """
    Add product_id column to vinted_products for 1:1 relationship.
    """
    conn = op.get_bind()

    # Get all user schemas
    user_schemas = conn.execute(text("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%'
        AND schema_name != 'user_invalid'
        ORDER BY schema_name
    """)).fetchall()

    for (schema_name,) in user_schemas:
        print(f"\n🔄 Processing schema: {schema_name}")

        # Check if vinted_products table exists
        table_exists = conn.execute(text(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = '{schema_name}'
                AND table_name = 'vinted_products'
            )
        """)).scalar()

        if not table_exists:
            print(f"  ⏭️  vinted_products table doesn't exist in {schema_name}, skipping")
            continue

        # Check if product_id column already exists
        column_exists = conn.execute(text(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.columns
                WHERE table_schema = '{schema_name}'
                AND table_name = 'vinted_products'
                AND column_name = 'product_id'
            )
        """)).scalar()

        if column_exists:
            print(f"  ⏭️  product_id column already exists in {schema_name}.vinted_products")
            continue

        # Add product_id column (nullable for existing data)
        conn.execute(text(f"""
            ALTER TABLE {schema_name}.vinted_products
            ADD COLUMN product_id INTEGER
        """))
        print(f"  ✓ Added product_id column to {schema_name}.vinted_products")

        # Add unique constraint (1:1 relationship)
        conn.execute(text(f"""
            ALTER TABLE {schema_name}.vinted_products
            ADD CONSTRAINT uq_{schema_name}_vinted_products_product_id
            UNIQUE (product_id)
        """))
        print(f"  ✓ Added unique constraint on product_id")

        # Add foreign key constraint to products table in same schema
        # Check if products table exists first
        products_exists = conn.execute(text(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = '{schema_name}'
                AND table_name = 'products'
            )
        """)).scalar()

        if products_exists:
            conn.execute(text(f"""
                ALTER TABLE {schema_name}.vinted_products
                ADD CONSTRAINT fk_{schema_name}_vinted_products_product_id
                FOREIGN KEY (product_id)
                REFERENCES {schema_name}.products (id)
                ON DELETE SET NULL
                ON UPDATE CASCADE
            """))
            print(f"  ✓ Added FK constraint to {schema_name}.products")
        else:
            print(f"  ⚠️  products table doesn't exist in {schema_name}, FK not added")

        # Create index for faster lookups
        conn.execute(text(f"""
            CREATE INDEX IF NOT EXISTS idx_{schema_name}_vinted_products_product_id
            ON {schema_name}.vinted_products (product_id)
            WHERE product_id IS NOT NULL
        """))
        print(f"  ✓ Created index on product_id")

    # Also process template_tenant for new users
    print(f"\n🔄 Processing template_tenant")
    template_table_exists = conn.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'template_tenant'
            AND table_name = 'vinted_products'
        )
    """)).scalar()

    if template_table_exists:
        template_column_exists = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns
                WHERE table_schema = 'template_tenant'
                AND table_name = 'vinted_products'
                AND column_name = 'product_id'
            )
        """)).scalar()

        if not template_column_exists:
            conn.execute(text("""
                ALTER TABLE template_tenant.vinted_products
                ADD COLUMN product_id INTEGER
            """))
            conn.execute(text("""
                ALTER TABLE template_tenant.vinted_products
                ADD CONSTRAINT uq_template_vinted_products_product_id
                UNIQUE (product_id)
            """))
            conn.execute(text("""
                ALTER TABLE template_tenant.vinted_products
                ADD CONSTRAINT fk_template_vinted_products_product_id
                FOREIGN KEY (product_id)
                REFERENCES template_tenant.products (id)
                ON DELETE SET NULL
                ON UPDATE CASCADE
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_template_vinted_products_product_id
                ON template_tenant.vinted_products (product_id)
                WHERE product_id IS NOT NULL
            """))
            print(f"  ✓ Added product_id to template_tenant.vinted_products")
        else:
            print(f"  ⏭️  product_id already exists in template_tenant.vinted_products")
    else:
        print(f"  ⏭️  template_tenant.vinted_products doesn't exist")

    print("\n=== Migration complete ===")


def downgrade():
    """
    Remove product_id column from vinted_products.
    """
    conn = op.get_bind()

    # Get all user schemas + template_tenant
    schemas = conn.execute(text("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE (schema_name LIKE 'user_%' OR schema_name = 'template_tenant')
        AND schema_name != 'user_invalid'
        ORDER BY schema_name
    """)).fetchall()

    for (schema_name,) in schemas:
        # Check if column exists
        column_exists = conn.execute(text(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.columns
                WHERE table_schema = '{schema_name}'
                AND table_name = 'vinted_products'
                AND column_name = 'product_id'
            )
        """)).scalar()

        if column_exists:
            # Drop FK constraint first (if exists)
            try:
                fk_name = f"fk_{schema_name}_vinted_products_product_id"
                if schema_name == 'template_tenant':
                    fk_name = "fk_template_vinted_products_product_id"
                conn.execute(text(f"""
                    ALTER TABLE {schema_name}.vinted_products
                    DROP CONSTRAINT IF EXISTS {fk_name}
                """))
            except Exception:
                pass

            # Drop unique constraint
            try:
                uq_name = f"uq_{schema_name}_vinted_products_product_id"
                if schema_name == 'template_tenant':
                    uq_name = "uq_template_vinted_products_product_id"
                conn.execute(text(f"""
                    ALTER TABLE {schema_name}.vinted_products
                    DROP CONSTRAINT IF EXISTS {uq_name}
                """))
            except Exception:
                pass

            # Drop index
            try:
                idx_name = f"idx_{schema_name}_vinted_products_product_id"
                if schema_name == 'template_tenant':
                    idx_name = "idx_template_vinted_products_product_id"
                conn.execute(text(f"""
                    DROP INDEX IF EXISTS {schema_name}.{idx_name}
                """))
            except Exception:
                pass

            # Drop column
            conn.execute(text(f"""
                ALTER TABLE {schema_name}.vinted_products
                DROP COLUMN product_id
            """))
            print(f"  ✓ Removed product_id from {schema_name}.vinted_products")
        else:
            print(f"  ⏭️  product_id doesn't exist in {schema_name}.vinted_products")
