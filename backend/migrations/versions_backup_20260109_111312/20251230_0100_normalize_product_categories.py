"""normalize_product_categories

Revision ID: 20251230_0100
Revises: 20251224_3000
Create Date: 2025-12-30

This migration normalizes product categories and extracts hidden attributes.

Changes:
1. Normalize category names (e.g., 'Jeans' -> 'jeans', 'Cargo pants' -> 'cargo-pants')
2. Extract material from category names (e.g., 'Denim shorts' -> material='denim')
3. Extract neckline from category names (e.g., 'Crewneck sweatshirt' -> neckline='crew neck')
4. Extract pattern from category names (e.g., 'Graphic t-shirt' -> pattern='graphic')
5. Extract fit from category names (e.g., 'Slim Jeans' -> fit='slim')
6. Set products without mapping (Other, Sunglasses, Uncategorized) to DRAFT with NULL category
7. Apply to all user schemas (user_1, user_2, etc.)

Author: Claude
Date: 2025-12-30
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20251230_0100'
down_revision: Union[str, None] = '20251224_3000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Category mapping: old_category -> (new_category, extracted_material, extracted_neckline, extracted_pattern, extracted_fit)
CATEGORY_MAPPING = {
    # Main categories
    'Jeans': ('jeans', None, None, None, None),
    'Slim Jeans': ('jeans', None, None, None, 'slim'),
    'Pants': ('pants', None, None, None, None),
    'Work pants': ('pants', None, None, None, None),
    'Corduroy pants': ('pants', 'corduroy', None, None, None),
    'Cargo pants': ('cargo-pants', None, None, None, None),

    # T-shirts
    'T-shirt': ('t-shirt', None, None, None, None),
    'Short sleeve t-shirt': ('t-shirt', None, None, None, None),
    'Long sleeve t-shirt': ('t-shirt', None, None, None, None),
    'Graphic t-shirt': ('t-shirt', None, None, 'graphic', None),

    # Shirts
    'Short sleeve shirt': ('shirt', None, None, None, None),
    'Long sleeve shirt': ('shirt', None, None, None, None),
    'Denim shirt': ('shirt', 'denim', None, None, None),

    # Shorts
    'Shorts': ('shorts', None, None, None, None),
    'Denim shorts': ('shorts', 'denim', None, None, None),
    'Cargo shorts': ('shorts', None, None, None, None),
    'Chino shorts': ('shorts', None, None, None, None),
    'Work shorts': ('shorts', None, None, None, None),
    'Sport shorts': ('sports-shorts', None, None, None, None),

    # Sweatshirts & Hoodies
    'Crewneck sweatshirt': ('sweatshirt', None, 'crew neck', None, None),
    'Hoodie sweatshirt': ('hoodie', None, 'hood', None, None),

    # Sweaters
    'V-neck sweater': ('sweater', None, 'v-neck', None, None),
    'Turtleneck sweater': ('sweater', None, 'turtleneck', None, None),
    'Crew neck sweater': ('sweater', None, 'crew neck', None, None),

    # Jackets
    'Jacket': ('jacket', None, None, None, None),
    'Denim jacket': ('jacket', 'denim', None, None, None),
    'Leather jacket': ('jacket', 'leather', None, None, None),
    'Work jacket': ('jacket', None, None, None, None),
    'Sport jacket': ('jacket', None, None, None, None),
    'Rework jacket': ('jacket', None, None, None, None),
    'Puffer jacket': ('puffer', None, None, None, None),
    'Varsity jacket': ('jacket', None, None, None, None),
    'Raincoat/Windbreaker': ('windbreaker', None, None, None, None),
    'Trench Coat': ('trench', None, None, None, None),

    # Other clothing
    'Joggers': ('joggers', None, None, None, None),
    'Half-zip': ('half-zip', None, None, None, None),
    'Fleece': ('fleece', None, None, None, None),
    'Vest': ('vest', None, None, None, None),
    'Polo': ('polo', None, 'polo collar', None, None),
    'Denim skirt': ('skirt', 'denim', None, None, None),
    'Work coveralls': ('overalls', None, None, None, None),

    # Sports
    'Rugby jersey': ('sports-jersey', None, None, None, None),
    'Baseball jersey': ('sports-jersey', None, None, None, None),
}

# Categories to map to 'other' and set as DRAFT
CATEGORIES_TO_OTHER = ['Other', 'Sunglasses', 'Uncategorized']


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
    Normalize categories and extract attributes for all user schemas.
    """
    connection = op.get_bind()

    # 1. First, create 'other' category if it doesn't exist
    print("\n=== Creating 'other' category if needed ===")
    connection.execute(sa.text("""
        INSERT INTO product_attributes.categories (name_en, name_fr, parent_category)
        VALUES ('other', 'Autre', NULL)
        ON CONFLICT (name_en) DO NOTHING
    """))
    print("  ✓ Category 'other' ensured\n")

    # Get all user schemas
    user_schemas = get_user_schemas(connection)
    print(f"=== Normalizing categories for {len(user_schemas)} user schemas ===\n")

    for schema in user_schemas:
        print(f"Processing {schema}...")

        # Skip if products table doesn't exist in this schema
        if not table_exists(connection, schema, 'products'):
            print(f"  ⚠️  Skipping {schema} - products table does not exist\n")
            continue

        # 1. Apply category mapping and extract attributes
        for old_cat, (new_cat, material, neckline, pattern, fit) in CATEGORY_MAPPING.items():
            # Build the UPDATE query dynamically
            update_parts = [f"category = '{new_cat}'"]

            if material:
                update_parts.append(f"material = COALESCE(material, '{material}')")
            if neckline:
                update_parts.append(f"neckline = COALESCE(neckline, '{neckline}')")
            if pattern:
                update_parts.append(f"pattern = COALESCE(pattern, '{pattern}')")
            if fit:
                update_parts.append(f"fit = COALESCE(fit, '{fit}')")

            update_sql = f"""
                UPDATE {schema}.products
                SET {', '.join(update_parts)}
                WHERE category = '{old_cat}'
            """
            result = connection.execute(sa.text(update_sql))
            if result.rowcount > 0:
                extracted = []
                if material: extracted.append(f"material={material}")
                if neckline: extracted.append(f"neckline={neckline}")
                if pattern: extracted.append(f"pattern={pattern}")
                if fit: extracted.append(f"fit={fit}")
                extras = f" (extracted: {', '.join(extracted)})" if extracted else ""
                print(f"  {old_cat} -> {new_cat}: {result.rowcount} rows{extras}")

        # 2. Set products without mapping to 'other' and DRAFT status
        for old_cat in CATEGORIES_TO_OTHER:
            result = connection.execute(sa.text(f"""
                UPDATE {schema}.products
                SET category = 'other', status = 'DRAFT'
                WHERE category = '{old_cat}'
            """))
            if result.rowcount > 0:
                print(f"  {old_cat} -> other (set to DRAFT): {result.rowcount} rows")

        print(f"  ✓ {schema} completed\n")

    # Also update template_tenant
    print("Processing template_tenant...")
    for old_cat, (new_cat, material, neckline, pattern, fit) in CATEGORY_MAPPING.items():
        update_parts = [f"category = '{new_cat}'"]
        if material:
            update_parts.append(f"material = COALESCE(material, '{material}')")
        if neckline:
            update_parts.append(f"neckline = COALESCE(neckline, '{neckline}')")
        if pattern:
            update_parts.append(f"pattern = COALESCE(pattern, '{pattern}')")
        if fit:
            update_parts.append(f"fit = COALESCE(fit, '{fit}')")

        connection.execute(sa.text(f"""
            UPDATE template_tenant.products
            SET {', '.join(update_parts)}
            WHERE category = '{old_cat}'
        """))

    for old_cat in CATEGORIES_TO_OTHER:
        connection.execute(sa.text(f"""
            UPDATE template_tenant.products
            SET category = 'other', status = 'DRAFT'
            WHERE category = '{old_cat}'
        """))

    print("  ✓ template_tenant completed\n")
    print("=== Category normalization complete ===\n")


def downgrade() -> None:
    """
    Revert category normalization is complex and potentially lossy.
    This is a one-way migration - manual intervention required for rollback.
    """
    print("\n⚠️  WARNING: This migration cannot be automatically reverted.")
    print("The original category names have been transformed and attributes extracted.")
    print("Manual data restoration from backup would be required.\n")

    # We don't automatically revert because:
    # 1. The original category names are lost
    # 2. Extracted attributes may have been modified by users
    # 3. Products set to DRAFT may have been edited
    pass
