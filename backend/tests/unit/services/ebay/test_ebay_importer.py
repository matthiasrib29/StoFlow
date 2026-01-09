"""
Tests for EbayImporter

Comprehensive unit tests for the eBay Importer service that imports products
from eBay Inventory API to Stoflow.

Tests cover:
- Pagination logic for fetching inventory items
- Offer fetching for SKUs
- Import workflow (create/update/skip)
- Product data extraction with aspects
- Error handling at all levels

Author: Claude
Date: 2025-01-08
"""
import json
import pytest
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch, PropertyMock


class TestEbayImporterFetchInventory:
    """Tests for fetch_all_inventory_items method."""

    @pytest.fixture
    def mock_importer(self):
        """Create an EbayImporter with mocked dependencies."""
        with patch(
            "services.ebay.ebay_importer.EbayImporter.__init__",
            return_value=None
        ):
            from services.ebay.ebay_importer import EbayImporter
            importer = EbayImporter.__new__(EbayImporter)
            importer.db = MagicMock()
            importer.user_id = 1
            importer.marketplace_id = "EBAY_FR"
            importer.inventory_client = MagicMock()
            importer.offer_client = MagicMock()
            importer._aspect_reverse_map = {
                "Marque": "brand",
                "Brand": "brand",
                "Couleur": "color",
                "Color": "color",
                "Taille": "size",
                "Size": "size",
                "Matiere": "material",
                "Material": "material",
            }
            return importer

    def test_fetch_all_inventory_items_success_single_page(self, mock_importer):
        """
        Test fetching inventory items when all items fit in a single page.

        Verifies that:
        - API is called with correct parameters
        - All items are returned
        - Pagination stops when no more items
        """
        mock_importer.inventory_client.get_inventory_items.return_value = {
            "inventoryItems": [
                {"sku": "SKU-001", "product": {"title": "Item 1"}},
                {"sku": "SKU-002", "product": {"title": "Item 2"}},
            ],
            "total": 2
        }

        result = mock_importer.fetch_all_inventory_items()

        assert len(result) == 2
        assert result[0]["sku"] == "SKU-001"
        assert result[1]["sku"] == "SKU-002"
        mock_importer.inventory_client.get_inventory_items.assert_called_once_with(
            limit=100, offset=0
        )

    def test_fetch_all_inventory_items_success_paginated(self, mock_importer):
        """
        Test fetching inventory items with pagination across multiple pages.

        Verifies that:
        - Multiple API calls are made for each page
        - All items from all pages are collected
        - Pagination stops at correct point
        """
        # First page: 100 items, more available
        first_page_items = [
            {"sku": f"SKU-{i:03d}", "product": {"title": f"Item {i}"}}
            for i in range(100)
        ]
        # Second page: remaining 50 items
        second_page_items = [
            {"sku": f"SKU-{i:03d}", "product": {"title": f"Item {i}"}}
            for i in range(100, 150)
        ]

        mock_importer.inventory_client.get_inventory_items.side_effect = [
            {"inventoryItems": first_page_items, "total": 150},
            {"inventoryItems": second_page_items, "total": 150},
        ]

        result = mock_importer.fetch_all_inventory_items()

        assert len(result) == 150
        assert mock_importer.inventory_client.get_inventory_items.call_count == 2

        # Verify pagination parameters
        calls = mock_importer.inventory_client.get_inventory_items.call_args_list
        assert calls[0].kwargs == {"limit": 100, "offset": 0}
        assert calls[1].kwargs == {"limit": 100, "offset": 100}

    def test_fetch_all_inventory_items_empty(self, mock_importer):
        """
        Test fetching when no inventory items exist.

        Verifies that:
        - Empty list is returned
        - Single API call is made
        - No errors occur
        """
        mock_importer.inventory_client.get_inventory_items.return_value = {
            "inventoryItems": [],
            "total": 0
        }

        result = mock_importer.fetch_all_inventory_items()

        assert result == []
        mock_importer.inventory_client.get_inventory_items.assert_called_once()

    def test_fetch_all_inventory_items_handles_api_error(self, mock_importer):
        """
        Test error handling when API call fails.

        Verifies that:
        - Exception is caught and logged
        - Partial results are returned (items fetched before error)
        - Loop breaks on error
        """
        # First call succeeds, second fails
        mock_importer.inventory_client.get_inventory_items.side_effect = [
            {
                "inventoryItems": [{"sku": "SKU-001", "product": {"title": "Item 1"}}],
                "total": 200  # More pages expected
            },
            RuntimeError("API Error: 500 Internal Server Error"),
        ]

        with patch("services.ebay.ebay_importer.logger") as mock_logger:
            result = mock_importer.fetch_all_inventory_items()

        # Should return items from first page only
        assert len(result) == 1
        assert result[0]["sku"] == "SKU-001"
        mock_logger.error.assert_called()

    def test_fetch_all_inventory_items_stops_at_total(self, mock_importer):
        """
        Test that pagination stops when offset + limit >= total.

        Verifies correct stopping condition to avoid unnecessary API calls.
        """
        mock_importer.inventory_client.get_inventory_items.return_value = {
            "inventoryItems": [
                {"sku": "SKU-001", "product": {"title": "Item 1"}},
            ],
            "total": 1
        }

        result = mock_importer.fetch_all_inventory_items()

        assert len(result) == 1
        # Should only call once since total <= limit
        mock_importer.inventory_client.get_inventory_items.assert_called_once()


