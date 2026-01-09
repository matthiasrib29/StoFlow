"""Add FK constraint on products.category to categories.name_en

Revision ID: 20251218_1900
Revises: 20251218_1800
Create Date: 2025-12-18
"""
from alembic import op
import sqlalchemy as sa


revision = '20251218_1900'
down_revision = '20251218_1800'
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
                AND kcu.column_name = 'category'
            )
        ''')).scalar()

        if fk_exists:
            print(f"  ⏭️  FK on {schema}.products.category already exists, skipping")
            continue

        # Add FK constraint
        fk_name = f"fk_{schema}_products_category"
        conn.execute(sa.text(f'''
            ALTER TABLE {schema}.products
            ADD CONSTRAINT {fk_name}
            FOREIGN KEY (category)
            REFERENCES product_attributes.categories(name_en)
            ON DELETE SET NULL
        '''))
        print(f"  ✓ Added FK {fk_name}")

    # Also update template_tenant
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
                AND kcu.column_name = 'category'
            )
        ''')).scalar()

        if not fk_exists:
            conn.execute(sa.text('''
                ALTER TABLE template_tenant.products
                ADD CONSTRAINT fk_template_tenant_products_category
                FOREIGN KEY (category)
                REFERENCES product_attributes.categories(name_en)
                ON DELETE SET NULL
            '''))
            print("  ✓ Added FK on template_tenant.products.category")

    print("\n=== FK constraint on category added ===")


def downgrade():
    conn = op.get_bind()

    # Get all user schemas
    result = conn.execute(sa.text('''
        SELECT schema_name FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%' AND schema_name != 'user_invalid'
    '''))
    user_schemas = [row[0] for row in result]

    for schema in user_schemas:
        fk_name = f"fk_{schema}_products_category"
        conn.execute(sa.text(f'''
            ALTER TABLE {schema}.products
            DROP CONSTRAINT IF EXISTS {fk_name}
        '''))

    # Drop from template_tenant
    conn.execute(sa.text('''
        ALTER TABLE template_tenant.products
        DROP CONSTRAINT IF EXISTS fk_template_tenant_products_category
    '''))
