"""
Unit tests for PricingService

Tests the core pricing service orchestrating all calculators and generation.

Test Coverage:
- Data fetching/generation logic (BrandGroup, Model)
- Price calculation with all 6 calculators
- 3 price levels (quick, standard, premium)
- Integration scenarios (end-to-end)
- Edge cases and error handling

Created: 2026-01-12
Author: Claude
"""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

from models.public.brand_group import BrandGroup
from models.public.model import Model
from repositories.brand_group_repository import BrandGroupRepository
from repositories.model_repository import ModelRepository
from schemas.pricing import PriceInput, PriceOutput
from services.pricing_service import PricingService
from services.pricing.pricing_generation_service import PricingGenerationService
from shared.exceptions import ServiceError


# ===== FIXTURES =====


@pytest.fixture
def mock_db():
    """Mock database session."""
    return MagicMock()


@pytest.fixture
def mock_brand_group_repo():
    """Mock BrandGroupRepository."""
    return MagicMock(spec=BrandGroupRepository)


@pytest.fixture
def mock_model_repo():
    """Mock ModelRepository."""
    return MagicMock(spec=ModelRepository)


@pytest.fixture
def mock_generation_service():
    """Mock PricingGenerationService."""
    return MagicMock(spec=PricingGenerationService)


@pytest.fixture
def pricing_service(
    mock_db, mock_brand_group_repo, mock_model_repo, mock_generation_service
):
    """PricingService instance with mocked dependencies."""
    return PricingService(
        db=mock_db,
        brand_group_repo=mock_brand_group_repo,
        model_repo=mock_model_repo,
        generation_service=mock_generation_service,
    )


@pytest.fixture
def sample_brand_group():
    """Sample BrandGroup for testing."""
    return BrandGroup(
        id=1,
        brand="Nike",
        group="sneakers",
        base_price=Decimal("100.00"),
        condition_sensitivity=Decimal("1.0"),
        expected_origins=["China", "Vietnam"],
        expected_decades=["2010s", "2020s"],
        expected_trends=["streetwear", "athleisure"],
        generated_by_ai=False,
    )


@pytest.fixture
def sample_model():
    """Sample Model for testing."""
    return Model(
        id=1,
        brand="Nike",
        group="sneakers",
        name="Air Max 90",
        coefficient=Decimal("1.5"),
        expected_features=["og_colorway"],
        generated_by_ai=False,
    )


@pytest.fixture
def sample_input():
    """Sample PriceInput for testing."""
    return PriceInput(
        brand="Nike",
        category="sneakers",
        materials=["leather"],
        model_name="Air Max 90",
        condition_score=4,
        supplements=["original_box"],
        condition_sensitivity=Decimal("1.0"),
        actual_origin="Italy",
        expected_origins=[],
        actual_decade="1990s",
        expected_decades=[],
        actual_trends=["vintage"],
        expected_trends=[],
        actual_features=["og_colorway"],
        expected_features=[],
    )


# ===== TEST CLASS: DATA FETCHING/GENERATION =====


