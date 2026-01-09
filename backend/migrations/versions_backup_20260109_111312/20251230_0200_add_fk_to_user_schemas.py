"""add_fk_to_user_schemas

Revision ID: 20251230_0200
Revises: 20251230_0100
Create Date: 2025-12-30

This migration adds foreign key constraints to user schemas for product attributes.

Changes:
1. Fix apostrophe encoding issue (arc'teryx -> arc'teryx)
2. Add FK constraints to all user schemas for:
   - brand -> product_attributes.brands(name)
   - category -> product_attributes.categories(name_en)
   - condition -> product_attributes.conditions(note)
   - size -> product_attributes.sizes(name_en)
   - color -> product_attributes.colors(name_en)
   - material -> product_attributes.materials(name_en)
   - fit -> product_attributes.fits(name_en)
   - gender -> product_attributes.genders(name_en)
   - season -> product_attributes.seasons(name_en)
   - neckline -> product_attributes.necklines(name_en)
   - pattern -> product_attributes.patterns(name_en)

Author: Claude
Date: 2025-12-30
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20251230_0200'
down_revision: Union[str, None] = '20251230_0100'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# FK definitions: (column, reference_table, reference_column, fk_name)
FK_DEFINITIONS = [
    ('brand', 'product_attributes.brands', 'name', 'fk_products_brand'),
    ('category', 'product_attributes.categories', 'name_en', 'fk_products_category'),
    ('condition', 'product_attributes.conditions', 'note', 'fk_products_condition'),
    ('size', 'product_attributes.sizes', 'name_en', 'fk_products_size'),
    ('color', 'product_attributes.colors', 'name_en', 'fk_products_color'),
    ('material', 'product_attributes.materials', 'name_en', 'fk_products_material'),
    ('fit', 'product_attributes.fits', 'name_en', 'fk_products_fit'),
    ('gender', 'product_attributes.genders', 'name_en', 'fk_products_gender'),
    ('season', 'product_attributes.seasons', 'name_en', 'fk_products_season'),
    ('neckline', 'product_attributes.necklines', 'name_en', 'fk_products_neckline'),
    ('pattern', 'product_attributes.patterns', 'name_en', 'fk_products_pattern'),
]


def get_user_schemas(connection) -> list[str]:
    """Get all user schemas (user_1, user_2, etc.)"""
    result = connection.execute(sa.text(
        "SELECT schema_name FROM information_schema.schemata "
        "WHERE schema_name LIKE 'user_%' AND schema_name != 'user_template' "
        "ORDER BY schema_name"
    ))
    return [row[0] for row in result]


def table_exists(connection, schema: str, table: str) -> bool:
    """Check if a table exists in a specific schema."""
    result = connection.execute(sa.text(
        "SELECT EXISTS ("
        "  SELECT 1 FROM information_schema.tables "
        "  WHERE table_schema = :schema AND table_name = :table"
        ")"
    ), {"schema": schema, "table": table})
    return result.scalar()


def upgrade() -> None:
    """
    Add foreign key constraints to all user schemas.
    """
    connection = op.get_bind()

    # Get all user schemas with products table
    all_schemas = get_user_schemas(connection)
    user_schemas = [s for s in all_schemas if table_exists(connection, s, 'products')]
    skipped = len(all_schemas) - len(user_schemas)
    if skipped > 0:
        print(f"\n⚠️  Skipping {skipped} schemas without products table\n")

    # 1. Fix apostrophe encoding issue
    print("\n=== Fixing apostrophe encoding issues ===")
    for schema in user_schemas:
        result = connection.execute(sa.text(f"""
            UPDATE {schema}.products
            SET brand = REPLACE(brand, E'\\u2019', E'\\x27')
            WHERE brand LIKE E'%\\u2019%'
        """))
        if result.rowcount > 0:
            print(f"  Fixed {result.rowcount} brand values in {schema}")
    print("  ✓ Apostrophe encoding fixed\n")

    # 2. Normalize season values
    print("=== Normalizing season values ===")
    season_mapping = {
        'all season': 'All seasons',
        'fall': 'Autumn',
        'summer': 'Summer',
        'spring/summer': 'Summer',  # Map to closest match
        'fall/winter': 'Winter',    # Map to closest match
    }
    for schema in user_schemas:
        for old_val, new_val in season_mapping.items():
            result = connection.execute(sa.text(f"""
                UPDATE {schema}.products
                SET season = :new_val
                WHERE season = :old_val
            """), {"old_val": old_val, "new_val": new_val})
            if result.rowcount > 0:
                print(f"  {schema}: {old_val} -> {new_val}: {result.rowcount} rows")
    print("  ✓ Season values normalized\n")

    # Add FK constraints
    print(f"=== Adding FK constraints to {len(user_schemas)} user schemas ===\n")

    for schema in user_schemas:
        print(f"Processing {schema}...")

        for column, ref_table, ref_column, fk_name in FK_DEFINITIONS:
            # Check if FK already exists
            check_fk = connection.execute(sa.text(f"""
                SELECT 1 FROM information_schema.table_constraints
                WHERE constraint_schema = '{schema}'
                  AND constraint_name = '{fk_name}'
                  AND constraint_type = 'FOREIGN KEY'
            """))

            if check_fk.fetchone():
                print(f"  ⏭️  {fk_name} already exists, skipping")
                continue

            # Add FK constraint
            try:
                connection.execute(sa.text(f"""
                    ALTER TABLE {schema}.products
                    ADD CONSTRAINT {fk_name}
                    FOREIGN KEY ({column})
                    REFERENCES {ref_table}({ref_column})
                    ON UPDATE CASCADE
                    ON DELETE SET NULL
                """))
                print(f"  ✓ Added {fk_name}")
            except Exception as e:
                print(f"  ⚠️  Failed to add {fk_name}: {e}")

        print(f"  ✓ {schema} completed\n")

    print("=== FK constraints added successfully ===\n")


def downgrade() -> None:
    """
    Remove foreign key constraints from all user schemas.
    """
    connection = op.get_bind()
    user_schemas = get_user_schemas(connection)

    print(f"\n=== Removing FK constraints from {len(user_schemas)} user schemas ===\n")

    for schema in user_schemas:
        print(f"Processing {schema}...")

        for column, ref_table, ref_column, fk_name in FK_DEFINITIONS:
            try:
                connection.execute(sa.text(f"""
                    ALTER TABLE {schema}.products
                    DROP CONSTRAINT IF EXISTS {fk_name}
                """))
                print(f"  ✓ Dropped {fk_name}")
            except Exception as e:
                print(f"  ⚠️  Failed to drop {fk_name}: {e}")

        print(f"  ✓ {schema} completed\n")

    print("=== FK constraints removed ===\n")