class TestEbayImporterFetchOffers:
    """Tests for fetch_offers_for_sku method."""

    @pytest.fixture
    def mock_importer(self):
        """Create an EbayImporter with mocked dependencies."""
        with patch(
            "services.ebay.ebay_importer.EbayImporter.__init__",
            return_value=None
        ):
            from services.ebay.ebay_importer import EbayImporter
            importer = EbayImporter.__new__(EbayImporter)
            importer.db = MagicMock()
            importer.user_id = 1
            importer.marketplace_id = "EBAY_FR"
            importer.inventory_client = MagicMock()
            importer.offer_client = MagicMock()
            importer._aspect_reverse_map = {}
            return importer

    def test_fetch_offers_for_sku_success(self, mock_importer):
        """
        Test successful fetching of offers for a SKU.

        Verifies that:
        - Offer client is called with correct SKU
        - Offers list is returned
        """
        mock_importer.offer_client.get_offers.return_value = {
            "offers": [
                {
                    "offerId": "123456",
                    "sku": "SKU-001",
                    "marketplaceId": "EBAY_FR",
                    "pricingSummary": {"price": {"value": "49.90", "currency": "EUR"}}
                }
            ],
            "total": 1
        }

        result = mock_importer.fetch_offers_for_sku("SKU-001")

        assert len(result) == 1
        assert result[0]["offerId"] == "123456"
        mock_importer.offer_client.get_offers.assert_called_once_with(sku="SKU-001")

    def test_fetch_offers_for_sku_empty(self, mock_importer):
        """
        Test fetching offers when SKU has no offers.

        Verifies empty list is returned.
        """
        mock_importer.offer_client.get_offers.return_value = {
            "offers": [],
            "total": 0
        }

        result = mock_importer.fetch_offers_for_sku("SKU-NOOFFERS")

        assert result == []

    def test_fetch_offers_for_sku_handles_error(self, mock_importer):
        """
        Test error handling when fetching offers fails.

        Verifies that:
        - Exception is caught
        - Empty list is returned (graceful degradation)
        - Warning is logged
        """
        mock_importer.offer_client.get_offers.side_effect = RuntimeError(
            "API Error: 404 Not Found"
        )

        with patch("services.ebay.ebay_importer.logger") as mock_logger:
            result = mock_importer.fetch_offers_for_sku("SKU-INVALID")

        assert result == []
        mock_logger.warning.assert_called()


