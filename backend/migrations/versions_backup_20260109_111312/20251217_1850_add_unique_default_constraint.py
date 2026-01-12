"""Add unique constraint for default per couple

Revision ID: 20251217_1850
Revises: 20251217_1840
Create Date: 2025-12-17 18:50:00.000000

Adds a partial unique index to ensure each (my_category, my_gender) couple
has exactly one default mapping. This prevents data integrity issues.

Author: Claude
Date: 2025-12-17
"""
from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = '20251217_1850'
down_revision = '20251217_1840'
branch_labels = None
depends_on = None


def upgrade():
    """
    Add unique partial index on is_default per couple.
    """
    conn = op.get_bind()

    # Check if index already exists
    index_exists = conn.execute(text("""
        SELECT EXISTS (
            SELECT FROM pg_indexes
            WHERE schemaname = 'public'
            AND tablename = 'vinted_mapping'
            AND indexname = 'unique_default_per_couple'
        )
    """)).scalar()

    if index_exists:
        print("  ⏭️  unique_default_per_couple index already exists, skipping")
    else:
        # First verify no duplicates exist
        duplicates = conn.execute(text("""
            SELECT my_category, my_gender, COUNT(*) as cnt
            FROM public.vinted_mapping
            WHERE is_default = TRUE
            GROUP BY my_category, my_gender
            HAVING COUNT(*) > 1
        """)).fetchall()

        if duplicates:
            raise Exception(
                f"Cannot create unique index: {len(duplicates)} couples have multiple defaults. "
                "Fix data first."
            )

        # Create partial unique index
        conn.execute(text("""
            CREATE UNIQUE INDEX unique_default_per_couple
            ON public.vinted_mapping (my_category, my_gender)
            WHERE is_default = TRUE
        """))
        print("  ✓ Created unique_default_per_couple index")
        print("    → Only one default allowed per (my_category, my_gender) couple")


def downgrade():
    """
    Drop unique partial index.
    """
    conn = op.get_bind()

    # Check if index exists
    index_exists = conn.execute(text("""
        SELECT EXISTS (
            SELECT FROM pg_indexes
            WHERE schemaname = 'public'
            AND tablename = 'vinted_mapping'
            AND indexname = 'unique_default_per_couple'
        )
    """)).scalar()

    if index_exists:
        op.drop_index('unique_default_per_couple', table_name='vinted_mapping', schema='public')
        print("  ✓ Dropped unique_default_per_couple index")
    else:
        print("  ⏭️  unique_default_per_couple index doesn't exist, skipping")
