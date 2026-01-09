"""remove_condition_sup_duplicates

Revision ID: 312dfe0a7c07
Revises: b5ac89614dfc
Create Date: 2026-01-07 13:17:42.294960+01:00

Remove duplicates between CONDITIONS and CONDITION_SUP:
- "Acceptable condition" (duplicate of "Acceptable")
- "Excellent condition" (duplicate of "Excellent")
- "Good condition" (duplicate of "Good")
- "Like new" (exact duplicate)
- "Very good condition" (duplicate of "Very good")
"""
from typing import Sequence, Union


from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

from logging import getLogger

logger = getLogger(__name__)


# revision identifiers, used by Alembic.
revision: str = '312dfe0a7c07'
down_revision: Union[str, None] = 'b5ac89614dfc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def table_exists(conn, schema, table):
    """Check if a table exists."""
    result = conn.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = :schema AND table_name = :table
        )
    """), {"schema": schema, "table": table})
    return result.scalar()


def upgrade() -> None:
    """Remove duplicate condition_sups values."""
    conn = op.get_bind()

    # Check if table exists (idempotent)
    if not table_exists(conn, 'product_attributes', 'condition_sups'):
        logger.info("⏭️  condition_sups table does not exist, skipping")
        return

    duplicates_to_remove = [
        'Acceptable condition',
        'Excellent condition',
        'Good condition',
        'Like new',
        'Very good condition'
    ]

    logger.info(f"Removing {len(duplicates_to_remove)} duplicate condition_sups values...")

    for duplicate in duplicates_to_remove:
        logger.info(f"  🗑️  Deleting: {duplicate}")
        conn.execute(text("""
            DELETE FROM product_attributes.condition_sups
            WHERE name_en = :duplicate
        """), {"duplicate": duplicate})

    logger.info("✅ Duplicates removed successfully!")


def downgrade() -> None:
    """Restore removed condition_sups duplicates."""
    conn = op.get_bind()

    # Check if table exists (idempotent)
    if not table_exists(conn, 'product_attributes', 'condition_sups'):
        logger.info("⏭️  condition_sups table does not exist, skipping")
        return

    duplicates_to_restore = [
        'Acceptable condition',
        'Excellent condition',
        'Good condition',
        'Like new',
        'Very good condition'
    ]

    logger.info(f"Restoring {len(duplicates_to_restore)} condition_sups values...")

    for duplicate in duplicates_to_restore:
        logger.info(f"  ✏️  Restoring: {duplicate}")
        conn.execute(text("""
            INSERT INTO product_attributes.condition_sups (name_en)
            VALUES (:duplicate)
            ON CONFLICT (name_en) DO NOTHING
        """), {"duplicate": duplicate})

    logger.info("✅ Duplicates restored successfully!")
