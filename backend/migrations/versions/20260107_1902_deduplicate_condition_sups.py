"""deduplicate condition_sups

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-01-07 19:02:00.000000+01:00

Purpose:
    Remove duplicate lowercase condition_sup values from product_attributes.condition_sups.

    Strategy:
    - Keep Title Case versions (e.g., "Damaged Button", "Frayed Hems")
    - Delete lowercase versions (e.g., "damaged button", "frayed hems")

    Total: 13 duplicate pairs identified

    ⚠️  WARNING: This migration is NOT reversible - deleted data cannot be restored.
"""
from typing import Sequence, Union


from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

from logging import getLogger

logger = getLogger(__name__)


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove duplicate lowercase condition_sups."""
    conn = op.get_bind()

    logger.info("\n" + "=" * 70)
    logger.info("🧹 DEDUPLICATING CONDITION_SUPS")
    logger.info("=" * 70 + "\n")

    # Doublons identifiés (lowercase à supprimer, Title Case à garder)
    duplicates_to_remove = [
        "damaged button",      # Keep: "Damaged Button"
        "frayed hems",         # Keep: "Frayed Hems"
        "general wear",        # Keep: "General Wear"
        "knee wear",           # Keep: "Knee Wear"
        "light discoloration", # Keep: "Light Discoloration"
        "marked discoloration",# Keep: "Marked Discoloration"
        "multiple holes",      # Keep: "Multiple Holes"
        "multiple stains",     # Keep: "Multiple Stains"
        "seam to fix",         # Keep: "Seam To Fix"
        "single stain",        # Keep: "Single Stain"
        "small hole",          # Keep: "Small Hole"
        "vintage patina",      # Keep: "Vintage Patina"
        "vintage wear"         # Keep: "Vintage Wear"
    ]

    logger.info(f"Removing {len(duplicates_to_remove)} lowercase duplicates...\n")

    removed_count = 0
    for duplicate in duplicates_to_remove:
        result = conn.execute(text("""
            DELETE FROM product_attributes.condition_sups
            WHERE name_en = :duplicate
        """), {"duplicate": duplicate})

        if result.rowcount > 0:
            logger.info(f"  - Deleted: '{duplicate}'")
            removed_count += 1

    logger.info(f"\n✅ Removed {removed_count} duplicate condition_sups")

    # Verify no case-insensitive duplicates remain
    result = conn.execute(text("""
        SELECT LOWER(name_en) as normalized, COUNT(*) as count
        FROM product_attributes.condition_sups
        GROUP BY LOWER(name_en)
        HAVING COUNT(*) > 1;
    """))

    remaining_duplicates = result.fetchall()
    if remaining_duplicates:
        logger.info(f"\n⚠️  WARNING: {len(remaining_duplicates)} case-insensitive duplicates still exist:")
        for normalized, count in remaining_duplicates:
            logger.info(f"  - '{normalized}': {count} variants")
    else:
        logger.info("\n✅ No case-insensitive duplicates remain")

    logger.info("\n" + "=" * 70)
    logger.info("✅ DEDUPLICATION COMPLETE")
    logger.info("=" * 70)


def downgrade() -> None:
    """Cannot restore deleted data."""
    logger.info("\n⚠️  WARNING: Downgrade not available - deleted data cannot be restored.")
    logger.info("    Backup database before running this migration if rollback is required.")
