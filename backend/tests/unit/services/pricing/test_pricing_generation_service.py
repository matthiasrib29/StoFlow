"""
Unit Tests for PricingGenerationService

Tests for LLM-powered BrandGroup generation via Google Gemini API.
Covers success paths, validation, fallbacks, and error handling.
"""

import json
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch

import pytest
from google import genai

from models.public.brand_group import BrandGroup
from services.pricing.pricing_generation_service import PricingGenerationService
from shared.exceptions import AIGenerationError


# ===== Test Data =====

VALID_RESPONSE_DATA = {
    "base_price": 45.0,
    "expected_origins": ["USA", "Mexico"],
    "expected_decades": ["1990s", "2000s"],
    "expected_trends": ["vintage", "workwear"],
    "condition_sensitivity": 1.2,
}

VALID_RESPONSE_JSON = json.dumps(VALID_RESPONSE_DATA)


# ===== Fixtures =====

@pytest.fixture
def mock_gemini_client():
    """Mock Gemini client for testing."""
    with patch("services.pricing.pricing_generation_service.genai.Client") as MockClient:
        mock_client = MagicMock()
        MockClient.return_value = mock_client

        # Setup default valid response
        mock_response = Mock()
        mock_response.text = VALID_RESPONSE_JSON
        mock_response.usage_metadata = Mock(
            prompt_token_count=100,
            candidates_token_count=50,
        )

        mock_client.models.generate_content.return_value = mock_response

        yield mock_client


# ===== TestGenerateBrandGroupSuccess =====

class TestGenerateBrandGroupSuccess:
    """Test successful BrandGroup generation."""

    @pytest.mark.asyncio
    async def test_generate_brand_group_valid_response(self, mock_gemini_client):
        """Test generate_brand_group with valid LLM response."""
        brand = "Levi's"
        group = "jeans"

        result = await PricingGenerationService.generate_brand_group(brand, group)

        # Assertions
        assert isinstance(result, BrandGroup)
        assert result.brand == brand
        assert result.group == group
        assert result.base_price == Decimal("45.0")
        assert result.condition_sensitivity == Decimal("1.2")
        assert result.expected_origins == ["USA", "Mexico"]
        assert result.expected_decades == ["1990s", "2000s"]
        assert result.expected_trends == ["vintage", "workwear"]

        # Verify API called once
        mock_gemini_client.models.generate_content.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_brand_group_with_empty_lists(self, mock_gemini_client):
        """Test generate_brand_group with empty lists (valid case)."""
        response_data = {
            "base_price": 30.0,
            "expected_origins": [],
            "expected_decades": [],
            "expected_trends": [],
            "condition_sensitivity": 1.0,
        }
        mock_gemini_client.models.generate_content.return_value.text = json.dumps(
            response_data
        )

        result = await PricingGenerationService.generate_brand_group("Generic", "t-shirt")

        assert result.base_price == Decimal("30.0")
        assert result.expected_origins == []
        assert result.expected_decades == []
        assert result.expected_trends == []

    @pytest.mark.asyncio
    async def test_generate_brand_group_edge_values(self, mock_gemini_client):
        """Test generate_brand_group with edge valid values."""
        response_data = {
            "base_price": 5.0,  # Min
            "expected_origins": ["A", "B", "C", "D", "E"],  # Max 5
            "expected_decades": ["2010s", "2000s", "1990s"],  # Max 3
            "expected_trends": ["T1", "T2", "T3", "T4", "T5"],  # Max 5
            "condition_sensitivity": 0.5,  # Min
        }
        mock_gemini_client.models.generate_content.return_value.text = json.dumps(
            response_data
        )

        result = await PricingGenerationService.generate_brand_group("Budget", "basic")

        assert result.base_price == Decimal("5.0")
        assert result.condition_sensitivity == Decimal("0.5")
        assert len(result.expected_origins) == 5
        assert len(result.expected_decades) == 3
        assert len(result.expected_trends) == 5


# ===== TestGenerateBrandGroupValidation =====

