"""seed condition_sups table with valid values

Revision ID: 001b85a9a3be
Revises: 6e32427bc9b3
Create Date: 2026-01-07 18:12:06.408506+01:00

Purpose:
    Populate product_attributes.condition_sups table with common condition
    supplement values found in existing product data.

    These values describe specific wear/damage details on products beyond
    the basic condition rating (0-10).

"""
from typing import Sequence, Union


from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

from logging import getLogger

logger = getLogger(__name__)


# revision identifiers, used by Alembic.
revision: str = '001b85a9a3be'
down_revision: Union[str, None] = '6e32427bc9b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Seed condition_sups table with valid values."""
    conn = op.get_bind()

    logger.info("\n" + "=" * 70)
    logger.info("📊 SEEDING CONDITION_SUPS TABLE")
    logger.info("=" * 70 + "\n")

    # List of condition supplements found in existing data
    # Format: (name_en, name_fr) - Title Case for consistency
    condition_sups = [
        ("Damaged Button", "Bouton Endommagé"),
        ("Distressed", "Usé"),
        ("Faded", "Délavé"),
        ("Frayed Hems", "Ourlets Effilochés"),
        ("General Wear", "Usure Générale"),
        ("Hemmed/Shortened", "Raccourci"),
        ("Knee Wear", "Usure Aux Genoux"),
        ("Light Discoloration", "Légère Décoloration"),
        ("Marked Discoloration", "Décoloration Marquée"),
        ("Multiple Holes", "Plusieurs Trous"),
        ("Multiple Stains", "Plusieurs Taches"),
        ("Resewn", "Recousu"),
        ("Seam To Fix", "Couture À Réparer"),
        ("Single Stain", "Tache Unique"),
        ("Small Hole", "Petit Trou"),
        ("Stretched", "Étiré"),
        ("Vintage Patina", "Patine Vintage"),
        ("Vintage Wear", "Usure Vintage"),
        ("Worn", "Porté"),
    ]

    # Insert condition supplements
    for name_en, name_fr in condition_sups:
        conn.execute(text("""
            INSERT INTO product_attributes.condition_sups (name_en, name_fr)
            VALUES (:name_en, :name_fr)
            ON CONFLICT (name_en) DO NOTHING;
        """), {"name_en": name_en, "name_fr": name_fr})

    logger.info(f"✅ Inserted {len(condition_sups)} condition supplements")
    logger.info("\nCondition supplements added:")
    for name_en, name_fr in condition_sups:
        logger.info(f"  - {name_en} / {name_fr}")

    logger.info("\n" + "=" * 70)
    logger.info("✅ SEEDING COMPLETE")
    logger.info("=" * 70)


def downgrade() -> None:
    """Remove seeded condition supplements."""
    conn = op.get_bind()

    logger.info("\n⚠️  Removing seeded condition supplements...")

    # List of English names to delete
    names_to_delete = [
        "Damaged Button", "Distressed", "Faded", "Frayed Hems", "General Wear",
        "Hemmed/Shortened", "Knee Wear", "Light Discoloration", "Marked Discoloration",
        "Multiple Holes", "Multiple Stains", "Resewn", "Seam To Fix", "Single Stain",
        "Small Hole", "Stretched", "Vintage Patina", "Vintage Wear", "Worn"
    ]

    for name_en in names_to_delete:
        conn.execute(text("""
            DELETE FROM product_attributes.condition_sups
            WHERE name_en = :name_en;
        """), {"name_en": name_en})

    logger.info(f"✅ Removed {len(names_to_delete)} condition supplements")
