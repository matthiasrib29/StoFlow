"""normalize_all_remaining_attributes_title_case

Revision ID: b5ac89614dfc
Revises: 1111dba9b7f2
Create Date: 2026-01-07 13:12:40.783308+01:00

Normalize ALL remaining attributes to Title Case:
- colors, genders, closures, origins, rises, sleeve_lengths, necklines, lengths
- condition_sups, decades, trends, unique_features, sports, patterns
- Total: ~8628 products affected
"""
from typing import Sequence, Union


from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

from logging import getLogger

logger = getLogger(__name__)


# revision identifiers, used by Alembic.
revision: str = 'b5ac89614dfc'
down_revision: Union[str, None] = '1111dba9b7f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def get_user_schemas(conn):
    """Get list of user schemas."""
    result = conn.execute(text("""
        SELECT schema_name FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%'
        ORDER BY schema_name
    """))
    return [row[0] for row in result]


def table_exists(conn, schema, table):
    """Check if a table exists."""
    result = conn.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = :schema AND table_name = :table
        )
    """), {"schema": schema, "table": table})
    return result.scalar()


def normalize_table(conn, table_name, schemas=None):
    """
    Normalize all lowercase values in a table to Title Case.
    If schemas provided, also update products.

    Args:
        conn: Database connection
        table_name: Name of the attribute table
        schemas: List of user schemas (for product updates)
    """
    # Check if table exists first (idempotent)
    if not table_exists(conn, 'product_attributes', table_name):
        logger.info(f"  ⏭️  {table_name}: Table does not exist, skipping")
        return 0

    # Get all lowercase values
    result = conn.execute(text(f"""
        SELECT name_en FROM product_attributes.{table_name}
        WHERE name_en ~ '^[a-z]'
        ORDER BY name_en
    """))
    lowercase_values = [row[0] for row in result]

    if not lowercase_values:
        logger.info(f"  ✅ {table_name}: Already normalized")
        return 0

    logger.info(f"  🔄 {table_name}: Normalizing {len(lowercase_values)} values...")

    # Create mapping
    mappings = {val: val.capitalize() for val in lowercase_values}

    # Update attribute table
    for old_val, new_val in mappings.items():
        conn.execute(text(f"""
            UPDATE product_attributes.{table_name}
            SET name_en = :new_val
            WHERE name_en = :old_val
        """), {"old_val": old_val, "new_val": new_val})

    return len(lowercase_values)


def normalize_products_column(conn, schemas, column_name, mappings):
    """Update product column with normalized values."""
    if not mappings:
        return

    updated = 0
    for schema in schemas:
        if not table_exists(conn, schema, 'products'):
            continue

        for old_val, new_val in mappings.items():
            result = conn.execute(text(f"""
                UPDATE {schema}.products
                SET {column_name} = :new_val
                WHERE {column_name} = :old_val
            """), {"old_val": old_val, "new_val": new_val})
            updated += result.rowcount

    return updated


def upgrade() -> None:
    """Normalize all remaining attributes to Title Case."""
    conn = op.get_bind()

    logger.info("=" * 70)
    logger.info("🔄 NORMALIZING ALL ATTRIBUTES TO TITLE CASE")
    logger.info("=" * 70)

    # Get user schemas
    user_schemas = get_user_schemas(conn)
    logger.info(f"\nFound {len(user_schemas)} user schemas\n")

    # Tables with products FK (need product updates)
    tables_with_fk = [
        ('colors', 'color'),
        ('genders', 'gender'),
        ('closures', 'closure'),
        ('origins', 'origin'),
        ('rises', 'rise'),
        ('sleeve_lengths', 'sleeve_length'),
        ('necklines', 'neckline'),
        ('lengths', 'length'),
    ]

    # Tables without products FK (just attribute normalization)
    tables_no_fk = [
        'condition_sups',
        'decades',
        'trends',
        'unique_features',
        'sports',
        'patterns',
    ]

    total_normalized = 0
    total_products = 0

    # ===== 1. NORMALIZE ATTRIBUTE TABLES FIRST (FK constraint) =====

    logger.info("📦 STEP 1: Normalizing attribute tables...")

    # Tables with FK
    for table_name, column_name in tables_with_fk:
        count = normalize_table(conn, table_name)
        total_normalized += count

    # Tables without FK
    for table_name in tables_no_fk:
        count = normalize_table(conn, table_name)
        total_normalized += count

    # ===== 2. UPDATE PRODUCTS =====

    logger.info(f"\n📦 STEP 2: Updating products in {len(user_schemas)} schemas...")

    for table_name, column_name in tables_with_fk:
        # Skip if table doesn't exist
        if not table_exists(conn, 'product_attributes', table_name):
            continue

        # Get lowercase values (before normalization)
        result = conn.execute(text(f"""
            SELECT name_en FROM product_attributes.{table_name}
            WHERE name_en ~ '^[A-Z]'
            ORDER BY name_en
        """))
        capitalized_values = [row[0] for row in result]

        if not capitalized_values:
            continue

        # Recreate mapping (capitalized → original lowercase)
        mappings = {val.lower(): val for val in capitalized_values}

        logger.info(f"  🔄 Updating {column_name} column...")
        updated = normalize_products_column(conn, user_schemas, column_name, mappings)
        total_products += updated
        logger.info(f"     Updated {updated} products")

    logger.info("\n" + "=" * 70)
    logger.info(f"✅ NORMALIZATION COMPLETE")
    logger.info(f"   Attribute values normalized: {total_normalized}")
    logger.info(f"   Products updated: {total_products}")
    logger.info("=" * 70)


def downgrade() -> None:
    """Revert Title Case normalization."""
    conn = op.get_bind()

    logger.info("=" * 70)
    logger.info("🔙 REVERTING NORMALIZATION")
    logger.info("=" * 70)

    # Get user schemas
    user_schemas = get_user_schemas(conn)

    # Tables to revert
    all_tables = [
        ('colors', 'color'),
        ('genders', 'gender'),
        ('closures', 'closure'),
        ('origins', 'origin'),
        ('rises', 'rise'),
        ('sleeve_lengths', 'sleeve_length'),
        ('necklines', 'neckline'),
        ('lengths', 'length'),
        ('condition_sups', None),
        ('decades', None),
        ('trends', None),
        ('unique_features', None),
        ('sports', None),
        ('patterns', None),
    ]

    # Revert: Title Case → lowercase
    for table_info in all_tables:
        table_name = table_info[0] if isinstance(table_info, tuple) else table_info
        column_name = table_info[1] if isinstance(table_info, tuple) and len(table_info) > 1 else None

        logger.info(f"  🔄 Reverting {table_name}...")

        # Get all Title Case values
        result = conn.execute(text(f"""
            SELECT name_en FROM product_attributes.{table_name}
            WHERE name_en ~ '^[A-Z]'
        """))
        capitalized = [row[0] for row in result]

        if not capitalized:
            continue

        # Revert attribute table
        for val in capitalized:
            lower_val = val.lower()
            conn.execute(text(f"""
                UPDATE product_attributes.{table_name}
                SET name_en = :lower_val
                WHERE name_en = :val
            """), {"lower_val": lower_val, "val": val})

        # Revert products if FK exists
        if column_name:
            for schema in user_schemas:
                if not table_exists(conn, schema, 'products'):
                    continue

                for val in capitalized:
                    lower_val = val.lower()
                    conn.execute(text(f"""
                        UPDATE {schema}.products
                        SET {column_name} = :lower_val
                        WHERE {column_name} = :val
                    """), {"lower_val": lower_val, "val": val})

    logger.info("✅ Normalization reverted successfully!")