class TestEbayImporterImportAllProducts:
    """Tests for import_all_products method."""

    @pytest.fixture
    def mock_importer(self):
        """Create an EbayImporter with mocked dependencies."""
        with patch(
            "services.ebay.ebay_importer.EbayImporter.__init__",
            return_value=None
        ):
            from services.ebay.ebay_importer import EbayImporter
            importer = EbayImporter.__new__(EbayImporter)
            importer.db = MagicMock()
            importer.user_id = 1
            importer.marketplace_id = "EBAY_FR"
            importer.inventory_client = MagicMock()
            importer.offer_client = MagicMock()
            importer._aspect_reverse_map = {
                "Brand": "brand",
                "Marque": "brand",
            }
            return importer

    def test_import_all_products_success(self, mock_importer):
        """
        Test successful import of multiple products.

        Verifies that:
        - All products are processed
        - Correct counts returned
        - DB commit is called
        """
        # Mock fetch_all_inventory_items
        mock_importer.fetch_all_inventory_items = MagicMock(return_value=[
            {"sku": "SKU-001", "product": {"title": "Item 1"}},
            {"sku": "SKU-002", "product": {"title": "Item 2"}},
        ])

        # Mock _import_single_item
        mock_importer._import_single_item = MagicMock(side_effect=[
            {"sku": "SKU-001", "status": "imported", "id": 1, "title": "Item 1"},
            {"sku": "SKU-002", "status": "updated", "id": 2, "title": "Item 2"},
        ])

        result = mock_importer.import_all_products()

        assert result["imported"] == 1
        assert result["updated"] == 1
        assert result["skipped"] == 0
        assert result["errors"] == 0
        assert len(result["details"]) == 2
        mock_importer.db.commit.assert_called_once()

    def test_import_all_products_creates_new(self, mock_importer):
        """
        Test that new products are created when they don't exist.

        Verifies import counter is incremented.
        """
        mock_importer.fetch_all_inventory_items = MagicMock(return_value=[
            {"sku": "SKU-NEW", "product": {"title": "New Product"}},
        ])
        mock_importer._import_single_item = MagicMock(return_value={
            "sku": "SKU-NEW", "status": "imported", "id": 1, "title": "New Product"
        })

        result = mock_importer.import_all_products()

        assert result["imported"] == 1
        assert result["updated"] == 0

    def test_import_all_products_updates_existing(self, mock_importer):
        """
        Test that existing products are updated.

        Verifies update counter is incremented.
        """
        mock_importer.fetch_all_inventory_items = MagicMock(return_value=[
            {"sku": "SKU-EXISTING", "product": {"title": "Updated Product"}},
        ])
        mock_importer._import_single_item = MagicMock(return_value={
            "sku": "SKU-EXISTING", "status": "updated", "id": 1, "title": "Updated Product"
        })

        result = mock_importer.import_all_products()

        assert result["imported"] == 0
        assert result["updated"] == 1

    def test_import_all_products_skips_no_sku(self, mock_importer):
        """
        Test that items without SKU are skipped.

        Verifies skipped counter is incremented.
        """
        mock_importer.fetch_all_inventory_items = MagicMock(return_value=[
            {"product": {"title": "No SKU Item"}},  # Missing SKU
        ])
        mock_importer._import_single_item = MagicMock(return_value={
            "sku": None, "status": "skipped", "reason": "no_sku"
        })

        result = mock_importer.import_all_products()

        assert result["skipped"] == 1
        assert result["imported"] == 0

    def test_import_all_products_handles_errors(self, mock_importer):
        """
        Test error handling during import.

        Verifies that:
        - Errors are counted
        - Other products continue processing
        - Error details are captured
        """
        mock_importer.fetch_all_inventory_items = MagicMock(return_value=[
            {"sku": "SKU-001", "product": {"title": "Item 1"}},
            {"sku": "SKU-ERROR", "product": {"title": "Error Item"}},
            {"sku": "SKU-003", "product": {"title": "Item 3"}},
        ])

        # Second call raises exception
        mock_importer._import_single_item = MagicMock(side_effect=[
            {"sku": "SKU-001", "status": "imported", "id": 1, "title": "Item 1"},
            ValueError("Processing error"),
            {"sku": "SKU-003", "status": "imported", "id": 3, "title": "Item 3"},
        ])

        with patch("services.ebay.ebay_importer.logger"):
            result = mock_importer.import_all_products()

        assert result["imported"] == 2
        assert result["errors"] == 1
        assert len(result["details"]) == 3

        # Verify error detail captured
        error_detail = next(d for d in result["details"] if d["status"] == "error")
        assert error_detail["sku"] == "SKU-ERROR"
        assert "Processing error" in error_detail["error"]

    def test_import_all_products_empty_inventory(self, mock_importer):
        """
        Test import when no inventory items exist.

        Verifies zero counts and no commit.
        """
        mock_importer.fetch_all_inventory_items = MagicMock(return_value=[])

        result = mock_importer.import_all_products()

        assert result["imported"] == 0
        assert result["updated"] == 0
        assert result["skipped"] == 0
        assert result["errors"] == 0
        assert result["details"] == []
        # Commit should not be called if no items
        mock_importer.db.commit.assert_not_called()

    def test_import_all_products_handles_commit_error(self, mock_importer):
        """
        Test error handling when DB commit fails.

        Verifies that:
        - Rollback is called
        - Exception is re-raised
        """
        mock_importer.fetch_all_inventory_items = MagicMock(return_value=[
            {"sku": "SKU-001", "product": {"title": "Item 1"}},
        ])
        mock_importer._import_single_item = MagicMock(return_value={
            "sku": "SKU-001", "status": "imported", "id": 1, "title": "Item 1"
        })
        mock_importer.db.commit.side_effect = Exception("DB commit failed")

        with patch("services.ebay.ebay_importer.logger"):
            with pytest.raises(Exception) as exc_info:
                mock_importer.import_all_products()

        assert "DB commit failed" in str(exc_info.value)
        mock_importer.db.rollback.assert_called_once()


