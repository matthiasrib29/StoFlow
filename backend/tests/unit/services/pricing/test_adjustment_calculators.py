"""
Unit Tests for Adjustment Calculators

Tests for model coefficient and condition adjustment calculators.
Covers success paths, edge cases, validation, capping, and supplements.

Updated 2026-01-22: Decade, Trend, and Feature calculators now receive
coefficients as parameters (loaded from database) instead of hardcoded dicts.
"""

from decimal import Decimal
from unittest.mock import Mock

import pytest

from models.product_attributes.model import Model
from services.pricing.adjustment_calculators import (
    calculateConditionAdjustment,
    calculateDecadeAdjustment,
    calculateFeatureAdjustment,
    calculateModelCoefficient,
    calculateOriginAdjustment,
    calculateTrendAdjustment,
)


# ===== Test Coefficients (simulating database values) =====

TEST_DECADE_COEFFICIENTS = {
    "1950s": Decimal("0.20"),
    "1960s": Decimal("0.18"),
    "1970s": Decimal("0.15"),
    "1980s": Decimal("0.12"),
    "1990s": Decimal("0.08"),
    "2000s": Decimal("0.05"),
    "2010s": Decimal("0.02"),
    "2020s": Decimal("0.00"),
}

TEST_TREND_COEFFICIENTS = {
    "y2k": Decimal("0.20"),
    "vintage": Decimal("0.18"),
    "grunge": Decimal("0.15"),
    "streetwear": Decimal("0.12"),
    "minimalist": Decimal("0.08"),
    "bohemian": Decimal("0.06"),
    "preppy": Decimal("0.04"),
    "athleisure": Decimal("0.02"),
}

TEST_FEATURE_COEFFICIENTS = {
    "deadstock": Decimal("0.20"),
    "selvedge": Decimal("0.15"),
    "og_colorway": Decimal("0.15"),
    "limited_edition": Decimal("0.12"),
    "vintage_label": Decimal("0.10"),
    "original_box": Decimal("0.10"),
    "chain_stitching": Decimal("0.08"),
}


# ===== TestCalculateModelCoefficient =====


class TestCalculateModelCoefficient:
    """Test model coefficient extraction from Model entity."""

    def test_extract_coefficient_standard(self):
        """Should return coefficient 1.5 for standard model."""
        model = Mock(spec=Model)
        model.coefficient = Decimal("1.5")

        result = calculateModelCoefficient(model)

        assert result == Decimal("1.5")
        assert isinstance(result, Decimal)

    def test_extract_coefficient_minimum(self):
        """Should return coefficient 0.5 for minimum value."""
        model = Mock(spec=Model)
        model.coefficient = Decimal("0.5")

        result = calculateModelCoefficient(model)

        assert result == Decimal("0.5")

    def test_extract_coefficient_maximum(self):
        """Should return coefficient 3.0 for maximum value."""
        model = Mock(spec=Model)
        model.coefficient = Decimal("3.0")

        result = calculateModelCoefficient(model)

        assert result == Decimal("3.0")

    def test_extract_coefficient_neutral(self):
        """Should return coefficient 1.0 for neutral multiplier."""
        model = Mock(spec=Model)
        model.coefficient = Decimal("1.0")

        result = calculateModelCoefficient(model)

        assert result == Decimal("1.0")

    def test_raises_error_when_model_is_none(self):
        """Should raise ValueError when model is None."""
        with pytest.raises(ValueError, match="Model cannot be None"):
            calculateModelCoefficient(None)

    def test_raises_error_when_coefficient_is_none(self):
        """Should raise ValueError when coefficient is None."""
        model = Mock(spec=Model)
        model.coefficient = None

        with pytest.raises(ValueError, match="Model coefficient cannot be None"):
            calculateModelCoefficient(model)

    def test_returns_decimal_type(self):
        """Should always return Decimal type for precision."""
        model = Mock(spec=Model)
        model.coefficient = Decimal("2.25")

        result = calculateModelCoefficient(model)

        assert isinstance(result, Decimal)


# ===== TestCalculateConditionAdjustment =====


