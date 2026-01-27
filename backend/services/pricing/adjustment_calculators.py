"""
Adjustment Calculators

Price adjustment calculators for the pricing algorithm.
Includes model coefficient extraction and condition/origin-based adjustments.

Updated 2026-01-22: All coefficients are now loaded from the database
(product_attributes schema) instead of being hardcoded.

NEW LOGIC: Adjustment = MAX(actual coefficients) - MAX(expected coefficients)
- If no expected → expected = 0.00
- Negative adjustments (malus) are applied
- Features: capped at +0.30
"""

from decimal import Decimal
from typing import Optional

from models.product_attributes.model import Model


# Adjustment caps for features
MAX_FEATURE_ADJUSTMENT = Decimal("0.30")


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
    Calculate origin-based price adjustment using difference logic.

    Formula: Adjustment = actual_coefficient - MAX(expected_coefficients)

    Logic:
    - Get coefficient for actual origin from DB
    - Get MAX coefficient from expected origins
    - Return the difference (can be negative = malus)

    Args:
        actual_origin: The actual product origin country (can be None/empty).
        expected_origins: List of expected origin countries.
        origin_coefficients: Dict mapping origin names to their pricing coefficients.

    Returns:
        Adjustment as Decimal (can be negative).

    Examples:
        actual=France(+0.18), expected=[China(-0.05)] → +0.18 - (-0.05) = +0.23
        actual=China(-0.05), expected=[France(+0.18)] → -0.05 - 0.18 = -0.23
        actual=Italy(+0.18), expected=[France(+0.18)] → +0.18 - 0.18 = 0.00
    """
    # Get actual coefficient (default 0.00 if unknown or empty)
    if not actual_origin or (isinstance(actual_origin, str) and not actual_origin.strip()):
        actual_coef = Decimal("0.00")
    else:
        actual_coef = origin_coefficients.get(actual_origin, Decimal("0.00"))

    # Get MAX expected coefficient (default 0.00 if no expected)
    if not expected_origins:
        expected_coef = Decimal("0.00")
    else:
        expected_coef = max(
            origin_coefficients.get(origin, Decimal("0.00"))
            for origin in expected_origins
        )

    # Return difference
    return actual_coef - expected_coef


def calculateDecadeAdjustment(
    actual_decade: Optional[str],
    expected_decades: list[str],
    decade_coefficients: dict[str, Decimal],
) -> Decimal:
    """
    Calculate decade-based price adjustment using difference logic.

    Formula: Adjustment = actual_coefficient - MAX(expected_coefficients)

    Logic:
    - Get coefficient for actual decade from DB
    - Get MAX coefficient from expected decades
    - Return the difference (can be negative = malus)

    Args:
        actual_decade: The actual product decade (e.g., "90s"). Can be None/empty.
        expected_decades: List of expected decades.
        decade_coefficients: Dict mapping decade names to their pricing coefficients.

    Returns:
        Adjustment as Decimal (can be negative).

    Examples:
        actual=90s(+0.15), expected=[2000s(+0.12)] → +0.15 - 0.12 = +0.03
        actual=2020s(0.00), expected=[90s(+0.15)] → 0.00 - 0.15 = -0.15
        actual=90s(+0.15), expected=[90s(+0.15)] → +0.15 - 0.15 = 0.00
    """
    # Get actual coefficient (default 0.00 if unknown or empty)
    if not actual_decade or (isinstance(actual_decade, str) and not actual_decade.strip()):
        actual_coef = Decimal("0.00")
    else:
        actual_coef = decade_coefficients.get(actual_decade, Decimal("0.00"))

    # Get MAX expected coefficient (default 0.00 if no expected)
    if not expected_decades:
        expected_coef = Decimal("0.00")
    else:
        expected_coef = max(
            decade_coefficients.get(decade, Decimal("0.00"))
            for decade in expected_decades
        )

    # Return difference
    return actual_coef - expected_coef


def calculateTrendAdjustment(
    actual_trends: list[str],
    expected_trends: list[str],
    trend_coefficients: dict[str, Decimal],
) -> Decimal:
    """
    Calculate trend-based price adjustment using difference logic.

    Formula: Adjustment = MAX(actual_coefficients) - MAX(expected_coefficients)

    Logic:
    - Get MAX coefficient from actual trends
    - Get MAX coefficient from expected trends
    - Return the difference (can be negative = malus)

    Args:
        actual_trends: List of actual product trends.
        expected_trends: List of expected trends for the product group.
        trend_coefficients: Dict mapping trend names to their pricing coefficients.

    Returns:
        Adjustment as Decimal (can be negative).

    Examples:
        actual=[Techwear(+0.20)], expected=[Y2K(+0.12)] → +0.20 - 0.12 = +0.08
        actual=[Normcore(0.00)], expected=[Techwear(+0.20)] → 0.00 - 0.20 = -0.20
        actual=[Techwear(+0.20), Y2K(+0.12)], expected=[Gorpcore(+0.18)] → +0.20 - 0.18 = +0.02
    """
    # Get MAX actual coefficient (default 0.00 if no actual or all unknown)
    if not actual_trends:
        actual_coef = Decimal("0.00")
    else:
        known_actual = [
            trend_coefficients.get(trend, Decimal("0.00"))
            for trend in actual_trends
            if trend in trend_coefficients
        ]
        actual_coef = max(known_actual) if known_actual else Decimal("0.00")

    # Get MAX expected coefficient (default 0.00 if no expected)
    if not expected_trends:
        expected_coef = Decimal("0.00")
    else:
        known_expected = [
            trend_coefficients.get(trend, Decimal("0.00"))
            for trend in expected_trends
            if trend in trend_coefficients
        ]
        expected_coef = max(known_expected) if known_expected else Decimal("0.00")

    # Return difference
    return actual_coef - expected_coef


def calculateFeatureAdjustment(
    actual_features: list[str],
    expected_features: list[str],
    feature_coefficients: dict[str, Decimal],
) -> Decimal:
    """
    Calculate feature-based price adjustment using difference logic.

    Formula: Adjustment = MAX(actual_coefficients) - MAX(expected_coefficients)
    Result is capped at +0.30

    Logic:
    - Get MAX coefficient from actual features
    - Get MAX coefficient from expected features
    - Return the difference, capped at +0.30 (can be negative = malus)

    Args:
        actual_features: List of actual product features.
        expected_features: List of expected features for the product group.
        feature_coefficients: Dict mapping feature names to their pricing coefficients.

    Returns:
        Adjustment as Decimal (capped at +0.30, can be negative).

    Examples:
        actual=[Selvedge(+0.20)], expected=[Distressed(+0.05)] → +0.20 - 0.05 = +0.15
        actual=[Printed(+0.01)], expected=[Selvedge(+0.20)] → +0.01 - 0.20 = -0.19
        actual=[Deadstock(+0.20), Selvedge(+0.20)], expected=[] → +0.20 - 0.00 = +0.20
    """
    # Get MAX actual coefficient (default 0.00 if no actual or all unknown)
    if not actual_features:
        actual_coef = Decimal("0.00")
    else:
        known_actual = [
            feature_coefficients.get(feature, Decimal("0.00"))
            for feature in actual_features
            if feature in feature_coefficients
        ]
        actual_coef = max(known_actual) if known_actual else Decimal("0.00")

    # Get MAX expected coefficient (default 0.00 if no expected)
    if not expected_features:
        expected_coef = Decimal("0.00")
    else:
        known_expected = [
            feature_coefficients.get(feature, Decimal("0.00"))
            for feature in expected_features
            if feature in feature_coefficients
        ]
        expected_coef = max(known_expected) if known_expected else Decimal("0.00")

    # Calculate difference
    adjustment = actual_coef - expected_coef

    # Cap at +0.30 (no cap on negative side)
    if adjustment > MAX_FEATURE_ADJUSTMENT:
        return MAX_FEATURE_ADJUSTMENT

    return adjustment


def calculateFitAdjustment(
    actual_fit: Optional[str],
    expected_fits: list[str],
    fit_coefficients: dict[str, Decimal],
) -> Decimal:
    """
    Calculate fit-based price adjustment using difference logic.

    Formula: Adjustment = actual_coefficient - MAX(expected_coefficients)

    Logic:
    - Get coefficient for actual fit from DB
    - Get MAX coefficient from expected fits
    - Return the difference (can be negative = malus)

    Args:
        actual_fit: The actual product fit (e.g., "Bootcut", "Slim"). Can be None/empty.
        expected_fits: List of expected fits for the product group.
        fit_coefficients: Dict mapping fit names to their pricing coefficients.

    Returns:
        Adjustment as Decimal (can be negative).

    Examples:
        actual=Bootcut(+0.15), expected=[Slim(0.00)] → +0.15 - 0.00 = +0.15
        actual=Skinny(-0.10), expected=[Bootcut(+0.15)] → -0.10 - 0.15 = -0.25
        actual=Regular(0.00), expected=[Regular(0.00)] → 0.00 - 0.00 = 0.00
    """
    # Get actual coefficient (default 0.00 if unknown or empty)
    if not actual_fit or (isinstance(actual_fit, str) and not actual_fit.strip()):
        actual_coef = Decimal("0.00")
    else:
        actual_coef = fit_coefficients.get(actual_fit, Decimal("0.00"))

    # Get MAX expected coefficient (default 0.00 if no expected)
    if not expected_fits:
        expected_coef = Decimal("0.00")
    else:
        expected_coef = max(
            fit_coefficients.get(fit, Decimal("0.00"))
            for fit in expected_fits
        )

    # Return difference
    return actual_coef - expected_coef
