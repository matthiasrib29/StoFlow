"""Drop default_gender from categories

Revision ID: 20251217_1600
Revises: 20251217_1500
Create Date: 2025-12-17 16:00:00.000000

Removes the deprecated default_gender column from categories table.
This column is replaced by the genders array column.

Author: Claude
Date: 2025-12-17
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = '20251217_1600'
down_revision = '20251217_1500'
branch_labels = None
depends_on = None


def upgrade():
    """
    Drop default_gender column from categories.
    """
    conn = op.get_bind()

    # Check if column exists
    column_exists = conn.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.columns
            WHERE table_schema = 'product_attributes'
            AND table_name = 'categories'
            AND column_name = 'default_gender'
        )
    """)).scalar()

    if column_exists:
        op.drop_column('categories', 'default_gender', schema='product_attributes')
        print("  ✓ Dropped default_gender column from categories")
    else:
        print("  ⏭️  default_gender column doesn't exist, skipping")

    # Drop the enum type if it exists and is not used elsewhere
    try:
        conn.execute(text("DROP TYPE IF EXISTS gender"))
        print("  ✓ Dropped gender enum type")
    except Exception:
        print("  ⏭️  gender enum type still in use or doesn't exist")


def downgrade():
    """
    Restore default_gender column to categories.
    """
    conn = op.get_bind()

    # Check if column already exists
    column_exists = conn.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.columns
            WHERE table_schema = 'product_attributes'
            AND table_name = 'categories'
            AND column_name = 'default_gender'
        )
    """)).scalar()

    if column_exists:
        print("  ⏭️  default_gender column already exists, skipping")
        return

    # Recreate the enum type
    conn.execute(text("""
        DO $$ BEGIN
            CREATE TYPE gender AS ENUM ('male', 'female', 'unisex');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$
    """))

    # Add the column back
    op.add_column(
        'categories',
        sa.Column(
            'default_gender',
            sa.Enum('male', 'female', 'unisex', name='gender'),
            server_default='unisex',
            nullable=False
        ),
        schema='product_attributes'
    )
    print("  ✓ Restored default_gender column to categories")
