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

# Premium origins for origin adjustment
PREMIUM_ORIGINS = {"Italy", "France", "Japan", "USA", "UK", "Germany"}

# Country neighbors mapping (key countries and their neighbors)
COUNTRY_NEIGHBORS = {
    "France": {"Belgium", "Switzerland", "Spain", "Italy", "Germany"},
    "Italy": {"France", "Switzerland", "Austria"},
    "Germany": {"France", "Belgium", "Netherlands", "Austria", "Switzerland", "Poland"},
    "Spain": {"France", "Portugal"},
    "UK": {"Ireland"},
    "USA": {"Canada", "Mexico"},
}

# Decade coefficients for vintage bonuses
DECADE_COEFFICIENTS = {
    "1950s": Decimal("0.20"),
    "1960s": Decimal("0.18"),
    "1970s": Decimal("0.15"),
    "1980s": Decimal("0.12"),
    "1990s": Decimal("0.08"),
    "2000s": Decimal("0.05"),
    "2010s": Decimal("0.02"),
    "2020s": Decimal("0.00"),
}


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


def calculateOriginAdjustment(
    actual_origin: Optional[str],
    expected_origins: list[str]
) -> Decimal:
    """
    Calculate origin-based price adjustment using 4-tier system.

    Tier logic (order matters):
    - Tier 1 (expected): actual in expected_origins → 0.00
    - Tier 3 (premium): actual in PREMIUM_ORIGINS and not expected → +0.15
    - Tier 2 (neighbor): actual is neighbor of any expected → 0.00
    - Tier 4 (other): fallback → -0.10

    Args:
        actual_origin: The actual product origin country.
        expected_origins: List of expected origin countries.

    Returns:
        Adjustment as Decimal (-0.10 to +0.15).

    Raises:
        ValueError: If actual_origin is None or empty.
    """
    # Validate inputs
    if not actual_origin or (isinstance(actual_origin, str) and not actual_origin.strip()):
        raise ValueError("Actual origin cannot be None or empty")

    # Tier 1: Expected match
    if actual_origin in expected_origins:
        return Decimal("0.00")

    # Tier 3: Premium origin (not expected)
    if actual_origin in PREMIUM_ORIGINS:
        return Decimal("0.15")

    # Tier 2: Neighbor of expected
    for expected in expected_origins:
        if expected in COUNTRY_NEIGHBORS:
            neighbors = COUNTRY_NEIGHBORS[expected]
            if actual_origin in neighbors:
                return Decimal("0.00")

    # Tier 4: Other (fallback)
    return Decimal("-0.10")


def calculateDecadeAdjustment(
    actual_decade: Optional[str],
    expected_decades: list[str]
) -> Decimal:
    """
    Calculate decade-based price adjustment with vintage bonuses.

    Logic:
    - If actual in expected_decades → 0.00 (as expected, no bonus)
    - If actual NOT in expected_decades → bonus from DECADE_COEFFICIENTS
    - Vintage items (older decades) have higher bonuses

    Args:
        actual_decade: The actual product decade (e.g., "1990s").
        expected_decades: List of expected decades.

    Returns:
        Adjustment as Decimal (0.00 to +0.20).

    Raises:
        ValueError: If actual_decade is None, empty, or unknown.
    """
    # Validate inputs
    if not actual_decade or (isinstance(actual_decade, str) and not actual_decade.strip()):
        raise ValueError("Actual decade cannot be None or empty")

    # Check if decade is known
    if actual_decade not in DECADE_COEFFICIENTS:
        raise ValueError(f"Unknown decade: {actual_decade}")

    # If actual is in expected list, no bonus (as expected)
    if actual_decade in expected_decades:
        return Decimal("0.00")

    # If actual is NOT in expected list, apply vintage bonus
    return DECADE_COEFFICIENTS[actual_decade]