class TestEbayImporterImportSingleItem:
    """Tests for _import_single_item method."""

    @pytest.fixture
    def mock_importer(self):
        """Create an EbayImporter with mocked dependencies."""
        with patch(
            "services.ebay.ebay_importer.EbayImporter.__init__",
            return_value=None
        ):
            from services.ebay.ebay_importer import EbayImporter
            importer = EbayImporter.__new__(EbayImporter)
            importer.db = MagicMock()
            importer.user_id = 1
            importer.marketplace_id = "EBAY_FR"
            importer._aspect_reverse_map = {
                "Brand": "brand",
                "Marque": "brand",
                "Couleur": "color",
                "Color": "color",
            }
            return importer

    @pytest.fixture
    def sample_inventory_item(self):
        """Sample inventory item from eBay API."""
        return {
            "sku": "SKU-TEST-001",
            "product": {
                "title": "Test Product Title",
                "description": "Test product description",
                "imageUrls": ["https://example.com/img1.jpg"],
                "aspects": {
                    "Brand": ["Nike"],
                    "Color": ["Blue"],
                }
            },
            "condition": "NEW",
            "availability": {
                "shipToLocationAvailability": {"quantity": 5}
            }
        }

    def test_import_single_item_creates_new(self, mock_importer, sample_inventory_item):
        """
        Test creating a new EbayProduct when SKU doesn't exist.

        Verifies that:
        - DB query returns None (not found)
        - New record is created with db.add()
        - db.flush() is called to get ID
        - Correct status returned
        """
        # Mock _extract_product_data
        mock_importer._extract_product_data = MagicMock(return_value={
            "title": "Test Product Title",
            "brand": "Nike",
            "color": "Blue",
            "quantity": 5,
        })

        # Mock DB query - product not found
        mock_importer.db.query.return_value.filter.return_value.first.return_value = None

        # Mock EbayProduct class
        with patch("services.ebay.ebay_importer.EbayProduct") as MockEbayProduct:
            mock_product = MagicMock()
            mock_product.id = 123
            MockEbayProduct.return_value = mock_product

            with patch("services.ebay.ebay_importer.utc_now") as mock_utc:
                mock_utc.return_value = datetime(2025, 1, 8, 12, 0, 0, tzinfo=timezone.utc)
                result = mock_importer._import_single_item(sample_inventory_item)

        assert result["status"] == "imported"
        assert result["sku"] == "SKU-TEST-001"
        assert result["id"] == 123
        mock_importer.db.add.assert_called_once()
        mock_importer.db.flush.assert_called_once()

    def test_import_single_item_updates_existing(self, mock_importer, sample_inventory_item):
        """
        Test updating an existing EbayProduct when SKU exists.

        Verifies that:
        - Existing record is found
        - Attributes are updated via setattr
        - No db.add() called
        - Correct status returned
        """
        mock_importer._extract_product_data = MagicMock(return_value={
            "title": "Updated Title",
            "brand": "Nike",
            "quantity": 10,
        })

        # Mock existing product
        existing_product = MagicMock()
        existing_product.id = 456
        existing_product.title = "Old Title"
        existing_product.brand = "Adidas"
        existing_product.quantity = 5

        mock_importer.db.query.return_value.filter.return_value.first.return_value = (
            existing_product
        )

        with patch("services.ebay.ebay_importer.utc_now") as mock_utc:
            mock_utc.return_value = datetime(2025, 1, 8, 12, 0, 0, tzinfo=timezone.utc)
            result = mock_importer._import_single_item(sample_inventory_item)

        assert result["status"] == "updated"
        assert result["id"] == 456
        assert result["title"] == "Updated Title"
        # Verify attributes were updated
        assert existing_product.title == "Updated Title"
        assert existing_product.brand == "Nike"
        mock_importer.db.add.assert_not_called()

    def test_import_single_item_skips_no_sku(self, mock_importer):
        """
        Test that items without SKU are skipped.
        """
        item_no_sku = {"product": {"title": "No SKU"}}

        result = mock_importer._import_single_item(item_no_sku)

        assert result["status"] == "skipped"
        assert result["reason"] == "no_sku"
        assert result["sku"] is None
        mock_importer.db.query.assert_not_called()