class TestPricingServiceDataFetching:
    """Tests for data fetching and generation logic."""

    @pytest.mark.asyncio
    async def test_fetch_existing_brand_group_no_generation(
        self, pricing_service, mock_brand_group_repo, sample_brand_group
    ):
        """BrandGroup exists in DB, no generation needed."""
        # Arrange
        mock_brand_group_repo.get_by_brand_and_group.return_value = sample_brand_group

        # Act
        result = await pricing_service.fetch_or_generate_pricing_data(
            brand="Nike", category="sneakers", materials=["leather"]
        )

        # Assert
        assert result["base_price"] == Decimal("100.00")
        assert result["brand_group"] == sample_brand_group
        mock_brand_group_repo.get_by_brand_and_group.assert_called_once()
        pricing_service.generation_service.generate_brand_group.assert_not_called()

    @pytest.mark.asyncio
    async def test_generate_brand_group_when_missing(
        self,
        pricing_service,
        mock_brand_group_repo,
        mock_db,
        sample_brand_group,
    ):
        """BrandGroup missing, generate and save to DB."""
        # Arrange
        mock_brand_group_repo.get_by_brand_and_group.return_value = None
        mock_brand_group_repo.create.return_value = sample_brand_group
        pricing_service.generation_service.generate_brand_group = AsyncMock(
            return_value=sample_brand_group
        )

        # Act
        result = await pricing_service.fetch_or_generate_pricing_data(
            brand="Nike", category="sneakers", materials=["leather"]
        )

        # Assert
        assert result["base_price"] == Decimal("100.00")
        pricing_service.generation_service.generate_brand_group.assert_called_once_with(
            "Nike", "sneakers"
        )
        mock_brand_group_repo.create.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_existing_model_no_generation(
        self,
        pricing_service,
        mock_brand_group_repo,
        mock_model_repo,
        sample_brand_group,
        sample_model,
    ):
        """Model exists in DB, no generation needed."""
        # Arrange
        mock_brand_group_repo.get_by_brand_and_group.return_value = sample_brand_group
        mock_model_repo.get_by_brand_group_and_name.return_value = sample_model

        # Act
        result = await pricing_service.fetch_or_generate_pricing_data(
            brand="Nike",
            category="sneakers",
            materials=["leather"],
            model_name="Air Max 90",
        )

        # Assert
        assert result["model_coeff"] == Decimal("1.5")
        assert result["model"] == sample_model
        mock_model_repo.get_by_brand_group_and_name.assert_called_once()
        pricing_service.generation_service.generate_model.assert_not_called()

    @pytest.mark.asyncio
    async def test_generate_model_when_missing(
        self,
        pricing_service,
        mock_brand_group_repo,
        mock_model_repo,
        mock_db,
        sample_brand_group,
        sample_model,
    ):
        """Model missing, generate and save to DB."""
        # Arrange
        mock_brand_group_repo.get_by_brand_and_group.return_value = sample_brand_group
        mock_model_repo.get_by_brand_group_and_name.return_value = None
        mock_model_repo.create.return_value = sample_model
        pricing_service.generation_service.generate_model = AsyncMock(
            return_value=sample_model
        )

        # Act
        result = await pricing_service.fetch_or_generate_pricing_data(
            brand="Nike",
            category="sneakers",
            materials=["leather"],
            model_name="Air Max 90",
        )

        # Assert
        assert result["model_coeff"] == Decimal("1.5")
        pricing_service.generation_service.generate_model.assert_called_once_with(
            "Nike", "sneakers", "Air Max 90", Decimal("100.00")
        )
        mock_model_repo.create.assert_called_once()
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_no_model_name_defaults_to_coefficient_one(
        self, pricing_service, mock_brand_group_repo, sample_brand_group
    ):
        """No model_name provided, coefficient defaults to 1.0."""
        # Arrange
        mock_brand_group_repo.get_by_brand_and_group.return_value = sample_brand_group

        # Act
        result = await pricing_service.fetch_or_generate_pricing_data(
            brand="Nike", category="sneakers", materials=["leather"], model_name=None
        )

        # Assert
        assert result["model_coeff"] == Decimal("1.0")
        assert result["model"] is None

    @pytest.mark.asyncio
    async def test_group_determination_failure_raises_value_error(
        self, pricing_service
    ):
        """Group determination fails, raise ValueError."""
        # Act & Assert
        with pytest.raises(ValueError, match="Cannot determine pricing group"):
            await pricing_service.fetch_or_generate_pricing_data(
                brand="Nike", category="", materials=[]
            )

    @pytest.mark.asyncio
    async def test_brand_group_generation_failure_raises_service_error(
        self, pricing_service, mock_brand_group_repo
    ):
        """LLM generation fails, raise ServiceError."""
        # Arrange
        mock_brand_group_repo.get_by_brand_and_group.return_value = None
        pricing_service.generation_service.generate_brand_group = AsyncMock(
            side_effect=Exception("LLM API error")
        )

        # Act & Assert
        with pytest.raises(ServiceError, match="Failed to generate BrandGroup"):
            await pricing_service.fetch_or_generate_pricing_data(
                brand="Nike", category="sneakers", materials=["leather"]
            )

    @pytest.mark.asyncio
    async def test_model_generation_failure_raises_service_error(
        self,
        pricing_service,
        mock_brand_group_repo,
        mock_model_repo,
        sample_brand_group,
    ):
        """Model generation fails, raise ServiceError."""
        # Arrange
        mock_brand_group_repo.get_by_brand_and_group.return_value = sample_brand_group
        mock_model_repo.get_by_brand_group_and_name.return_value = None
        pricing_service.generation_service.generate_model = AsyncMock(
            side_effect=Exception("LLM API error")
        )

        # Act & Assert
        with pytest.raises(ServiceError, match="Failed to generate Model"):
            await pricing_service.fetch_or_generate_pricing_data(
                brand="Nike",
                category="sneakers",
                materials=["leather"],
                model_name="Air Max 90",
            )


