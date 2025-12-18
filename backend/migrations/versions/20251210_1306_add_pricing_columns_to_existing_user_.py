"""add_pricing_columns_to_existing_user_schemas

Revision ID: 89d945359837
Revises: 519b0731226b
Create Date: 2025-12-10 13:06:06.691595+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '89d945359837'
down_revision: Union[str, None] = '519b0731226b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add pricing columns to existing user schemas if they don't have them.

    This migration adds the pricing_edit, pricing_rarity, pricing_quality,
    pricing_details, and pricing_style columns to products table in all
    existing user schemas.
    """
    # Get connection
    conn = op.get_bind()

    # Get all user schemas
    result = conn.execute(sa.text("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%'
    """))

    user_schemas = [row[0] for row in result]

    # For each user schema, add columns if they don't exist
    for schema_name in user_schemas:
        # Check if products table exists
        table_exists = conn.execute(sa.text(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = '{schema_name}'
                AND table_name = 'products'
            )
        """)).scalar()

        if not table_exists:
            continue

        # Check if pricing_edit column exists
        column_exists = conn.execute(sa.text(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.columns
                WHERE table_schema = '{schema_name}'
                AND table_name = 'products'
                AND column_name = 'pricing_edit'
            )
        """)).scalar()

        if not column_exists:
            # Add all pricing columns
            op.execute(sa.text(f"""
                ALTER TABLE {schema_name}.products
                ADD COLUMN IF NOT EXISTS pricing_edit VARCHAR(100),
                ADD COLUMN IF NOT EXISTS pricing_rarity VARCHAR(100),
                ADD COLUMN IF NOT EXISTS pricing_quality VARCHAR(100),
                ADD COLUMN IF NOT EXISTS pricing_details VARCHAR(100),
                ADD COLUMN IF NOT EXISTS pricing_style VARCHAR(100)
            """))
            print(f"Added pricing columns to {schema_name}.products")


def downgrade() -> None:
    """
    Remove pricing columns from user schemas.
    """
    # Get connection
    conn = op.get_bind()

    # Get all user schemas
    result = conn.execute(sa.text("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%'
    """))

    user_schemas = [row[0] for row in result]

    # For each user schema, remove columns if they exist
    for schema_name in user_schemas:
        # Check if products table exists
        table_exists = conn.execute(sa.text(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = '{schema_name}'
                AND table_name = 'products'
            )
        """)).scalar()

        if table_exists:
            op.execute(sa.text(f"""
                ALTER TABLE {schema_name}.products
                DROP COLUMN IF EXISTS pricing_edit,
                DROP COLUMN IF EXISTS pricing_rarity,
                DROP COLUMN IF EXISTS pricing_quality,
                DROP COLUMN IF EXISTS pricing_details,
                DROP COLUMN IF EXISTS pricing_style
            """))
            print(f"Removed pricing columns from {schema_name}.products")
