"""
Simplified unit tests for AI credits system.

Tests credit logic without complex fixtures or database dependencies.
Focuses on the core business logic: credit checking, consumption, and quota management.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from decimal import Decimal

from models.public.ai_credit import AICredit
from services.ai.vision_service import AIVisionService
from shared.exceptions import AIQuotaExceededError


class TestAICreditsCalculation:
    """Test credit calculation logic."""

    def test_get_remaining_credits_with_sufficient_credits(self):
        """Test remaining credits calculation when user has enough."""
        # Arrange
        ai_credit = AICredit(
            user_id=1,
            ai_credits_purchased=10,
            ai_credits_used_this_month=5
        )
        monthly_credits = 20

        # Act
        remaining = ai_credit.get_remaining_credits(monthly_credits)

        # Assert
        # Total = 20 (monthly) + 10 (purchased) = 30
        # Remaining = 30 - 5 (used) = 25
        assert remaining == 25

    def test_get_remaining_credits_with_no_purchased_credits(self):
        """Test remaining credits when user only has monthly credits."""
        # Arrange
        ai_credit = AICredit(
            user_id=1,
            ai_credits_purchased=0,
            ai_credits_used_this_month=5
        )
        monthly_credits = 10

        # Act
        remaining = ai_credit.get_remaining_credits(monthly_credits)

        # Assert
        # Total = 10 (monthly) + 0 (purchased) = 10
        # Remaining = 10 - 5 (used) = 5
        assert remaining == 5

    def test_get_remaining_credits_all_exhausted(self):
        """Test remaining credits when all credits are used."""
        # Arrange
        ai_credit = AICredit(
            user_id=1,
            ai_credits_purchased=5,
            ai_credits_used_this_month=25
        )
        monthly_credits = 20

        # Act
        remaining = ai_credit.get_remaining_credits(monthly_credits)

        # Assert
        # Total = 20 (monthly) + 5 (purchased) = 25
        # Remaining = 25 - 25 (used) = 0
        assert remaining == 0

    def test_get_remaining_credits_cannot_go_negative(self):
        """Test that remaining credits never go below zero."""
        # Arrange
        ai_credit = AICredit(
            user_id=1,
            ai_credits_purchased=0,
            ai_credits_used_this_month=30
        )
        monthly_credits = 10

        # Act
        remaining = ai_credit.get_remaining_credits(monthly_credits)

        # Assert
        # Total = 10 (monthly) + 0 (purchased) = 10
        # Used = 30 (more than available)
        # Remaining = max(0, 10 - 30) = 0
        assert remaining == 0


class TestAICreditsCheckLogic:
    """Test credit checking logic with mocked database."""

    def test_check_credits_passes_when_sufficient(self):
        """Test that check_credits doesn't raise when credits are sufficient."""
        # Arrange: Mock database session
        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query

        # User with sufficient credits
        mock_ai_credit = AICredit(
            user_id=1,
            ai_credits_purchased=10,
            ai_credits_used_this_month=5
        )
        mock_query.first.return_value = mock_ai_credit

        # Act & Assert: Should not raise
        AIVisionService._check_credits(mock_db, user_id=1, monthly_credits=20)
        # Remaining = 20 + 10 - 5 = 25 > 0 ✓

    def test_check_credits_raises_when_insufficient(self):
        """Test that check_credits raises AIQuotaExceededError when no credits left."""
        # Arrange: Mock database session
        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query

        # User with no credits left
        mock_ai_credit = AICredit(
            user_id=1,
            ai_credits_purchased=0,
            ai_credits_used_this_month=10
        )
        mock_query.first.return_value = mock_ai_credit

        # Act & Assert
        with pytest.raises(AIQuotaExceededError) as exc_info:
            AIVisionService._check_credits(mock_db, user_id=1, monthly_credits=10)

        assert "Crédits IA insuffisants" in str(exc_info.value)

    # NOTE: The test for record creation when missing is complex to mock properly
    # because it requires initializing SQLAlchemy defaults. This is tested in
    # integration tests instead where we have a real database.