# ===== TEST CLASS: PRICE CALCULATION =====


class TestPricingServiceCalculation:
    """Tests for price calculation logic with all 6 calculators."""

    @pytest.mark.asyncio
    async def test_basic_calculation_no_adjustments(
        self,
        pricing_service,
        mock_brand_group_repo,
        mock_model_repo,
        sample_brand_group,
        sample_model,
    ):
        """Basic calculation: base_price=100, model_coeff=1.5, no adjustments."""
        # Arrange
        mock_brand_group_repo.get_by_brand_and_group.return_value = sample_brand_group
        mock_model_repo.get_by_brand_group_and_name.return_value = sample_model

        input_data = PriceInput(
            brand="Nike",
            category="sneakers",
            materials=["leather"],
            model_name="Air Max 90",
            condition_score=3,  # Baseline condition
            supplements=[],
            condition_sensitivity=Decimal("1.0"),
            actual_origin="China",  # Expected origin
            expected_origins=[],
            actual_decade="2010s",  # Expected decade
            expected_decades=[],
            actual_trends=[],
            expected_trends=[],
            actual_features=[],
            expected_features=[],
        )

        # Act
        result = await pricing_service.calculate_price(input_data)

        # Assert
        # Formula: 100 × 1.5 × (1 + 0) = 150
        assert result.standard_price == Decimal("150.00")
        assert result.quick_price == Decimal("112.50")  # 150 × 0.75
        assert result.premium_price == Decimal("195.00")  # 150 × 1.30
        assert result.model_coefficient == Decimal("1.5")
        assert result.adjustments.total == Decimal("0.00")

    @pytest.mark.asyncio
    async def test_calculation_with_positive_adjustments(
        self,
        pricing_service,
        mock_brand_group_repo,
        mock_model_repo,
        sample_brand_group,
        sample_model,
    ):
        """Calculation with all positive adjustments."""
        # Arrange
        mock_brand_group_repo.get_by_brand_and_group.return_value = sample_brand_group
        mock_model_repo.get_by_brand_group_and_name.return_value = sample_model

        input_data = PriceInput(
            brand="Nike",
            category="sneakers",
            materials=["leather"],
            model_name="Air Max 90",
            condition_score=5,  # Excellent condition
            supplements=["original_box"],
            condition_sensitivity=Decimal("1.0"),
            actual_origin="Italy",  # Premium origin
            expected_origins=["China"],
            actual_decade="1990s",  # Vintage
            expected_decades=["2020s"],
            actual_trends=["vintage"],
            expected_trends=[],
            actual_features=["og_colorway"],
            expected_features=[],
        )

        # Act
        result = await pricing_service.calculate_price(input_data)

        # Assert
        # Condition: (5-3)/10 * 1.0 + 0.05 = 0.25
        # Origin: +0.15 (premium)
        # Decade: +0.08 (1990s)
        # Trend: +0.18 (vintage)
        # Feature: +0.00 (og_colorway is expected by Model, so no bonus)
        # Total: 0.66
        # Price: 100 × 1.5 × (1 + 0.66) = 249.00
        assert result.adjustments.condition == Decimal("0.25")
        assert result.adjustments.origin == Decimal("0.15")
        assert result.adjustments.decade == Decimal("0.08")
        assert result.adjustments.trend == Decimal("0.18")
        assert result.adjustments.feature == Decimal("0.00")
        assert result.standard_price == Decimal("249.00")
        assert result.quick_price < result.standard_price < result.premium_price

    @pytest.mark.asyncio
    async def test_calculation_with_negative_adjustments(
        self,
        pricing_service,
        mock_brand_group_repo,
        mock_model_repo,
        sample_brand_group,
        sample_model,
    ):
        """Calculation with negative adjustments (poor condition, unexpected origin)."""
        # Arrange
        mock_brand_group_repo.get_by_brand_and_group.return_value = sample_brand_group
        mock_model_repo.get_by_brand_group_and_name.return_value = sample_model

        input_data = PriceInput(
            brand="Nike",
            category="sneakers",
            materials=["leather"],
            model_name="Air Max 90",
            condition_score=1,  # Poor condition
            supplements=[],
            condition_sensitivity=Decimal("1.0"),
            actual_origin="Unknown",  # Non-premium, not expected
            expected_origins=["China"],
            actual_decade="2020s",
            expected_decades=["2020s"],
            actual_trends=[],
            expected_trends=[],
            actual_features=[],
            expected_features=[],
        )

        # Act
        result = await pricing_service.calculate_price(input_data)

        # Assert
        # Condition: (1-3)/10 * 1.0 = -0.20
        # Origin: -0.10 (other)
        # Total: -0.30
        # Price: 100 × 1.5 × (1 - 0.30) = 105.00
        assert result.adjustments.condition == Decimal("-0.20")
        assert result.adjustments.origin == Decimal("-0.10")
        assert result.standard_price == Decimal("105.00")

    @pytest.mark.asyncio
    async def test_price_levels_ratios(
        self,
        pricing_service,
        mock_brand_group_repo,
        mock_model_repo,
        sample_brand_group,
        sample_model,
    ):
        """Verify price level ratios (quick=×0.75, premium=×1.30)."""
        # Arrange
        mock_brand_group_repo.get_by_brand_and_group.return_value = sample_brand_group
        mock_model_repo.get_by_brand_group_and_name.return_value = sample_model

        input_data = PriceInput(
            brand="Nike",
            category="sneakers",
            materials=["leather"],
            model_name="Air Max 90",
            condition_score=3,
            supplements=[],
            condition_sensitivity=Decimal("1.0"),
            actual_origin="China",
            expected_origins=[],
            actual_decade="2010s",
            expected_decades=[],
            actual_trends=[],
            expected_trends=[],
            actual_features=[],
            expected_features=[],
        )

        # Act
        result = await pricing_service.calculate_price(input_data)

        # Assert
        assert result.quick_price == result.standard_price * Decimal("0.75")
        assert result.premium_price == result.standard_price * Decimal("1.30")
        assert result.quick_price < result.standard_price < result.premium_price

    @pytest.mark.asyncio
    async def test_breakdown_includes_all_adjustment_values(
        self,
        pricing_service,
        mock_brand_group_repo,
        mock_model_repo,
        sample_brand_group,
        sample_model,
    ):
        """Breakdown includes all 6 adjustment values."""
        # Arrange
        mock_brand_group_repo.get_by_brand_and_group.return_value = sample_brand_group
        mock_model_repo.get_by_brand_group_and_name.return_value = sample_model

        input_data = PriceInput(
            brand="Nike",
            category="sneakers",
            materials=["leather"],
            model_name="Air Max 90",
            condition_score=4,
            supplements=["original_box"],
            condition_sensitivity=Decimal("1.0"),
            actual_origin="Italy",
            expected_origins=["China"],
            actual_decade="1990s",
            expected_decades=["2020s"],
            actual_trends=["vintage"],
            expected_trends=[],
            actual_features=["og_colorway"],
            expected_features=[],
        )

        # Act
        result = await pricing_service.calculate_price(input_data)

        # Assert
        assert hasattr(result.adjustments, "condition")
        assert hasattr(result.adjustments, "origin")
        assert hasattr(result.adjustments, "decade")
        assert hasattr(result.adjustments, "trend")
        assert hasattr(result.adjustments, "feature")
        assert hasattr(result.adjustments, "total")
        assert result.adjustments.total == (
            result.adjustments.condition
            + result.adjustments.origin
            + result.adjustments.decade
            + result.adjustments.trend
            + result.adjustments.feature
        )

    @pytest.mark.asyncio
    async def test_decimal_precision_two_decimal_places(
        self,
        pricing_service,
        mock_brand_group_repo,
        mock_model_repo,
        sample_brand_group,
        sample_model,
    ):
        """All prices have 2 decimal places (currency precision)."""
        # Arrange
        mock_brand_group_repo.get_by_brand_and_group.return_value = sample_brand_group
        mock_model_repo.get_by_brand_group_and_name.return_value = sample_model

        input_data = PriceInput(
            brand="Nike",
            category="sneakers",
            materials=["leather"],
            model_name="Air Max 90",
            condition_score=4,
            supplements=["original_box"],
            condition_sensitivity=Decimal("1.0"),
            actual_origin="Italy",
            expected_origins=[],
            actual_decade="1990s",
            expected_decades=[],
            actual_trends=["vintage"],
            expected_trends=[],
            actual_features=["og_colorway"],
            expected_features=[],
        )

        # Act
        result = await pricing_service.calculate_price(input_data)

        # Assert
        assert result.quick_price == result.quick_price.quantize(Decimal("0.01"))
        assert result.standard_price == result.standard_price.quantize(Decimal("0.01"))
        assert result.premium_price == result.premium_price.quantize(Decimal("0.01"))

    @pytest.mark.asyncio
    async def test_edge_case_all_adjustments_zero(
        self,
        pricing_service,
        mock_brand_group_repo,
        mock_model_repo,
        sample_brand_group,
        sample_model,
    ):
        """Edge case: all adjustments = 0, standard_price = base_price × model_coeff."""
        # Arrange
        mock_brand_group_repo.get_by_brand_and_group.return_value = sample_brand_group
        mock_model_repo.get_by_brand_group_and_name.return_value = sample_model

        input_data = PriceInput(
            brand="Nike",
            category="sneakers",
            materials=["leather"],
            model_name="Air Max 90",
            condition_score=3,  # Baseline
            supplements=[],
            condition_sensitivity=Decimal("1.0"),
            actual_origin="China",  # Expected
            expected_origins=["China"],
            actual_decade="2010s",  # Expected
            expected_decades=["2010s"],
            actual_trends=[],
            expected_trends=[],
            actual_features=[],
            expected_features=[],
        )

        # Act
        result = await pricing_service.calculate_price(input_data)

        # Assert
        assert result.adjustments.total == Decimal("0.00")
        assert result.standard_price == Decimal("150.00")  # 100 × 1.5

    @pytest.mark.asyncio
    async def test_edge_case_very_high_adjustments(
        self,
        pricing_service,
        mock_brand_group_repo,
        mock_model_repo,
        sample_brand_group,
        sample_model,
    ):
        """Edge case: very high adjustments, formula still applies."""
        # Arrange
        mock_brand_group_repo.get_by_brand_and_group.return_value = sample_brand_group
        mock_model_repo.get_by_brand_group_and_name.return_value = sample_model

        input_data = PriceInput(
            brand="Nike",
            category="sneakers",
            materials=["leather"],
            model_name="Air Max 90",
            condition_score=5,
            supplements=["original_box", "tags", "dust_bag", "authenticity_card"],
            condition_sensitivity=Decimal("1.5"),
            actual_origin="Italy",
            expected_origins=["China"],
            actual_decade="1950s",
            expected_decades=["2020s"],
            actual_trends=["y2k"],
            expected_trends=[],
            actual_features=["deadstock", "selvedge"],
            expected_features=[],
        )

        # Act
        result = await pricing_service.calculate_price(input_data)

        # Assert
        # Condition: capped at +0.30
        # Origin: +0.15
        # Decade: +0.20
        # Trend: +0.20
        # Feature: +0.30 (capped)
        # Total: 1.15
        # Price: 100 × 1.5 × (1 + 1.15) = 322.50
        assert result.adjustments.total == Decimal("1.15")
        assert result.standard_price == Decimal("322.50")

    @pytest.mark.asyncio
    async def test_output_schema_validation(
        self,
        pricing_service,
        mock_brand_group_repo,
        mock_model_repo,
        sample_brand_group,
        sample_model,
    ):
        """Output conforms to PriceOutput schema."""
        # Arrange
        mock_brand_group_repo.get_by_brand_and_group.return_value = sample_brand_group
        mock_model_repo.get_by_brand_group_and_name.return_value = sample_model

        input_data = PriceInput(
            brand="Nike",
            category="sneakers",
            materials=["leather"],
            model_name="Air Max 90",
            condition_score=4,
            supplements=[],
            condition_sensitivity=Decimal("1.0"),
            actual_origin="Italy",
            expected_origins=[],
            actual_decade="1990s",
            expected_decades=[],
            actual_trends=[],
            expected_trends=[],
            actual_features=[],
            expected_features=[],
        )

        # Act
        result = await pricing_service.calculate_price(input_data)

        # Assert
        assert isinstance(result, PriceOutput)
        assert result.brand == "Nike"
        assert result.group == "sneakers"
        assert result.model_name == "Air Max 90"


