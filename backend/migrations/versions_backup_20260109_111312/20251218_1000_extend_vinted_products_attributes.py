"""extend_vinted_products_attributes

Add complete product attributes to vinted_products table:
- IDs for brand, size, catalog, condition
- Material, measurements (with parsed width/length)
- Manufacturer labelling
- Additional status flags (is_reserved, is_hidden)
- Seller info (seller_id, seller_login)
- Fees (service_fee, buyer_protection_fee, shipping_price, total_price)
- Rename date -> published_at (DateTime for precise timestamps from images)

Revision ID: 20251218_1000
Revises: ca33d9632b06
Create Date: 2025-12-18 10:00:00.000000

Author: Claude
Date: 2025-12-18
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '20251218_1000'
down_revision: Union[str, None] = 'ca33d9632b06'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def get_user_schemas(connection) -> list[str]:
    """Get all user schemas (user_X pattern)."""
    result = connection.execute(text("""
        SELECT schema_name FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%'
        ORDER BY schema_name
    """))
    return [row[0] for row in result]


def column_exists(connection, schema: str, table: str, column: str) -> bool:
    """Check if column exists in table."""
    result = connection.execute(text(f"""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = '{schema}'
            AND table_name = '{table}'
            AND column_name = '{column}'
        )
    """))
    return result.scalar()


def add_columns_to_schema(connection, schema: str) -> None:
    """Add new columns to vinted_products in a schema."""

    # Check if table exists
    table_exists = connection.execute(text(f"""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = '{schema}'
            AND table_name = 'vinted_products'
        )
    """)).scalar()

    if not table_exists:
        print(f"  ⏭️  {schema}.vinted_products doesn't exist, skipping")
        return

    # List of columns to add: (name, type, default, comment)
    new_columns = [
        ('total_price', 'NUMERIC(10,2)', None, 'Prix total avec frais'),
        ('brand_id', 'INTEGER', None, 'ID Vinted de la marque'),
        ('size_id', 'INTEGER', None, 'ID Vinted de la taille'),
        ('catalog_id', 'INTEGER', None, 'ID Vinted de la catégorie'),
        ('condition_id', 'INTEGER', None, 'ID Vinted de l''état'),
        ('material', 'VARCHAR(100)', None, 'Matière'),
        ('measurements', 'VARCHAR(100)', None, 'Dimensions texte (l X cm / L Y cm)'),
        ('measurement_width', 'INTEGER', None, 'Largeur en cm'),
        ('measurement_length', 'INTEGER', None, 'Longueur en cm'),
        ('manufacturer_labelling', 'TEXT', None, 'Étiquetage du fabricant'),
        ('is_reserved', 'BOOLEAN', 'FALSE', 'Est réservé'),
        ('is_hidden', 'BOOLEAN', 'FALSE', 'Est masqué'),
        ('seller_id', 'BIGINT', None, 'ID vendeur Vinted'),
        ('seller_login', 'VARCHAR(100)', None, 'Login vendeur'),
        ('service_fee', 'NUMERIC(10,2)', None, 'Frais de service'),
        ('buyer_protection_fee', 'NUMERIC(10,2)', None, 'Frais protection acheteur'),
        ('shipping_price', 'NUMERIC(10,2)', None, 'Frais de port'),
    ]

    for col_name, col_type, default, comment in new_columns:
        if not column_exists(connection, schema, 'vinted_products', col_name):
            default_clause = f" DEFAULT {default}" if default else ""
            not_null = " NOT NULL" if default else ""
            connection.execute(text(f"""
                ALTER TABLE {schema}.vinted_products
                ADD COLUMN {col_name} {col_type}{not_null}{default_clause}
            """))
            if comment:
                connection.execute(text(f"""
                    COMMENT ON COLUMN {schema}.vinted_products.{col_name} IS '{comment}'
                """))
            print(f"  ✓ Added {schema}.vinted_products.{col_name}")
        else:
            print(f"  ⏭️  {schema}.vinted_products.{col_name} exists, skipping")

    # Rename date -> published_at and change type to TIMESTAMP WITH TIME ZONE
    if column_exists(connection, schema, 'vinted_products', 'date'):
        # Add published_at column
        if not column_exists(connection, schema, 'vinted_products', 'published_at'):
            connection.execute(text(f"""
                ALTER TABLE {schema}.vinted_products
                ADD COLUMN published_at TIMESTAMP WITH TIME ZONE
            """))
            # Copy data from date (if any) - date will be at midnight
            connection.execute(text(f"""
                UPDATE {schema}.vinted_products
                SET published_at = date::timestamp with time zone
                WHERE date IS NOT NULL
            """))
            connection.execute(text(f"""
                COMMENT ON COLUMN {schema}.vinted_products.published_at IS
                'Date de publication sur Vinted (from image timestamp)'
            """))
            print(f"  ✓ Added {schema}.vinted_products.published_at (migrated from date)")

        # Drop old date column
        connection.execute(text(f"""
            ALTER TABLE {schema}.vinted_products DROP COLUMN date
        """))
        print(f"  ✓ Dropped {schema}.vinted_products.date (replaced by published_at)")
    elif not column_exists(connection, schema, 'vinted_products', 'published_at'):
        # No date column, just add published_at
        connection.execute(text(f"""
            ALTER TABLE {schema}.vinted_products
            ADD COLUMN published_at TIMESTAMP WITH TIME ZONE
        """))
        connection.execute(text(f"""
            COMMENT ON COLUMN {schema}.vinted_products.published_at IS
            'Date de publication sur Vinted (from image timestamp)'
        """))
        print(f"  ✓ Added {schema}.vinted_products.published_at")

    # Add new indexes
    # catalog_id index
    index_name = f"idx_{schema.replace('user_', '')}_vinted_products_catalog_id"
    idx_exists = connection.execute(text(f"""
        SELECT EXISTS (
            SELECT 1 FROM pg_indexes
            WHERE schemaname = '{schema}'
            AND indexname = '{index_name}'
        )
    """)).scalar()
    if not idx_exists:
        try:
            connection.execute(text(f"""
                CREATE INDEX {index_name} ON {schema}.vinted_products(catalog_id)
            """))
            print(f"  ✓ Created index {index_name}")
        except Exception as e:
            print(f"  ⚠️  Could not create index {index_name}: {e}")

    # seller_id index
    index_name = f"idx_{schema.replace('user_', '')}_vinted_products_seller_id"
    idx_exists = connection.execute(text(f"""
        SELECT EXISTS (
            SELECT 1 FROM pg_indexes
            WHERE schemaname = '{schema}'
            AND indexname = '{index_name}'
        )
    """)).scalar()
    if not idx_exists:
        try:
            connection.execute(text(f"""
                CREATE INDEX {index_name} ON {schema}.vinted_products(seller_id)
            """))
            print(f"  ✓ Created index {index_name}")
        except Exception as e:
            print(f"  ⚠️  Could not create index {index_name}: {e}")

    # published_at index (replace date index)
    index_name = f"idx_{schema.replace('user_', '')}_vinted_products_published_at"
    idx_exists = connection.execute(text(f"""
        SELECT EXISTS (
            SELECT 1 FROM pg_indexes
            WHERE schemaname = '{schema}'
            AND indexname = '{index_name}'
        )
    """)).scalar()
    if not idx_exists:
        try:
            connection.execute(text(f"""
                CREATE INDEX {index_name} ON {schema}.vinted_products(published_at)
            """))
            print(f"  ✓ Created index {index_name}")
        except Exception as e:
            print(f"  ⚠️  Could not create index {index_name}: {e}")


def upgrade() -> None:
    """Add extended attributes to vinted_products in all schemas."""
    connection = op.get_bind()

    print("\n=== Extending vinted_products with new attributes ===\n")

    # Update template_tenant
    print("Processing template_tenant...")
    add_columns_to_schema(connection, 'template_tenant')

    # Update all user schemas
    user_schemas = get_user_schemas(connection)
    print(f"\nProcessing {len(user_schemas)} user schemas...")

    for schema in user_schemas:
        print(f"\nProcessing {schema}...")
        add_columns_to_schema(connection, schema)

    print("\n=== Migration complete ===\n")


def downgrade() -> None:
    """Remove extended attributes from vinted_products."""
    connection = op.get_bind()

    columns_to_drop = [
        'total_price', 'brand_id', 'size_id', 'catalog_id', 'condition_id',
        'material', 'measurements', 'measurement_width', 'measurement_length',
        'manufacturer_labelling', 'is_reserved', 'is_hidden',
        'seller_id', 'seller_login', 'service_fee', 'buyer_protection_fee', 'shipping_price'
    ]

    schemas = ['template_tenant'] + get_user_schemas(connection)

    for schema in schemas:
        table_exists = connection.execute(text(f"""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = '{schema}'
                AND table_name = 'vinted_products'
            )
        """)).scalar()

        if not table_exists:
            continue

        for col in columns_to_drop:
            if column_exists(connection, schema, 'vinted_products', col):
                connection.execute(text(f"""
                    ALTER TABLE {schema}.vinted_products DROP COLUMN {col}
                """))

        # Restore date column from published_at
        if column_exists(connection, schema, 'vinted_products', 'published_at'):
            connection.execute(text(f"""
                ALTER TABLE {schema}.vinted_products ADD COLUMN date DATE
            """))
            connection.execute(text(f"""
                UPDATE {schema}.vinted_products SET date = published_at::date
                WHERE published_at IS NOT NULL
            """))
            connection.execute(text(f"""
                ALTER TABLE {schema}.vinted_products DROP COLUMN published_at
            """))
