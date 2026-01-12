"""Move sports-jersey from tops to sportswear

Revision ID: 20251217_1250
Revises: 20251217_1200
Create Date: 2025-12-17 12:50:00.000000

Deplace la categorie sports-jersey de tops vers sportswear
pour une meilleure coherence avec les autres vetements de sport.

Changes:
- sports-jersey.parent_category: tops -> sportswear

Author: Claude
Date: 2025-12-17
"""
from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = '20251217_1250'
down_revision = '20251217_1200'
branch_labels = None
depends_on = None


def upgrade():
    """
    Move sports-jersey from tops to sportswear.

    Business Rules:
    - sports-jersey is more logically grouped with sportswear
    - Keeps consistency with other sports clothing (sports-bra, sports-top, etc.)
    """
    conn = op.get_bind()

    # Check current parent
    result = conn.execute(text("""
        SELECT parent_category
        FROM product_attributes.categories
        WHERE name_en = 'sports-jersey'
    """)).fetchone()

    if result and result[0] == 'tops':
        conn.execute(text("""
            UPDATE product_attributes.categories
            SET parent_category = 'sportswear'
            WHERE name_en = 'sports-jersey'
        """))
        print("  ✓ Moved sports-jersey from tops to sportswear")
    elif result and result[0] == 'sportswear':
        print("  ⏭️  sports-jersey already under sportswear, skipping")
    else:
        print("  ⚠️  sports-jersey not found or has unexpected parent")


def downgrade():
    """
    Move sports-jersey back from sportswear to tops.
    """
    conn = op.get_bind()

    # Check current parent
    result = conn.execute(text("""
        SELECT parent_category
        FROM product_attributes.categories
        WHERE name_en = 'sports-jersey'
    """)).fetchone()

    if result and result[0] == 'sportswear':
        conn.execute(text("""
            UPDATE product_attributes.categories
            SET parent_category = 'tops'
            WHERE name_en = 'sports-jersey'
        """))
        print("  ✓ Moved sports-jersey back from sportswear to tops")
    elif result and result[0] == 'tops':
        print("  ⏭️  sports-jersey already under tops, skipping")
    else:
        print("  ⚠️  sports-jersey not found or has unexpected parent")