class TestAICreditsConsumption:
    """Test credit consumption logic."""

    def test_consume_credit_increments_usage(self):
        """Test that consuming a credit increments used_this_month."""
        # Arrange: Mock database session
        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query

        # Existing AI credit with some usage
        mock_ai_credit = AICredit(
            user_id=1,
            ai_credits_purchased=10,
            ai_credits_used_this_month=5
        )
        mock_query.first.return_value = mock_ai_credit

        # Act
        AIVisionService._consume_credit(mock_db, user_id=1)

        # Assert
        assert mock_ai_credit.ai_credits_used_this_month == 6

    def test_consume_credit_handles_missing_record_gracefully(self):
        """Test that consume_credit doesn't crash if AICredit doesn't exist."""
        # Arrange: Mock database session
        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query

        # No existing AI credit record
        mock_query.first.return_value = None

        # Act & Assert: Should not raise
        AIVisionService._consume_credit(mock_db, user_id=1)
        # Function should handle gracefully


class TestAIPricingCalculation:
    """Test AI cost calculation."""

    def test_gemini_3_flash_pricing(self):
        """Test that Gemini 3 Flash pricing is correctly configured."""
        # Act
        pricing = AIVisionService.MODEL_PRICING.get("gemini-3-flash")

        # Assert
        assert pricing is not None
        assert "input" in pricing
        assert "output" in pricing
        assert pricing["input"] == 0.075  # $0.075 per million input tokens
        assert pricing["output"] == 0.30   # $0.30 per million output tokens

    def test_cost_calculation_example(self):
        """Test example cost calculation."""
        # Arrange
        model = "gemini-3-flash"
        prompt_tokens = 1000
        completion_tokens = 500
        total_tokens = 1500

        pricing = AIVisionService.MODEL_PRICING[model]

        # Act: Calculate cost (USD)
        input_cost = (prompt_tokens / 1_000_000) * pricing["input"]
        output_cost = (completion_tokens / 1_000_000) * pricing["output"]
        total_cost = input_cost + output_cost

        # Assert
        assert input_cost == pytest.approx(0.000075, rel=1e-6)  # $0.000075
        assert output_cost == pytest.approx(0.00015, rel=1e-6)   # $0.00015
        assert total_cost == pytest.approx(0.000225, rel=1e-6)   # $0.000225


class TestPromptGeneration:
    """Test AI prompt generation."""

    def test_build_prompt_is_in_english(self):
        """Test that the generated prompt is in English."""
        # Arrange
        attributes = {
            "brands": ["Nike", "Adidas"],
            "categories": ["T-shirt", "Jeans"],
            "colors": ["Blue", "Red"]
        }

        # Act
        prompt = AIVisionService._build_prompt(attributes)

        # Assert
        assert "You are an expert" in prompt
        assert "CRITICAL RULES" in prompt
        assert "VALID ATTRIBUTE VALUES" in prompt
        # Ensure it's in English, not French
        assert "Vous êtes" not in prompt

    def test_build_prompt_injects_attribute_values(self):
        """Test that attribute values are injected into the prompt."""
        # Arrange
        attributes = {
            "brands": ["Nike", "Adidas", "Zara"],
            "categories": ["T-shirt", "Jeans"],
            "colors": ["Blue", "Red", "Black"]
        }

        # Act
        prompt = AIVisionService._build_prompt(attributes)

        # Assert
        assert "Nike" in prompt
        assert "Adidas" in prompt
        assert "T-shirt" in prompt
        assert "Blue" in prompt

    def test_build_prompt_contains_required_sections(self):
        """Test that prompt contains all required sections."""
        # Arrange
        attributes = {
            "brands": ["Nike"],
            "categories": ["T-shirt"],
            "colors": ["Blue"]
        }

        # Act
        prompt = AIVisionService._build_prompt(attributes)

        # Assert
        assert "Categories:" in prompt
        assert "Brands:" in prompt
        assert "Colors:" in prompt
        assert "ATTRIBUTES TO EXTRACT:" in prompt