class TestCalculateConditionAdjustment:
    """Test condition-based price adjustment with supplements and caps."""

    # --- Base calculation tests (no supplements, sensitivity=1.0) ---

    def test_perfect_condition_score_5(self):
        """Score 5 (perfect) should return +0.20."""
        result = calculateConditionAdjustment(
            condition_score=5,
            supplements=[],
            condition_sensitivity=Decimal("1.0")
        )

        assert result == Decimal("0.20")

    def test_excellent_condition_score_4(self):
        """Score 4 (excellent) should return +0.10."""
        result = calculateConditionAdjustment(
            condition_score=4,
            supplements=[],
            condition_sensitivity=Decimal("1.0")
        )

        assert result == Decimal("0.10")

    def test_good_condition_score_3_baseline(self):
        """Score 3 (good, baseline) should return 0.00."""
        result = calculateConditionAdjustment(
            condition_score=3,
            supplements=[],
            condition_sensitivity=Decimal("1.0")
        )

        assert result == Decimal("0.00")

    def test_fair_condition_score_2(self):
        """Score 2 (fair) should return -0.10."""
        result = calculateConditionAdjustment(
            condition_score=2,
            supplements=[],
            condition_sensitivity=Decimal("1.0")
        )

        assert result == Decimal("-0.10")

    def test_poor_condition_score_1(self):
        """Score 1 (poor) should return -0.20."""
        result = calculateConditionAdjustment(
            condition_score=1,
            supplements=[],
            condition_sensitivity=Decimal("1.0")
        )

        assert result == Decimal("-0.20")

    def test_damaged_condition_score_0(self):
        """Score 0 (damaged) should return -0.30 (capped)."""
        result = calculateConditionAdjustment(
            condition_score=0,
            supplements=[],
            condition_sensitivity=Decimal("1.0")
        )

        assert result == Decimal("-0.30")

    # --- Sensitivity scaling tests (score=4, no supplements) ---

    def test_sensitivity_low_half(self):
        """Sensitivity 0.5 should halve the adjustment."""
        result = calculateConditionAdjustment(
            condition_score=4,
            supplements=[],
            condition_sensitivity=Decimal("0.5")
        )

        assert result == Decimal("0.05")

    def test_sensitivity_neutral(self):
        """Sensitivity 1.0 should apply neutral adjustment."""
        result = calculateConditionAdjustment(
            condition_score=4,
            supplements=[],
            condition_sensitivity=Decimal("1.0")
        )

        assert result == Decimal("0.10")

    def test_sensitivity_high(self):
        """Sensitivity 1.5 should increase the adjustment."""
        result = calculateConditionAdjustment(
            condition_score=4,
            supplements=[],
            condition_sensitivity=Decimal("1.5")
        )

        assert result == Decimal("0.15")

    # --- Supplement bonus tests (score=3, sensitivity=1.0) ---

    def test_supplement_original_box(self):
        """Original box should add +0.05."""
        result = calculateConditionAdjustment(
            condition_score=3,
            supplements=["original_box"],
            condition_sensitivity=Decimal("1.0")
        )

        assert result == Decimal("0.05")

    def test_supplement_tags(self):
        """Tags should add +0.03."""
        result = calculateConditionAdjustment(
            condition_score=3,
            supplements=["tags"],
            condition_sensitivity=Decimal("1.0")
        )

        assert result == Decimal("0.03")

    def test_supplement_dust_bag(self):
        """Dust bag should add +0.03."""
        result = calculateConditionAdjustment(
            condition_score=3,
            supplements=["dust_bag"],
            condition_sensitivity=Decimal("1.0")
        )

        assert result == Decimal("0.03")

    def test_supplement_authenticity_card(self):
        """Authenticity card should add +0.04."""
        result = calculateConditionAdjustment(
            condition_score=3,
            supplements=["authenticity_card"],
            condition_sensitivity=Decimal("1.0")
        )

        assert result == Decimal("0.04")

    def test_multiple_supplements(self):
        """Multiple supplements should sum their bonuses."""
        result = calculateConditionAdjustment(
            condition_score=3,
            supplements=["original_box", "tags"],
            condition_sensitivity=Decimal("1.0")
        )

        # Base 0.00 + 0.05 (box) + 0.03 (tags) = 0.08
        assert result == Decimal("0.08")

    def test_empty_supplements(self):
        """Empty supplements should have no bonus."""
        result = calculateConditionAdjustment(
            condition_score=3,
            supplements=[],
            condition_sensitivity=Decimal("1.0")
        )

        assert result == Decimal("0.00")

    def test_unknown_supplement_ignored(self):
        """Unknown supplements should be ignored."""
        result = calculateConditionAdjustment(
            condition_score=3,
            supplements=["unknown_item", "original_box"],
            condition_sensitivity=Decimal("1.0")
        )

        # Should only count original_box (+0.05)
        assert result == Decimal("0.05")

    # --- Capping tests ---

    def test_positive_cap_at_030(self):
        """Result should cap at +0.30."""
        result = calculateConditionAdjustment(
            condition_score=5,
            supplements=["original_box", "tags", "dust_bag", "authenticity_card"],
            condition_sensitivity=Decimal("1.5")
        )

        # Base: (5-3)/10 * 1.5 = 0.30
        # Supplements: 0.05 + 0.03 + 0.03 + 0.04 = 0.15
        # Total: 0.30 + 0.15 = 0.45 → should cap at 0.30
        assert result == Decimal("0.30")

    def test_negative_cap_at_minus_030(self):
        """Result should cap at -0.30."""
        result = calculateConditionAdjustment(
            condition_score=0,
            supplements=[],
            condition_sensitivity=Decimal("1.5")
        )

        # Base: (0-3)/10 * 1.5 = -0.45 → should cap at -0.30
        assert result == Decimal("-0.30")

    # --- Edge case validation tests ---

    def test_raises_error_when_score_below_0(self):
        """Should raise ValueError when score < 0."""
        with pytest.raises(ValueError, match="Condition score must be between 0 and 5"):
            calculateConditionAdjustment(
                condition_score=-1,
                supplements=[],
                condition_sensitivity=Decimal("1.0")
            )

    def test_raises_error_when_score_above_5(self):
        """Should raise ValueError when score > 5."""
        with pytest.raises(ValueError, match="Condition score must be between 0 and 5"):
            calculateConditionAdjustment(
                condition_score=6,
                supplements=[],
                condition_sensitivity=Decimal("1.0")
            )

    def test_raises_error_when_sensitivity_below_min(self):
        """Should raise ValueError when sensitivity < 0.5."""
        with pytest.raises(ValueError, match="Condition sensitivity must be between 0.5 and 1.5"):
            calculateConditionAdjustment(
                condition_score=3,
                supplements=[],
                condition_sensitivity=Decimal("0.4")
            )

    def test_raises_error_when_sensitivity_above_max(self):
        """Should raise ValueError when sensitivity > 1.5."""
        with pytest.raises(ValueError, match="Condition sensitivity must be between 0.5 and 1.5"):
            calculateConditionAdjustment(
                condition_score=3,
                supplements=[],
                condition_sensitivity=Decimal("1.6")
            )

    def test_returns_decimal_type(self):
        """Should always return Decimal type for precision."""
        result = calculateConditionAdjustment(
            condition_score=4,
            supplements=["original_box"],
            condition_sensitivity=Decimal("1.2")
        )

        assert isinstance(result, Decimal)

    def test_result_has_two_decimal_places(self):
        """Result should be rounded to 2 decimal places."""
        result = calculateConditionAdjustment(
            condition_score=4,
            supplements=[],
            condition_sensitivity=Decimal("1.33")
        )

        # Base: (4-3)/10 * 1.33 = 0.133 → should round to 0.13
        assert result == Decimal("0.13")