class TestGenerateBrandGroupValidation:
    """Test validation logic and fallback on invalid responses."""

    @pytest.mark.asyncio
    async def test_base_price_too_low(self, mock_gemini_client):
        """Test fallback when base_price < 5€."""
        response_data = VALID_RESPONSE_DATA.copy()
        response_data["base_price"] = 4.0  # Too low
        mock_gemini_client.models.generate_content.return_value.text = json.dumps(
            response_data
        )

        result = await PricingGenerationService.generate_brand_group("Brand", "group")

        # Should use fallback
        assert result.base_price == Decimal("30.00")
        assert result.condition_sensitivity == Decimal("1.0")
        assert result.expected_origins == []

    @pytest.mark.asyncio
    async def test_base_price_too_high(self, mock_gemini_client):
        """Test fallback when base_price > 500€."""
        response_data = VALID_RESPONSE_DATA.copy()
        response_data["base_price"] = 501.0  # Too high
        mock_gemini_client.models.generate_content.return_value.text = json.dumps(
            response_data
        )

        result = await PricingGenerationService.generate_brand_group("Brand", "group")

        # Should use fallback
        assert result.base_price == Decimal("30.00")

    @pytest.mark.asyncio
    async def test_sensitivity_too_low(self, mock_gemini_client):
        """Test fallback when condition_sensitivity < 0.5."""
        response_data = VALID_RESPONSE_DATA.copy()
        response_data["condition_sensitivity"] = 0.4  # Too low
        mock_gemini_client.models.generate_content.return_value.text = json.dumps(
            response_data
        )

        result = await PricingGenerationService.generate_brand_group("Brand", "group")

        # Should use fallback
        assert result.condition_sensitivity == Decimal("1.0")

    @pytest.mark.asyncio
    async def test_sensitivity_too_high(self, mock_gemini_client):
        """Test fallback when condition_sensitivity > 1.5."""
        response_data = VALID_RESPONSE_DATA.copy()
        response_data["condition_sensitivity"] = 1.6  # Too high
        mock_gemini_client.models.generate_content.return_value.text = json.dumps(
            response_data
        )

        result = await PricingGenerationService.generate_brand_group("Brand", "group")

        # Should use fallback
        assert result.condition_sensitivity == Decimal("1.0")

    @pytest.mark.asyncio
    async def test_invalid_origins_format(self, mock_gemini_client):
        """Test fallback when expected_origins is not a list."""
        response_data = VALID_RESPONSE_DATA.copy()
        response_data["expected_origins"] = "USA,Mexico"  # String instead of list
        mock_gemini_client.models.generate_content.return_value.text = json.dumps(
            response_data
        )

        result = await PricingGenerationService.generate_brand_group("Brand", "group")

        # Should use fallback
        assert result.expected_origins == []

    @pytest.mark.asyncio
    async def test_too_many_origins(self, mock_gemini_client):
        """Test fallback when expected_origins has > 5 items."""
        response_data = VALID_RESPONSE_DATA.copy()
        response_data["expected_origins"] = ["A", "B", "C", "D", "E", "F"]  # 6 items
        mock_gemini_client.models.generate_content.return_value.text = json.dumps(
            response_data
        )

        result = await PricingGenerationService.generate_brand_group("Brand", "group")

        # Should use fallback
        assert result.expected_origins == []

    @pytest.mark.asyncio
    async def test_empty_string_in_list(self, mock_gemini_client):
        """Test fallback when list contains empty strings."""
        response_data = VALID_RESPONSE_DATA.copy()
        response_data["expected_origins"] = ["USA", "", "Mexico"]  # Empty string
        mock_gemini_client.models.generate_content.return_value.text = json.dumps(
            response_data
        )

        result = await PricingGenerationService.generate_brand_group("Brand", "group")

        # Should use fallback
        assert result.expected_origins == []

    @pytest.mark.asyncio
    async def test_missing_required_field(self, mock_gemini_client):
        """Test fallback when required field is missing."""
        response_data = {
            "base_price": 30.0,
            # Missing expected_origins
            "expected_decades": [],
            "expected_trends": [],
            "condition_sensitivity": 1.0,
        }
        mock_gemini_client.models.generate_content.return_value.text = json.dumps(
            response_data
        )

        result = await PricingGenerationService.generate_brand_group("Brand", "group")

        # Should use fallback
        assert result.base_price == Decimal("30.00")
        assert result.expected_origins == []


# ===== TestGenerateBrandGroupFallback =====

