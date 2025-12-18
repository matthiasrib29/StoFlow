"""Add circular reference check for categories

Revision ID: 20251205_1520
Revises: 20251204_1619_add_product_attributes_and_images
Create Date: 2025-12-05 15:20:00

Business Rules (2025-12-05):
- Empêche une catégorie d'être son propre parent
- Première ligne de défense au niveau base de données contre références circulaires
- Complète la validation Python dans CategoryService
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "e3a9c8f12345"
down_revision = "d59ff27961f4"
branch_labels = None
depends_on = None


def upgrade():
    """Add CHECK constraint to prevent direct self-reference."""
    # Add CHECK constraint to prevent name_en = parent_category
    op.execute("""
        ALTER TABLE public.categories
        ADD CONSTRAINT chk_category_not_self_parent
        CHECK (name_en <> parent_category)
    """)


def downgrade():
    """Remove CHECK constraint."""
    op.execute("""
        ALTER TABLE public.categories
        DROP CONSTRAINT IF EXISTS chk_category_not_self_parent
    """)
