"""
Adjustment Calculators

Price adjustment calculators for the pricing algorithm.
Includes model coefficient extraction and condition/origin-based adjustments.

Updated 2026-01-22: All coefficients are now loaded from the database
(product_attributes schema) instead of being hardcoded.
- Condition: uses coefficient from conditions table (multiplier 0.2-1.0)
- Origin: uses pricing_coefficient from origins table
- Decades, Trends, Features: use pricing_coefficient from respective tables
"""

from decimal import Decimal
from typing import Optional

from models.product_attributes.model import Model


# Adjustment caps for features
MAX_ADJUSTMENT = Decimal("0.30")


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


def calculateConditionMultiplier(
    condition_coefficient: Decimal,
) -> Decimal:
    """
    Get condition multiplier from database coefficient.

    The condition coefficient is a direct multiplier (0.2 to 1.15):
    - New with tags: 1.15 (115% - deadstock premium)
    - Like new: 1.08 (108%)
    - Excellent: 1.00 (100% - REFERENCE)
    - Very good: 0.92 (92%)
    - Good: 0.85 (85%)
    - Shows wear: 0.65 (65% - big drop, defects appear)
    - Acceptable: 0.50 (50%)
    - Poor: 0.40 (40%)
    - Very poor: 0.30 (30%)
    - For parts only: 0.25 (25%)
    - Major defects: 0.20 (20%)

    Args:
        condition_coefficient: Coefficient from conditions table (0.2-1.15).

    Returns:
        Multiplier as Decimal (0.2-1.15).

    Raises:
        ValueError: If coefficient not in valid range.
    """
    if condition_coefficient is None:
        return Decimal("1.0")

    if not (Decimal("0.1") <= condition_coefficient <= Decimal("1.2")):
        raise ValueError(f"Condition coefficient must be between 0.1 and 1.2, got {condition_coefficient}")

    return condition_coefficient


def calculateOriginAdjustment(
    actual_origin: Optional[str],
    expected_origins: list[str],
    origin_coefficients: dict[str, Decimal],
) -> Decimal:
    """
    Calculate origin-based price adjustment using database coefficients.

    Logic:
    - Unknown/empty: actual is None or empty → 0.00 (neutral)
    - Expected: actual in expected_origins → 0.00 (as expected)
    - Unexpected: actual NOT in expected_origins → use DB coefficient
      (premium origins have +0.15, others have 0.00)

    Args:
        actual_origin: The actual product origin country (can be None/empty).
        expected_origins: List of expected origin countries.
        origin_coefficients: Dict mapping origin names to their pricing coefficients.
                            Loaded from product_attributes.origins table.

    Returns:
        Adjustment as Decimal (0.00 to +0.15).
    """
    # If origin is unknown, return neutral adjustment
    if not actual_origin or (isinstance(actual_origin, str) and not actual_origin.strip()):
        return Decimal("0.00")

    # If origin is expected, no bonus
    if actual_origin in expected_origins:
        return Decimal("0.00")

    # If origin is unexpected, return its coefficient from DB (premium = 0.15, others = 0.00)
    return origin_coefficients.get(actual_origin, Decimal("0.00"))


def calculateDecadeAdjustment(
    actual_decade: Optional[str],
    expected_decades: list[str],
    decade_coefficients: dict[str, Decimal],
) -> Decimal:
    """
    Calculate decade-based price adjustment with vintage bonuses.

    Logic:
    - Unknown/empty: actual is None or empty → 0.00 (neutral)
    - If actual in expected_decades → 0.00 (as expected, no bonus)
    - If actual NOT in expected_decades → bonus from decade_coefficients
    - Vintage items (older decades) have higher bonuses

    Args:
        actual_decade: The actual product decade (e.g., "1990s"). Can be None/empty.
        expected_decades: List of expected decades.
        decade_coefficients: Dict mapping decade names to their pricing coefficients.
                            Loaded from product_attributes.decades table.

    Returns:
        Adjustment as Decimal (0.00 to +0.20), or 0.00 if decade unknown.
    """
    # If decade is unknown or empty, return neutral adjustment
    if not actual_decade or (isinstance(actual_decade, str) and not actual_decade.strip()):
        return Decimal("0.00")

    # If decade is not in our known coefficients, return neutral
    if actual_decade not in decade_coefficients:
        return Decimal("0.00")

    # If actual is in expected list, no bonus (as expected)
    if actual_decade in expected_decades:
        return Decimal("0.00")

    # If actual is NOT in expected list, apply vintage bonus
    return decade_coefficients[actual_decade]


