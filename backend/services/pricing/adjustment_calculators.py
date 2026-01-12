"""
Adjustment Calculators

Price adjustment calculators for the pricing algorithm.
Includes model coefficient extraction and condition-based adjustments.
"""

from decimal import Decimal
from typing import Optional

from models.public.model import Model


# Supplement values for condition adjustment
SUPPLEMENT_VALUES = {
    "original_box": Decimal("0.05"),
    "tags": Decimal("0.03"),
    "dust_bag": Decimal("0.03"),
    "authenticity_card": Decimal("0.04"),
}

# Adjustment caps
MAX_ADJUSTMENT = Decimal("0.30")
MIN_ADJUSTMENT = Decimal("-0.30")


def calculateModelCoefficient(model: Optional[Model]) -> Decimal:
    """
    Extract model coefficient from Model entity.

    Args:
        model: Model entity with coefficient field.

    Returns:
        Model coefficient as Decimal (0.5-3.0 range).

    Raises:
        ValueError: If model is None or coefficient is None.
    """
    if model is None:
        raise ValueError("Model cannot be None")

    if model.coefficient is None:
        raise ValueError("Model coefficient cannot be None")

    return model.coefficient


def calculateConditionAdjustment(
    condition_score: int,
    supplements: list[str],
    condition_sensitivity: Decimal
) -> Decimal:
    """
    Calculate condition-based price adjustment with supplement bonuses and caps.

    Formula: (score - 3.0) / 10.0 * sensitivity + supplement_sum
    Result is capped at ±0.30

    Args:
        condition_score: Condition score (0-5, where 3 is baseline).
        supplements: List of supplement keys (e.g., ["original_box", "tags"]).
        condition_sensitivity: Sensitivity multiplier (0.5-1.5 range).

    Returns:
        Adjustment as Decimal, capped at ±0.30 and rounded to 2 decimal places.

    Raises:
        ValueError: If score not in [0-5] or sensitivity not in [0.5-1.5].
    """
    # Validate inputs
    if not (0 <= condition_score <= 5):
        raise ValueError("Condition score must be between 0 and 5")

    if not (Decimal("0.5") <= condition_sensitivity <= Decimal("1.5")):
        raise ValueError("Condition sensitivity must be between 0.5 and 1.5")

    # Base calculation: (score - 3.0) / 10.0 * sensitivity
    score_decimal = Decimal(str(condition_score))
    base_adjustment = (score_decimal - Decimal("3.0")) / Decimal("10.0") * condition_sensitivity

    # Sum supplement bonuses (ignore unknown supplements)
    supplement_sum = sum(
        SUPPLEMENT_VALUES.get(supplement, Decimal("0.0"))
        for supplement in supplements
    )

    # Total adjustment
    total_adjustment = base_adjustment + supplement_sum

    # Apply caps
    if total_adjustment > MAX_ADJUSTMENT:
        total_adjustment = MAX_ADJUSTMENT
    elif total_adjustment < MIN_ADJUSTMENT:
        total_adjustment = MIN_ADJUSTMENT

    # Round to 2 decimal places
    return total_adjustment.quantize(Decimal("0.01"))
