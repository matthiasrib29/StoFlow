"""Remove photo_url, manufacturer, model from vinted_products

Revision ID: 20260105_1450
Revises: 20260105_1400
Create Date: 2026-01-05 14:30:00.000000

Removes deprecated columns:
- photo_url: Replaced by primary_photo_url property (reads from photos_data)
- manufacturer: Never used in business logic
- model: Never used in business logic
"""
from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = '20260105_1450'
down_revision = '20260105_1400'
branch_labels = None
depends_on = None


COLUMNS_TO_DROP = [
    "photo_url",
    "manufacturer",
    "model",
]


def upgrade():
    """Remove deprecated columns from vinted_products in all user schemas and template_tenant."""
    conn = op.get_bind()

    # Get all user schemas + template_tenant
    result = conn.execute(text("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%'
           OR schema_name = 'template_tenant'
        ORDER BY schema_name
    """))
    schemas = [row[0] for row in result]

    if not schemas:
        print("No schemas found, skipping migration")
        return

    print(f"Found {len(schemas)} schemas to migrate")

    for schema in schemas:
        # Check if table exists in this schema
        table_exists = conn.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = :schema AND table_name = 'vinted_products'
            )
        """), {"schema": schema}).scalar()

        if not table_exists:
            print(f"  {schema}: vinted_products table not found, skipping")
            continue

        # Drop each column if it exists
        for column in COLUMNS_TO_DROP:
            column_exists = conn.execute(text("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = :schema
                    AND table_name = 'vinted_products'
                    AND column_name = :column
                )
            """), {"schema": schema, "column": column}).scalar()

            if column_exists:
                conn.execute(text(f"""
                    ALTER TABLE {schema}.vinted_products
                    DROP COLUMN IF EXISTS {column}
                """))
                print(f"  {schema}: dropped column {column}")

    print("Migration completed successfully")


def downgrade():
    """Re-add the removed columns to vinted_products in all schemas."""
    conn = op.get_bind()

    # Get all user schemas + template_tenant
    result = conn.execute(text("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%'
           OR schema_name = 'template_tenant'
        ORDER BY schema_name
    """))
    schemas = [row[0] for row in result]

    if not schemas:
        return

    # Column definitions for recreation
    columns_to_add = [
        ("photo_url", "TEXT DEFAULT NULL"),
        ("manufacturer", "VARCHAR(200) DEFAULT NULL"),
        ("model", "VARCHAR(200) DEFAULT NULL"),
    ]

    for schema in schemas:
        table_exists = conn.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = :schema AND table_name = 'vinted_products'
            )
        """), {"schema": schema}).scalar()

        if not table_exists:
            continue

        for column_name, column_type in columns_to_add:
            column_exists = conn.execute(text("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = :schema
                    AND table_name = 'vinted_products'
                    AND column_name = :column
                )
            """), {"schema": schema, "column": column_name}).scalar()

            if not column_exists:
                conn.execute(text(f"""
                    ALTER TABLE {schema}.vinted_products
                    ADD COLUMN {column_name} {column_type}
                """))
                print(f"  {schema}: added column {column_name}")
