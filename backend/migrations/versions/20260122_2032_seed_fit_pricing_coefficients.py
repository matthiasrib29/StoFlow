"""seed_fit_pricing_coefficients

Revision ID: e7ca75754b9e
Revises: 566f29854d44
Create Date: 2026-01-22 20:32:12.223487+01:00

Sets pricing coefficients for all fits based on market trends.
Coefficients are adjustments (multiplier - 1.00):
- Positive = premium fit (Baggy +0.20, Oversized +0.15)
- Neutral = standard (Straight 0.00, Regular 0.00)
- Negative = less desirable (Skinny -0.40, Tight -0.30)
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'e7ca75754b9e'
down_revision: Union[str, None] = '566f29854d44'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Fit coefficients: adjustment = multiplier - 1.00
FIT_COEFFICIENTS = {
    "Baggy": 0.20,      # 1.20 → +0.20 | Le roi du marché
    "Balloon": 0.20,    # 1.20 → +0.20 | Très mode, volume recherché
    "Oversized": 0.15,  # 1.15 → +0.15 | Toujours le standard du cool
    "Loose": 0.15,      # 1.15 → +0.15 | Très demandé
    "Flare": 0.12,      # 1.12 → +0.12 | Niche mais très recherché (70s/Y2K)
    "Bootcut": 0.10,    # 1.10 → +0.10 | Le seul "fit serré" accepté (s'évase en bas)
    "Relaxed": 0.05,    # 1.05 → +0.05 | Le standard minimum pour être à la mode
    "Straight": 0.00,   # 1.00 → 0.00  | Le neutre absolu
    "Regular": 0.00,    # 1.00 → 0.00  | Référence (non dans la liste user, gardé neutre)
    "Athletic": -0.10,  # 0.90 → -0.10 | Souvent mal aimé (pantalon sport/mal coupé)
    "Slim": -0.20,      # 0.80 → -0.20 | Le "nouveau ringard" (-20%)
    "Tight": -0.30,     # 0.70 → -0.30 | Très dur à vendre, hors tendance
    "Skinny": -0.40,    # 0.60 → -0.40 | La punition (-40%), rédhibitoire pour jeunes
}


def upgrade() -> None:
    """Set pricing coefficients for all fits."""
    conn = op.get_bind()

    for fit_name, coefficient in FIT_COEFFICIENTS.items():
        conn.execute(
            text("""
                UPDATE product_attributes.fits
                SET pricing_coefficient = :coefficient
                WHERE name_en = :name
            """),
            {"name": fit_name, "coefficient": coefficient}
        )


def downgrade() -> None:
    """Reset all fit coefficients to 0.00 (neutral)."""
    conn = op.get_bind()
    conn.execute(
        text("""
            UPDATE product_attributes.fits
            SET pricing_coefficient = 0.00
        """)
    )