# ===== TEST CLASS: INTEGRATION =====


class TestPricingServiceIntegration:
    """Integration tests for end-to-end scenarios."""

    @pytest.mark.asyncio
    async def test_end_to_end_with_valid_input(
        self,
        pricing_service,
        mock_brand_group_repo,
        mock_model_repo,
        sample_brand_group,
        sample_model,
        sample_input,
    ):
        """End-to-end: valid input → valid output with all fields."""
        # Arrange
        mock_brand_group_repo.get_by_brand_and_group.return_value = sample_brand_group
        mock_model_repo.get_by_brand_group_and_name.return_value = sample_model

        # Act
        result = await pricing_service.calculate_price(sample_input)

        # Assert
        assert result.quick_price > Decimal("0")
        assert result.standard_price > Decimal("0")
        assert result.premium_price > Decimal("0")
        assert result.quick_price < result.standard_price < result.premium_price
        assert result.base_price == Decimal("100.00")
        assert result.model_coefficient == Decimal("1.5")
        assert result.brand == "Nike"
        assert result.group == "sneakers"

    @pytest.mark.asyncio
    async def test_different_product_types(
        self, pricing_service, mock_brand_group_repo, mock_model_repo
    ):
        """Different product types (sneakers, jacket, jeans) → correct calculations."""
        # Arrange - Jeans
        jeans_brand_group = BrandGroup(
            id=2,
            brand="Levi's",
            group="jeans",
            base_price=Decimal("50.00"),
            condition_sensitivity=Decimal("1.0"),
            expected_origins=["USA", "Mexico"],
            expected_decades=["1990s", "2000s"],
            expected_trends=["vintage", "workwear"],
        )

        mock_brand_group_repo.get_by_brand_and_group.return_value = jeans_brand_group
        mock_model_repo.get_by_brand_group_and_name.return_value = None

        input_data = PriceInput(
            brand="Levi's",
            category="jeans",
            materials=["cotton"],
            model_name=None,
            condition_score=3,
            supplements=[],
            condition_sensitivity=Decimal("1.0"),
            actual_origin="USA",
            expected_origins=[],
            actual_decade="2000s",
            expected_decades=[],
            actual_trends=[],
            expected_trends=[],
            actual_features=[],
            expected_features=[],
        )

        # Act
        result = await pricing_service.calculate_price(input_data)

        # Assert
        assert result.group == "jeans"
        assert result.base_price == Decimal("50.00")
        assert result.model_coefficient == Decimal("1.0")  # No model
        assert result.standard_price == Decimal("50.00")  # 50 × 1.0 × (1 + 0)

    @pytest.mark.asyncio
    async def test_with_model_vs_without_model(
        self,
        pricing_service,
        mock_brand_group_repo,
        mock_model_repo,
        sample_brand_group,
        sample_model,
    ):
        """With model → coefficient applied, without model → coefficient = 1.0."""
        # Arrange
        mock_brand_group_repo.get_by_brand_and_group.return_value = sample_brand_group

        # Test with model
        mock_model_repo.get_by_brand_group_and_name.return_value = sample_model

        input_with_model = PriceInput(
            brand="Nike",
            category="sneakers",
            materials=["leather"],
            model_name="Air Max 90",
            condition_score=3,
            supplements=[],
            condition_sensitivity=Decimal("1.0"),
            actual_origin="China",
            expected_origins=[],
            actual_decade="2010s",
            expected_decades=[],
            actual_trends=[],
            expected_trends=[],
            actual_features=[],
            expected_features=[],
        )

        result_with_model = await pricing_service.calculate_price(input_with_model)

        # Test without model
        input_without_model = input_with_model.model_copy(update={"model_name": None})
        result_without_model = await pricing_service.calculate_price(input_without_model)

        # Assert
        assert result_with_model.model_coefficient == Decimal("1.5")
        assert result_without_model.model_coefficient == Decimal("1.0")
        assert result_with_model.standard_price == Decimal("150.00")
        assert result_without_model.standard_price == Decimal("100.00")
