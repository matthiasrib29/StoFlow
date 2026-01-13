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

# Trend coefficients for unexpected trend bonuses
TREND_COEFFICIENTS = {
    "y2k": Decimal("0.20"),
    "vintage": Decimal("0.18"),
    "grunge": Decimal("0.15"),
    "streetwear": Decimal("0.12"),
    "minimalist": Decimal("0.08"),
    "bohemian": Decimal("0.06"),
    "preppy": Decimal("0.04"),
    "athleisure": Decimal("0.02"),
}

# Feature coefficients for unexpected feature bonuses
FEATURE_COEFFICIENTS = {
    "deadstock": Decimal("0.20"),
    "selvedge": Decimal("0.15"),
    "og_colorway": Decimal("0.15"),
    "limited_edition": Decimal("0.12"),
    "vintage_label": Decimal("0.10"),
    "original_box": Decimal("0.10"),
    "chain_stitching": Decimal("0.08"),
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

    Formula: (score - 5.0) * 0.06 * sensitivity + supplement_sum
    Result is capped at ±0.30

    Args:
        condition_score: Condition score (0-10, where 5 is baseline).
        supplements: List of supplement keys (e.g., ["original_box", "tags"]).
        condition_sensitivity: Sensitivity multiplier (0.5-1.5 range).

    Returns:
        Adjustment as Decimal, capped at ±0.30 and rounded to 2 decimal places.

    Raises:
        ValueError: If score not in [0-10] or sensitivity not in [0.5-1.5].
    """
    # Validate inputs
    if not (0 <= condition_score <= 10):
        raise ValueError("Condition score must be between 0 and 10")

    if not (Decimal("0.5") <= condition_sensitivity <= Decimal("1.5")):
        raise ValueError("Condition sensitivity must be between 0.5 and 1.5")

    # Base calculation: (score - 5.0) * 0.06 * sensitivity
    # Score 0 → -0.30, Score 5 → 0, Score 10 → +0.30 (before sensitivity)
    score_decimal = Decimal(str(condition_score))
    base_adjustment = (score_decimal - Decimal("5.0")) * Decimal("0.06") * condition_sensitivity

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
    - Unknown/empty: actual is None or empty → 0.00 (neutral)
    - Tier 1 (expected): actual in expected_origins → 0.00
    - Tier 3 (premium): actual in PREMIUM_ORIGINS and not expected → +0.15
    - Tier 2 (neighbor): actual is neighbor of any expected → 0.00
    - Tier 4 (other): fallback → -0.10

    Args:
        actual_origin: The actual product origin country (can be None/empty).
        expected_origins: List of expected origin countries.

    Returns:
        Adjustment as Decimal (-0.10 to +0.15), or 0.00 if origin unknown.
    """
    # If origin is unknown, return neutral adjustment
    if not actual_origin or (isinstance(actual_origin, str) and not actual_origin.strip()):
        return Decimal("0.00")

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
    - Unknown/empty: actual is None or empty → 0.00 (neutral)
    - If actual in expected_decades → 0.00 (as expected, no bonus)
    - If actual NOT in expected_decades → bonus from DECADE_COEFFICIENTS
    - Vintage items (older decades) have higher bonuses

    Args:
        actual_decade: The actual product decade (e.g., "1990s"). Can be None/empty.
        expected_decades: List of expected decades.

    Returns:
        Adjustment as Decimal (0.00 to +0.20), or 0.00 if decade unknown.
    """
    # If decade is unknown or empty, return neutral adjustment
    if not actual_decade or (isinstance(actual_decade, str) and not actual_decade.strip()):
        return Decimal("0.00")

    # If decade is not in our known coefficients, return neutral
    if actual_decade not in DECADE_COEFFICIENTS:
        return Decimal("0.00")

    # If actual is in expected list, no bonus (as expected)
    if actual_decade in expected_decades:
        return Decimal("0.00")

    # If actual is NOT in expected list, apply vintage bonus
    return DECADE_COEFFICIENTS[actual_decade]


def calculateTrendAdjustment(
    actual_trends: list[str],
    expected_trends: list[str]
) -> Decimal:
    """
    Calculate trend-based price adjustment with best unexpected trend logic.

    Logic:
    - Find trends in actual_trends that are NOT in expected_trends
    - For each unexpected trend, get coefficient from TREND_COEFFICIENTS
    - Return the MAXIMUM coefficient (best unexpected trend)
    - If no unexpected trends or all actual are expected → 0.00
    - Unknown trends in actual_trends are ignored (don't crash)

    Args:
        actual_trends: List of actual product trends (e.g., ["y2k", "vintage"]).
        expected_trends: List of expected trends for the product group.

    Returns:
        Adjustment as Decimal (0.00 to +0.20).

    Examples:
        actual=["y2k"], expected=["y2k"] → 0.00 (expected, no bonus)
        actual=["y2k"], expected=["vintage"] → +0.20 (unexpected y2k)
        actual=["y2k", "vintage"], expected=["grunge"] → +0.20 (max of 0.20, 0.18)
        actual=["y2k", "vintage"], expected=["y2k"] → +0.18 (vintage unexpected)
    """
    # Find unexpected trends (actual NOT in expected) that are known
    unexpected_trends = [
        trend for trend in actual_trends
        if trend not in expected_trends and trend in TREND_COEFFICIENTS
    ]

    # If no unexpected trends, return 0.00
    if not unexpected_trends:
        return Decimal("0.00")

    # Return MAX coefficient (best unexpected trend)
    return max(TREND_COEFFICIENTS[trend] for trend in unexpected_trends)


def calculateFeatureAdjustment(
    actual_features: list[str],
    expected_features: list[str]
) -> Decimal:
    """
    Calculate feature-based price adjustment with sum and cap logic.

    Logic:
    - Find features in actual_features that are NOT in expected_features
    - For each unexpected feature, get coefficient from FEATURE_COEFFICIENTS
    - Return the SUM of coefficients, capped at +0.30
    - If no unexpected features or all actual are expected → 0.00
    - Unknown features in actual_features are ignored (don't crash)

    Args:
        actual_features: List of actual product features (e.g., ["deadstock", "selvedge"]).
        expected_features: List of expected features for the product group.

    Returns:
        Adjustment as Decimal (0.00 to +0.30, capped).

    Examples:
        actual=["selvedge"], expected=["selvedge"] → 0.00 (expected, no bonus)
        actual=["deadstock"], expected=["selvedge"] → +0.20 (unexpected deadstock)
        actual=["selvedge", "original_box"], expected=[] → +0.25 (0.15 + 0.10)
        actual=["deadstock", "selvedge"], expected=[] → +0.30 (capped from 0.35)
    """
    # Find unexpected features (actual NOT in expected) that are known
    unexpected_features = [
        feature for feature in actual_features
        if feature not in expected_features and feature in FEATURE_COEFFICIENTS
    ]

    # If no unexpected features, return 0.00
    if not unexpected_features:
        return Decimal("0.00")

    # Sum all unexpected feature coefficients
    total_adjustment = sum(FEATURE_COEFFICIENTS[feature] for feature in unexpected_features)

    # Cap at +0.30
    if total_adjustment > MAX_ADJUSTMENT:
        return MAX_ADJUSTMENT

    return total_adjustment
