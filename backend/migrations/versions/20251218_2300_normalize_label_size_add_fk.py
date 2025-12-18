"""Normalize label_size values and add FK constraint

Revision ID: 20251218_2300
Revises: 20251218_2200
Create Date: 2025-12-18
"""
from alembic import op
import sqlalchemy as sa
import re


revision = '20251218_2300'
down_revision = '20251218_2200'
branch_labels = None
depends_on = None


# Simple size mappings (case-insensitive)
SIMPLE_SIZE_MAPPING = {
    'xs': 'XS',
    'xxs': 'XXS',
    's': 'S',
    'm': 'M',
    'l': 'L',
    'xl': 'XL',
    'xxl': 'XXL',
    '2xl': 'XXL',
    '3xl': '3XL',
    '4xl': '4XL',
    'one-size': 'one-size',
    'l/g': 'L',
    's/p': 'S',
    's/p/ch': 'S',
    'medium': 'M',
    '2x': 'XXL',
    '3x large': '3XL',
}


def normalize_waist_length(value: str) -> str | None:
    """
    Normalize waist/length format to W##/L## or W## format.

    Handles formats like:
    - w30/l32, W30/L32 -> W30/L32
    - W30 L32, w30 l32 -> W30/L32
    - 30 x 32, 30x32, 30 X 32 -> W30/L32
    - 30-32, 30/32 -> W30/L32
    - w30, W30, 30 (waist only) -> W30
    """
    if not value:
        return None

    val = value.strip()

    # Pattern 1: Already correct format W##/L##
    match = re.match(r'^W(\d+)/L(\d+)$', val, re.IGNORECASE)
    if match:
        return f"W{match.group(1)}/L{match.group(2)}"

    # Pattern 2: W## L## (space instead of slash)
    match = re.match(r'^W(\d+)\s+L(\d+)$', val, re.IGNORECASE)
    if match:
        return f"W{match.group(1)}/L{match.group(2)}"

    # Pattern 3: ## x ## or ##x## or ## X ##
    match = re.match(r'^(\d+)\s*[xX]\s*(\d+)$', val)
    if match:
        return f"W{match.group(1)}/L{match.group(2)}"

    # Pattern 4: ##-## (dash separator)
    match = re.match(r'^(\d+)-(\d+)$', val)
    if match:
        return f"W{match.group(1)}/L{match.group(2)}"

    # Pattern 5: ##/## (slash separator, no W/L prefix)
    match = re.match(r'^(\d+)/(\d+)$', val)
    if match:
        return f"W{match.group(1)}/L{match.group(2)}"

    # Pattern 6: W## only (waist without length)
    match = re.match(r'^W(\d+)$', val, re.IGNORECASE)
    if match:
        return f"W{match.group(1)}"

    # Pattern 7: ## only (numeric, assume waist)
    match = re.match(r'^(\d+)$', val)
    if match:
        waist = int(match.group(1))
        # Only convert if it's a reasonable waist size (24-52)
        if 24 <= waist <= 52:
            return f"W{waist}"

    return None


