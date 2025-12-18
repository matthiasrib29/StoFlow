"""
Tests for EtsyMapper

Tests the bidirectional mapping between Etsy and Stoflow product formats.
"""
import pytest
from services.etsy.etsy_mapper import EtsyMapper


class TestEtsyMapperPlatformToStoflow:
    """Tests for EtsyMapper.platform_to_stoflow (Etsy → Stoflow)."""

    def test_basic_mapping(self):
        """Test basic Etsy listing mapping to Stoflow format."""
        etsy_listing = {
            "listing_id": 123456789,
            "title": "Vintage Handmade Necklace",
            "description": "Beautiful vintage necklace...",
            "price": {"amount": 4599, "divisor": 100, "currency_code": "USD"},
            "quantity": 3,
            "who_made": "i_did",
            "when_made": "2020_2023",
            "taxonomy_id": 1234,
            "images": [
                {"url_570xN": "https://example.com/img1.jpg"},
                {"url_fullxfull": "https://example.com/img2.jpg"},
            ],
            "url": "https://etsy.com/listing/123456789",
        }

        result = EtsyMapper.platform_to_stoflow(etsy_listing)

        assert result["title"] == "Vintage Handmade Necklace"
        assert result["description"] == "Beautiful vintage necklace..."
        assert result["price"] == 45.99  # 4599 / 100
        assert result["condition"] == "EXCELLENT"  # who_made = i_did
        assert result["category"] == "Handmade"  # Default for Etsy
        assert len(result["images"]) == 2
        assert result["stock_quantity"] == 3

    def test_price_calculation(self):
        """Test price calculation from Etsy format."""
        etsy_listing = {
            "listing_id": 1,
            "title": "Test",
            "price": {"amount": 2500, "divisor": 100},
        }

        result = EtsyMapper.platform_to_stoflow(etsy_listing)
        assert result["price"] == 25.0

    def test_condition_mapping_from_who_made(self):
        """Test condition mapping based on who_made."""
        conditions = {
            "i_did": "EXCELLENT",
            "collective": "EXCELLENT",
            "someone_else": "GOOD",
        }

        for who_made, expected_condition in conditions.items():
            etsy_listing = {
                "listing_id": 1,
                "title": "Test",
                "who_made": who_made,
            }
            result = EtsyMapper.platform_to_stoflow(etsy_listing)
            assert result["condition"] == expected_condition

    def test_integration_metadata(self):
        """Test that integration metadata is correctly built."""
        etsy_listing = {
            "listing_id": 123456789,
            "title": "Test",
            "url": "https://etsy.com/listing/123456789",
            "taxonomy_id": 1234,
            "who_made": "i_did",
            "when_made": "2020_2023",
        }

        result = EtsyMapper.platform_to_stoflow(etsy_listing)
        metadata = result["integration_metadata"]

        assert metadata["source"] == "etsy"
        assert metadata["etsy_id"] == 123456789
        assert metadata["etsy_url"] == "https://etsy.com/listing/123456789"
        assert metadata["etsy_taxonomy_id"] == 1234
        assert metadata["etsy_who_made"] == "i_did"


class TestEtsyMapperStoflowToPlatform:
    """Tests for EtsyMapper.stoflow_to_platform (Stoflow → Etsy)."""

    def test_basic_mapping(self):
        """Test basic Stoflow product mapping to Etsy format."""
        stoflow_product = {
            "title": "Vintage Necklace",
            "description": "Beautiful vintage piece",
            "price": 45.99,
            "condition": "EXCELLENT",
            "stock_quantity": 2,
        }

        result = EtsyMapper.stoflow_to_platform(stoflow_product)

        assert result["title"] == "Vintage Necklace"
        assert result["description"] == "Beautiful vintage piece"
        assert result["price"] == 4599  # Converted to cents
        assert result["quantity"] == 2
        assert result["who_made"] == "i_did"  # EXCELLENT maps to i_did

    def test_price_conversion_to_cents(self):
        """Test that price is correctly converted to cents."""
        stoflow_product = {
            "title": "Test",
            "price": 25.50,
        }

        result = EtsyMapper.stoflow_to_platform(stoflow_product)
        assert result["price"] == 2550

    def test_condition_reverse_mapping(self):
        """Test reverse condition mapping to who_made."""
        conditions = {
            "NEW": "made_to_order",
            "EXCELLENT": "i_did",
            "GOOD": "someone_else",
            "FAIR": "someone_else",
            "POOR": "someone_else",
        }

        for condition, expected_who_made in conditions.items():
            stoflow_product = {
                "title": "Test",
                "condition": condition,
            }
            result = EtsyMapper.stoflow_to_platform(stoflow_product)
            assert result["who_made"] == expected_who_made


class TestEtsyMapperHelpers:
    """Tests for EtsyMapper helper methods."""

    def test_all_categories_supported(self):
        """Test that Etsy supports all categories (handmade/vintage oriented)."""
        # Etsy should return True for any category
        assert EtsyMapper.is_category_supported("Jeans") is True
        assert EtsyMapper.is_category_supported("Handmade Jewelry") is True
        assert EtsyMapper.is_category_supported("Anything") is True

    def test_get_supported_categories_returns_empty(self):
        """Test that get_supported_categories returns empty (all supported)."""
        categories = EtsyMapper.get_supported_categories()
        assert categories == []

    def test_backward_compatibility_aliases(self):
        """Test that backward compatibility aliases work."""
        etsy_listing = {
            "listing_id": 1,
            "title": "Test",
        }

        result1 = EtsyMapper.etsy_to_stoflow(etsy_listing)
        result2 = EtsyMapper.platform_to_stoflow(etsy_listing)

        assert result1 == result2