def calculateTrendAdjustment(
    actual_trends: list[str],
    expected_trends: list[str],
    trend_coefficients: dict[str, Decimal],
) -> Decimal:
    """
    Calculate trend-based price adjustment with best unexpected trend logic.

    Logic:
    - Find trends in actual_trends that are NOT in expected_trends
    - For each unexpected trend, get coefficient from trend_coefficients
    - Return the MAXIMUM coefficient (best unexpected trend)
    - If no unexpected trends or all actual are expected → 0.00
    - Unknown trends in actual_trends are ignored (don't crash)

    Args:
        actual_trends: List of actual product trends (e.g., ["y2k", "vintage"]).
        expected_trends: List of expected trends for the product group.
        trend_coefficients: Dict mapping trend names to their pricing coefficients.
                           Loaded from product_attributes.trends table.

    Returns:
        Adjustment as Decimal (0.00 to +0.20).

    Examples:
        actual=["y2k"], expected=["y2k"] → 0.00 (expected, no bonus)
        actual=["y2k"], expected=["vintage"] → +0.12 (unexpected y2k)
        actual=["Techwear", "vintage"], expected=["grunge"] → +0.20 (max of 0.20, 0.05)
    """
    # Find unexpected trends (actual NOT in expected) that are known
    unexpected_trends = [
        trend for trend in actual_trends
        if trend not in expected_trends and trend in trend_coefficients
    ]

    # If no unexpected trends, return 0.00
    if not unexpected_trends:
        return Decimal("0.00")

    # Return MAX coefficient (best unexpected trend)
    return max(trend_coefficients[trend] for trend in unexpected_trends)


def calculateFeatureAdjustment(
    actual_features: list[str],
    expected_features: list[str],
    feature_coefficients: dict[str, Decimal],
) -> Decimal:
    """
    Calculate feature-based price adjustment with sum and cap logic.

    Logic:
    - Find features in actual_features that are NOT in expected_features
    - For each unexpected feature, get coefficient from feature_coefficients
    - Return the SUM of coefficients, capped at +0.30
    - If no unexpected features or all actual are expected → 0.00
    - Unknown features in actual_features are ignored (don't crash)

    Args:
        actual_features: List of actual product features (e.g., ["Deadstock fabric", "Selvedge"]).
        expected_features: List of expected features for the product group.
        feature_coefficients: Dict mapping feature names to their pricing coefficients.
                             Loaded from product_attributes.unique_features table.

    Returns:
        Adjustment as Decimal (0.00 to +0.30, capped).

    Examples:
        actual=["Selvedge"], expected=["Selvedge"] → 0.00 (expected, no bonus)
        actual=["Deadstock fabric"], expected=["Selvedge"] → +0.20 (unexpected deadstock)
        actual=["Selvedge", "Chain stitching"], expected=[] → +0.32 → capped to +0.30
    """
    # Find unexpected features (actual NOT in expected) that are known
    unexpected_features = [
        feature for feature in actual_features
        if feature not in expected_features and feature in feature_coefficients
    ]

    # If no unexpected features, return 0.00
    if not unexpected_features:
        return Decimal("0.00")

    # Sum all unexpected feature coefficients
    total_adjustment = sum(feature_coefficients[feature] for feature in unexpected_features)

    # Cap at +0.30
    if total_adjustment > MAX_ADJUSTMENT:
        return MAX_ADJUSTMENT

    return total_adjustment
