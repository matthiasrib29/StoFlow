"""Fix size FK to reference sizes.name_en instead of sizes.name

Revision ID: 20251222_1200
Revises: 9a0b65decb46
Create Date: 2025-12-22 12:00:00

The previous migrations (20251218_2300, 20251218_2400) incorrectly looked for
product_attributes.sizes.name, but the table uses name_en as the primary key.

This migration:
1. Adds FK constraint on products.size -> sizes.name_en for template_tenant
2. Adds FK constraint on products.size -> sizes.name_en for all user_X schemas

Note: Any values in products.size that don't exist in sizes.name_en will be
set to NULL before adding the FK constraint.
"""
from alembic import op
import sqlalchemy as sa


revision = '20251222_1200'
down_revision = '9a0b65decb46'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # Check if sizes table with name_en column exists
    sizes_exists = conn.execute(sa.text('''
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'product_attributes'
            AND table_name = 'sizes'
            AND column_name = 'name_en'
        )
    ''')).scalar()

    if not sizes_exists:
        print("⏭️  product_attributes.sizes.name_en does not exist, skipping")
        return

    # Get valid sizes
    valid_sizes = set()
    result = conn.execute(sa.text('SELECT name_en FROM product_attributes.sizes'))
    for row in result:
        if row[0]:
            valid_sizes.add(row[0])

    print(f"📏 Found {len(valid_sizes)} valid sizes in reference table")

    # Process template_tenant
    template_exists = conn.execute(sa.text('''
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'template_tenant' AND table_name = 'products'
        )
    ''')).scalar()

    if template_exists:
        # Check if size column exists
        size_col_exists = conn.execute(sa.text('''
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'template_tenant'
                AND table_name = 'products'
                AND column_name = 'size'
            )
        ''')).scalar()

        if size_col_exists:
            # Check if FK already exists
            fk_exists = conn.execute(sa.text('''
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND tc.table_schema = 'template_tenant'
                    AND tc.table_name = 'products'
                    AND kcu.column_name = 'size'
                )
            ''')).scalar()

            if fk_exists:
                print("⏭️  template_tenant: FK on size already exists, skipping")
            else:
                # Nullify invalid values
                result = conn.execute(sa.text('''
                    UPDATE template_tenant.products
                    SET size = NULL
                    WHERE size IS NOT NULL
                    AND size NOT IN (SELECT name_en FROM product_attributes.sizes)
                '''))
                if result.rowcount > 0:
                    print(f"  ⚠️ Nullified {result.rowcount} invalid size values in template_tenant")

                # Add FK
                conn.execute(sa.text('''
                    ALTER TABLE template_tenant.products
                    ADD CONSTRAINT fk_template_tenant_products_size
                    FOREIGN KEY (size)
                    REFERENCES product_attributes.sizes(name_en)
                    ON DELETE SET NULL
                '''))
                print("  ✓ Added FK on template_tenant.products.size -> sizes.name_en")

    # Process user schemas
    result = conn.execute(sa.text('''
        SELECT schema_name FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%' AND schema_name != 'user_invalid'
    '''))
    user_schemas = [row[0] for row in result]

    for schema in user_schemas:
        table_exists = conn.execute(sa.text(f'''
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = '{schema}' AND table_name = 'products'
            )
        ''')).scalar()

        if not table_exists:
            continue

        size_col_exists = conn.execute(sa.text(f'''
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = '{schema}'
                AND table_name = 'products'
                AND column_name = 'size'
            )
        ''')).scalar()

        if not size_col_exists:
            continue

        fk_exists = conn.execute(sa.text(f'''
            SELECT EXISTS (
                SELECT 1 FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_schema = '{schema}'
                AND tc.table_name = 'products'
                AND kcu.column_name = 'size'
            )
        ''')).scalar()

        if fk_exists:
            continue

        # Nullify invalid values
        result = conn.execute(sa.text(f'''
            UPDATE {schema}.products
            SET size = NULL
            WHERE size IS NOT NULL
            AND size NOT IN (SELECT name_en FROM product_attributes.sizes)
        '''))
        if result.rowcount > 0:
            print(f"  ⚠️ Nullified {result.rowcount} invalid size values in {schema}")

        # Add FK
        conn.execute(sa.text(f'''
            ALTER TABLE {schema}.products
            ADD CONSTRAINT fk_{schema}_products_size
            FOREIGN KEY (size)
            REFERENCES product_attributes.sizes(name_en)
            ON DELETE SET NULL
        '''))
        print(f"  ✓ Added FK on {schema}.products.size")

    print("\n=== size FK constraint added (references sizes.name_en) ===")


def downgrade():
    conn = op.get_bind()

    # Drop FK from template_tenant
    conn.execute(sa.text('''
        ALTER TABLE template_tenant.products
        DROP CONSTRAINT IF EXISTS fk_template_tenant_products_size
    '''))

    # Drop FK from user schemas
    result = conn.execute(sa.text('''
        SELECT schema_name FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%' AND schema_name != 'user_invalid'
    '''))
    user_schemas = [row[0] for row in result]

    for schema in user_schemas:
        conn.execute(sa.text(f'''
            ALTER TABLE {schema}.products
            DROP CONSTRAINT IF EXISTS fk_{schema}_products_size
        '''))
