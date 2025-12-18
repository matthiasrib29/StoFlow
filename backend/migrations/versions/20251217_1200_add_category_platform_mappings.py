"""Add category_platform_mappings table

Revision ID: 20251217_1200
Revises: 20251217_1105
Create Date: 2025-12-17 12:00:00.000000

Table de mapping generique des categories internes vers les IDs des plateformes
(Vinted, Etsy, eBay).

Tables creees:
- public.category_platform_mappings

Indexes:
- idx_category_platform_lookup (category, gender, fit)
- Unique constraint on (category, gender, fit)

Author: Claude
Date: 2025-12-17
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = '20251217_1200'
down_revision = '20251217_1105'
branch_labels = None
depends_on = None


def upgrade():
    """
    Create category_platform_mappings table in public schema.

    Business Rules:
    - Composite key: (category, gender, fit) -> platform IDs
    - One table for all platforms (no duplication)
    - FKs to product_attributes tables (categories, genders, fits)
    - eBay has different IDs per marketplace (FR, DE, GB, IT, ES)
    """
    conn = op.get_bind()

    # ===== 1. CHECK IF TABLE EXISTS =====
    table_exists = conn.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = 'category_platform_mappings'
        )
    """)).scalar()

    if table_exists:
        print("  ⏭️  category_platform_mappings table already exists, skipping")
        return

    # ===== 2. CREATE TABLE =====
    op.create_table(
        'category_platform_mappings',
        # Primary key
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),

        # Composite key (lookup)
        sa.Column('category', sa.String(100), nullable=False,
                  comment='Category name (EN) - FK to categories'),
        sa.Column('gender', sa.String(100), nullable=False,
                  comment='Gender name (EN) - FK to genders'),
        sa.Column('fit', sa.String(100), nullable=True,
                  comment='Fit name (EN) - FK to fits (optional)'),

        # VINTED
        sa.Column('vinted_category_id', sa.Integer(), nullable=True,
                  comment='Vinted catalog_id'),
        sa.Column('vinted_category_name', sa.String(255), nullable=True,
                  comment='Vinted category name (for display)'),
        sa.Column('vinted_category_path', sa.String(500), nullable=True,
                  comment='Vinted category path (e.g. Hommes > Jeans > Slim)'),

        # ETSY
        sa.Column('etsy_taxonomy_id', sa.BigInteger(), nullable=True,
                  comment='Etsy taxonomy_id'),
        sa.Column('etsy_category_name', sa.String(255), nullable=True,
                  comment='Etsy category name'),
        sa.Column('etsy_category_path', sa.String(500), nullable=True,
                  comment='Etsy category path'),
        sa.Column('etsy_required_attributes', sa.Text(), nullable=True,
                  comment='JSON: Required attributes for Etsy listings'),

        # EBAY (per marketplace)
        sa.Column('ebay_category_id_fr', sa.Integer(), nullable=True,
                  comment='eBay category ID for EBAY_FR'),
        sa.Column('ebay_category_id_de', sa.Integer(), nullable=True,
                  comment='eBay category ID for EBAY_DE'),
        sa.Column('ebay_category_id_gb', sa.Integer(), nullable=True,
                  comment='eBay category ID for EBAY_GB'),
        sa.Column('ebay_category_id_it', sa.Integer(), nullable=True,
                  comment='eBay category ID for EBAY_IT'),
        sa.Column('ebay_category_id_es', sa.Integer(), nullable=True,
                  comment='eBay category ID for EBAY_ES'),
        sa.Column('ebay_category_name', sa.String(255), nullable=True,
                  comment='eBay category name (EN)'),
        sa.Column('ebay_item_specifics', sa.Text(), nullable=True,
                  comment='JSON: Required item specifics for eBay'),

        # Constraints
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(
            ['category'],
            ['product_attributes.categories.name_en'],
            onupdate='CASCADE',
            ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['gender'],
            ['product_attributes.genders.name_en'],
            onupdate='CASCADE',
            ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['fit'],
            ['product_attributes.fits.name_en'],
            onupdate='CASCADE',
            ondelete='SET NULL'
        ),
        sa.UniqueConstraint('category', 'gender', 'fit', name='uq_category_platform_mapping'),

        schema='public'
    )
    print("  ✓ Created category_platform_mappings table")

    # ===== 3. CREATE INDEX =====
    op.create_index(
        'idx_category_platform_lookup',
        'category_platform_mappings',
        ['category', 'gender', 'fit'],
        unique=False,
        schema='public'
    )
    print("  ✓ Created idx_category_platform_lookup index")

    # ===== 4. CREATE ID INDEX =====
    op.create_index(
        'ix_public_category_platform_mappings_id',
        'category_platform_mappings',
        ['id'],
        unique=False,
        schema='public'
    )
    print("  ✓ Created id index")


def downgrade():
    """
    Drop category_platform_mappings table.
    """
    conn = op.get_bind()

    # Check if table exists
    table_exists = conn.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = 'category_platform_mappings'
        )
    """)).scalar()

    if not table_exists:
        print("  ⏭️  category_platform_mappings table does not exist, skipping")
        return

    # Drop indexes
    op.drop_index('ix_public_category_platform_mappings_id',
                  table_name='category_platform_mappings', schema='public')
    op.drop_index('idx_category_platform_lookup',
                  table_name='category_platform_mappings', schema='public')

    # Drop table
    op.drop_table('category_platform_mappings', schema='public')
    print("  ✓ Dropped category_platform_mappings table")