# ===== TestCalculateOriginAdjustment =====


class TestCalculateOriginAdjustment:
    """Test origin-based price adjustment with 4-tier system."""

    # --- Tier 1 (expected) tests - should return 0.00 ---

    def test_expected_origin_single_match(self):
        """Expected origin (single) should return 0.00."""
        result = calculateOriginAdjustment(
            actual_origin="France",
            expected_origins=["France"]
        )

        assert result == Decimal("0.00")

    def test_expected_origin_multiple_match(self):
        """Expected origin (in list) should return 0.00."""
        result = calculateOriginAdjustment(
            actual_origin="Italy",
            expected_origins=["France", "Italy", "Spain"]
        )

        assert result == Decimal("0.00")

    # --- Tier 2 (neighbor) tests - should return 0.00 ---

    def test_neighbor_origin_france_belgium(self):
        """Belgium is neighbor of France, should return 0.00."""
        result = calculateOriginAdjustment(
            actual_origin="Belgium",
            expected_origins=["France"]
        )

        assert result == Decimal("0.00")

    def test_neighbor_origin_italy_switzerland(self):
        """Switzerland is neighbor of Italy, should return 0.00."""
        result = calculateOriginAdjustment(
            actual_origin="Switzerland",
            expected_origins=["Italy"]
        )

        assert result == Decimal("0.00")

    # --- Tier 3 (premium) tests - should return +0.15 ---

    def test_premium_origin_italy_not_expected(self):
        """Italy is premium but not expected, should return +0.15."""
        result = calculateOriginAdjustment(
            actual_origin="Italy",
            expected_origins=["China"]
        )

        assert result == Decimal("0.15")

    def test_premium_origin_france_not_expected(self):
        """France is premium but not expected, should return +0.15."""
        result = calculateOriginAdjustment(
            actual_origin="France",
            expected_origins=["Turkey"]
        )

        assert result == Decimal("0.15")

    def test_premium_origin_japan_not_expected(self):
        """Japan is premium but not expected, should return +0.15."""
        result = calculateOriginAdjustment(
            actual_origin="Japan",
            expected_origins=["China"]
        )

        assert result == Decimal("0.15")

    # --- Tier 4 (other) tests - should return -0.10 ---

    def test_other_origin_china(self):
        """China is not premium nor neighbor, should return -0.10."""
        result = calculateOriginAdjustment(
            actual_origin="China",
            expected_origins=["Italy"]
        )

        assert result == Decimal("-0.10")

    def test_other_origin_turkey(self):
        """Turkey is not premium nor neighbor, should return -0.10."""
        result = calculateOriginAdjustment(
            actual_origin="Turkey",
            expected_origins=["France"]
        )

        assert result == Decimal("-0.10")

    # --- Edge cases ---

    def test_empty_expected_origins(self):
        """Empty expected origins should use tier logic (no Tier 1 match)."""
        result = calculateOriginAdjustment(
            actual_origin="Italy",
            expected_origins=[]
        )

        # Italy is premium → Tier 3 → +0.15
        assert result == Decimal("0.15")

    def test_raises_error_when_actual_origin_is_none(self):
        """Should raise ValueError when actual_origin is None."""
        with pytest.raises(ValueError, match="Actual origin cannot be None or empty"):
            calculateOriginAdjustment(
                actual_origin=None,
                expected_origins=["France"]
            )

    def test_raises_error_when_actual_origin_is_empty(self):
        """Should raise ValueError when actual_origin is empty."""
        with pytest.raises(ValueError, match="Actual origin cannot be None or empty"):
            calculateOriginAdjustment(
                actual_origin="",
                expected_origins=["France"]
            )

    def test_unknown_country_fallback(self):
        """Unknown country should fallback to Tier 4 (-0.10)."""
        result = calculateOriginAdjustment(
            actual_origin="UnknownCountry",
            expected_origins=["France"]
        )

        assert result == Decimal("-0.10")

    def test_returns_decimal_type(self):
        """Should always return Decimal type for precision."""
        result = calculateOriginAdjustment(
            actual_origin="France",
            expected_origins=["Italy"]
        )

        assert isinstance(result, Decimal)


