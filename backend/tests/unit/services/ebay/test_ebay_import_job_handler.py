"""
Unit Tests for EbayImportJobHandler

Tests for the eBay import job handler:
- Basic import flow
- Pagination handling
- Cancellation support
- Error handling
- Enrichment with offers

Created: 2026-01-21
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timezone

from services.ebay.jobs.ebay_import_job_handler import EbayImportJobHandler
from models.user.marketplace_job import JobStatus, MarketplaceJob


@pytest.fixture
def mock_db():
    """Mock SQLAlchemy session."""
    db = MagicMock()
    db.execute = MagicMock()
    db.commit = MagicMock()
    db.rollback = MagicMock()
    db.refresh = MagicMock()
    return db


@pytest.fixture
def mock_job():
    """Mock MarketplaceJob."""
    job = MagicMock(spec=MarketplaceJob)
    job.id = 123
    job.status = JobStatus.RUNNING
    job.cancel_requested = False
    job.input_data = {"marketplace_id": "EBAY_FR"}
    job.result_data = {}
    return job


@pytest.fixture
def handler(mock_db):
    """Create handler instance."""
    h = EbayImportJobHandler(db=mock_db)
    h.user_id = 1  # Set user_id after init
    return h


class TestEbayImportJobHandlerBasic:
    """Test basic handler functionality."""

    def test_action_code(self):
        """Should have correct action code."""
        assert EbayImportJobHandler.ACTION_CODE == "import_ebay"

    def test_enrichment_batch_size(self):
        """Should have reasonable batch size."""
        assert EbayImportJobHandler.ENRICHMENT_BATCH_SIZE == 30

    def test_get_service_returns_none(self, handler):
        """Should return None for get_service."""
        assert handler.get_service() is None

    def test_get_service_method_name_returns_empty(self, handler):
        """Should return empty string for service method."""
        assert handler.get_service_method_name() == ""

    def test_create_tasks_returns_empty_list(self, handler, mock_job):
        """Should return empty task list."""
        assert handler.create_tasks(mock_job) == []


class TestEbayImportJobHandlerExecute:
    """Test execute method."""

    @pytest.mark.asyncio
    async def test_execute_empty_inventory(self, handler, mock_db, mock_job):
        """Should handle empty inventory gracefully."""
        with patch("services.ebay.jobs.ebay_import_job_handler.configure_schema_translate_map"):
            with patch("services.ebay.jobs.ebay_import_job_handler.EbayImporter") as MockImporter:
                mock_importer = MagicMock()
                mock_importer.inventory_client.get_inventory_items.return_value = {
                    "inventoryItems": [],
                    "total": 0,
                }
                MockImporter.return_value = mock_importer

                # Mock cleanup query
                mock_cleanup_result = MagicMock()
                mock_cleanup_result.rowcount = 0
                mock_db.execute.return_value = mock_cleanup_result

                result = await handler.execute(mock_job)

        assert result["success"] is True
        assert result["imported"] == 0
        assert result["deleted"] == 0

    @pytest.mark.asyncio
    async def test_execute_single_page(self, handler, mock_db, mock_job):
        """Should import single page of inventory items."""
        with patch("services.ebay.jobs.ebay_import_job_handler.configure_schema_translate_map"):
            with patch("services.ebay.jobs.ebay_import_job_handler.EbayImporter") as MockImporter:
                # Setup mock importer
                mock_importer = MagicMock()
                mock_importer.inventory_client.get_inventory_items.return_value = {
                    "inventoryItems": [
                        {"sku": "SKU001", "product": {"title": "Test 1"}},
                        {"sku": "SKU002", "product": {"title": "Test 2"}},
                    ],
                    "total": 2,
                }

                # Mock import results
                mock_product1 = MagicMock()
                mock_product1.ebay_sku = "SKU001"
                mock_product2 = MagicMock()
                mock_product2.ebay_sku = "SKU002"

                mock_importer._import_single_item.side_effect = [
                    {"status": "imported", "product": mock_product1},
                    {"status": "imported", "product": mock_product2},
                ]
                mock_importer.fetch_offers_for_sku.return_value = []
                mock_importer.marketplace_id = "EBAY_FR"

                MockImporter.return_value = mock_importer

                # Mock cleanup query
                mock_cleanup_result = MagicMock()
                mock_cleanup_result.rowcount = 0
                mock_db.execute.return_value = mock_cleanup_result

                result = await handler.execute(mock_job)

        assert result["success"] is True
        # Import calls made
        assert mock_importer._import_single_item.call_count == 2

    @pytest.mark.asyncio
    async def test_execute_handles_cancellation(self, handler, mock_db, mock_job):
        """Should stop on job cancellation."""
        mock_job.cancel_requested = True

        with patch("services.ebay.jobs.ebay_import_job_handler.configure_schema_translate_map"):
            with patch("services.ebay.jobs.ebay_import_job_handler.EbayImporter") as MockImporter:
                mock_importer = MagicMock()
                MockImporter.return_value = mock_importer

                # Simulate cancellation check returns True
                with patch.object(handler, "is_cancelled", return_value=True):
                    result = await handler.execute(mock_job)

        assert result["success"] is False
        assert result["error"] == "cancelled"

    @pytest.mark.asyncio
    async def test_execute_handles_api_error(self, handler, mock_db, mock_job):
        """Should handle API errors gracefully."""
        with patch("services.ebay.jobs.ebay_import_job_handler.configure_schema_translate_map"):
            with patch("services.ebay.jobs.ebay_import_job_handler.EbayImporter") as MockImporter:
                mock_importer = MagicMock()
                mock_importer.inventory_client.get_inventory_items.side_effect = Exception("API Error")
                MockImporter.return_value = mock_importer

                result = await handler.execute(mock_job)

        assert result["success"] is False
        assert "API Error" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_pagination(self, handler, mock_db, mock_job):
        """Should handle pagination correctly."""
        with patch("services.ebay.jobs.ebay_import_job_handler.configure_schema_translate_map"):
            with patch("services.ebay.jobs.ebay_import_job_handler.EbayImporter") as MockImporter:
                mock_importer = MagicMock()

                # First call returns page 1 (100 items)
                # Second call returns page 2 (50 items)
                # Pagination stops when offset + limit >= total
                mock_importer.inventory_client.get_inventory_items.side_effect = [
                    {
                        "inventoryItems": [{"sku": f"SKU{i}"} for i in range(100)],
                        "total": 150,
                    },
                    {
                        "inventoryItems": [{"sku": f"SKU{i}"} for i in range(100, 150)],
                        "total": 150,
                    },
                ]

                # Mock products
                mock_product = MagicMock()
                mock_product.ebay_sku = "SKU_TEST"
                mock_importer._import_single_item.return_value = {
                    "status": "imported",
                    "product": mock_product
                }
                mock_importer.fetch_offers_for_sku.return_value = []
                mock_importer.marketplace_id = "EBAY_FR"

                MockImporter.return_value = mock_importer

                # Mock cleanup
                mock_cleanup_result = MagicMock()
                mock_cleanup_result.rowcount = 0
                mock_db.execute.return_value = mock_cleanup_result

                result = await handler.execute(mock_job)

        assert result["success"] is True
        # Should have called inventory API 2 times (pagination stops at offset >= total)
        assert mock_importer.inventory_client.get_inventory_items.call_count == 2


class TestEbayImportJobHandlerEnrichment:
    """Test enrichment functionality."""

    def test_enrich_products_parallel_empty_list(self, handler, mock_db):
        """Should handle empty product list."""
        mock_importer = MagicMock()

        result = handler._enrich_products_parallel(mock_importer, [], "user_1")

        assert result == 0

    def test_apply_offer_to_product_published(self, handler):
        """Should apply offer data to product correctly."""
        product = MagicMock()
        product.quantity = 10
        product.available_quantity = None

        offers = [{
            "offerId": "OFFER123",
            "marketplaceId": "EBAY_FR",
            "status": "PUBLISHED",
            "format": "FIXED_PRICE",
            "listingDuration": "GTC",
            "categoryId": "12345",
            "availableQuantity": 8,
            "listing": {
                "listingId": "LISTING123",
                "soldQuantity": 2,
                "listingStatus": "ACTIVE",
            },
            "pricingSummary": {
                "price": {"value": "29.99", "currency": "EUR"}
            },
        }]

        handler._apply_offer_to_product(product, offers, "EBAY_FR")

        assert product.ebay_offer_id == "OFFER123"
        assert product.ebay_listing_id == "LISTING123"
        assert product.marketplace_id == "EBAY_FR"
        assert product.price == 29.99
        assert product.currency == "EUR"
        assert product.status == "active"
        assert product.availability_type == "IN_STOCK"
        assert product.available_quantity == 8

    def test_apply_offer_to_product_out_of_stock(self, handler):
        """Should set OUT_OF_STOCK status correctly."""
        product = MagicMock()
        product.quantity = 0
        product.available_quantity = 0

        offers = [{
            "offerId": "OFFER123",
            "marketplaceId": "EBAY_FR",
            "status": "PUBLISHED",
            "availableQuantity": 0,
            "listing": {
                "listingId": "LISTING123",
                "listingStatus": "OUT_OF_STOCK",
            },
            "pricingSummary": {},
        }]

        handler._apply_offer_to_product(product, offers, "EBAY_FR")

        assert product.status == "inactive"
        assert product.availability_type == "OUT_OF_STOCK"

    def test_apply_offer_to_product_ended(self, handler):
        """Should handle ENDED offer status."""
        product = MagicMock()
        product.quantity = 0  # Set integer value
        product.available_quantity = 0

        offers = [{
            "offerId": "OFFER123",
            "marketplaceId": "EBAY_FR",
            "status": "ENDED",
            "listing": {},
            "pricingSummary": {},
        }]

        handler._apply_offer_to_product(product, offers, "EBAY_FR")

        assert product.status == "ended"
        assert product.availability_type == "OUT_OF_STOCK"

    def test_apply_offer_to_product_empty_offers(self, handler):
        """Should handle empty offers list."""
        product = MagicMock()

        # Should not crash
        handler._apply_offer_to_product(product, [], "EBAY_FR")
        handler._apply_offer_to_product(product, None, "EBAY_FR")

    def test_apply_offer_selects_correct_marketplace(self, handler):
        """Should prefer offer from configured marketplace."""
        product = MagicMock()
        product.quantity = 5

        offers = [
            {
                "offerId": "OFFER_GB",
                "marketplaceId": "EBAY_GB",
                "status": "PUBLISHED",
                "availableQuantity": 3,
                "listing": {"listingId": "LIST_GB"},
                "pricingSummary": {"price": {"value": "25.00", "currency": "GBP"}},
            },
            {
                "offerId": "OFFER_FR",
                "marketplaceId": "EBAY_FR",
                "status": "PUBLISHED",
                "availableQuantity": 5,
                "listing": {"listingId": "LIST_FR"},
                "pricingSummary": {"price": {"value": "29.99", "currency": "EUR"}},
            },
        ]

        handler._apply_offer_to_product(product, offers, "EBAY_FR")

        # Should select French offer
        assert product.ebay_offer_id == "OFFER_FR"
        assert product.marketplace_id == "EBAY_FR"
        assert product.currency == "EUR"


class TestEbayImportJobHandlerSkipCases:
    """Test cases where items are skipped."""

    @pytest.mark.asyncio
    async def test_execute_skips_items_without_sku(self, handler, mock_db, mock_job):
        """Should skip items without SKU."""
        with patch("services.ebay.jobs.ebay_import_job_handler.configure_schema_translate_map"):
            with patch("services.ebay.jobs.ebay_import_job_handler.EbayImporter") as MockImporter:
                mock_importer = MagicMock()
                mock_importer.inventory_client.get_inventory_items.return_value = {
                    "inventoryItems": [
                        {"sku": "SKU001"},
                        {"sku": ""},  # Empty SKU
                        {},  # No SKU
                    ],
                    "total": 3,
                }

                mock_product = MagicMock()
                mock_product.ebay_sku = "SKU001"
                mock_importer._import_single_item.side_effect = [
                    {"status": "imported", "product": mock_product},
                    {"status": "skipped", "product": None},
                    {"status": "skipped", "product": None},
                ]
                mock_importer.fetch_offers_for_sku.return_value = []
                mock_importer.marketplace_id = "EBAY_FR"

                MockImporter.return_value = mock_importer

                mock_cleanup_result = MagicMock()
                mock_cleanup_result.rowcount = 0
                mock_db.execute.return_value = mock_cleanup_result

                result = await handler.execute(mock_job)

        assert result["success"] is True
        # All 3 items processed (even if some skipped)
        assert mock_importer._import_single_item.call_count == 3

    @pytest.mark.asyncio
    async def test_execute_handles_import_error_per_item(self, handler, mock_db, mock_job):
        """Should continue after per-item import error."""
        with patch("services.ebay.jobs.ebay_import_job_handler.configure_schema_translate_map"):
            with patch("services.ebay.jobs.ebay_import_job_handler.EbayImporter") as MockImporter:
                mock_importer = MagicMock()
                mock_importer.inventory_client.get_inventory_items.return_value = {
                    "inventoryItems": [
                        {"sku": "SKU001"},
                        {"sku": "SKU002"},
                        {"sku": "SKU003"},
                    ],
                    "total": 3,
                }

                mock_product = MagicMock()
                mock_product.ebay_sku = "SKU_TEST"

                # Second item fails
                mock_importer._import_single_item.side_effect = [
                    {"status": "imported", "product": mock_product},
                    Exception("Item import failed"),
                    {"status": "imported", "product": mock_product},
                ]
                mock_importer.fetch_offers_for_sku.return_value = []
                mock_importer.marketplace_id = "EBAY_FR"

                MockImporter.return_value = mock_importer

                mock_cleanup_result = MagicMock()
                mock_cleanup_result.rowcount = 0
                mock_db.execute.return_value = mock_cleanup_result

                result = await handler.execute(mock_job)

        assert result["success"] is True
        # All 3 items attempted
        assert mock_importer._import_single_item.call_count == 3
        # Rollback called for failed item
        mock_db.rollback.assert_called()
