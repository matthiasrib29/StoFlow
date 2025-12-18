"""Create vinted_categories table

Revision ID: 20251217_1400
Revises: 20251217_1300
Create Date: 2025-12-17 14:00:00.000000

Creates the vinted_categories table to store Vinted's category hierarchy.
This table contains only clothing categories imported from Vinted's catalog.

Changes:
- Create public.vinted_categories table with self-referencing FK for hierarchy

Author: Claude
Date: 2025-12-17
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = '20251217_1400'
down_revision = '20251217_1300'
branch_labels = None
depends_on = None


def upgrade():
    """
    Create vinted_categories table.

    Business Rules:
    - Stores Vinted category hierarchy for clothing items only
    - ID matches Vinted's internal category IDs
    - Parent-child hierarchy via self-referencing FK
    - Gender determined from path (Femmes, Hommes, Filles, Garçons)
    - is_leaf indicates categories that can be selected for products
    """
    conn = op.get_bind()

    # Check if table already exists
    table_exists = conn.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = 'vinted_categories'
        )
    """)).scalar()

    if table_exists:
        print("  ⏭️  vinted_categories table already exists, skipping")
        return

    # Create the table
    op.create_table(
        'vinted_categories',
        sa.Column('id', sa.Integer(), nullable=False, comment='Vinted category ID'),
        sa.Column('code', sa.String(100), nullable=True, comment='Vinted category code'),
        sa.Column('title', sa.String(255), nullable=False, comment='Category title'),
        sa.Column('parent_id', sa.Integer(), nullable=True, comment='Parent category ID'),
        sa.Column('path', sa.String(500), nullable=True, comment='Full path (e.g., Femmes > Vêtements > Jeans)'),
        sa.Column('is_leaf', sa.Boolean(), server_default='false', nullable=False, comment='True if category can be selected for products'),
        sa.Column('gender', sa.String(20), nullable=True, comment='Gender: women, men, girls, boys'),
        sa.PrimaryKeyConstraint('id'),
        schema='public'
    )

    # Add foreign key for parent_id (self-reference)
    op.create_foreign_key(
        'fk_vinted_categories_parent',
        'vinted_categories', 'vinted_categories',
        ['parent_id'], ['id'],
        source_schema='public',
        referent_schema='public',
        ondelete='CASCADE'
    )

    # Create indexes for common queries
    op.create_index(
        'idx_vinted_categories_parent_id',
        'vinted_categories',
        ['parent_id'],
        schema='public'
    )
    op.create_index(
        'idx_vinted_categories_gender',
        'vinted_categories',
        ['gender'],
        schema='public'
    )
    op.create_index(
        'idx_vinted_categories_is_leaf',
        'vinted_categories',
        ['is_leaf'],
        schema='public'
    )

    print("  ✓ Created vinted_categories table")


def downgrade():
    """
    Drop vinted_categories table.
    """
    conn = op.get_bind()

    # Check if table exists
    table_exists = conn.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = 'vinted_categories'
        )
    """)).scalar()

    if not table_exists:
        print("  ⏭️  vinted_categories table doesn't exist, skipping")
        return

    # Drop indexes first
    op.drop_index('idx_vinted_categories_is_leaf', table_name='vinted_categories', schema='public')
    op.drop_index('idx_vinted_categories_gender', table_name='vinted_categories', schema='public')
    op.drop_index('idx_vinted_categories_parent_id', table_name='vinted_categories', schema='public')

    # Drop FK constraint
    op.drop_constraint('fk_vinted_categories_parent', 'vinted_categories', schema='public', type_='foreignkey')

    # Drop table
    op.drop_table('vinted_categories', schema='public')

    print("  ✓ Dropped vinted_categories table")