# ===== TestCalculateDecadeAdjustment =====


class TestCalculateDecadeAdjustment:
    """Test decade-based price adjustment with vintage bonuses."""

    # --- Expected decade tests - should return 0.00 ---

    def test_expected_decade_single_match(self):
        """Expected decade (single) should return 0.00."""
        result = calculateDecadeAdjustment(
            actual_decade="1990s",
            expected_decades=["1990s"],
            decade_coefficients=TEST_DECADE_COEFFICIENTS,
        )

        assert result == Decimal("0.00")

    def test_expected_decade_multiple_match(self):
        """Expected decade (in list) should return 0.00."""
        result = calculateDecadeAdjustment(
            actual_decade="2010s",
            expected_decades=["1990s", "2000s", "2010s"],
            decade_coefficients=TEST_DECADE_COEFFICIENTS,
        )

        assert result == Decimal("0.00")

    # --- Unexpected decade tests - should return vintage bonus ---

    def test_unexpected_decade_1950s_vintage_premium(self):
        """1950s not expected should return +0.20 (highest vintage)."""
        result = calculateDecadeAdjustment(
            actual_decade="1950s",
            expected_decades=["2000s"],
            decade_coefficients=TEST_DECADE_COEFFICIENTS,
        )

        assert result == Decimal("0.20")

    def test_unexpected_decade_1960s(self):
        """1960s not expected should return +0.18."""
        result = calculateDecadeAdjustment(
            actual_decade="1960s",
            expected_decades=["2000s"],
            decade_coefficients=TEST_DECADE_COEFFICIENTS,
        )

        assert result == Decimal("0.18")

    def test_unexpected_decade_1970s(self):
        """1970s not expected should return +0.15."""
        result = calculateDecadeAdjustment(
            actual_decade="1970s",
            expected_decades=["2000s"],
            decade_coefficients=TEST_DECADE_COEFFICIENTS,
        )

        assert result == Decimal("0.15")

    def test_unexpected_decade_1980s(self):
        """1980s not expected should return +0.12."""
        result = calculateDecadeAdjustment(
            actual_decade="1980s",
            expected_decades=["2000s"],
            decade_coefficients=TEST_DECADE_COEFFICIENTS,
        )

        assert result == Decimal("0.12")

    def test_unexpected_decade_1990s(self):
        """1990s not expected should return +0.08."""
        result = calculateDecadeAdjustment(
            actual_decade="1990s",
            expected_decades=["2000s"],
            decade_coefficients=TEST_DECADE_COEFFICIENTS,
        )

        assert result == Decimal("0.08")

    def test_unexpected_decade_2000s(self):
        """2000s not expected should return +0.05."""
        result = calculateDecadeAdjustment(
            actual_decade="2000s",
            expected_decades=["2010s"],
            decade_coefficients=TEST_DECADE_COEFFICIENTS,
        )

        assert result == Decimal("0.05")

    def test_unexpected_decade_2010s(self):
        """2010s not expected should return +0.02."""
        result = calculateDecadeAdjustment(
            actual_decade="2010s",
            expected_decades=["2020s"],
            decade_coefficients=TEST_DECADE_COEFFICIENTS,
        )

        assert result == Decimal("0.02")

    def test_unexpected_decade_2020s(self):
        """2020s not expected should return 0.00 (modern, no vintage value)."""
        result = calculateDecadeAdjustment(
            actual_decade="2020s",
            expected_decades=["1990s"],
            decade_coefficients=TEST_DECADE_COEFFICIENTS,
        )

        assert result == Decimal("0.00")

    # --- Edge cases ---

    def test_empty_expected_decades(self):
        """Empty expected decades should apply bonus (all unexpected)."""
        result = calculateDecadeAdjustment(
            actual_decade="1950s",
            expected_decades=[],
            decade_coefficients=TEST_DECADE_COEFFICIENTS,
        )

        # 1950s is unexpected → +0.20
        assert result == Decimal("0.20")

    def test_none_decade_returns_zero(self):
        """Should return 0.00 when actual_decade is None."""
        result = calculateDecadeAdjustment(
            actual_decade=None,
            expected_decades=["1990s"],
            decade_coefficients=TEST_DECADE_COEFFICIENTS,
        )

        assert result == Decimal("0.00")

    def test_empty_decade_returns_zero(self):
        """Should return 0.00 when actual_decade is empty."""
        result = calculateDecadeAdjustment(
            actual_decade="",
            expected_decades=["1990s"],
            decade_coefficients=TEST_DECADE_COEFFICIENTS,
        )

        assert result == Decimal("0.00")

    def test_unknown_decade_returns_zero(self):
        """Should return 0.00 when actual_decade format is unknown (not in coefficients)."""
        result = calculateDecadeAdjustment(
            actual_decade="1945s",
            expected_decades=["1990s"],
            decade_coefficients=TEST_DECADE_COEFFICIENTS,
        )

        assert result == Decimal("0.00")

    def test_returns_decimal_type(self):
        """Should always return Decimal type for precision."""
        result = calculateDecadeAdjustment(
            actual_decade="1990s",
            expected_decades=["2000s"],
            decade_coefficients=TEST_DECADE_COEFFICIENTS,
        )

        assert isinstance(result, Decimal)


