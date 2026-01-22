"""populate_trends_pricing_coefficients

Populate pricing_coefficient for trends table.
Coefficients converted from multipliers (1.20) to adjustments (0.20).

Revision ID: f909c29bf8cf
Revises: 9bb2236304c8
Create Date: 2026-01-22 11:59:01.563620+01:00

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'f909c29bf8cf'
down_revision: Union[str, None] = '9bb2236304c8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Trend coefficients (converted from multipliers: 1.20 → 0.20)
TREND_COEFFICIENTS = {
    # Premium trends (0.20) - Top tier, luxury/avant-garde
    "Japanese streetwear": "0.20",
    "Techwear": "0.20",

    # High value trends (0.18)
    "Gorpcore": "0.18",
    "Old money": "0.18",
    "Quiet luxury": "0.18",

    # Strong trends (0.15)
    "Indie sleaze": "0.15",
    "Eclectic grandpa": "0.15",

    # Solid trends (0.12)
    "Y2k": "0.12",
    "Workwear": "0.12",

    # Good trends (0.10)
    "Office siren": "0.10",
    "Mob wife": "0.10",

    # Notable trends (0.08)
    "Skater": "0.08",
    "Balletcore": "0.08",
    "Coquette": "0.08",
    "Grunge": "0.08",

    # Decent trends (0.06)
    "Dark academia": "0.06",

    # Small bonuses (0.05)
    "Streetwear": "0.05",
    "Western": "0.05",
    "Vintage": "0.05",
    "Vamp romance": "0.05",
    "Wilderkind": "0.05",

    # Minimal bonuses (0.04)
    "Poetcore": "0.04",
    "Light academia": "0.04",
    "Khaki coded": "0.04",
    "Boho revival": "0.04",

    # Very small bonuses (0.03)
    "Neo deco": "0.03",
    "Retro": "0.03",

    # Tiny bonuses (0.02)
    "Clean girl": "0.02",
    "Punk": "0.02",
    "Gothic": "0.02",
    "Cottagecore": "0.02",
    "Bohemian": "0.02",
    "Preppy": "0.02",

    # Negligible bonuses (0.01)
    "Sportswear": "0.01",
    "Glamoratti": "0.01",

    # Neutral (0.00) - Generic/no added value
    "Athleisure": "0.00",
    "Normcore": "0.00",
    "Minimalist": "0.00",
    "Modern": "0.00",
    "Geek chic": "0.00",
    "Downtown girl": "0.00",
}


def upgrade() -> None:
    conn = op.get_bind()

    for trend_name, coefficient in TREND_COEFFICIENTS.items():
        conn.execute(
            text("""
                UPDATE product_attributes.trends
                SET pricing_coefficient = :coefficient
                WHERE name_en = :name
            """),
            {"name": trend_name, "coefficient": coefficient}
        )


def downgrade() -> None:
    conn = op.get_bind()

    # Reset all coefficients to default 0.00
    conn.execute(
        text("""
            UPDATE product_attributes.trends
            SET pricing_coefficient = 0.00
        """)
    )
