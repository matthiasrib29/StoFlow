"""fix_attribute_inconsistencies

Revision ID: edc8822ba716
Revises: 4d2e58dae912
Create Date: 2026-01-07 12:57:34.555687+01:00

Fixes:
1. Materials: merge lowercase → Capitalized (cotton → Cotton)
2. Fits: merge lowercase → Capitalized (loose → Loose)
3. Patterns: delete 'embroidered' and 'printed' (duplicates with unique_features)
4. Unique features: merge 'selvage denim' → 'selvedge'
5. Decades: harmonize format (2000s → 00s, 2010s → 10s, 2020s → 20s)
6. Categories: delete 'dresses-jumpsuits' (redundant)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'edc8822ba716'
down_revision: Union[str, None] = '4d2e58dae912'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def get_user_schemas(conn):
    """Get list of user schemas."""
    result = conn.execute(text("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%'
        ORDER BY schema_name
    """))
    return [row[0] for row in result]


def table_exists(conn, schema, table):
    """Check if a table exists in a schema."""
    result = conn.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = :schema AND table_name = :table
        )
    """), {"schema": schema, "table": table})
    return result.scalar()


def upgrade() -> None:
    """Apply attribute inconsistency fixes."""
    conn = op.get_bind()

    # Get all user schemas
    user_schemas = get_user_schemas(conn)
    print(f"Found {len(user_schemas)} user schemas")

    # ===== 1. UPDATE PRODUCTS IN USER SCHEMAS =====

    # Materials mapping (lowercase → Capitalized)
    materials_map = {
        'acrylic': 'Acrylic',
        'cashmere': 'Cashmere',
        'cotton': 'Cotton',
        'denim': 'Denim',
        'fleece': 'Fleece',
        'leather': 'Leather',
        'linen': 'Linen',
        'nylon': 'Nylon',
        'polyester': 'Polyester',
        'silk': 'Silk',
        'spandex': 'Spandex',
        'suede': 'Suede',
        'velvet': 'Velvet',
        'viscose': 'Viscose',
        'wool': 'Wool',
    }

    # Fits mapping (lowercase → Capitalized)
    fits_map = {
        'loose': 'Loose',
        'oversized': 'Oversized',
        'regular': 'Regular',
        'relaxed': 'Relaxed',
        'slim': 'Slim',
    }

    for schema in user_schemas:
        if not table_exists(conn, schema, 'products'):
            continue

        print(f"Updating products in {schema}...")

        # Update materials
        for old_val, new_val in materials_map.items():
            conn.execute(text(f"""
                UPDATE {schema}.products
                SET material = :new_val
                WHERE material = :old_val
            """), {"old_val": old_val, "new_val": new_val})

        # Update fits
        for old_val, new_val in fits_map.items():
            conn.execute(text(f"""
                UPDATE {schema}.products
                SET fit = :new_val
                WHERE fit = :old_val
            """), {"old_val": old_val, "new_val": new_val})

    # ===== 2. CLEAN ATTRIBUTE TABLES =====

    # 2.1 Materials - Delete lowercase duplicates
    print("Cleaning materials table...")
    for old_val in materials_map.keys():
        conn.execute(text("""
            DELETE FROM product_attributes.materials
            WHERE name_en = :old_val
        """), {"old_val": old_val})

    # 2.2 Fits - Delete lowercase duplicates
    print("Cleaning fits table...")
    for old_val in fits_map.keys():
        conn.execute(text("""
            DELETE FROM product_attributes.fits
            WHERE name_en = :old_val
        """), {"old_val": old_val})

    # 2.3 Patterns - Delete embroidered and printed
    print("Deleting duplicate patterns...")
    conn.execute(text("""
        DELETE FROM product_attributes.patterns
        WHERE name_en IN ('embroidered', 'printed')
    """))

    # 2.4 Unique features - Merge selvage denim → selvedge
    print("Merging unique features...")
    # Check if 'selvedge' exists
    result = conn.execute(text("""
        SELECT COUNT(*) FROM product_attributes.unique_features
        WHERE name_en = 'selvedge'
    """))
    if result.scalar() > 0:
        # Delete 'selvage denim' (selvedge already exists)
        conn.execute(text("""
            DELETE FROM product_attributes.unique_features
            WHERE name_en = 'selvage denim'
        """))
    else:
        # Rename 'selvage denim' to 'selvedge'
        conn.execute(text("""
            UPDATE product_attributes.unique_features
            SET name_en = 'selvedge'
            WHERE name_en = 'selvage denim'
        """))

    # 2.5 Decades - Harmonize format
    print("Harmonizing decades format...")
    decades_map = {
        '2000s': '00s',
        '2010s': '10s',
        '2020s': '20s',
    }
    for old_val, new_val in decades_map.items():
        conn.execute(text("""
            UPDATE product_attributes.decades
            SET name_en = :new_val
            WHERE name_en = :old_val
        """), {"old_val": old_val, "new_val": new_val})

    # 2.6 Categories - Delete dresses-jumpsuits
    print("Deleting redundant category...")
    conn.execute(text("""
        DELETE FROM product_attributes.categories
        WHERE name_en = 'dresses-jumpsuits'
    """))

    print("✅ Migration completed successfully!")


def downgrade() -> None:
    """Rollback attribute inconsistency fixes."""
    conn = op.get_bind()

    # Get all user schemas
    user_schemas = get_user_schemas(conn)
    print(f"Rolling back changes in {len(user_schemas)} user schemas")

    # ===== 1. RESTORE ATTRIBUTE TABLES =====

    # 1.1 Restore materials (lowercase)
    print("Restoring lowercase materials...")
    materials_to_restore = [
        'acrylic', 'cashmere', 'cotton', 'denim', 'fleece',
        'leather', 'linen', 'nylon', 'polyester', 'silk',
        'spandex', 'suede', 'velvet', 'viscose', 'wool'
    ]
    for material in materials_to_restore:
        conn.execute(text("""
            INSERT INTO product_attributes.materials (name_en)
            VALUES (:material)
            ON CONFLICT (name_en) DO NOTHING
        """), {"material": material})

    # 1.2 Restore fits (lowercase)
    print("Restoring lowercase fits...")
    fits_to_restore = ['loose', 'oversized', 'regular', 'relaxed', 'slim']
    for fit in fits_to_restore:
        conn.execute(text("""
            INSERT INTO product_attributes.fits (name_en)
            VALUES (:fit)
            ON CONFLICT (name_en) DO NOTHING
        """), {"fit": fit})

    # 1.3 Restore patterns
    print("Restoring deleted patterns...")
    patterns_to_restore = ['embroidered', 'printed']
    for pattern in patterns_to_restore:
        conn.execute(text("""
            INSERT INTO product_attributes.patterns (name_en)
            VALUES (:pattern)
            ON CONFLICT (name_en) DO NOTHING
        """), {"pattern": pattern})

    # 1.4 Restore unique features
    print("Restoring unique features...")
    conn.execute(text("""
        INSERT INTO product_attributes.unique_features (name_en)
        VALUES ('selvage denim')
        ON CONFLICT (name_en) DO NOTHING
    """))

    # 1.5 Restore decades
    print("Restoring old decades format...")
    decades_to_restore = {'00s': '2000s', '10s': '2010s', '20s': '2020s'}
    for new_val, old_val in decades_to_restore.items():
        conn.execute(text("""
            UPDATE product_attributes.decades
            SET name_en = :old_val
            WHERE name_en = :new_val
        """), {"old_val": old_val, "new_val": new_val})

    # 1.6 Restore category
    print("Restoring deleted category...")
    conn.execute(text("""
        INSERT INTO product_attributes.categories (name_en)
        VALUES ('dresses-jumpsuits')
        ON CONFLICT (name_en) DO NOTHING
    """))

    # ===== 2. REVERT PRODUCTS IN USER SCHEMAS =====

    materials_map = {
        'Acrylic': 'acrylic',
        'Cashmere': 'cashmere',
        'Cotton': 'cotton',
        'Denim': 'denim',
        'Fleece': 'fleece',
        'Leather': 'leather',
        'Linen': 'linen',
        'Nylon': 'nylon',
        'Polyester': 'polyester',
        'Silk': 'silk',
        'Spandex': 'spandex',
        'Suede': 'suede',
        'Velvet': 'velvet',
        'Viscose': 'viscose',
        'Wool': 'wool',
    }

    fits_map = {
        'Loose': 'loose',
        'Oversized': 'oversized',
        'Regular': 'regular',
        'Relaxed': 'relaxed',
        'Slim': 'slim',
    }

    for schema in user_schemas:
        if not table_exists(conn, schema, 'products'):
            continue

        print(f"Reverting products in {schema}...")

        # Revert materials
        for new_val, old_val in materials_map.items():
            conn.execute(text(f"""
                UPDATE {schema}.products
                SET material = :old_val
                WHERE material = :new_val
            """), {"old_val": old_val, "new_val": new_val})

        # Revert fits
        for new_val, old_val in fits_map.items():
            conn.execute(text(f"""
                UPDATE {schema}.products
                SET fit = :old_val
                WHERE fit = :new_val
            """), {"old_val": old_val, "new_val": new_val})

    print("✅ Rollback completed successfully!")
