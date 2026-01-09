"""rename_size_columns

Revision ID: 20251230_0300
Revises: 20251230_0200
Create Date: 2025-12-30

This migration renames size columns for clarity:
- size -> size_normalized (standardized size, FK to product_attributes.sizes)
- label_size -> size_original (original size from label, free text)

Author: Claude
Date: 2025-12-30
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20251230_0300'
down_revision: Union[str, None] = '20251230_0200'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def get_user_schemas(connection) -> list[str]:
    """Get all user schemas (user_1, user_2, etc.) + template_tenant"""
    result = connection.execute(sa.text(
        "SELECT schema_name FROM information_schema.schemata "
        "WHERE schema_name LIKE 'user_%' AND schema_name != 'user_template' "
        "ORDER BY schema_name"
    ))
    schemas = [row[0] for row in result]
    schemas.append('template_tenant')
    return schemas


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
    Rename size columns in all schemas.
    """
    connection = op.get_bind()
    schemas = get_user_schemas(connection)

    print(f"\n=== Renaming size columns in {len(schemas)} schemas ===\n")

    for schema in schemas:
        print(f"Processing {schema}...")

        # Skip if products table doesn't exist in this schema
        if not table_exists(connection, schema, 'products'):
            print(f"  ⚠️  Skipping {schema} - products table does not exist\n")
            continue

        # 1. Drop FK constraint on size (if exists)
        try:
            connection.execute(sa.text(f"""
                ALTER TABLE {schema}.products
                DROP CONSTRAINT IF EXISTS fk_products_size
            """))
        except Exception:
            pass

        # 2. Rename size -> size_normalized
        try:
            connection.execute(sa.text(f"""
                ALTER TABLE {schema}.products
                RENAME COLUMN size TO size_normalized
            """))
            print(f"  ✓ size -> size_normalized")
        except Exception as e:
            print(f"  ⚠️ size rename failed: {e}")

        # 3. Rename label_size -> size_original
        try:
            connection.execute(sa.text(f"""
                ALTER TABLE {schema}.products
                RENAME COLUMN label_size TO size_original
            """))
            print(f"  ✓ label_size -> size_original")
        except Exception as e:
            print(f"  ⚠️ label_size rename failed: {e}")

        # 4. Rename index if exists
        try:
            connection.execute(sa.text(f"""
                ALTER INDEX IF EXISTS {schema}.idx_product_size
                RENAME TO idx_product_size_normalized
            """))
        except Exception:
            pass

        # 5. Re-add FK constraint with new column name
        try:
            connection.execute(sa.text(f"""
                ALTER TABLE {schema}.products
                ADD CONSTRAINT fk_products_size_normalized
                FOREIGN KEY (size_normalized)
                REFERENCES product_attributes.sizes(name_en)
                ON UPDATE CASCADE
                ON DELETE SET NULL
            """))
            print(f"  ✓ FK constraint re-added")
        except Exception as e:
            print(f"  ⚠️ FK re-add failed: {e}")

        print(f"  ✓ {schema} completed\n")

    print("=== Column rename complete ===\n")


def downgrade() -> None:
    """
    Revert column renames.
    """
    connection = op.get_bind()
    schemas = get_user_schemas(connection)

    print(f"\n=== Reverting size column renames in {len(schemas)} schemas ===\n")

    for schema in schemas:
        print(f"Processing {schema}...")

        # Drop new FK
        try:
            connection.execute(sa.text(f"""
                ALTER TABLE {schema}.products
                DROP CONSTRAINT IF EXISTS fk_products_size_normalized
            """))
        except Exception:
            pass

        # Rename back
        try:
            connection.execute(sa.text(f"""
                ALTER TABLE {schema}.products
                RENAME COLUMN size_normalized TO size
            """))
            connection.execute(sa.text(f"""
                ALTER TABLE {schema}.products
                RENAME COLUMN size_original TO label_size
            """))
        except Exception as e:
            print(f"  ⚠️ Rename failed: {e}")

        # Re-add original FK
        try:
            connection.execute(sa.text(f"""
                ALTER TABLE {schema}.products
                ADD CONSTRAINT fk_products_size
                FOREIGN KEY (size)
                REFERENCES product_attributes.sizes(name_en)
                ON UPDATE CASCADE
                ON DELETE SET NULL
            """))
        except Exception:
            pass

        print(f"  ✓ {schema} completed\n")

    print("=== Revert complete ===\n")
