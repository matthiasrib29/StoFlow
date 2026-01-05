"""Add item_upload API fields to vinted_products

Revision ID: 20260105_1000
Revises: 151b3e941a9c
Create Date: 2026-01-05 10:00:00.000000

Adds new columns from Vinted item_upload API response:
- color1_id: Vinted color ID (primary)
- color2_id: Vinted color ID (secondary)
- color2: Secondary color name
- status_id: Vinted condition/status ID
- is_unisex: Whether item is unisex
- measurement_unit: Unit for measurements (cm, inches)
- item_attributes: JSON array of additional attributes
- manufacturer: Manufacturer name
- model: Model name
"""
from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = '20260105_1000'
down_revision = '151b3e941a9c'
branch_labels = None
depends_on = None


NEW_COLUMNS = [
    ("color1_id", "INTEGER DEFAULT NULL"),
    ("color2_id", "INTEGER DEFAULT NULL"),
    ("color2", "VARCHAR(50) DEFAULT NULL"),
    ("status_id", "INTEGER DEFAULT NULL"),
    ("is_unisex", "BOOLEAN DEFAULT FALSE"),
    ("measurement_unit", "VARCHAR(20) DEFAULT NULL"),
    ("item_attributes", "JSONB DEFAULT NULL"),
    ("manufacturer", "VARCHAR(200) DEFAULT NULL"),
    ("model", "VARCHAR(200) DEFAULT NULL"),
]


def upgrade():
    """Add item_upload API fields to vinted_products in all user schemas."""
    conn = op.get_bind()

    # Get all user schemas
    result = conn.execute(text("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%'
        AND schema_name <> 'user_invalid'
        ORDER BY schema_name
    """))
    user_schemas = [row[0] for row in result.fetchall()]

    for schema in user_schemas:
        # Check if vinted_products table exists in this schema
        table_exists = conn.execute(text(f"""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = '{schema}'
                AND table_name = 'vinted_products'
            )
        """)).scalar()

        if not table_exists:
            print(f"vinted_products table doesn't exist in {schema}, skipping")
            continue

        # Check if color1_id column already exists (first column we add)
        column_exists = conn.execute(text(f"""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = '{schema}'
                AND table_name = 'vinted_products'
                AND column_name = 'color1_id'
            )
        """)).scalar()

        if column_exists:
            print(f"Item upload columns already exist in {schema}.vinted_products, skipping")
            continue

        print(f"Adding item_upload columns to {schema}.vinted_products")

        # Add all new columns
        for col_name, col_type in NEW_COLUMNS:
            conn.execute(text(f"""
                ALTER TABLE {schema}.vinted_products
                ADD COLUMN {col_name} {col_type}
            """))

        print(f"  -> Added {len(NEW_COLUMNS)} columns to {schema}.vinted_products")

    # Also update template_tenant if it exists
    template_exists = conn.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'template_tenant'
            AND table_name = 'vinted_products'
        )
    """)).scalar()

    if template_exists:
        column_exists = conn.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'template_tenant'
                AND table_name = 'vinted_products'
                AND column_name = 'color1_id'
            )
        """)).scalar()

        if not column_exists:
            print("Adding item_upload columns to template_tenant.vinted_products")
            for col_name, col_type in NEW_COLUMNS:
                conn.execute(text(f"""
                    ALTER TABLE template_tenant.vinted_products
                    ADD COLUMN {col_name} {col_type}
                """))
            print(f"  -> Added {len(NEW_COLUMNS)} columns to template_tenant.vinted_products")


def downgrade():
    """Remove item_upload columns from vinted_products."""
    conn = op.get_bind()

    # Build DROP COLUMN list
    drop_columns = ", ".join([f"DROP COLUMN IF EXISTS {col[0]}" for col in NEW_COLUMNS])

    # Get all user schemas
    result = conn.execute(text("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%'
        AND schema_name <> 'user_invalid'
        ORDER BY schema_name
    """))
    user_schemas = [row[0] for row in result.fetchall()]

    for schema in user_schemas:
        table_exists = conn.execute(text(f"""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = '{schema}'
                AND table_name = 'vinted_products'
            )
        """)).scalar()

        if table_exists:
            conn.execute(text(f"""
                ALTER TABLE {schema}.vinted_products
                {drop_columns}
            """))
            print(f"Removed item_upload columns from {schema}.vinted_products")

    # Also update template_tenant
    template_exists = conn.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'template_tenant'
            AND table_name = 'vinted_products'
        )
    """)).scalar()

    if template_exists:
        conn.execute(text(f"""
            ALTER TABLE template_tenant.vinted_products
            {drop_columns}
        """))
        print("Removed item_upload columns from template_tenant.vinted_products")
