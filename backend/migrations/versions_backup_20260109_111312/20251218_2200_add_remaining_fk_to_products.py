"""Add remaining FK constraints on products

Revision ID: 20251218_2200
Revises: 20251218_2100
Create Date: 2025-12-18
"""
from alembic import op
import sqlalchemy as sa


revision = '20251218_2200'
down_revision = '20251218_2100'
branch_labels = None
depends_on = None

# Season mappings to fix before FK
SEASON_MAPPING = {
    'fall': 'autumn',
    'fall/winter': 'all season',
    'spring/summer': 'all season',
}

# FK configs: (column_name, reference_table, reference_column)
FK_CONFIGS = [
    ('gender', 'product_attributes.genders', 'name_en'),
    ('season', 'product_attributes.seasons', 'name_en'),
    ('rise', 'product_attributes.rises', 'name_en'),
    ('closure', 'product_attributes.closures', 'name_en'),
    ('sleeve_length', 'product_attributes.sleeve_lengths', 'name_en'),
    ('origin', 'product_attributes.origins', 'name_en'),
    ('decade', 'product_attributes.decades', 'name_en'),
    ('trend', 'product_attributes.trends', 'name_en'),
    ('sport', 'product_attributes.sports', 'name_en'),
    ('neckline', 'product_attributes.necklines', 'name_en'),
    ('length', 'product_attributes.lengths', 'name_en'),
    ('pattern', 'product_attributes.patterns', 'name_en'),
]


def upgrade():
    conn = op.get_bind()

    # Get all user schemas
    result = conn.execute(sa.text('''
        SELECT schema_name FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%' AND schema_name != 'user_invalid'
    '''))
    user_schemas = [row[0] for row in result]

    # Step 1: Fix season values
    print("\n🔄 Fixing season values...")
    for schema in user_schemas:
        table_exists = conn.execute(sa.text(f'''
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = '{schema}' AND table_name = 'products'
            )
        ''')).scalar()

        if not table_exists:
            continue

        for old_val, new_val in SEASON_MAPPING.items():
            result = conn.execute(sa.text(f'''
                UPDATE {schema}.products
                SET season = :new_val
                WHERE season = :old_val
            '''), {'old_val': old_val, 'new_val': new_val})
            if result.rowcount > 0:
                print(f"  ✓ {schema}: {old_val} → {new_val} ({result.rowcount})")

    # Also fix template_tenant
    for old_val, new_val in SEASON_MAPPING.items():
        conn.execute(sa.text('''
            UPDATE template_tenant.products
            SET season = :new_val
            WHERE season = :old_val
        '''), {'old_val': old_val, 'new_val': new_val})

    # Step 2: Add FK constraints
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
                continue

            fk_name = f"fk_{schema}_products_{col_name}"
            conn.execute(sa.text(f'''
                ALTER TABLE {schema}.products
                ADD CONSTRAINT {fk_name}
                FOREIGN KEY ({col_name})
                REFERENCES {ref_table}({ref_col})
                ON DELETE SET NULL
            '''))
            print(f"  ✓ {fk_name}")

        # template_tenant
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
            print(f"  ✓ fk_template_tenant_products_{col_name}")

    print("\n=== All remaining FK constraints added ===")


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
