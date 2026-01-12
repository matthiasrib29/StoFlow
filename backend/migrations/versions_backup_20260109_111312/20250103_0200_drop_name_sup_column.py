"""Drop name_sup column from products

The name_sup column was never used and is redundant with title.

Revision ID: 20250103_0200
Revises: 20250103_0100
Create Date: 2025-01-03
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers
revision = "20250103_0200"
down_revision = "20250103_0100"
branch_labels = None
depends_on = None


def get_user_schemas(connection) -> list[str]:
    """Get all user_X schemas."""
    result = connection.execute(
        text("""
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name LIKE 'user_%'
            ORDER BY schema_name
        """)
    )
    return [row[0] for row in result.fetchall()]


def table_exists(connection, schema: str, table: str) -> bool:
    """Check if a table exists in a specific schema."""
    result = connection.execute(
        text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = :schema AND table_name = :table
            )
        """),
        {"schema": schema, "table": table}
    )
    return result.scalar()


def upgrade() -> None:
    """Drop name_sup column from all products tables."""
    connection = op.get_bind()

    print("\n" + "=" * 60)
    print("Dropping name_sup column from products")
    print("=" * 60)

    # Get all user schemas
    user_schemas = get_user_schemas(connection)
    all_schemas = ["template_tenant"] + user_schemas

    # Filter schemas that have products table
    schemas_with_products = [s for s in all_schemas if table_exists(connection, s, "products")]
    skipped = len(all_schemas) - len(schemas_with_products)
    if skipped > 0:
        print(f"\n⚠️  Skipping {skipped} schemas without products table")

    print(f"\nSchemas to process: {len(schemas_with_products)}")

    for schema in schemas_with_products:
        # Check if column exists
        result = connection.execute(
            text("""
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = :schema
                AND table_name = 'products'
                AND column_name = 'name_sup'
            """),
            {"schema": schema}
        )

        if result.fetchone():
            connection.execute(
                text(f"ALTER TABLE {schema}.products DROP COLUMN name_sup")
            )
            print(f"  ✓ {schema}: name_sup dropped")
        else:
            print(f"  - {schema}: name_sup not found (already dropped)")

    print("\n✅ Migration complete")


def downgrade() -> None:
    """Re-add name_sup column to all products tables."""
    connection = op.get_bind()

    print("\n" + "=" * 60)
    print("Re-adding name_sup column to products")
    print("=" * 60)

    # Get all user schemas
    user_schemas = get_user_schemas(connection)
    all_schemas = ["template_tenant"] + user_schemas

    # Filter schemas that have products table
    schemas_with_products = [s for s in all_schemas if table_exists(connection, s, "products")]

    for schema in schemas_with_products:
        connection.execute(
            text(f"""
                ALTER TABLE {schema}.products
                ADD COLUMN name_sup VARCHAR(100) NULL
            """)
        )
        print(f"  ✓ {schema}: name_sup re-added")

    print("\n✅ Downgrade complete")