class TestGenerateBrandGroupFallback:
    """Test error handling and fallback logic."""

    @pytest.mark.asyncio
    async def test_gemini_connection_error(self, mock_gemini_client):
        """Test fallback on connection errors (simulates ClientError behavior)."""
        # Connection errors trigger fallback just like Gemini errors
        mock_gemini_client.models.generate_content.side_effect = ConnectionError(
            "Failed to connect to Gemini API"
        )

        result = await PricingGenerationService.generate_brand_group("Brand", "group")

        # Should use fallback
        assert result.base_price == Decimal("30.00")
        assert result.condition_sensitivity == Decimal("1.0")
        assert result.expected_origins == []
        assert result.expected_decades == []
        assert result.expected_trends == []

    @pytest.mark.asyncio
    async def test_gemini_timeout_error(self, mock_gemini_client):
        """Test fallback on timeout errors (simulates ServerError behavior)."""
        # Timeout errors trigger fallback just like Gemini errors
        mock_gemini_client.models.generate_content.side_effect = TimeoutError(
            "Request to Gemini API timed out"
        )

        result = await PricingGenerationService.generate_brand_group("Brand", "group")

        # Should use fallback
        assert result.base_price == Decimal("30.00")

    @pytest.mark.asyncio
    async def test_gemini_value_error(self, mock_gemini_client):
        """Test fallback on value errors (simulates APIError behavior)."""
        # Value errors (e.g., quota exceeded) trigger fallback
        mock_gemini_client.models.generate_content.side_effect = ValueError(
            "API quota exceeded"
        )

        result = await PricingGenerationService.generate_brand_group("Brand", "group")

        # Should use fallback
        assert result.base_price == Decimal("30.00")

    @pytest.mark.asyncio
    async def test_unexpected_exception(self, mock_gemini_client):
        """Test fallback on unexpected exception."""
        mock_gemini_client.models.generate_content.side_effect = RuntimeError(
            "Unexpected error"
        )

        result = await PricingGenerationService.generate_brand_group("Brand", "group")

        # Should use fallback
        assert result.base_price == Decimal("30.00")

    @pytest.mark.asyncio
    async def test_invalid_json_response(self, mock_gemini_client):
        """Test fallback when LLM returns invalid JSON."""
        mock_gemini_client.models.generate_content.return_value.text = "not valid json {{"

        result = await PricingGenerationService.generate_brand_group("Brand", "group")

        # Should use fallback
        assert result.base_price == Decimal("30.00")

    @pytest.mark.asyncio
    async def test_fallback_values_correct(self):
        """Test _get_fallback_brand_group returns correct values."""
        fallback = PricingGenerationService._get_fallback_brand_group("TestBrand", "TestGroup")

        assert isinstance(fallback, BrandGroup)
        assert fallback.brand == "TestBrand"
        assert fallback.group == "TestGroup"
        assert fallback.base_price == Decimal("30.00")
        assert fallback.condition_sensitivity == Decimal("1.0")
        assert fallback.expected_origins == []
        assert fallback.expected_decades == []
        assert fallback.expected_trends == []


# ===== TestGenerateBrandGroupPrompt =====

class TestGenerateBrandGroupPrompt:
    """Test prompt construction and content."""

    @pytest.mark.asyncio
    async def test_prompt_includes_brand_and_group(self, mock_gemini_client):
        """Test that prompt contains brand and group names."""
        await PricingGenerationService.generate_brand_group("Nike", "sneakers")

        # Get the actual call arguments
        call_args = mock_gemini_client.models.generate_content.call_args
        prompt_contents = call_args.kwargs["contents"]

        assert isinstance(prompt_contents, list)
        prompt_text = prompt_contents[0]
        assert "Nike" in prompt_text
        assert "sneakers" in prompt_text

    @pytest.mark.asyncio
    async def test_prompt_includes_secondhand_context(self, mock_gemini_client):
        """Test that prompt mentions secondhand/vintage context."""
        await PricingGenerationService.generate_brand_group("Hermès", "bags")

        call_args = mock_gemini_client.models.generate_content.call_args
        prompt_text = call_args.kwargs["contents"][0]

        assert "secondhand" in prompt_text.lower()

    @pytest.mark.asyncio
    async def test_prompt_specifies_output_format(self, mock_gemini_client):
        """Test that prompt specifies JSON output format."""
        await PricingGenerationService.generate_brand_group("Zara", "dress")

        call_args = mock_gemini_client.models.generate_content.call_args
        prompt_text = call_args.kwargs["contents"][0]

        # Check that all required fields are mentioned
        assert "base_price" in prompt_text
        assert "expected_origins" in prompt_text
        assert "expected_decades" in prompt_text
        assert "expected_trends" in prompt_text
        assert "condition_sensitivity" in prompt_text

    @pytest.mark.asyncio
    async def test_prompt_includes_examples(self, mock_gemini_client):
        """Test that prompt includes examples for guidance."""
        await PricingGenerationService.generate_brand_group("Adidas", "sneakers")

        call_args = mock_gemini_client.models.generate_content.call_args
        prompt_text = call_args.kwargs["contents"][0]

        # Check for example patterns
        assert "Examples:" in prompt_text or "Example:" in prompt_text

    @pytest.mark.asyncio
    async def test_gemini_model_used(self, mock_gemini_client):
        """Test that gemini-2.5-flash model is used."""
        await PricingGenerationService.generate_brand_group("Brand", "group")

        call_args = mock_gemini_client.models.generate_content.call_args
        assert call_args.kwargs["model"] == "gemini-2.5-flash"

    @pytest.mark.asyncio
    async def test_json_response_mime_type(self, mock_gemini_client):
        """Test that JSON response MIME type is set."""
        await PricingGenerationService.generate_brand_group("Brand", "group")

        call_args = mock_gemini_client.models.generate_content.call_args
        config = call_args.kwargs["config"]

        assert config.response_mime_type == "application/json"
