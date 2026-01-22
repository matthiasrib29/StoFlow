"""populate_origins_pricing_coefficients

Populate pricing_coefficient for all origins.
Coefficients converted from multipliers (1.20) to adjustments (0.20).
Premium origins also marked with is_premium=true.

Revision ID: fcc07a5c49cf
Revises: 219f1f322a89
Create Date: 2026-01-22 12:17:29.672127+01:00

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'fcc07a5c49cf'
down_revision: Union[str, None] = '219f1f322a89'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Origin coefficients (converted from multipliers: 1.20 → 0.20)
# Format: (name_en, coefficient, is_premium)
ORIGIN_COEFFICIENTS = [
    # Premium tier (0.20) - Top quality, collectors pay premium
    ("Japan", "0.20", True),      # Denim, Techwear - the best
    ("Usa", "0.20", True),        # "Made in USA" = often pre-2000s vintage

    # High value (0.18) - Luxury, craftsmanship
    ("Italy", "0.18", True),      # Luxury, leather, tailoring
    ("France", "0.18", True),     # Luxury, heritage, rarity

    # Strong value (0.15) - Quality European
    ("United kingdom", "0.15", True),  # Quality woolens, Dr Martens vintage

    # Good value (0.10) - Solid reputation
    ("Germany", "0.10", True),    # Robust, Techwear, Boss/Adidas vintage
    ("Canada", "0.10", False),    # Heavy outerwear, Arc'teryx, Supreme

    # Above average (0.08)
    ("Belgium", "0.08", False),   # Antwerp fashion, high quality

    # Slight bonus (0.05) - Premium European/quality
    ("Portugal", "0.05", False),  # Current "Premium" European standard
    ("Australia", "0.05", False), # Merino wool, vintage surf brands
    ("Norway", "0.05", False),    # High quality cold weather gear

    # Small bonus (0.02) - Vintage indicator
    ("South korea", "0.02", False),   # 90s vintage production
    ("Taiwan", "0.02", False),        # 80s/90s sneaker production
    ("Hong kong", "0.02", False),     # 80s/90s indicator

    # Neutral (0.00) - Standard European
    ("Spain", "0.00", False),         # Good leather, but also Zara
    ("Netherlands", "0.00", False),   # Standard European
    ("Slovakia", "0.00", False),      # Eastern European (luxury brands)
    ("Poland", "0.00", False),        # Good textile industry

    # Slight penalty (-0.02) - Europe's factory
    ("Turkey", "-0.02", False),       # Europe's denim factory
    ("Tunisia", "-0.02", False),      # Mid-range brands
    ("Morocco", "-0.02", False),      # Similar to Tunisia
    ("Mauritius", "-0.02", False),    # Knitwear (Ralph Lauren)
    ("Mexico", "-0.02", False),       # Replaced USA for Carhartt/Levi's

    # Small penalty (-0.05) - Mass production modern
    ("Brazil", "-0.05", False),       # Local production
    ("Indonesia", "-0.05", False),    # Modern mass production
    ("Vietnam", "-0.05", False),      # Current technical/sneaker hub
    ("China", "-0.05", False),        # World's factory, often post-2005
    ("Thailand", "-0.05", False),     # Some vintage, mostly modern
    ("Malaysia", "-0.05", False),     # Mass production
    ("Philippines", "-0.05", False),  # Mass production

    # Moderate penalty (-0.08) - Lower quality perception
    ("India", "-0.08", False),        # Light cotton, fast-fashion bohemian
    ("Pakistan", "-0.08", False),     # Low-end denim, fast-fashion sweats

    # Significant penalty (-0.10) - Fast fashion / basic
    ("Bangladesh", "-0.10", False),   # Fast Fashion symbol (H&M, Primark)
    ("Cambodia", "-0.10", False),     # Recent low-cost mass production
    ("Haiti", "-0.10", False),        # Basic promo t-shirts
    ("Honduras", "-0.10", False),     # Gildan, Fruit of the Loom modern
    ("Dominican republic", "-0.10", False),  # Basic t-shirts
    ("El salvador", "-0.10", False),  # Basic t-shirts
    ("Guatemala", "-0.10", False),    # Mass production
    ("Nicaragua", "-0.10", False),    # Mass production
    ("Costa rica", "-0.10", False),   # Mass production
    ("Egypt", "-0.10", False),        # Basic cotton
    ("Jordan", "-0.10", False),       # Mass production sportswear
    ("Kenya", "-0.10", False),        # Recent low-cost textile
    ("Brunei", "-0.10", False),       # Rare, mass production
    ("Malta", "-0.10", False),        # Basic offshore manufacturing
    ("Turkmenistan", "-0.10", False), # Raw/basic cotton production
    ("Bahrain", "-0.10", False),      # Specific, often uniforms/basic
]


def upgrade() -> None:
    conn = op.get_bind()

    for origin_name, coefficient, is_premium in ORIGIN_COEFFICIENTS:
        conn.execute(
            text("""
                UPDATE product_attributes.origins
                SET pricing_coefficient = :coefficient,
                    is_premium = :is_premium
                WHERE name_en = :name
            """),
            {"name": origin_name, "coefficient": coefficient, "is_premium": is_premium}
        )


def downgrade() -> None:
    conn = op.get_bind()

    # Reset all coefficients to default 0.00 and is_premium to false
    conn.execute(
        text("""
            UPDATE product_attributes.origins
            SET pricing_coefficient = 0.00,
                is_premium = false
        """)
    )
