"""Add size column (regulated) and make label_size free text

Revision ID: 20251218_2400
Revises: 20251218_2300
Create Date: 2025-12-18

Logic:
- size: regulated field with FK to product_attributes.sizes (standardized values)
- label_size: free text field (what's written on the label, no FK)
"""
from alembic import op
import sqlalchemy as sa


revision = '20251218_2400'
down_revision = '20251218_2300'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # Get all user schemas
    result = conn.execute(sa.text('''
        SELECT schema_name FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%' AND schema_name != 'user_invalid'
    '''))
    user_schemas = [row[0] for row in result]

    # Process each schema
    for schema in user_schemas:
        table_exists = conn.execute(sa.text(f'''
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = '{schema}' AND table_name = 'products'
            )
        ''')).scalar()

        if not table_exists:
            continue

        print(f"\n🔄 Processing {schema}...")

        # Step 1: Add size column if not exists
        size_exists = conn.execute(sa.text(f'''
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = '{schema}'
                AND table_name = 'products'
                AND column_name = 'size'
            )
        ''')).scalar()

        if not size_exists:
            conn.execute(sa.text(f'''
                ALTER TABLE {schema}.products
                ADD COLUMN size VARCHAR(100)
            '''))
            print(f"  ✓ Added {schema}.products.size column")

        # Step 2: Copy normalized label_size values to size
        result = conn.execute(sa.text(f'''
            UPDATE {schema}.products
            SET size = label_size
            WHERE label_size IS NOT NULL
            AND size IS NULL
        '''))
        if result.rowcount > 0:
            print(f"  ✓ Copied {result.rowcount} values from label_size to size")

        # Step 3: Drop FK on label_size
        conn.execute(sa.text(f'''
            ALTER TABLE {schema}.products
            DROP CONSTRAINT IF EXISTS fk_{schema}_products_label_size
        '''))
        print(f"  ✓ Dropped FK on label_size (now free text)")

        # Step 4: Add FK on size
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

        if not fk_exists:
            conn.execute(sa.text(f'''
                ALTER TABLE {schema}.products
                ADD CONSTRAINT fk_{schema}_products_size
                FOREIGN KEY (size)
                REFERENCES product_attributes.sizes(name)
                ON DELETE SET NULL
            '''))
            print(f"  ✓ Added FK on size → product_attributes.sizes(name)")

    # Process template_tenant
    template_exists = conn.execute(sa.text('''
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'template_tenant' AND table_name = 'products'
        )
    ''')).scalar()

    if template_exists:
        print("\n🔄 Processing template_tenant...")

        # Add size column
        size_exists = conn.execute(sa.text('''
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'template_tenant'
                AND table_name = 'products'
                AND column_name = 'size'
            )
        ''')).scalar()

        if not size_exists:
            conn.execute(sa.text('''
                ALTER TABLE template_tenant.products
                ADD COLUMN size VARCHAR(100)
            '''))
            print("  ✓ Added template_tenant.products.size column")

        # Copy values
        conn.execute(sa.text('''
            UPDATE template_tenant.products
            SET size = label_size
            WHERE label_size IS NOT NULL
            AND size IS NULL
        '''))

        # Drop FK on label_size
        conn.execute(sa.text('''
            ALTER TABLE template_tenant.products
            DROP CONSTRAINT IF EXISTS fk_template_tenant_products_label_size
        '''))
        print("  ✓ Dropped FK on label_size")

        # Add FK on size
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

        if not fk_exists:
            conn.execute(sa.text('''
                ALTER TABLE template_tenant.products
                ADD CONSTRAINT fk_template_tenant_products_size
                FOREIGN KEY (size)
                REFERENCES product_attributes.sizes(name)
                ON DELETE SET NULL
            '''))
            print("  ✓ Added FK on size")

    print("\n=== size column added (regulated), label_size is now free text ===")


def downgrade():
    conn = op.get_bind()

    result = conn.execute(sa.text('''
        SELECT schema_name FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%' AND schema_name != 'user_invalid'
    '''))
    user_schemas = [row[0] for row in result]

    for schema in user_schemas:
        # Drop FK on size
        conn.execute(sa.text(f'''
            ALTER TABLE {schema}.products
            DROP CONSTRAINT IF EXISTS fk_{schema}_products_size
        '''))

        # Drop size column
        conn.execute(sa.text(f'''
            ALTER TABLE {schema}.products
            DROP COLUMN IF EXISTS size
        '''))

        # Re-add FK on label_size
        conn.execute(sa.text(f'''
            ALTER TABLE {schema}.products
            ADD CONSTRAINT fk_{schema}_products_label_size
            FOREIGN KEY (label_size)
            REFERENCES product_attributes.sizes(name)
            ON DELETE SET NULL
        '''))

    # template_tenant
    conn.execute(sa.text('''
        ALTER TABLE template_tenant.products
        DROP CONSTRAINT IF EXISTS fk_template_tenant_products_size
    '''))
    conn.execute(sa.text('''
        ALTER TABLE template_tenant.products
        DROP COLUMN IF EXISTS size
    '''))
    conn.execute(sa.text('''
        ALTER TABLE template_tenant.products
        ADD CONSTRAINT fk_template_tenant_products_label_size
        FOREIGN KEY (label_size)
        REFERENCES product_attributes.sizes(name)
        ON DELETE SET NULL
    '''))