class TestEbayImporterExtractProductData:
    """Tests for _extract_product_data method."""

    @pytest.fixture
    def mock_importer(self):
        """Create an EbayImporter with mocked dependencies."""
        with patch(
            "services.ebay.ebay_importer.EbayImporter.__init__",
            return_value=None
        ):
            from services.ebay.ebay_importer import EbayImporter
            importer = EbayImporter.__new__(EbayImporter)
            importer.db = MagicMock()
            importer.user_id = 1
            importer.marketplace_id = "EBAY_FR"
            importer._aspect_reverse_map = {
                # English
                "Brand": "brand",
                "Color": "color",
                "Colour": "color",
                "Size": "size",
                "Material": "material",
                # French
                "Marque": "brand",
                "Couleur": "color",
                "Taille": "size",
                "Matiere": "material",
                # German
                "Marke": "brand",
                "Farbe": "color",
            }
            return importer

    def test_extract_product_data_complete(self, mock_importer):
        """
        Test extraction with all fields populated.

        Verifies that all data is correctly extracted and formatted.
        """
        inventory_item = {
            "sku": "SKU-COMPLETE",
            "product": {
                "title": "Complete Product",
                "description": "Full description here",
                "imageUrls": [
                    "https://example.com/img1.jpg",
                    "https://example.com/img2.jpg"
                ],
                "aspects": {
                    "Brand": ["Nike"],
                    "Color": ["Red"],
                    "Size": ["L"],
                    "Material": ["Cotton"]
                }
            },
            "condition": "LIKE_NEW",
            "conditionDescription": "Worn once, excellent condition",
            "availability": {
                "shipToLocationAvailability": {"quantity": 3}
            },
            "packageWeightAndSize": {
                "weight": {"value": 0.5, "unit": "KILOGRAM"},
                "dimensions": {
                    "length": 30,
                    "width": 20,
                    "height": 10,
                    "unit": "CENTIMETER"
                }
            }
        }

        result = mock_importer._extract_product_data(inventory_item)

        # Basic product info
        assert result["title"] == "Complete Product"
        assert result["description"] == "Full description here"
        assert result["condition"] == "LIKE_NEW"
        assert result["condition_description"] == "Worn once, excellent condition"

        # Aspects extracted via DB mapping
        assert result["brand"] == "Nike"
        assert result["color"] == "Red"
        assert result["size"] == "L"
        assert result["material"] == "Cotton"

        # Availability
        assert result["quantity"] == 3
        assert result["availability_type"] == "IN_STOCK"
        assert result["status"] == "active"

        # Package details
        assert result["package_weight_value"] == 0.5
        assert result["package_weight_unit"] == "KILOGRAM"
        assert result["package_length_value"] == 30
        assert result["package_width_value"] == 20
        assert result["package_height_value"] == 10
        assert result["package_length_unit"] == "CENTIMETER"

        # Marketplace
        assert result["marketplace_id"] == "EBAY_FR"

        # Images as JSON
        image_urls = json.loads(result["image_urls"])
        assert len(image_urls) == 2

        # Aspects as JSON
        aspects = json.loads(result["aspects"])
        assert aspects["Brand"] == ["Nike"]

    def test_extract_product_data_minimal(self, mock_importer):
        """
        Test extraction with minimal data (only required fields).

        Verifies graceful handling of missing optional fields.
        """
        inventory_item = {
            "sku": "SKU-MINIMAL",
            "product": {
                "title": "Minimal Product"
            },
            "availability": {}
        }

        result = mock_importer._extract_product_data(inventory_item)

        # Required fields
        assert result["title"] == "Minimal Product"
        assert result["marketplace_id"] == "EBAY_FR"

        # Optional fields should be None or default
        assert result["description"] is None
        assert result["brand"] is None
        assert result["color"] is None
        assert result["size"] is None
        assert result["material"] is None
        assert result["condition"] is None

        # Quantity defaults
        assert result["quantity"] == 0
        assert result["availability_type"] == "OUT_OF_STOCK"
        assert result["status"] == "inactive"

        # No images
        assert result["image_urls"] is None

        # No aspects
        assert result["aspects"] is None

    def test_extract_product_data_with_aspects_multilang(self, mock_importer):
        """
        Test aspect extraction with different languages.

        Verifies that aspects are extracted regardless of language
        using the reverse mapping from DB.
        """
        # French aspects
        inventory_item_fr = {
            "sku": "SKU-FR",
            "product": {
                "title": "French Product",
                "aspects": {
                    "Marque": ["Adidas"],
                    "Couleur": ["Bleu"],
                    "Taille": ["42"],
                }
            },
            "availability": {"shipToLocationAvailability": {"quantity": 1}}
        }

        result = mock_importer._extract_product_data(inventory_item_fr)

        assert result["brand"] == "Adidas"
        assert result["color"] == "Bleu"
        assert result["size"] == "42"

    def test_extract_product_data_with_aspects_german(self, mock_importer):
        """
        Test aspect extraction with German language aspects.
        """
        inventory_item_de = {
            "sku": "SKU-DE",
            "product": {
                "title": "German Product",
                "aspects": {
                    "Marke": ["Puma"],
                    "Farbe": ["Schwarz"],
                }
            },
            "availability": {"shipToLocationAvailability": {"quantity": 2}}
        }

        result = mock_importer._extract_product_data(inventory_item_de)

        assert result["brand"] == "Puma"
        assert result["color"] == "Schwarz"

    def test_extract_product_data_aspects_string_value(self, mock_importer):
        """
        Test handling of aspects with string values instead of lists.

        Some eBay responses may have string values instead of arrays.
        """
        inventory_item = {
            "sku": "SKU-STRING",
            "product": {
                "title": "String Aspect Product",
                "aspects": {
                    "Brand": "Nike",  # String instead of list
                }
            },
            "availability": {"shipToLocationAvailability": {"quantity": 1}}
        }

        result = mock_importer._extract_product_data(inventory_item)

        # Should handle string value
        assert result["brand"] == "Nike"

    def test_extract_product_data_zero_quantity(self, mock_importer):
        """
        Test that zero quantity sets correct availability status.
        """
        inventory_item = {
            "sku": "SKU-ZERO",
            "product": {"title": "Out of Stock Item"},
            "availability": {"shipToLocationAvailability": {"quantity": 0}}
        }

        result = mock_importer._extract_product_data(inventory_item)

        assert result["quantity"] == 0
        assert result["availability_type"] == "OUT_OF_STOCK"
        assert result["status"] == "inactive"

    def test_extract_product_data_positive_quantity(self, mock_importer):
        """
        Test that positive quantity sets correct availability status.
        """
        inventory_item = {
            "sku": "SKU-STOCK",
            "product": {"title": "In Stock Item"},
            "availability": {"shipToLocationAvailability": {"quantity": 10}}
        }

        result = mock_importer._extract_product_data(inventory_item)

        assert result["quantity"] == 10
        assert result["availability_type"] == "IN_STOCK"
        assert result["status"] == "active"


