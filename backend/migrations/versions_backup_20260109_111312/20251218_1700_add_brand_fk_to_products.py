"""Add FK constraint on products.brand to brands.name

Revision ID: 20251218_1700
Revises: 20251218_1600
Create Date: 2025-12-18
"""
from alembic import op
import sqlalchemy as sa


revision = '20251218_1700'
down_revision = '20251218_1600'
branch_labels = None
depends_on = None

# Brands to add before FK constraint
MISSING_BRANDS = [
    {'name': 'esprit', 'description': None, 'monitoring': False},
    {'name': 'pure oxygen', 'description': None, 'monitoring': False},
    {'name': 'wonderful', 'description': None, 'monitoring': False},
]


def upgrade():
    conn = op.get_bind()

    # Step 1: Add missing brands
    for brand in MISSING_BRANDS:
        exists = conn.execute(sa.text(
            "SELECT 1 FROM product_attributes.brands WHERE name = :name"
        ), {'name': brand['name']}).fetchone()

        if not exists:
            conn.execute(sa.text('''
                INSERT INTO product_attributes.brands (name, description, monitoring)
                VALUES (:name, :description, :monitoring)
            '''), brand)
            print(f"  ✓ Added brand: {brand['name']}")
        else:
            print(f"  ⏭️  Brand {brand['name']} already exists")

    # Step 2: Get all user schemas
    result = conn.execute(sa.text('''
        SELECT schema_name FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%' AND schema_name != 'user_invalid'
    '''))
    user_schemas = [row[0] for row in result]

    # Step 3: Add FK constraint to each schema
    for schema in user_schemas:
        # Check if products table exists
        table_exists = conn.execute(sa.text(f'''
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = '{schema}' AND table_name = 'products'
            )
        ''')).scalar()

        if not table_exists:
            print(f"  ⏭️  Table {schema}.products doesn't exist, skipping")
            continue

        # Check if FK already exists
        fk_exists = conn.execute(sa.text(f'''
            SELECT EXISTS (
                SELECT 1 FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_schema = '{schema}'
                AND tc.table_name = 'products'
                AND kcu.column_name = 'brand'
            )
        ''')).scalar()

        if fk_exists:
            print(f"  ⏭️  FK on {schema}.products.brand already exists, skipping")
            continue

        # Add FK constraint
        fk_name = f"fk_{schema}_products_brand"
        conn.execute(sa.text(f'''
            ALTER TABLE {schema}.products
            ADD CONSTRAINT {fk_name}
            FOREIGN KEY (brand)
            REFERENCES product_attributes.brands(name)
            ON DELETE SET NULL
        '''))
        print(f"  ✓ Added FK {fk_name}")

    # Step 4: Also update template_tenant
    template_exists = conn.execute(sa.text('''
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'template_tenant' AND table_name = 'products'
        )
    ''')).scalar()

    if template_exists:
        fk_exists = conn.execute(sa.text('''
            SELECT EXISTS (
                SELECT 1 FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_schema = 'template_tenant'
                AND tc.table_name = 'products'
                AND kcu.column_name = 'brand'
            )
        ''')).scalar()

        if not fk_exists:
            conn.execute(sa.text('''
                ALTER TABLE template_tenant.products
                ADD CONSTRAINT fk_template_tenant_products_brand
                FOREIGN KEY (brand)
                REFERENCES product_attributes.brands(name)
                ON DELETE SET NULL
            '''))
            print("  ✓ Added FK on template_tenant.products.brand")

    print("\n=== FK constraint on brand added ===")


def downgrade():
    conn = op.get_bind()

    # Get all user schemas
    result = conn.execute(sa.text('''
        SELECT schema_name FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%' AND schema_name != 'user_invalid'
    '''))
    user_schemas = [row[0] for row in result]

    for schema in user_schemas:
        fk_name = f"fk_{schema}_products_brand"
        conn.execute(sa.text(f'''
            ALTER TABLE {schema}.products
            DROP CONSTRAINT IF EXISTS {fk_name}
        '''))

    # Drop from template_tenant
    conn.execute(sa.text('''
        ALTER TABLE template_tenant.products
        DROP CONSTRAINT IF EXISTS fk_template_tenant_products_brand
    '''))

    # Remove added brands
    for brand in MISSING_BRANDS:
        conn.execute(sa.text(
            "DELETE FROM product_attributes.brands WHERE name = :name"
        ), {'name': brand['name']})
