"""Convert unique_feature and condition_sup to JSONB

Converts:
- unique_feature: Text (comma-separated) -> JSONB array
- condition_sup: String(255) -> JSONB array

Benefits:
- Better querying with PostgreSQL JSONB operators
- No parsing needed in application
- Can use GIN indexes for fast searches

Revision ID: 20250103_0300
Revises: 20250103_0200
Create Date: 2025-01-03
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers
revision = "20250103_0300"
down_revision = "20250103_0200"
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
    """Convert unique_feature and condition_sup to JSONB."""
    connection = op.get_bind()

    print("\n" + "=" * 60)
    print("Converting unique_feature and condition_sup to JSONB")
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
        print(f"\n--- Processing {schema} ---")

        # 1. Convert unique_feature: comma-separated string -> JSONB array
        # First, add a temporary column
        connection.execute(
            text(f"""
                ALTER TABLE {schema}.products
                ADD COLUMN IF NOT EXISTS unique_feature_new JSONB
            """)
        )

        # Convert existing data: "a,b,c" -> ["a", "b", "c"]
        connection.execute(
            text(f"""
                UPDATE {schema}.products
                SET unique_feature_new = (
                    SELECT jsonb_agg(trim(elem))
                    FROM unnest(string_to_array(unique_feature, ',')) AS elem
                    WHERE trim(elem) != ''
                )
                WHERE unique_feature IS NOT NULL AND unique_feature != ''
            """)
        )

        # Drop old column and rename new
        connection.execute(
            text(f"ALTER TABLE {schema}.products DROP COLUMN IF EXISTS unique_feature")
        )
        connection.execute(
            text(f"ALTER TABLE {schema}.products RENAME COLUMN unique_feature_new TO unique_feature")
        )

        print(f"  ✓ unique_feature converted to JSONB array")

        # 2. Convert condition_sup: string -> JSONB array
        # First, add a temporary column
        connection.execute(
            text(f"""
                ALTER TABLE {schema}.products
                ADD COLUMN IF NOT EXISTS condition_sup_new JSONB
            """)
        )

        # Convert existing data: "detail text" -> ["detail text"]
        # If comma-separated, split into array
        connection.execute(
            text(f"""
                UPDATE {schema}.products
                SET condition_sup_new = (
                    CASE
                        WHEN condition_sup LIKE '%,%' THEN (
                            SELECT jsonb_agg(trim(elem))
                            FROM unnest(string_to_array(condition_sup, ',')) AS elem
                            WHERE trim(elem) != ''
                        )
                        ELSE jsonb_build_array(condition_sup)
                    END
                )
                WHERE condition_sup IS NOT NULL AND condition_sup != ''
            """)
        )

        # Drop old column and rename new
        connection.execute(
            text(f"ALTER TABLE {schema}.products DROP COLUMN IF EXISTS condition_sup")
        )
        connection.execute(
            text(f"ALTER TABLE {schema}.products RENAME COLUMN condition_sup_new TO condition_sup")
        )

        print(f"  ✓ condition_sup converted to JSONB array")

    print("\n" + "=" * 60)
    print("✅ Migration complete - both columns now JSONB")
    print("=" * 60)


def downgrade() -> None:
    """Convert back to text/string columns."""
    connection = op.get_bind()

    print("\n" + "=" * 60)
    print("Converting unique_feature and condition_sup back to text")
    print("=" * 60)

    # Get all user schemas
    user_schemas = get_user_schemas(connection)
    all_schemas = ["template_tenant"] + user_schemas

    # Filter schemas that have products table
    schemas_with_products = [s for s in all_schemas if table_exists(connection, s, "products")]

    for schema in schemas_with_products:
        print(f"\n--- Processing {schema} ---")

        # 1. Convert unique_feature: JSONB array -> comma-separated string
        connection.execute(
            text(f"""
                ALTER TABLE {schema}.products
                ADD COLUMN IF NOT EXISTS unique_feature_old TEXT
            """)
        )

        # Convert: ["a", "b", "c"] -> "a,b,c"
        connection.execute(
            text(f"""
                UPDATE {schema}.products
                SET unique_feature_old = (
                    SELECT string_agg(elem::text, ',')
                    FROM jsonb_array_elements_text(unique_feature) AS elem
                )
                WHERE unique_feature IS NOT NULL
            """)
        )

        connection.execute(
            text(f"ALTER TABLE {schema}.products DROP COLUMN IF EXISTS unique_feature")
        )
        connection.execute(
            text(f"ALTER TABLE {schema}.products RENAME COLUMN unique_feature_old TO unique_feature")
        )

        print(f"  ✓ unique_feature converted back to TEXT")

        # 2. Convert condition_sup: JSONB array -> string
        connection.execute(
            text(f"""
                ALTER TABLE {schema}.products
                ADD COLUMN IF NOT EXISTS condition_sup_old VARCHAR(255)
            """)
        )

        # Convert: ["a", "b"] -> "a,b"
        connection.execute(
            text(f"""
                UPDATE {schema}.products
                SET condition_sup_old = (
                    SELECT string_agg(elem::text, ',')
                    FROM jsonb_array_elements_text(condition_sup) AS elem
                )
                WHERE condition_sup IS NOT NULL
            """)
        )

        connection.execute(
            text(f"ALTER TABLE {schema}.products DROP COLUMN IF EXISTS condition_sup")
        )
        connection.execute(
            text(f"ALTER TABLE {schema}.products RENAME COLUMN condition_sup_old TO condition_sup")
        )

        print(f"  ✓ condition_sup converted back to VARCHAR(255)")

    print("\n✅ Downgrade complete")