class TestEbayImporterGetAspectByKey:
    """Tests for _get_aspect_by_key method."""

    @pytest.fixture
    def mock_importer(self):
        """Create an EbayImporter with mocked dependencies."""
        with patch(
            "services.ebay.ebay_importer.EbayImporter.__init__",
            return_value=None
        ):
            from services.ebay.ebay_importer import EbayImporter
            importer = EbayImporter.__new__(EbayImporter)
            importer._aspect_reverse_map = {
                "Brand": "brand",
                "Marque": "brand",
                "Color": "color",
                "Colour": "color",
                "Couleur": "color",
            }
            return importer

    def test_get_aspect_by_key_found_list(self, mock_importer):
        """Test finding aspect when value is a list."""
        aspects = {"Brand": ["Nike", "Jordan"]}

        result = mock_importer._get_aspect_by_key(aspects, "brand")

        assert result == "Nike"  # First value

    def test_get_aspect_by_key_found_string(self, mock_importer):
        """Test finding aspect when value is a string."""
        aspects = {"Marque": "Adidas"}

        result = mock_importer._get_aspect_by_key(aspects, "brand")

        assert result == "Adidas"

    def test_get_aspect_by_key_not_found(self, mock_importer):
        """Test when aspect key is not in the mapping."""
        aspects = {"UnknownAspect": ["Value"]}

        result = mock_importer._get_aspect_by_key(aspects, "brand")

        assert result is None

    def test_get_aspect_by_key_empty_list(self, mock_importer):
        """Test handling of empty list value."""
        aspects = {"Brand": []}

        result = mock_importer._get_aspect_by_key(aspects, "brand")

        assert result is None

    def test_get_aspect_by_key_multiple_languages(self, mock_importer):
        """Test that any language variant finds the correct key."""
        # Test with French
        aspects_fr = {"Couleur": ["Rouge"]}
        assert mock_importer._get_aspect_by_key(aspects_fr, "color") == "Rouge"

        # Test with British English
        aspects_gb = {"Colour": ["Red"]}
        assert mock_importer._get_aspect_by_key(aspects_gb, "color") == "Red"

        # Test with American English
        aspects_us = {"Color": ["Blue"]}
        assert mock_importer._get_aspect_by_key(aspects_us, "color") == "Blue"


class TestEbayImporterIntegration:
    """Integration-style tests for EbayImporter."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        return MagicMock()

    def test_init_loads_aspect_mapping(self, mock_session):
        """
        Test that constructor loads aspect mapping from DB.
        """
        with patch(
            "services.ebay.ebay_importer.EbayInventoryClient"
        ) as MockInventory, patch(
            "services.ebay.ebay_importer.EbayOfferClient"
        ) as MockOffer, patch(
            "services.ebay.ebay_importer.AspectMapping"
        ) as MockAspect:
            MockAspect.get_reverse_mapping.return_value = {
                "Brand": "brand",
                "Marque": "brand",
            }

            from services.ebay.ebay_importer import EbayImporter
            importer = EbayImporter(mock_session, user_id=1, marketplace_id="EBAY_FR")

            MockAspect.get_reverse_mapping.assert_called_once_with(mock_session)
            assert importer._aspect_reverse_map == {"Brand": "brand", "Marque": "brand"}
            assert importer.marketplace_id == "EBAY_FR"
            assert importer.user_id == 1
