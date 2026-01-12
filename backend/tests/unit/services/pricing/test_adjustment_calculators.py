"""
Unit Tests for Adjustment Calculators

Tests for model coefficient and condition adjustment calculators.
Covers success paths, edge cases, validation, capping, and supplements.
"""

from decimal import Decimal
from unittest.mock import Mock

import pytest

from models.public.model import Model
from services.pricing.adjustment_calculators import (
    calculateConditionAdjustment,
    calculateDecadeAdjustment,
    calculateModelCoefficient,
    calculateOriginAdjustment,
)


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
            expected_decades=["1990s"]
        )

        assert result == Decimal("0.00")

    def test_expected_decade_multiple_match(self):
        """Expected decade (in list) should return 0.00."""
        result = calculateDecadeAdjustment(
            actual_decade="2010s",
            expected_decades=["1990s", "2000s", "2010s"]
        )

        assert result == Decimal("0.00")

    # --- Unexpected decade tests - should return vintage bonus ---

    def test_unexpected_decade_1950s_vintage_premium(self):
        """1950s not expected should return +0.20 (highest vintage)."""
        result = calculateDecadeAdjustment(
            actual_decade="1950s",
            expected_decades=["2000s"]
        )

        assert result == Decimal("0.20")

    def test_unexpected_decade_1960s(self):
        """1960s not expected should return +0.18."""
        result = calculateDecadeAdjustment(
            actual_decade="1960s",
            expected_decades=["2000s"]
        )

        assert result == Decimal("0.18")

    def test_unexpected_decade_1970s(self):
        """1970s not expected should return +0.15."""
        result = calculateDecadeAdjustment(
            actual_decade="1970s",
            expected_decades=["2000s"]
        )

        assert result == Decimal("0.15")

    def test_unexpected_decade_1980s(self):
        """1980s not expected should return +0.12."""
        result = calculateDecadeAdjustment(
            actual_decade="1980s",
            expected_decades=["2000s"]
        )

        assert result == Decimal("0.12")

    def test_unexpected_decade_1990s(self):
        """1990s not expected should return +0.08."""
        result = calculateDecadeAdjustment(
            actual_decade="1990s",
            expected_decades=["2000s"]
        )

        assert result == Decimal("0.08")

    def test_unexpected_decade_2000s(self):
        """2000s not expected should return +0.05."""
        result = calculateDecadeAdjustment(
            actual_decade="2000s",
            expected_decades=["2010s"]
        )

        assert result == Decimal("0.05")

    def test_unexpected_decade_2010s(self):
        """2010s not expected should return +0.02."""
        result = calculateDecadeAdjustment(
            actual_decade="2010s",
            expected_decades=["2020s"]
        )

        assert result == Decimal("0.02")

    def test_unexpected_decade_2020s(self):
        """2020s not expected should return 0.00 (modern, no vintage value)."""
        result = calculateDecadeAdjustment(
            actual_decade="2020s",
            expected_decades=["1990s"]
        )

        assert result == Decimal("0.00")

    # --- Edge cases ---

    def test_empty_expected_decades(self):
        """Empty expected decades should apply bonus (all unexpected)."""
        result = calculateDecadeAdjustment(
            actual_decade="1950s",
            expected_decades=[]
        )

        # 1950s is unexpected → +0.20
        assert result == Decimal("0.20")

    def test_raises_error_when_actual_decade_is_none(self):
        """Should raise ValueError when actual_decade is None."""
        with pytest.raises(ValueError, match="Actual decade cannot be None or empty"):
            calculateDecadeAdjustment(
                actual_decade=None,
                expected_decades=["1990s"]
            )

    def test_raises_error_when_actual_decade_is_empty(self):
        """Should raise ValueError when actual_decade is empty."""
        with pytest.raises(ValueError, match="Actual decade cannot be None or empty"):
            calculateDecadeAdjustment(
                actual_decade="",
                expected_decades=["1990s"]
            )

    def test_raises_error_when_actual_decade_unknown(self):
        """Should raise ValueError when actual_decade format is unknown."""
        with pytest.raises(ValueError, match="Unknown decade: 1945s"):
            calculateDecadeAdjustment(
                actual_decade="1945s",
                expected_decades=["1990s"]
            )

    def test_returns_decimal_type(self):
        """Should always return Decimal type for precision."""
        result = calculateDecadeAdjustment(
            actual_decade="1990s",
            expected_decades=["2000s"]
        )

        assert isinstance(result, Decimal)
