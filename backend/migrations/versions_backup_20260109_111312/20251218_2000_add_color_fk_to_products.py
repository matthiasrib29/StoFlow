"""Add FK constraint on products.color to colors.name_en

Revision ID: 20251218_2000
Revises: 20251218_1900
Create Date: 2025-12-18
"""
from alembic import op
import sqlalchemy as sa


revision = '20251218_2000'
down_revision = '20251218_1900'
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
        table_exists = conn.execute(sa.text(f'''
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = '{schema}' AND table_name = 'products'
            )
        ''')).scalar()

        if not table_exists:
            print(f"  ⏭️  {schema}.products doesn't exist, skipping")
            continue

        fk_exists = conn.execute(sa.text(f'''
            SELECT EXISTS (
                SELECT 1 FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_schema = '{schema}'
                AND tc.table_name = 'products'
                AND kcu.column_name = 'color'
            )
        ''')).scalar()

        if fk_exists:
            print(f"  ⏭️  FK on {schema}.products.color already exists")
            continue

        fk_name = f"fk_{schema}_products_color"
        conn.execute(sa.text(f'''
            ALTER TABLE {schema}.products
            ADD CONSTRAINT {fk_name}
            FOREIGN KEY (color)
            REFERENCES product_attributes.colors(name_en)
            ON DELETE SET NULL
        '''))
        print(f"  ✓ Added FK {fk_name}")

    # template_tenant
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
                AND kcu.column_name = 'color'
            )
        ''')).scalar()

        if not fk_exists:
            conn.execute(sa.text('''
                ALTER TABLE template_tenant.products
                ADD CONSTRAINT fk_template_tenant_products_color
                FOREIGN KEY (color)
                REFERENCES product_attributes.colors(name_en)
                ON DELETE SET NULL
            '''))
            print("  ✓ Added FK on template_tenant.products.color")

    print("\n=== FK on color added ===")


def downgrade():
    conn = op.get_bind()

    result = conn.execute(sa.text('''
        SELECT schema_name FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%' AND schema_name != 'user_invalid'
    '''))
    user_schemas = [row[0] for row in result]

    for schema in user_schemas:
        conn.execute(sa.text(f'''
            ALTER TABLE {schema}.products
            DROP CONSTRAINT IF EXISTS fk_{schema}_products_color
        '''))

    conn.execute(sa.text('''
        ALTER TABLE template_tenant.products
        DROP CONSTRAINT IF EXISTS fk_template_tenant_products_color
    '''))
