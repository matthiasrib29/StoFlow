"""Add FK constraints on products.material and products.fit

Revision ID: 20251218_2100
Revises: 20251218_2000
Create Date: 2025-12-18
"""
from alembic import op
import sqlalchemy as sa


revision = '20251218_2100'
down_revision = '20251218_2000'
branch_labels = None
depends_on = None

# Columns to add FK for: (column_name, reference_table, reference_column)
FK_CONFIGS = [
    ('material', 'product_attributes.materials', 'name_en'),
    ('fit', 'product_attributes.fits', 'name_en'),
]


def upgrade():
    conn = op.get_bind()

    result = conn.execute(sa.text('''
        SELECT schema_name FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%' AND schema_name != 'user_invalid'
    '''))
    user_schemas = [row[0] for row in result]

    for col_name, ref_table, ref_col in FK_CONFIGS:
        print(f"\n🔄 Adding FK on {col_name}...")

        for schema in user_schemas:
            table_exists = conn.execute(sa.text(f'''
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = '{schema}' AND table_name = 'products'
                )
            ''')).scalar()

            if not table_exists:
                continue

            fk_exists = conn.execute(sa.text(f'''
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND tc.table_schema = '{schema}'
                    AND tc.table_name = 'products'
                    AND kcu.column_name = '{col_name}'
                )
            ''')).scalar()

            if fk_exists:
                print(f"  ⏭️  FK on {schema}.products.{col_name} already exists")
                continue

            fk_name = f"fk_{schema}_products_{col_name}"
            conn.execute(sa.text(f'''
                ALTER TABLE {schema}.products
                ADD CONSTRAINT {fk_name}
                FOREIGN KEY ({col_name})
                REFERENCES {ref_table}({ref_col})
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
            fk_exists = conn.execute(sa.text(f'''
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND tc.table_schema = 'template_tenant'
                    AND tc.table_name = 'products'
                    AND kcu.column_name = '{col_name}'
                )
            ''')).scalar()

            if not fk_exists:
                conn.execute(sa.text(f'''
                    ALTER TABLE template_tenant.products
                    ADD CONSTRAINT fk_template_tenant_products_{col_name}
                    FOREIGN KEY ({col_name})
                    REFERENCES {ref_table}({ref_col})
                    ON DELETE SET NULL
                '''))
                print(f"  ✓ Added FK on template_tenant.products.{col_name}")

    print("\n=== FK on material and fit added ===")


def downgrade():
    conn = op.get_bind()

    result = conn.execute(sa.text('''
        SELECT schema_name FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%' AND schema_name != 'user_invalid'
    '''))
    user_schemas = [row[0] for row in result]

    for col_name, _, _ in FK_CONFIGS:
        for schema in user_schemas:
            conn.execute(sa.text(f'''
                ALTER TABLE {schema}.products
                DROP CONSTRAINT IF EXISTS fk_{schema}_products_{col_name}
            '''))

        conn.execute(sa.text(f'''
            ALTER TABLE template_tenant.products
            DROP CONSTRAINT IF EXISTS fk_template_tenant_products_{col_name}
        '''))
