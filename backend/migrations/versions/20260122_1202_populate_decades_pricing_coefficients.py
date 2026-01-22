"""populate_decades_pricing_coefficients

Populate pricing_coefficient for decades table.
Coefficients converted from multipliers (1.20) to adjustments (0.20).

Revision ID: f424dde129a1
Revises: f909c29bf8cf
Create Date: 2026-01-22 12:02:32.956939+01:00

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'f424dde129a1'
down_revision: Union[str, None] = 'f909c29bf8cf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Decade coefficients (converted from multipliers: 1.20 → 0.20)
DECADE_COEFFICIENTS = {
    # True Vintage - Collection pieces (0.20)
    "50s": "0.20",  # Very rare, often "Made in USA/France", indestructible quality
    "60s": "0.20",  # Very rare, Mod/Rockabilly era, maximum value if good condition

    # Increasingly rare (0.18)
    "70s": "0.18",  # Hippie/Disco/Punk era, collectors pay premium

    # Golden era demand (0.15)
    "80s": "0.15",  # Iconic cuts (Boxy fit), quality materials, "Stranger Things" look
    "90s": "0.15",  # Golden age of Streetwear/Sportswear, most demanded decade

    # Y2K demand (0.12)
    "2000s": "0.12",  # Y2K is what Gen Z buys en masse, sells quickly

    # New vintage (0.05)
    "2010s": "0.05",  # Tumblr/Hipster/Indie Sleaze style coming back

    # Contemporary (0.00)
    "2020s": "0.00",  # No historical added value, standard secondhand price
}


def upgrade() -> None:
    conn = op.get_bind()

    for decade_name, coefficient in DECADE_COEFFICIENTS.items():
        conn.execute(
            text("""
                UPDATE product_attributes.decades
                SET pricing_coefficient = :coefficient
                WHERE name_en = :name
            """),
            {"name": decade_name, "coefficient": coefficient}
        )


def downgrade() -> None:
    conn = op.get_bind()

    # Reset all coefficients to default 0.00
    conn.execute(
        text("""
            UPDATE product_attributes.decades
            SET pricing_coefficient = 0.00
        """)
    )
