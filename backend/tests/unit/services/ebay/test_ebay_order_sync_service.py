"""
Unit tests for EbayOrderSyncService.

Tests the eBay order synchronization service including:
- Order fetching from eBay Fulfillment API
- Order creation and updates in database
- Data mapping from API to model
- Date range filtering
- Error handling and statistics
- Line item processing

Author: Claude
Date: 2026-01-08
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, Mock, call, patch

import pytest


class TestEbayOrderSyncServiceInit:
    """Tests for EbayOrderSyncService initialization."""

    def test_init_creates_fulfillment_client(self):
        """Test that __init__ creates EbayFulfillmentClient."""
        mock_db = MagicMock()

        with patch(
            "services.ebay.ebay_order_sync_service.EbayFulfillmentClient"
        ) as MockClient:
            from services.ebay.ebay_order_sync_service import EbayOrderSyncService

            service = EbayOrderSyncService(mock_db, user_id=1)

            MockClient.assert_called_once_with(mock_db, 1)
            assert service.db == mock_db
            assert service.user_id == 1

    def test_init_stores_user_id(self):
        """Test that user_id is stored correctly."""
        mock_db = MagicMock()

        with patch(
            "services.ebay.ebay_order_sync_service.EbayFulfillmentClient"
        ):
            from services.ebay.ebay_order_sync_service import EbayOrderSyncService

            service = EbayOrderSyncService(mock_db, user_id=42)

            assert service.user_id == 42


class TestSyncOrders:
    """Tests for sync_orders method."""

    @pytest.fixture
    def mock_service(self):
        """Create a mock EbayOrderSyncService."""
        with patch(
            "services.ebay.ebay_order_sync_service.EbayFulfillmentClient"
        ) as MockClient:
            from services.ebay.ebay_order_sync_service import EbayOrderSyncService

            mock_db = MagicMock()
            service = EbayOrderSyncService(mock_db, user_id=1)
            service.fulfillment_client = MagicMock()
            return service

    def test_sync_orders_success_with_date_range(self, mock_service):
        """Test successful sync with date range filter."""
        api_orders = [
            {
                "orderId": "12-00001-00001",
                "buyer": {"username": "buyer1"},
                "pricingSummary": {"total": {"value": "50.00", "currency": "EUR"}},
                "lineItems": [],
            },
            {
                "orderId": "12-00001-00002",
                "buyer": {"username": "buyer2"},
                "pricingSummary": {"total": {"value": "75.00", "currency": "EUR"}},
                "lineItems": [],
            },
        ]

        mock_service.fulfillment_client.get_orders_by_date_range.return_value = (
            api_orders
        )

        with patch(
            "services.ebay.ebay_order_sync_service.EbayOrderRepository"
        ) as MockRepo:
            MockRepo.get_by_ebay_order_id.return_value = None  # New orders
            MockRepo.create.return_value = MagicMock(id=1)

            result = mock_service.sync_orders(modified_since_hours=24)

            assert result["total_fetched"] == 2
            assert result["created"] == 2
            assert result["updated"] == 0
            assert result["errors"] == 0
            mock_service.db.commit.assert_called_once()

    def test_sync_orders_all_orders_when_hours_is_zero(self, mock_service):
        """Test sync all orders when hours is 0."""
        api_orders = [
            {"orderId": "12-all-001", "buyer": {}, "pricingSummary": {}, "lineItems": []},
        ]

        mock_service.fulfillment_client.get_all_orders.return_value = api_orders

        with patch(
            "services.ebay.ebay_order_sync_service.EbayOrderRepository"
        ) as MockRepo:
            MockRepo.get_by_ebay_order_id.return_value = None
            MockRepo.create.return_value = MagicMock(id=1)

            result = mock_service.sync_orders(modified_since_hours=0)

            mock_service.fulfillment_client.get_all_orders.assert_called_once_with(
                status=None
            )
            assert result["total_fetched"] == 1

    def test_sync_orders_all_orders_when_hours_is_none(self, mock_service):
        """Test sync all orders when hours is None."""
        api_orders = []
        mock_service.fulfillment_client.get_all_orders.return_value = api_orders

        with patch(
            "services.ebay.ebay_order_sync_service.EbayOrderRepository"
        ):
            result = mock_service.sync_orders(modified_since_hours=None)

            mock_service.fulfillment_client.get_all_orders.assert_called_once()
            assert result["total_fetched"] == 0

    def test_sync_orders_with_status_filter(self, mock_service):
        """Test sync with status filter."""
        api_orders = [
            {
                "orderId": "12-pending-001",
                "buyer": {},
                "pricingSummary": {},
                "lineItems": [],
                "orderFulfillmentStatus": "NOT_STARTED",
            },
        ]

        mock_service.fulfillment_client.get_orders_by_date_range.return_value = (
            api_orders
        )

        with patch(
            "services.ebay.ebay_order_sync_service.EbayOrderRepository"
        ) as MockRepo:
            MockRepo.get_by_ebay_order_id.return_value = None
            MockRepo.create.return_value = MagicMock(id=1)

            result = mock_service.sync_orders(
                modified_since_hours=24, status_filter="NOT_STARTED"
            )

            mock_service.fulfillment_client.get_orders_by_date_range.assert_called_once()
            call_args = (
                mock_service.fulfillment_client.get_orders_by_date_range.call_args
            )
            assert call_args[1]["status"] == "NOT_STARTED"

    def test_sync_orders_invalid_hours_raises_value_error(self, mock_service):
        """Test that invalid hours raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            mock_service.sync_orders(modified_since_hours=1000)

        assert "720" in str(exc_info.value)
        assert "1" in str(exc_info.value)

    def test_sync_orders_negative_hours_raises_value_error(self, mock_service):
        """Test that negative hours raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            mock_service.sync_orders(modified_since_hours=-5)

        assert "720" in str(exc_info.value)

    def test_sync_orders_updates_existing_order(self, mock_service):
        """Test that existing orders are updated."""
        api_orders = [
            {
                "orderId": "12-existing-001",
                "buyer": {"username": "updated_buyer"},
                "pricingSummary": {"total": {"value": "100.00", "currency": "EUR"}},
                "lineItems": [],
            },
        ]

        mock_service.fulfillment_client.get_orders_by_date_range.return_value = (
            api_orders
        )

        existing_order = MagicMock()
        existing_order.products = []

        with patch(
            "services.ebay.ebay_order_sync_service.EbayOrderRepository"
        ) as MockRepo:
            MockRepo.get_by_ebay_order_id.return_value = existing_order
            MockRepo.update.return_value = existing_order

            result = mock_service.sync_orders(modified_since_hours=24)

            assert result["updated"] == 1
            assert result["created"] == 0
            MockRepo.update.assert_called_once()

    def test_sync_orders_handles_processing_error(self, mock_service):
        """Test that order processing errors are captured in stats."""
        api_orders = [
            {
                "orderId": "12-error-001",
                "buyer": {},
                "pricingSummary": {},
                "lineItems": [],
            },
        ]

        mock_service.fulfillment_client.get_orders_by_date_range.return_value = (
            api_orders
        )

        with patch(
            "services.ebay.ebay_order_sync_service.EbayOrderRepository"
        ) as MockRepo:
            MockRepo.get_by_ebay_order_id.side_effect = Exception("DB error")

            result = mock_service.sync_orders(modified_since_hours=24)

            assert result["errors"] == 1
            assert result["created"] == 0
            assert len(result["details"]) == 1
            assert result["details"][0]["action"] == "error"

    def test_sync_orders_rollback_on_fatal_error(self, mock_service):
        """Test that fatal errors trigger rollback."""
        mock_service.fulfillment_client.get_orders_by_date_range.side_effect = (
            Exception("API failure")
        )

        with pytest.raises(Exception) as exc_info:
            mock_service.sync_orders(modified_since_hours=24)

        mock_service.db.rollback.assert_called_once()
        assert "API failure" in str(exc_info.value)

    def test_sync_orders_empty_result(self, mock_service):
        """Test sync with no orders from API."""
        mock_service.fulfillment_client.get_orders_by_date_range.return_value = []

        with patch(
            "services.ebay.ebay_order_sync_service.EbayOrderRepository"
        ):
            result = mock_service.sync_orders(modified_since_hours=24)

            assert result["total_fetched"] == 0
            assert result["created"] == 0
            assert result["updated"] == 0
            assert result["details"] == []


class TestProcessSingleOrder:
    """Tests for _process_single_order method."""

    @pytest.fixture
    def mock_service(self):
        """Create a mock EbayOrderSyncService."""
        with patch(
            "services.ebay.ebay_order_sync_service.EbayFulfillmentClient"
        ):
            from services.ebay.ebay_order_sync_service import EbayOrderSyncService

            mock_db = MagicMock()
            service = EbayOrderSyncService(mock_db, user_id=1)
            return service

    def test_process_single_order_creates_new(self, mock_service):
        """Test processing creates new order when not exists."""
        api_order = {
            "orderId": "12-new-001",
            "buyer": {"username": "new_buyer"},
            "pricingSummary": {
                "total": {"value": "50.00", "currency": "EUR"},
                "deliveryCost": {"value": "5.00", "currency": "EUR"},
            },
            "lineItems": [],
        }

        with patch(
            "services.ebay.ebay_order_sync_service.EbayOrderRepository"
        ) as MockRepo:
            MockRepo.get_by_ebay_order_id.return_value = None
            MockRepo.create.return_value = MagicMock(id=1)

            result = mock_service._process_single_order(api_order)

            assert result["order_id"] == "12-new-001"
            assert result["action"] == "created"
            MockRepo.create.assert_called_once()

    def test_process_single_order_updates_existing(self, mock_service):
        """Test processing updates existing order."""
        api_order = {
            "orderId": "12-existing-001",
            "buyer": {"username": "updated_buyer"},
            "pricingSummary": {"total": {"value": "100.00", "currency": "EUR"}},
            "lineItems": [],
        }

        existing_order = MagicMock()
        existing_order.products = []

        with patch(
            "services.ebay.ebay_order_sync_service.EbayOrderRepository"
        ) as MockRepo:
            MockRepo.get_by_ebay_order_id.return_value = existing_order
            MockRepo.update.return_value = existing_order

            result = mock_service._process_single_order(api_order)

            assert result["order_id"] == "12-existing-001"
            assert result["action"] == "updated"
            MockRepo.update.assert_called_once()

    def test_process_single_order_missing_order_id_raises(self, mock_service):
        """Test processing raises error when orderId is missing."""
        api_order = {"buyer": {"username": "test"}}

        with pytest.raises(ValueError) as exc_info:
            mock_service._process_single_order(api_order)

        assert "orderId" in str(exc_info.value)

    def test_process_single_order_with_line_items(self, mock_service):
        """Test processing creates line items."""
        api_order = {
            "orderId": "12-items-001",
            "buyer": {},
            "pricingSummary": {},
            "lineItems": [
                {
                    "lineItemId": "item-001",
                    "sku": "12345-FR",
                    "title": "Test Product",
                    "quantity": 1,
                    "lineItemCost": {"value": "45.00", "currency": "EUR"},
                    "total": {"value": "45.00", "currency": "EUR"},
                },
            ],
        }

        with patch(
            "services.ebay.ebay_order_sync_service.EbayOrderRepository"
        ) as MockRepo:
            MockRepo.get_by_ebay_order_id.return_value = None
            MockRepo.create.return_value = MagicMock(id=1)

            result = mock_service._process_single_order(api_order)

            # Verify line item creation was called
            MockRepo.create_order_product.assert_called_once()

    def test_process_single_order_deletes_old_products_on_update(self, mock_service):
        """Test that existing products are deleted on update."""
        api_order = {
            "orderId": "12-update-001",
            "buyer": {},
            "pricingSummary": {},
            "lineItems": [
                {"lineItemId": "new-item", "sku": "NEW-SKU", "title": "New Product"},
            ],
        }

        old_product = MagicMock()
        existing_order = MagicMock()
        existing_order.products = [old_product]

        with patch(
            "services.ebay.ebay_order_sync_service.EbayOrderRepository"
        ) as MockRepo:
            MockRepo.get_by_ebay_order_id.return_value = existing_order
            MockRepo.update.return_value = existing_order

            mock_service._process_single_order(api_order)

            # Verify old product was deleted
            mock_service.db.delete.assert_called_with(old_product)


class TestMapApiOrderToModel:
    """Tests for _map_api_order_to_model method."""

    @pytest.fixture
    def mock_service(self):
        """Create a mock EbayOrderSyncService."""
        with patch(
            "services.ebay.ebay_order_sync_service.EbayFulfillmentClient"
        ):
            from services.ebay.ebay_order_sync_service import EbayOrderSyncService

            mock_db = MagicMock()
            service = EbayOrderSyncService(mock_db, user_id=1)
            return service

    def test_map_api_order_basic_fields(self, mock_service):
        """Test mapping basic order fields."""
        api_order = {
            "orderId": "12-test-001",
            "listingMarketplaceId": "EBAY_FR",
            "buyer": {
                "username": "test_buyer",
                "taxAddress": {"email": "buyer@example.com"},
            },
            "pricingSummary": {
                "total": {"value": "100.00", "currency": "EUR"},
                "deliveryCost": {"value": "10.00", "currency": "EUR"},
            },
            "orderFulfillmentStatus": "NOT_STARTED",
            "orderPaymentStatus": "PAID",
            "creationDate": "2024-12-10T10:30:00.000Z",
            "paidDate": "2024-12-10T10:35:00.000Z",
        }

        result = mock_service._map_api_order_to_model(api_order)

        assert result["order_id"] == "12-test-001"
        assert result["marketplace_id"] == "EBAY_FR"
        assert result["buyer_username"] == "test_buyer"
        assert result["buyer_email"] == "buyer@example.com"
        assert result["total_price"] == 100.00
        assert result["currency"] == "EUR"
        assert result["shipping_cost"] == 10.00
        assert result["order_fulfillment_status"] == "NOT_STARTED"
        assert result["order_payment_status"] == "PAID"

    def test_map_api_order_with_shipping_address(self, mock_service):
        """Test mapping order with shipping address."""
        api_order = {
            "orderId": "12-shipping-001",
            "buyer": {},
            "pricingSummary": {},
            "fulfillmentStartInstructions": [
                {
                    "shippingStep": {
                        "shipTo": {
                            "fullName": "John Doe",
                            "contactAddress": {
                                "addressLine1": "123 Main St",
                                "addressLine2": "Apt 4",
                                "city": "Paris",
                                "postalCode": "75001",
                                "countryCode": "FR",
                            },
                        }
                    }
                }
            ],
        }

        result = mock_service._map_api_order_to_model(api_order)

        assert result["shipping_name"] == "John Doe"
        assert result["shipping_address"] == "123 Main St, Apt 4"
        assert result["shipping_city"] == "Paris"
        assert result["shipping_postal_code"] == "75001"
        assert result["shipping_country"] == "FR"

    def test_map_api_order_missing_optional_fields(self, mock_service):
        """Test mapping order with missing optional fields."""
        api_order = {
            "orderId": "12-minimal-001",
            "buyer": {},
            "pricingSummary": {},
        }

        result = mock_service._map_api_order_to_model(api_order)

        assert result["order_id"] == "12-minimal-001"
        assert result["buyer_username"] is None
        assert result["buyer_email"] is None
        assert result["total_price"] is None


class TestMapLineItems:
    """Tests for _map_line_items method."""

    @pytest.fixture
    def mock_service(self):
        """Create a mock EbayOrderSyncService."""
        with patch(
            "services.ebay.ebay_order_sync_service.EbayFulfillmentClient"
        ):
            from services.ebay.ebay_order_sync_service import EbayOrderSyncService

            mock_db = MagicMock()
            service = EbayOrderSyncService(mock_db, user_id=1)
            return service

    def test_map_line_items_single_item(self, mock_service):
        """Test mapping a single line item."""
        line_items = [
            {
                "lineItemId": "item-001",
                "sku": "12345-FR",
                "title": "Test Product",
                "quantity": 1,
                "lineItemCost": {"value": "45.00", "currency": "EUR"},
                "total": {"value": "45.00", "currency": "EUR"},
                "legacyItemId": "legacy-123",
            }
        ]

        result = mock_service._map_line_items(line_items, "12-test-001")

        assert len(result) == 1
        product = result[0]
        assert product.order_id == "12-test-001"
        assert product.line_item_id == "item-001"
        assert product.sku == "12345-FR"
        assert product.sku_original == "12345"  # Derived from SKU
        assert product.title == "Test Product"
        assert product.quantity == 1
        assert product.unit_price == 45.00
        assert product.total_price == 45.00
        assert product.currency == "EUR"
        assert product.legacy_item_id == "legacy-123"

    def test_map_line_items_multiple_items(self, mock_service):
        """Test mapping multiple line items."""
        line_items = [
            {"lineItemId": "item-001", "sku": "SKU1-FR", "title": "Product 1"},
            {"lineItemId": "item-002", "sku": "SKU2-DE", "title": "Product 2"},
            {"lineItemId": "item-003", "sku": "SKU3-GB", "title": "Product 3"},
        ]

        result = mock_service._map_line_items(line_items, "12-multi-001")

        assert len(result) == 3
        assert result[0].line_item_id == "item-001"
        assert result[1].line_item_id == "item-002"
        assert result[2].line_item_id == "item-003"

    def test_map_line_items_sku_without_dash(self, mock_service):
        """Test mapping line item with SKU without dash."""
        line_items = [
            {"lineItemId": "item-001", "sku": "SIMPLESKU", "title": "Simple Product"},
        ]

        result = mock_service._map_line_items(line_items, "12-simple-001")

        assert result[0].sku == "SIMPLESKU"
        assert result[0].sku_original is None  # No dash, no original

    def test_map_line_items_empty_list(self, mock_service):
        """Test mapping empty line items list."""
        result = mock_service._map_line_items([], "12-empty-001")

        assert len(result) == 0


class TestHelperMethods:
    """Tests for helper methods."""

    @pytest.fixture
    def mock_service(self):
        """Create a mock EbayOrderSyncService."""
        with patch(
            "services.ebay.ebay_order_sync_service.EbayFulfillmentClient"
        ):
            from services.ebay.ebay_order_sync_service import EbayOrderSyncService

            mock_db = MagicMock()
            service = EbayOrderSyncService(mock_db, user_id=1)
            return service

    def test_format_address_full(self, mock_service):
        """Test formatting full address."""
        from services.ebay.ebay_order_sync_service import EbayOrderSyncService

        address = {
            "addressLine1": "123 Main St",
            "addressLine2": "Apt 4B",
        }

        result = EbayOrderSyncService._format_address(address)

        assert result == "123 Main St, Apt 4B"

    def test_format_address_line1_only(self, mock_service):
        """Test formatting address with only line 1."""
        from services.ebay.ebay_order_sync_service import EbayOrderSyncService

        address = {"addressLine1": "123 Main St"}

        result = EbayOrderSyncService._format_address(address)

        assert result == "123 Main St"

    def test_format_address_empty(self, mock_service):
        """Test formatting empty address."""
        from services.ebay.ebay_order_sync_service import EbayOrderSyncService

        result = EbayOrderSyncService._format_address({})

        assert result is None

    def test_format_address_none(self, mock_service):
        """Test formatting None address."""
        from services.ebay.ebay_order_sync_service import EbayOrderSyncService

        result = EbayOrderSyncService._format_address(None)

        assert result is None

    def test_parse_date_valid_iso(self, mock_service):
        """Test parsing valid ISO 8601 date."""
        from services.ebay.ebay_order_sync_service import EbayOrderSyncService

        date_str = "2024-12-10T10:30:00.000Z"

        result = EbayOrderSyncService._parse_date(date_str)

        assert isinstance(result, datetime)
        assert result.year == 2024
        assert result.month == 12
        assert result.day == 10
        assert result.hour == 10
        assert result.minute == 30

    def test_parse_date_none(self, mock_service):
        """Test parsing None date."""
        from services.ebay.ebay_order_sync_service import EbayOrderSyncService

        result = EbayOrderSyncService._parse_date(None)

        assert result is None

    def test_parse_date_invalid(self, mock_service):
        """Test parsing invalid date returns None."""
        from services.ebay.ebay_order_sync_service import EbayOrderSyncService

        result = EbayOrderSyncService._parse_date("not-a-date")

        assert result is None

    def test_parse_float_valid(self, mock_service):
        """Test parsing valid float string."""
        from services.ebay.ebay_order_sync_service import EbayOrderSyncService

        result = EbayOrderSyncService._parse_float("123.45")

        assert result == 123.45

    def test_parse_float_none(self, mock_service):
        """Test parsing None float."""
        from services.ebay.ebay_order_sync_service import EbayOrderSyncService

        result = EbayOrderSyncService._parse_float(None)

        assert result is None

    def test_parse_float_invalid(self, mock_service):
        """Test parsing invalid float returns None."""
        from services.ebay.ebay_order_sync_service import EbayOrderSyncService

        result = EbayOrderSyncService._parse_float("not-a-number")

        assert result is None

    def test_parse_float_integer_string(self, mock_service):
        """Test parsing integer string as float."""
        from services.ebay.ebay_order_sync_service import EbayOrderSyncService

        result = EbayOrderSyncService._parse_float("100")

        assert result == 100.0