# ===== TestCalculateTrendAdjustment =====


class TestCalculateTrendAdjustment:
    """Test trend-based price adjustment with best unexpected trend logic."""

    # --- All expected cases (no bonus) ---

    def test_single_expected_trend_returns_zero(self):
        """Should return 0.00 when single actual trend is in expected list."""
        result = calculateTrendAdjustment(
            actual_trends=["y2k"],
            expected_trends=["y2k"],
            trend_coefficients=TEST_TREND_COEFFICIENTS,
        )

        assert result == Decimal("0.00")

    def test_multiple_expected_trends_returns_zero(self):
        """Should return 0.00 when all actual trends are in expected list."""
        result = calculateTrendAdjustment(
            actual_trends=["y2k", "vintage"],
            expected_trends=["y2k", "vintage"],
            trend_coefficients=TEST_TREND_COEFFICIENTS,
        )

        assert result == Decimal("0.00")

    def test_empty_actual_trends_returns_zero(self):
        """Should return 0.00 when no actual trends provided."""
        result = calculateTrendAdjustment(
            actual_trends=[],
            expected_trends=["vintage"],
            trend_coefficients=TEST_TREND_COEFFICIENTS,
        )

        assert result == Decimal("0.00")

    # --- Single unexpected trend cases ---

    def test_unexpected_y2k_trend_highest_bonus(self):
        """Y2K trend (unexpected) should return +0.20 (highest bonus)."""
        result = calculateTrendAdjustment(
            actual_trends=["y2k"],
            expected_trends=["vintage"],
            trend_coefficients=TEST_TREND_COEFFICIENTS,
        )

        assert result == Decimal("0.20")

    def test_unexpected_vintage_trend(self):
        """Vintage trend (unexpected) should return +0.18."""
        result = calculateTrendAdjustment(
            actual_trends=["vintage"],
            expected_trends=["grunge"],
            trend_coefficients=TEST_TREND_COEFFICIENTS,
        )

        assert result == Decimal("0.18")

    def test_unexpected_grunge_trend(self):
        """Grunge trend (unexpected) should return +0.15."""
        result = calculateTrendAdjustment(
            actual_trends=["grunge"],
            expected_trends=["y2k"],
            trend_coefficients=TEST_TREND_COEFFICIENTS,
        )

        assert result == Decimal("0.15")

    def test_unexpected_streetwear_trend(self):
        """Streetwear trend (unexpected) should return +0.12."""
        result = calculateTrendAdjustment(
            actual_trends=["streetwear"],
            expected_trends=["minimalist"],
            trend_coefficients=TEST_TREND_COEFFICIENTS,
        )

        assert result == Decimal("0.12")

    # --- Multiple unexpected trends (MAX logic, not sum) ---

    def test_multiple_unexpected_returns_max_y2k_vintage(self):
        """Multiple unexpected trends should return MAX coefficient (y2k > vintage)."""
        result = calculateTrendAdjustment(
            actual_trends=["y2k", "vintage"],
            expected_trends=["grunge"],
            trend_coefficients=TEST_TREND_COEFFICIENTS,
        )

        # Max of y2k (0.20) and vintage (0.18) = 0.20
        assert result == Decimal("0.20")

    def test_multiple_unexpected_returns_max_streetwear_minimalist(self):
        """Multiple unexpected trends should return MAX coefficient (streetwear > minimalist)."""
        result = calculateTrendAdjustment(
            actual_trends=["streetwear", "minimalist"],
            expected_trends=["y2k"],
            trend_coefficients=TEST_TREND_COEFFICIENTS,
        )

        # Max of streetwear (0.12) and minimalist (0.08) = 0.12
        assert result == Decimal("0.12")

    def test_all_unexpected_returns_max(self):
        """All trends unexpected should return MAX coefficient."""
        result = calculateTrendAdjustment(
            actual_trends=["y2k", "vintage", "grunge"],
            expected_trends=[],
            trend_coefficients=TEST_TREND_COEFFICIENTS,
        )

        # Max of y2k (0.20), vintage (0.18), grunge (0.15) = 0.20
        assert result == Decimal("0.20")

    # --- Mixed expected/unexpected cases ---

    def test_mixed_expected_unexpected_returns_max_unexpected(self):
        """Mixed list should return MAX of unexpected trends only."""
        result = calculateTrendAdjustment(
            actual_trends=["y2k", "vintage"],
            expected_trends=["y2k"],
            trend_coefficients=TEST_TREND_COEFFICIENTS,
        )

        # y2k is expected (ignored), vintage is unexpected (0.18)
        assert result == Decimal("0.18")

    def test_mixed_grunge_streetwear_one_expected(self):
        """Mixed list with one expected should return MAX of unexpected."""
        result = calculateTrendAdjustment(
            actual_trends=["grunge", "streetwear"],
            expected_trends=["grunge"],
            trend_coefficients=TEST_TREND_COEFFICIENTS,
        )

        # grunge is expected (ignored), streetwear is unexpected (0.12)
        assert result == Decimal("0.12")

    # --- Edge cases ---

    def test_empty_actual_and_expected_returns_zero(self):
        """Both empty lists should return 0.00."""
        result = calculateTrendAdjustment(
            actual_trends=[],
            expected_trends=[],
            trend_coefficients=TEST_TREND_COEFFICIENTS,
        )

        assert result == Decimal("0.00")

    def test_unknown_trend_ignored(self):
        """Unknown trends in actual should be ignored, not crash."""
        result = calculateTrendAdjustment(
            actual_trends=["unknown_trend", "y2k"],
            expected_trends=["vintage"],
            trend_coefficients=TEST_TREND_COEFFICIENTS,
        )

        # Only y2k counts (unknown ignored), y2k is unexpected (0.20)
        assert result == Decimal("0.20")

    def test_all_unknown_trends_returns_zero(self):
        """All unknown trends should return 0.00."""
        result = calculateTrendAdjustment(
            actual_trends=["unknown1", "unknown2"],
            expected_trends=[],
            trend_coefficients=TEST_TREND_COEFFICIENTS,
        )

        assert result == Decimal("0.00")

    def test_returns_decimal_type(self):
        """Should always return Decimal type for precision."""
        result = calculateTrendAdjustment(
            actual_trends=["y2k"],
            expected_trends=["vintage"],
            trend_coefficients=TEST_TREND_COEFFICIENTS,
        )

        assert isinstance(result, Decimal)


