"""Add missing FK constraints for 8 product attributes

Adds Foreign Key constraints for columns that have corresponding
attribute tables but were missing FK definitions:
- sport -> product_attributes.sports.name_en
- length -> product_attributes.lengths.name_en
- rise -> product_attributes.rises.name_en
- closure -> product_attributes.closures.name_en
- sleeve_length -> product_attributes.sleeve_lengths.name_en
- origin -> product_attributes.origins.name_en
- decade -> product_attributes.decades.name_en
- trend -> product_attributes.trends.name_en

Revision ID: 20250103_0100
Revises: 20251230_0300
Create Date: 2025-01-03
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers
revision = "20250103_0100"
down_revision = "20251230_0300"
branch_labels = None
depends_on = None

# FK configurations: (column_name, target_table, target_column)
FK_CONFIGS = [
    ("sport", "sports", "name_en"),
    ("length", "lengths", "name_en"),
    ("rise", "rises", "name_en"),
    ("closure", "closures", "name_en"),
    ("sleeve_length", "sleeve_lengths", "name_en"),
    ("origin", "origins", "name_en"),
    ("decade", "decades", "name_en"),
    ("trend", "trends", "name_en"),
]


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


def normalize_values_for_column(connection, schema: str, column: str, target_table: str) -> dict:
    """
    Check and report invalid values for a column before adding FK.
    Returns dict with stats.
    """
    # Get distinct values in the column
    result = connection.execute(
        text(f"""
            SELECT DISTINCT {column}
            FROM {schema}.products
            WHERE {column} IS NOT NULL
        """)
    )
    product_values = {row[0] for row in result.fetchall()}

    if not product_values:
        return {"total": 0, "invalid": [], "valid": 0}

    # Get valid values from attribute table
    result = connection.execute(
        text(f"""
            SELECT name_en
            FROM product_attributes.{target_table}
        """)
    )
    valid_values = {row[0] for row in result.fetchall()}

    # Find invalid values
    invalid_values = product_values - valid_values

    return {
        "total": len(product_values),
        "invalid": list(invalid_values),
        "valid": len(product_values) - len(invalid_values)
    }


def upgrade() -> None:
    """Add FK constraints for 8 missing attributes."""
    connection = op.get_bind()

    print("\n" + "=" * 60)
    print("Adding 8 missing FK constraints to products table")
    print("=" * 60)

    # Get all user schemas
    user_schemas = get_user_schemas(connection)
    all_schemas = ["template_tenant"] + user_schemas

    print(f"\nSchemas to process: {len(all_schemas)}")

    errors = []

    for column, target_table, target_column in FK_CONFIGS:
        print(f"\n--- Processing: {column} -> {target_table}.{target_column} ---")

        for schema in all_schemas:
            # Check for invalid values first
            stats = normalize_values_for_column(connection, schema, column, target_table)

            if stats["invalid"]:
                print(f"  ⚠️  {schema}: {len(stats['invalid'])} invalid values found")
                for val in stats["invalid"][:5]:  # Show first 5
                    print(f"      - '{val}'")
                if len(stats["invalid"]) > 5:
                    print(f"      ... and {len(stats['invalid']) - 5} more")

                # Set invalid values to NULL
                for invalid_val in stats["invalid"]:
                    connection.execute(
                        text(f"""
                            UPDATE {schema}.products
                            SET {column} = NULL
                            WHERE {column} = :val
                        """),
                        {"val": invalid_val}
                    )
                print(f"      → Set {len(stats['invalid'])} invalid values to NULL")

            # Check if FK already exists
            fk_name = f"fk_{schema}_products_{column}"
            result = connection.execute(
                text("""
                    SELECT 1
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu
                        ON tc.constraint_name = kcu.constraint_name
                        AND tc.table_schema = kcu.table_schema
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND tc.table_schema = :schema
                    AND tc.table_name = 'products'
                    AND kcu.column_name = :column
                """),
                {"schema": schema, "column": column}
            )

            if result.fetchone():
                print(f"  ✓ {schema}: FK already exists, skipping")
                continue

            # Add FK constraint
            try:
                connection.execute(
                    text(f"""
                        ALTER TABLE {schema}.products
                        ADD CONSTRAINT {fk_name}
                        FOREIGN KEY ({column})
                        REFERENCES product_attributes.{target_table}({target_column})
                        ON UPDATE CASCADE
                        ON DELETE SET NULL
                    """)
                )
                print(f"  ✓ {schema}: FK added successfully")
            except Exception as e:
                error_msg = f"{schema}.{column}: {str(e)}"
                errors.append(error_msg)
                print(f"  ✗ {schema}: ERROR - {str(e)[:100]}")

    # Summary
    print("\n" + "=" * 60)
    print("MIGRATION SUMMARY")
    print("=" * 60)

    if errors:
        print(f"\n❌ {len(errors)} errors occurred:")
        for err in errors:
            print(f"  - {err}")
    else:
        print("\n✅ All FK constraints added successfully!")

    print("\n" + "=" * 60)


def downgrade() -> None:
    """Remove the 8 FK constraints."""
    connection = op.get_bind()

    print("\n" + "=" * 60)
    print("Removing 8 FK constraints from products table")
    print("=" * 60)

    # Get all user schemas
    user_schemas = get_user_schemas(connection)
    all_schemas = ["template_tenant"] + user_schemas

    for column, _, _ in FK_CONFIGS:
        print(f"\n--- Removing FK for: {column} ---")

        for schema in all_schemas:
            fk_name = f"fk_{schema}_products_{column}"
            try:
                connection.execute(
                    text(f"""
                        ALTER TABLE {schema}.products
                        DROP CONSTRAINT IF EXISTS {fk_name}
                    """)
                )
                print(f"  ✓ {schema}: FK removed")
            except Exception as e:
                print(f"  ✗ {schema}: ERROR - {str(e)[:100]}")

    print("\n✅ Downgrade complete")
