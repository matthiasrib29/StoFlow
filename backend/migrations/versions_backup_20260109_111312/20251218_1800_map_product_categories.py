"""Map product categories to normalized values and add FK

Revision ID: 20251218_1800
Revises: 20251218_1700
Create Date: 2025-12-18
"""
from alembic import op
import sqlalchemy as sa


revision = '20251218_1800'
down_revision = '20251218_1700'
branch_labels = None
depends_on = None

# Category mapping with optional attributes
# Format: (old_category, new_category, attribute_updates)
CATEGORY_MAPPING = [
    ('Baseball jersey', 'sports-jersey', {'sport': 'baseball'}),
    ('Cargo shorts', 'shorts', {}),
    ('Chino shorts', 'shorts', {}),
    ('Corduroy pants', 'pants', {'material': 'corduroy'}),
    ('Crew neck sweater', 'sweater', {'neckline': 'crew neck'}),
    ('Crewneck sweatshirt', 'sweatshirt', {'neckline': 'crew neck'}),
    ('Denim jacket', 'jacket', {'material': 'denim'}),
    ('Denim shirt', 'shirt', {'material': 'denim'}),
    ('Denim shorts', 'shorts', {'material': 'denim'}),
    ('Denim skirt', 'skirt', {'material': 'denim'}),
    ('Graphic t-shirt', 't-shirt', {'pattern': 'graphic'}),
    ('Hoodie sweatshirt', 'hoodie', {}),
    ('Leather jacket', 'jacket', {'material': 'leather'}),
    ('Long sleeve shirt', 'shirt', {'sleeve_length': 'long sleeve'}),
    ('Long sleeve t-shirt', 't-shirt', {'sleeve_length': 'long sleeve'}),
    ('Puffer jacket', 'puffer', {}),
    ('Raincoat/Windbreaker', 'windbreaker', {}),
    ('Rework jacket', 'jacket', {}),
    ('Rugby jersey', 'sports-jersey', {'sport': 'rugby'}),
    ('Short sleeve shirt', 'shirt', {'sleeve_length': 'short sleeve'}),
    ('Short sleeve t-shirt', 't-shirt', {'sleeve_length': 'short sleeve'}),
    ('Slim Jeans', 'jeans', {'fit': 'slim'}),
    ('Sport jacket', 'jacket', {}),
    ('Sport shorts', 'sports-shorts', {}),
    ('Trench Coat', 'trench', {}),
    ('Turtleneck sweater', 'sweater', {'neckline': 'turtleneck'}),
    ('V-neck sweater', 'sweater', {'neckline': 'v-neck'}),
    ('Varsity jacket', 'bomber', {}),
    ('Work coveralls', 'overalls', {}),
    ('Work jacket', 'jacket', {}),
    ('Work pants', 'pants', {}),
    ('Work shorts', 'shorts', {}),
]

# Categories to set NULL (not mappable)
NULL_CATEGORIES = ['Sunglasses', 'Uncategorized']

# Simple renames (already matching after normalization)
SIMPLE_RENAMES = [
    ('Cargo pants', 'cargo-pants'),
    ('Fleece', 'fleece'),
    ('Half-zip', 'half-zip'),
    ('Jacket', 'jacket'),
    ('Jeans', 'jeans'),
    ('Joggers', 'joggers'),
    ('Pants', 'pants'),
    ('Polo', 'polo'),
    ('Shorts', 'shorts'),
    ('T-shirt', 't-shirt'),
    ('Vest', 'vest'),
]


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

        print(f"\n🔄 Processing {schema}...")
        total_updated = 0

        # Apply category mappings with attributes
        for old_cat, new_cat, attrs in CATEGORY_MAPPING:
            # Build SET clause
            set_parts = ["category = :new_cat"]
            params = {'old_cat': old_cat, 'new_cat': new_cat}

            for attr_name, attr_value in attrs.items():
                set_parts.append(f"{attr_name} = COALESCE({attr_name}, :{attr_name})")
                params[attr_name] = attr_value

            set_clause = ", ".join(set_parts)

            result = conn.execute(sa.text(f'''
                UPDATE {schema}.products
                SET {set_clause}
                WHERE category = :old_cat
            '''), params)

            if result.rowcount > 0:
                attrs_str = f" + {attrs}" if attrs else ""
                print(f"  ✓ {old_cat} → {new_cat}{attrs_str} ({result.rowcount})")
                total_updated += result.rowcount

        # Apply simple renames
        for old_cat, new_cat in SIMPLE_RENAMES:
            result = conn.execute(sa.text(f'''
                UPDATE {schema}.products
                SET category = :new_cat
                WHERE category = :old_cat
            '''), {'old_cat': old_cat, 'new_cat': new_cat})

            if result.rowcount > 0:
                print(f"  ✓ {old_cat} → {new_cat} ({result.rowcount})")
                total_updated += result.rowcount

        # Set NULL for non-mappable categories
        for cat in NULL_CATEGORIES:
            result = conn.execute(sa.text(f'''
                UPDATE {schema}.products
                SET category = NULL
                WHERE category = :cat
            '''), {'cat': cat})

            if result.rowcount > 0:
                print(f"  ✓ {cat} → NULL ({result.rowcount})")
                total_updated += result.rowcount

        print(f"  📊 Total updated in {schema}: {total_updated}")

    # Also update template_tenant if it has products
    template_exists = conn.execute(sa.text('''
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'template_tenant' AND table_name = 'products'
        )
    ''')).scalar()

    if template_exists:
        # Apply same mappings to template_tenant
        for old_cat, new_cat, attrs in CATEGORY_MAPPING:
            set_parts = ["category = :new_cat"]
            params = {'old_cat': old_cat, 'new_cat': new_cat}
            for attr_name, attr_value in attrs.items():
                set_parts.append(f"{attr_name} = COALESCE({attr_name}, :{attr_name})")
                params[attr_name] = attr_value
            set_clause = ", ".join(set_parts)
            conn.execute(sa.text(f'''
                UPDATE template_tenant.products
                SET {set_clause}
                WHERE category = :old_cat
            '''), params)

        for old_cat, new_cat in SIMPLE_RENAMES:
            conn.execute(sa.text('''
                UPDATE template_tenant.products
                SET category = :new_cat
                WHERE category = :old_cat
            '''), {'old_cat': old_cat, 'new_cat': new_cat})

        for cat in NULL_CATEGORIES:
            conn.execute(sa.text('''
                UPDATE template_tenant.products
                SET category = NULL
                WHERE category = :cat
            '''), {'cat': cat})

    print("\n=== Category mapping complete ===")


def downgrade():
    # Note: This downgrade is lossy - attributes added during upgrade won't be removed
    conn = op.get_bind()

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

        # Reverse mappings (best effort)
        for old_cat, new_cat, _ in CATEGORY_MAPPING:
            conn.execute(sa.text(f'''
                UPDATE {schema}.products
                SET category = :old_cat
                WHERE category = :new_cat
            '''), {'old_cat': old_cat, 'new_cat': new_cat})

        for old_cat, new_cat in SIMPLE_RENAMES:
            conn.execute(sa.text(f'''
                UPDATE {schema}.products
                SET category = :old_cat
                WHERE category = :new_cat
            '''), {'old_cat': old_cat, 'new_cat': new_cat})
