"""update_conditions_coefficients

Update condition coefficients with new values.
Note 8 (Excellent) is now the reference (1.00).
Note 10 (New with tags) gets a deadstock premium (1.15).

Revision ID: 8a7c2e3f4d5b
Revises: fcc07a5c49cf
Create Date: 2026-01-22 12:21:00.000000+01:00

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '8a7c2e3f4d5b'
down_revision: Union[str, None] = 'fcc07a5c49cf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Condition coefficients (note → coefficient)
# Note 8 (Excellent) is the reference at 1.00
CONDITION_COEFFICIENTS = {
    10: "1.15",  # New with tags - Deadstock premium
    9: "1.08",   # Like new
    8: "1.00",   # Excellent - REFERENCE
    7: "0.92",   # Very good - minimal depreciation
    6: "0.85",   # Good - worn but no defects
    5: "0.65",   # Shows wear - defects appear (big drop from 6)
    4: "0.50",   # Acceptable - half price
    3: "0.40",   # Poor
    2: "0.30",   # Very poor
    1: "0.25",   # For parts only
    0: "0.20",   # Major defects - unsellable
}


def upgrade() -> None:
    conn = op.get_bind()

    for note, coefficient in CONDITION_COEFFICIENTS.items():
        conn.execute(
            text("""
                UPDATE product_attributes.conditions
                SET coefficient = :coefficient
                WHERE note = :note
            """),
            {"note": note, "coefficient": coefficient}
        )


def downgrade() -> None:
    conn = op.get_bind()

    # Restore old coefficients
    OLD_COEFFICIENTS = {
        10: "1.000",
        9: "0.950",
        8: "0.900",
        7: "0.850",
        6: "0.800",
        5: "0.700",
        4: "0.600",
        3: "0.500",
        2: "0.400",
        1: "0.300",
        0: "0.200",
    }

    for note, coefficient in OLD_COEFFICIENTS.items():
        conn.execute(
            text("""
                UPDATE product_attributes.conditions
                SET coefficient = :coefficient
                WHERE note = :note
            """),
            {"note": note, "coefficient": coefficient}
        )