def upgrade():
    conn = op.get_bind()

    # Get all user schemas
    result = conn.execute(sa.text('''
        SELECT schema_name FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%' AND schema_name != 'user_invalid'
    '''))
    user_schemas = [row[0] for row in result]

    # Get valid sizes from reference table
    valid_sizes = set()
    result = conn.execute(sa.text('SELECT name FROM product_attributes.sizes'))
    for row in result:
        valid_sizes.add(row[0])

    print(f"\n📏 Found {len(valid_sizes)} valid sizes in reference table")

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

        # Get distinct label_size values that need normalization
        result = conn.execute(sa.text(f'''
            SELECT DISTINCT label_size
            FROM {schema}.products
            WHERE label_size IS NOT NULL
            AND label_size NOT IN (SELECT name FROM product_attributes.sizes)
        '''))

        values_to_normalize = [row[0] for row in result]

        if not values_to_normalize:
            print(f"  ✓ All values already valid")
            continue

        normalized_count = 0
        nullified_count = 0

        for old_value in values_to_normalize:
            new_value = None

            # Try simple mapping first (case-insensitive)
            lower_val = old_value.lower().strip()
            if lower_val in SIMPLE_SIZE_MAPPING:
                candidate = SIMPLE_SIZE_MAPPING[lower_val]
                if candidate in valid_sizes:
                    new_value = candidate

            # Try waist/length normalization
            if new_value is None:
                candidate = normalize_waist_length(old_value)
                if candidate and candidate in valid_sizes:
                    new_value = candidate

            # Update the database
            if new_value:
                result = conn.execute(sa.text(f'''
                    UPDATE {schema}.products
                    SET label_size = :new_val
                    WHERE label_size = :old_val
                '''), {'old_val': old_value, 'new_val': new_value})
                if result.rowcount > 0:
                    print(f"  ✓ '{old_value}' → '{new_value}' ({result.rowcount})")
                    normalized_count += result.rowcount
            else:
                # Set to NULL if can't normalize
                result = conn.execute(sa.text(f'''
                    UPDATE {schema}.products
                    SET label_size = NULL
                    WHERE label_size = :old_val
                '''), {'old_val': old_value})
                if result.rowcount > 0:
                    print(f"  ⚠️ '{old_value}' → NULL ({result.rowcount})")
                    nullified_count += result.rowcount

        print(f"  📊 {schema}: {normalized_count} normalized, {nullified_count} set to NULL")

    # Also process template_tenant
    template_exists = conn.execute(sa.text('''
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'template_tenant' AND table_name = 'products'
        )
    ''')).scalar()

    if template_exists:
        result = conn.execute(sa.text('''
            SELECT DISTINCT label_size
            FROM template_tenant.products
            WHERE label_size IS NOT NULL
            AND label_size NOT IN (SELECT name FROM product_attributes.sizes)
        '''))

        for row in result:
            old_value = row[0]
            new_value = None

            lower_val = old_value.lower().strip()
            if lower_val in SIMPLE_SIZE_MAPPING:
                candidate = SIMPLE_SIZE_MAPPING[lower_val]
                if candidate in valid_sizes:
                    new_value = candidate

            if new_value is None:
                candidate = normalize_waist_length(old_value)
                if candidate and candidate in valid_sizes:
                    new_value = candidate

            if new_value:
                conn.execute(sa.text('''
                    UPDATE template_tenant.products
                    SET label_size = :new_val
                    WHERE label_size = :old_val
                '''), {'old_val': old_value, 'new_val': new_value})
            else:
                conn.execute(sa.text('''
                    UPDATE template_tenant.products
                    SET label_size = NULL
                    WHERE label_size = :old_val
                '''), {'old_val': old_value})

    # Now add FK constraints
    print("\n🔗 Adding FK constraints on label_size...")

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
                AND kcu.column_name = 'label_size'
            )
        ''')).scalar()

        if fk_exists:
            continue

        fk_name = f"fk_{schema}_products_label_size"
        conn.execute(sa.text(f'''
            ALTER TABLE {schema}.products
            ADD CONSTRAINT {fk_name}
            FOREIGN KEY (label_size)
            REFERENCES product_attributes.sizes(name)
            ON DELETE SET NULL
        '''))
        print(f"  ✓ {fk_name}")

    # template_tenant FK
    if template_exists:
        fk_exists = conn.execute(sa.text('''
            SELECT EXISTS (
                SELECT 1 FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_schema = 'template_tenant'
                AND tc.table_name = 'products'
                AND kcu.column_name = 'label_size'
            )
        ''')).scalar()

        if not fk_exists:
            conn.execute(sa.text('''
                ALTER TABLE template_tenant.products
                ADD CONSTRAINT fk_template_tenant_products_label_size
                FOREIGN KEY (label_size)
                REFERENCES product_attributes.sizes(name)
                ON DELETE SET NULL
            '''))
            print("  ✓ fk_template_tenant_products_label_size")

    print("\n=== label_size normalization and FK complete ===")


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
            DROP CONSTRAINT IF EXISTS fk_{schema}_products_label_size
        '''))

    conn.execute(sa.text('''
        ALTER TABLE template_tenant.products
        DROP CONSTRAINT IF EXISTS fk_template_tenant_products_label_size
    '''))
