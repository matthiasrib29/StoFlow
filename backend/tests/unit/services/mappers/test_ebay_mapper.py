"""
Tests for EbayMapper

Tests the bidirectional mapping between eBay and Stoflow product formats.
"""
import pytest
from services.ebay.ebay_mapper import EbayMapper


class TestEbayMapperPlatformToStoflow:
    """Tests for EbayMapper.platform_to_stoflow (eBay → Stoflow)."""

    def test_basic_mapping(self):
        """Test basic eBay item mapping to Stoflow format."""
        ebay_item = {
            "itemId": "123456789",
            "title": "Vintage Levi's 501 Jeans",
            "description": "Classic vintage jeans...",
            "price": {"value": "45.00", "currency": "USD"},
            "conditionId": "3000",
            "categoryId": "57989",
            "brand": "Levi's",
            "size": "32",
            "color": "Blue",
            "image": {"imageUrl": "https://example.com/img1.jpg"},
            "additionalImages": [
                {"imageUrl": "https://example.com/img2.jpg"},
            ],
            "listingUrl": "https://ebay.com/itm/123456789",
            "quantity": 2,
        }

        result = EbayMapper.platform_to_stoflow(ebay_item)

        assert result["title"] == "Vintage Levi's 501 Jeans"
        assert result["description"] == "Classic vintage jeans..."
        assert result["price"] == 45.0
        assert result["brand"] == "Levi's"
        assert result["condition"] == "EXCELLENT"  # conditionId 3000
        assert result["category"] == "Jeans"  # categoryId 57989
        assert result["label_size"] == "32"
        assert result["color"] == "Blue"
        assert len(result["images"]) == 2
        assert result["stock_quantity"] == 2

    def test_condition_mapping(self):
        """Test all eBay condition mappings."""
        conditions = {
            1000: "NEW",
            1500: "NEW",
            2000: "EXCELLENT",
            3000: "EXCELLENT",
            4000: "GOOD",
            5000: "FAIR",
            6000: "POOR",
            7000: "POOR",
        }

        for condition_id, expected_condition in conditions.items():
            ebay_item = {
                "itemId": "1",
                "title": "Test",
                "price": {"value": "10.00"},
                "conditionId": str(condition_id),
                "categoryId": "57989",
            }
            result = EbayMapper.platform_to_stoflow(ebay_item)
            assert result["condition"] == expected_condition

    def test_category_mapping(self):
        """Test category mapping from eBay categoryId."""
        categories = {
            1059: "T-Shirts",
            57989: "Jeans",
            53159: "Robes",
            93427: "Baskets",
            169291: "Sacs",
        }

        for category_id, expected_category in categories.items():
            ebay_item = {
                "itemId": "1",
                "title": "Test",
                "price": {"value": "10.00"},
                "categoryId": str(category_id),
            }
            result = EbayMapper.platform_to_stoflow(ebay_item)
            assert result["category"] == expected_category

    def test_integration_metadata(self):
        """Test that integration metadata is correctly built."""
        ebay_item = {
            "itemId": "123456789",
            "title": "Test",
            "price": {"value": "10.00"},
            "categoryId": "57989",
            "conditionId": "3000",
            "listingUrl": "https://ebay.com/itm/123456789",
        }

        result = EbayMapper.platform_to_stoflow(ebay_item)
        metadata = result["integration_metadata"]

        assert metadata["source"] == "ebay"
        assert metadata["ebay_id"] == "123456789"
        assert metadata["ebay_url"] == "https://ebay.com/itm/123456789"


class TestEbayMapperStoflowToPlatform:
    """Tests for EbayMapper.stoflow_to_platform (Stoflow → eBay)."""

    def test_basic_mapping(self):
        """Test basic Stoflow product mapping to eBay format."""
        stoflow_product = {
            "title": "Vintage Levi's 501 Jeans",
            "description": "Classic vintage jeans",
            "price": 45.99,
            "brand": "Levi's",
            "category": "Jeans",
            "condition": "EXCELLENT",
            "label_size": "32",
            "color": "Blue",
            "stock_quantity": 2,
        }

        result = EbayMapper.stoflow_to_platform(stoflow_product)

        assert result["title"] == "Vintage Levi's 501 Jeans"
        assert result["price"]["value"] == "45.99"
        assert result["price"]["currency"] == "EUR"
        # Jeans has multiple IDs (57989 homme, 11554 femme), reverse map picks one
        assert result["categoryId"] in ["57989", "11554"]
        assert result["conditionId"] == "3000"  # EXCELLENT
        assert result["quantity"] == 2

    def test_condition_reverse_mapping(self):
        """Test reverse condition mapping."""
        conditions = {
            "NEW": "1000",
            "EXCELLENT": "3000",
            "GOOD": "4000",
            "FAIR": "5000",
            "POOR": "6000",
        }

        for condition, expected_condition_id in conditions.items():
            stoflow_product = {
                "title": "Test",
                "category": "Jeans",
                "condition": condition,
            }
            result = EbayMapper.stoflow_to_platform(stoflow_product)
            assert result["conditionId"] == expected_condition_id

    def test_unsupported_category_raises_error(self):
        """Test that unsupported category raises ValueError."""
        stoflow_product = {
            "title": "Test",
            "category": "UnsupportedCategory",
            "condition": "GOOD",
        }

        with pytest.raises(ValueError) as exc_info:
            EbayMapper.stoflow_to_platform(stoflow_product)

        assert "Cannot map Stoflow category" in str(exc_info.value)


class TestEbayMapperHelpers:
    """Tests for EbayMapper helper methods."""

    def test_get_supported_categories(self):
        """Test getting list of supported categories."""
        categories = EbayMapper.get_supported_categories()

        assert isinstance(categories, list)
        assert "Jeans" in categories
        assert "T-Shirts" in categories

    def test_backward_compatibility_aliases(self):
        """Test that backward compatibility aliases work."""
        ebay_item = {
            "itemId": "1",
            "title": "Test",
            "price": {"value": "10.00"},
            "categoryId": "57989",
        }

        result1 = EbayMapper.ebay_to_stoflow(ebay_item)
        result2 = EbayMapper.platform_to_stoflow(ebay_item)

        assert result1 == result2
