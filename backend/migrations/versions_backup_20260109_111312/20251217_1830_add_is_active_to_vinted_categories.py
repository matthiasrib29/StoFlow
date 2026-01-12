"""Add is_active to vinted_categories

Revision ID: 20251217_1830
Revises: 20251217_1800
Create Date: 2025-12-17 18:30:00.000000

Adds is_active column to vinted_categories to mark which categories
are actually used/supported by the application.

Author: Claude
Date: 2025-12-17
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = '20251217_1830'
down_revision = '20251217_1800'
branch_labels = None
depends_on = None


def upgrade():
    """
    Add is_active column to vinted_categories.
    """
    conn = op.get_bind()

    # Check if column exists
    column_exists = conn.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name = 'vinted_categories'
            AND column_name = 'is_active'
        )
    """)).scalar()

    if column_exists:
        print("  ⏭️  is_active column already exists, skipping")
    else:
        op.add_column(
            'vinted_categories',
            sa.Column('is_active', sa.Boolean(), server_default='false', nullable=False),
            schema='public'
        )
        print("  ✓ Added is_active column to vinted_categories")

        # Create index for is_active
        op.create_index(
            'idx_vinted_categories_is_active',
            'vinted_categories',
            ['is_active'],
            schema='public'
        )
        print("  ✓ Created index on is_active")

    # Mark categories that are mapped as active
    result = conn.execute(text("""
        UPDATE public.vinted_categories vc
        SET is_active = TRUE
        WHERE EXISTS (
            SELECT 1 FROM public.vinted_mapping vm
            WHERE vm.vinted_id = vc.id
        )
    """))
    print(f"  ✓ Marked {result.rowcount} mapped categories as active")


def downgrade():
    """
    Remove is_active column from vinted_categories.
    """
    conn = op.get_bind()

    # Check if column exists
    column_exists = conn.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name = 'vinted_categories'
            AND column_name = 'is_active'
        )
    """)).scalar()

    if column_exists:
        op.drop_index('idx_vinted_categories_is_active', table_name='vinted_categories', schema='public')
        op.drop_column('vinted_categories', 'is_active', schema='public')
        print("  ✓ Dropped is_active column from vinted_categories")
    else:
        print("  ⏭️  is_active column doesn't exist, skipping")
