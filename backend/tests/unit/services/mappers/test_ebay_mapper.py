"""
Tests for EbayMapper

Tests the bidirectional mapping between eBay and Stoflow product formats.

Author: Claude
Date: 2025-12-06
Updated: 2025-12-22 - Added tests for DB-backed category mapping
"""
import pytest
from unittest.mock import MagicMock, patch
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
            "categoryId": "11483",  # Jeans (men) - valid eBay category ID
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
        assert result["category"] == "jeans"  # categoryId 11483 → jeans
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
        # Using actual eBay category IDs from CATEGORY_MAP
        categories = {
            15687: "t-shirt",    # T-Shirts (men)
            11483: "jeans",      # Jeans (men)
            11554: "jeans",      # Jeans (women)
            53159: "top",        # Tops & Shirts (women)
            63861: "dress",      # Dresses (women)
            57988: "jacket",     # Coats & Jackets (men)
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
        assert "jeans" in categories
        assert "t-shirt" in categories

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


class TestEbayMapperDbBackedCategoryMapping:
    """Tests for DB-backed category mapping (2025-12-22)."""

    def test_get_ebay_category_id_from_db_found(self):
        """Test DB lookup when category is found."""
        mock_session = MagicMock()

        with patch(
            "services.ebay.ebay_mapper.EbayCategoryMapping.get_ebay_category_id"
        ) as mock_get:
            mock_get.return_value = 11483  # jeans men

            result = EbayMapper.get_ebay_category_id_from_db(
                mock_session, "jeans", "men"
            )

            assert result == 11483
            mock_get.assert_called_once_with(mock_session, "jeans", "men")

    def test_get_ebay_category_id_from_db_not_found(self):
        """Test DB lookup when category is not found."""
        mock_session = MagicMock()

        with patch(
            "services.ebay.ebay_mapper.EbayCategoryMapping.get_ebay_category_id"
        ) as mock_get:
            mock_get.return_value = None

            result = EbayMapper.get_ebay_category_id_from_db(
                mock_session, "unknown", "men"
            )

            assert result is None

    def test_resolve_ebay_category_id_with_db_match(self):
        """Test resolve_ebay_category_id uses DB when match found."""
        mock_session = MagicMock()

        with patch.object(
            EbayMapper, "get_ebay_category_id_from_db", return_value=11483
        ):
            result = EbayMapper.resolve_ebay_category_id(
                mock_session, "jeans", "men"
            )

            assert result == 11483

    def test_resolve_ebay_category_id_fallback_to_static(self):
        """Test resolve_ebay_category_id falls back to static map."""
        mock_session = MagicMock()

        with patch.object(
            EbayMapper, "get_ebay_category_id_from_db", return_value=None
        ):
            # "jeans" is in REVERSE_CATEGORY_MAP
            result = EbayMapper.resolve_ebay_category_id(
                mock_session, "jeans", "men"
            )

            # Falls back to static map (11554 for jeans)
            assert result == EbayMapper.REVERSE_CATEGORY_MAP.get("jeans")

    def test_resolve_ebay_category_id_no_session(self):
        """Test resolve_ebay_category_id without session uses static map."""
        result = EbayMapper.resolve_ebay_category_id(None, "jeans", None)

        # Should use static fallback
        assert result == EbayMapper.REVERSE_CATEGORY_MAP.get("jeans")

    def test_resolve_ebay_category_id_no_gender(self):
        """Test resolve_ebay_category_id without gender uses static map."""
        mock_session = MagicMock()

        result = EbayMapper.resolve_ebay_category_id(mock_session, "jeans", None)

        # Should use static fallback (no gender = no DB lookup)
        assert result == EbayMapper.REVERSE_CATEGORY_MAP.get("jeans")

    def test_resolve_ebay_category_id_unknown_category(self):
        """Test resolve_ebay_category_id with unknown category returns None."""
        mock_session = MagicMock()

        with patch.object(
            EbayMapper, "get_ebay_category_id_from_db", return_value=None
        ):
            result = EbayMapper.resolve_ebay_category_id(
                mock_session, "unknown_category", "men"
            )

            assert result is None

    def test_resolve_ebay_category_id_normalizes_input(self):
        """Test that input is normalized (lowercase, stripped)."""
        mock_session = MagicMock()

        with patch.object(
            EbayMapper, "get_ebay_category_id_from_db", return_value=11483
        ) as mock_get:
            EbayMapper.resolve_ebay_category_id(
                mock_session, "  JEANS  ", "  MEN  "
            )

            # Should be called with normalized values
            mock_get.assert_called_once_with(mock_session, "jeans", "men")

    def test_stoflow_to_platform_with_session_uses_db(self):
        """Test stoflow_to_platform uses DB mapping when session provided."""
        mock_session = MagicMock()
        stoflow_product = {
            "title": "Test Jeans",
            "category": "jeans",
            "gender": "men",
            "condition": "GOOD",
        }

        with patch.object(
            EbayMapper, "resolve_ebay_category_id", return_value=11483
        ) as mock_resolve:
            result = EbayMapper.stoflow_to_platform(stoflow_product, mock_session)

            mock_resolve.assert_called_once_with(mock_session, "jeans", "men")
            assert result["categoryId"] == "11483"

    def test_stoflow_to_platform_without_session_uses_fallback(self):
        """Test stoflow_to_platform uses fallback when no session."""
        stoflow_product = {
            "title": "Test Jeans",
            "category": "jeans",
            "gender": "men",
            "condition": "GOOD",
        }

        # Without session, should use static fallback
        result = EbayMapper.stoflow_to_platform(stoflow_product, None)

        # Should get a valid category ID from fallback
        assert result["categoryId"] in ["11483", "11554"]  # jeans IDs