# ===== TestCalculateFeatureAdjustment =====


class TestCalculateFeatureAdjustment:
    """Test feature-based price adjustment with sum and cap logic."""

    # --- All expected cases (no bonus) ---

    def test_single_expected_feature_returns_zero(self):
        """Should return 0.00 when single actual feature is in expected list."""
        result = calculateFeatureAdjustment(
            actual_features=["selvedge"],
            expected_features=["selvedge"],
            feature_coefficients=TEST_FEATURE_COEFFICIENTS,
        )

        assert result == Decimal("0.00")

    def test_multiple_expected_features_returns_zero(self):
        """Should return 0.00 when all actual features are in expected list."""
        result = calculateFeatureAdjustment(
            actual_features=["selvedge", "original_box"],
            expected_features=["selvedge", "original_box"],
            feature_coefficients=TEST_FEATURE_COEFFICIENTS,
        )

        assert result == Decimal("0.00")

    def test_empty_actual_features_returns_zero(self):
        """Should return 0.00 when no actual features provided."""
        result = calculateFeatureAdjustment(
            actual_features=[],
            expected_features=["selvedge"],
            feature_coefficients=TEST_FEATURE_COEFFICIENTS,
        )

        assert result == Decimal("0.00")

    # --- Single unexpected feature cases ---

    def test_unexpected_deadstock_feature_highest(self):
        """Deadstock feature (unexpected) should return +0.20."""
        result = calculateFeatureAdjustment(
            actual_features=["deadstock"],
            expected_features=["selvedge"],
            feature_coefficients=TEST_FEATURE_COEFFICIENTS,
        )

        assert result == Decimal("0.20")

    def test_unexpected_selvedge_feature(self):
        """Selvedge feature (unexpected) should return +0.15."""
        result = calculateFeatureAdjustment(
            actual_features=["selvedge"],
            expected_features=["original_box"],
            feature_coefficients=TEST_FEATURE_COEFFICIENTS,
        )

        assert result == Decimal("0.15")

    def test_unexpected_og_colorway_feature(self):
        """OG colorway feature (unexpected) should return +0.15."""
        result = calculateFeatureAdjustment(
            actual_features=["og_colorway"],
            expected_features=["deadstock"],
            feature_coefficients=TEST_FEATURE_COEFFICIENTS,
        )

        assert result == Decimal("0.15")

    def test_unexpected_original_box_feature(self):
        """Original box feature (unexpected) should return +0.10."""
        result = calculateFeatureAdjustment(
            actual_features=["original_box"],
            expected_features=["selvedge"],
            feature_coefficients=TEST_FEATURE_COEFFICIENTS,
        )

        assert result == Decimal("0.10")

    # --- Multiple unexpected features (sum logic) ---

    def test_multiple_unexpected_sums_selvedge_box(self):
        """Multiple unexpected features should sum their coefficients."""
        result = calculateFeatureAdjustment(
            actual_features=["selvedge", "original_box"],
            expected_features=["deadstock"],
            feature_coefficients=TEST_FEATURE_COEFFICIENTS,
        )

        # 0.15 (selvedge) + 0.10 (original_box) = 0.25
        assert result == Decimal("0.25")

    def test_multiple_unexpected_sums_chain_label(self):
        """Multiple unexpected features should sum their coefficients."""
        result = calculateFeatureAdjustment(
            actual_features=["chain_stitching", "vintage_label"],
            expected_features=[],
            feature_coefficients=TEST_FEATURE_COEFFICIENTS,
        )

        # 0.08 (chain_stitching) + 0.10 (vintage_label) = 0.18
        assert result == Decimal("0.18")

    # --- Capping cases (sum > 0.30) ---

    def test_capping_deadstock_selvedge(self):
        """Sum exceeding 0.30 should cap at +0.30."""
        result = calculateFeatureAdjustment(
            actual_features=["deadstock", "selvedge"],
            expected_features=[],
            feature_coefficients=TEST_FEATURE_COEFFICIENTS,
        )

        # 0.20 (deadstock) + 0.15 (selvedge) = 0.35 → capped at 0.30
        assert result == Decimal("0.30")

    def test_capping_deadstock_og_colorway(self):
        """Sum exceeding 0.30 should cap at +0.30."""
        result = calculateFeatureAdjustment(
            actual_features=["deadstock", "og_colorway"],
            expected_features=[],
            feature_coefficients=TEST_FEATURE_COEFFICIENTS,
        )

        # 0.20 (deadstock) + 0.15 (og_colorway) = 0.35 → capped at 0.30
        assert result == Decimal("0.30")

    def test_capping_three_features(self):
        """Three features exceeding 0.30 should cap at +0.30."""
        result = calculateFeatureAdjustment(
            actual_features=["selvedge", "limited_edition", "vintage_label"],
            expected_features=[],
            feature_coefficients=TEST_FEATURE_COEFFICIENTS,
        )

        # 0.15 (selvedge) + 0.12 (limited_edition) + 0.10 (vintage_label) = 0.37 → capped at 0.30
        assert result == Decimal("0.30")

    # --- Mixed expected/unexpected cases ---

    def test_mixed_expected_unexpected_sums_unexpected_only(self):
        """Mixed list should sum unexpected features only."""
        result = calculateFeatureAdjustment(
            actual_features=["selvedge", "original_box"],
            expected_features=["selvedge"],
            feature_coefficients=TEST_FEATURE_COEFFICIENTS,
        )

        # selvedge is expected (ignored), original_box is unexpected (0.10)
        assert result == Decimal("0.10")

    def test_mixed_deadstock_selvedge_one_expected(self):
        """Mixed list with one expected should sum unexpected only."""
        result = calculateFeatureAdjustment(
            actual_features=["deadstock", "selvedge"],
            expected_features=["deadstock"],
            feature_coefficients=TEST_FEATURE_COEFFICIENTS,
        )

        # deadstock is expected (ignored), selvedge is unexpected (0.15)
        assert result == Decimal("0.15")

    # --- Edge cases ---

    def test_empty_actual_and_expected_returns_zero(self):
        """Both empty lists should return 0.00."""
        result = calculateFeatureAdjustment(
            actual_features=[],
            expected_features=[],
            feature_coefficients=TEST_FEATURE_COEFFICIENTS,
        )

        assert result == Decimal("0.00")

    def test_unknown_feature_ignored(self):
        """Unknown features in actual should be ignored, not crash."""
        result = calculateFeatureAdjustment(
            actual_features=["unknown_feature", "deadstock"],
            expected_features=["selvedge"],
            feature_coefficients=TEST_FEATURE_COEFFICIENTS,
        )

        # Only deadstock counts (unknown ignored), deadstock is unexpected (0.20)
        assert result == Decimal("0.20")

    def test_all_unknown_features_returns_zero(self):
        """All unknown features should return 0.00."""
        result = calculateFeatureAdjustment(
            actual_features=["unknown1", "unknown2"],
            expected_features=[],
            feature_coefficients=TEST_FEATURE_COEFFICIENTS,
        )

        assert result == Decimal("0.00")

    def test_returns_decimal_type(self):
        """Should always return Decimal type for precision."""
        result = calculateFeatureAdjustment(
            actual_features=["deadstock"],
            expected_features=["selvedge"],
            feature_coefficients=TEST_FEATURE_COEFFICIENTS,
        )

        assert isinstance(result, Decimal)
