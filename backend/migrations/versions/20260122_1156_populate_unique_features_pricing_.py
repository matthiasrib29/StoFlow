"""populate_unique_features_pricing_coefficients

Populate pricing_coefficient for unique_features table.
Coefficients converted from multipliers (1.20) to adjustments (0.20).

Revision ID: 9bb2236304c8
Revises: 273375b81d83
Create Date: 2026-01-22 11:56:06.067990+01:00

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '9bb2236304c8'
down_revision: Union[str, None] = '273375b81d83'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Feature coefficients (converted from multipliers: 1.20 → 0.20)
FEATURE_COEFFICIENTS = {
    # Premium features (0.20) - Rare, artisanal, unique
    "Deadstock fabric": "0.20",
    "Hand embroidered": "0.20",
    "Hand painted": "0.20",
    "Selvedge": "0.20",
    "Single stitch": "0.20",

    # High value features (0.18)
    "Custom design": "0.18",
    "Shuttle loom": "0.18",

    # Valuable features (0.15)
    "Patchwork": "0.15",
    "Hidden rivets": "0.15",
    "Raw denim": "0.15",

    # Notable features (0.12)
    "Chain stitching": "0.12",
    "Unsanforized": "0.12",

    # Good features (0.10)
    "Rope dyed": "0.10",
    "Vintage hardware": "0.10",
    "Original buttons": "0.10",

    # Quality features (0.08)
    "Leather patch": "0.08",
    "Triple stitch": "0.08",
    "Garment dyed": "0.08",
    "Embroidered": "0.08",
    "Appliqué": "0.08",
    "Paneled": "0.08",

    # Decent features (0.07)
    "Flat felled seams": "0.07",
    "Leather label": "0.07",

    # Minor features (0.06)
    "Reinforced seams": "0.06",

    # Small bonuses (0.05)
    "Acid wash": "0.05",
    "Painted": "0.05",
    "Studded": "0.05",
    "Distressed": "0.05",
    "Ripped": "0.05",
    "Frayed": "0.05",
    "Bleached": "0.05",
    "Gradient": "0.05",
    "Lace detail": "0.05",
    "Cutouts": "0.05",
    "Pleated": "0.05",

    # Minimal bonuses (0.04)
    "Tiered": "0.04",
    "Raw hem": "0.04",
    "Beaded": "0.04",
    "Sequined": "0.04",
    "Vintage wash": "0.04",

    # Very small bonuses (0.03)
    "Whiskering": "0.03",
    "Fading": "0.03",
    "Contrast stitching": "0.03",
    "Copper rivets": "0.03",
    "Brass rivets": "0.03",

    # Tiny bonuses (0.02)
    "Jacron patch": "0.02",
    "Paper patch": "0.02",
    "Stone washed": "0.02",
    "Double stitch": "0.02",
    "Zipper detail": "0.02",
    "Chain detail": "0.02",
    "Fringe": "0.02",

    # Negligible bonuses (0.01)
    "Cuffed": "0.01",
    "Sanforized": "0.01",
    "Embossed buttons": "0.01",
    "Printed": "0.01",

    # Neutral (0.00) - Standard features
    "Button detail": "0.00",
    "Belt loops": "0.00",
    "Coin pocket": "0.00",
    "Woven label": "0.00",
    "Lined": "0.00",
    "Padded": "0.00",
    "Decorative pockets": "0.00",
    "Bar tacks": "0.00",
}


def upgrade() -> None:
    conn = op.get_bind()

    for feature_name, coefficient in FEATURE_COEFFICIENTS.items():
        conn.execute(
            text("""
                UPDATE product_attributes.unique_features
                SET pricing_coefficient = :coefficient
                WHERE name_en = :name
            """),
            {"name": feature_name, "coefficient": coefficient}
        )


def downgrade() -> None:
    conn = op.get_bind()

    # Reset all coefficients to default 0.00
    conn.execute(
        text("""
            UPDATE product_attributes.unique_features
            SET pricing_coefficient = 0.00
        """)
    )
