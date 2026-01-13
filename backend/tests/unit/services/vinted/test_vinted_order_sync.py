"""
Unit Tests for VintedOrderSyncService

Tests order synchronization from Vinted API.

Business Rules Tested:
- sync_orders: Sync all history via /my_orders
- sync_orders_by_month: Sync specific month via /wallet/invoices
- Duplicate detection by transaction_id
- Error handling and rollback
- Data extraction from transaction response
- Invoice amount parsing

NOTE (2026-01-13): Tests for commit_and_restore_path and SchemaManager were
removed as part of the schema_translate_map migration. Multi-tenant schema
isolation is now handled by execution_options(schema_translate_map=...) which
survives COMMIT and ROLLBACK automatically.

Created: 2026-01-08
Updated: 2026-01-13
Phase 2.2: Unit testing
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock, patch, AsyncMock

from services.vinted.vinted_order_sync import VintedOrderSyncService


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def mock_db():
    """Mock database session."""
    session = MagicMock()
    session.query = Mock()
    session.add = Mock()
    session.commit = Mock()
    session.rollback = Mock()
    return session


@pytest.fixture
def service():
    """VintedOrderSyncService instance."""
    return VintedOrderSyncService()


@pytest.fixture
def mock_transaction():
    """Mock transaction data from Vinted API."""
    return {
        'id': 12345,
        'status': 400,  # completed
        'buyer': {
            'id': 111,
            'login': 'buyer_user'
        },
        'seller': {
            'id': 222,
            'login': 'seller_user'
        },
        'offer': {
            'price': {'amount': 49.99, 'currency_code': 'EUR'},
            'buyer_protection_fee': {'amount': 2.50, 'currency_code': 'EUR'}
        },
        'shipment': {
            'status': 400,
            'price': {'amount': 4.99, 'currency_code': 'EUR'},
            'tracking_code': 'TRACK123',
            'carrier_name': 'Mondial Relay',
            'shipped_at': '2025-12-15T10:00:00Z',
            'delivered_at': '2025-12-18T14:00:00Z'
        },
        'service_fee': {'amount': 1.50, 'currency_code': 'EUR'},
        'debit_processed_at': '2025-12-14T09:00:00Z',
        'status_updated_at': '2025-12-18T14:00:00Z',
        'order': {
            'items': [
                {
                    'id': 99999,
                    'title': 'Vintage Levi\'s 501',
                    'price': {'amount': 49.99},
                    'size_title': 'W32/L34',
                    'brand_title': 'Levi\'s',
                    'photos': [{'url': 'https://vinted.com/photo1.jpg'}]
                }
            ]
        }
    }


@pytest.fixture
def mock_invoice_line():
    """Mock invoice line from wallet/invoices API."""
    return {
        'entity_type': 'user_msg_thread',
        'title': 'Vente',
        'entity_id': 777,
        'amount': {
            'amount': 42.00,
            'currency_code': 'EUR'
        }
    }


# =============================================================================
# ORDER EXISTS CHECK TESTS
# =============================================================================


class TestOrderExists:
    """Tests for _order_exists method."""

    def test_order_exists_true(self, service, mock_db):
        """Should return True when order exists."""
        mock_db.query.return_value.filter.return_value.first.return_value = Mock()

        result = service._order_exists(mock_db, transaction_id=12345)

        assert result is True

    def test_order_exists_false(self, service, mock_db):
        """Should return False when order does not exist."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = service._order_exists(mock_db, transaction_id=99999)

        assert result is False


# =============================================================================
# SYNC ORDERS TESTS
# =============================================================================


class TestSyncOrders:
    """Tests for sync_orders method."""

    @pytest.mark.asyncio
    @patch('services.vinted.vinted_order_sync.create_and_wait')
    async def test_sync_orders_success(
        self, mock_create_and_wait, service, mock_db, mock_transaction
    ):
        """Should sync orders successfully."""
        # Mock API responses
        mock_create_and_wait.side_effect = [
            # First call: get_orders
            {'my_orders': [{'transaction_id': 12345}]},
            # Second call: get_transaction
            mock_transaction,
            # Third call: get_orders (empty = end)
            {'my_orders': []}
        ]

        # Mock order doesn't exist
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = await service.sync_orders(mock_db)

        assert result['synced'] == 1
        assert result['duplicates'] == 0
        assert result['errors'] == 0

    @pytest.mark.asyncio
    @patch('services.vinted.vinted_order_sync.create_and_wait')
    async def test_sync_orders_handles_duplicates(
        self, mock_create_and_wait, service, mock_db
    ):
        """Should skip duplicate orders."""
        mock_create_and_wait.return_value = {
            'my_orders': [{'transaction_id': 12345}]
        }

        # Mock order already exists
        mock_db.query.return_value.filter.return_value.first.return_value = Mock()

        # Will stop after duplicate threshold reached
        result = await service.sync_orders(mock_db, duplicate_threshold=0.8)

        assert result['duplicates'] >= 1

    @pytest.mark.asyncio
    @patch('services.vinted.vinted_order_sync.create_and_wait')
    async def test_sync_orders_handles_api_error(
        self, mock_create_and_wait, service, mock_db
    ):
        """Should handle API errors gracefully."""
        mock_create_and_wait.side_effect = Exception("API Error")

        result = await service.sync_orders(mock_db)

        assert result['pages'] == 1  # Stopped on first page error

    @pytest.mark.asyncio
    @patch('services.vinted.vinted_order_sync.create_and_wait')
    async def test_sync_orders_empty_response(
        self, mock_create_and_wait, service, mock_db
    ):
        """Should handle empty orders response."""
        mock_create_and_wait.return_value = {'my_orders': []}

        result = await service.sync_orders(mock_db)

        assert result['synced'] == 0
        assert result['pages'] == 1

    @pytest.mark.asyncio
    @patch('services.vinted.vinted_order_sync.create_and_wait')
    async def test_sync_orders_skips_missing_transaction_id(
        self, mock_create_and_wait, service, mock_db
    ):
        """Should skip orders without transaction_id."""
        mock_create_and_wait.side_effect = [
            {'my_orders': [{'no_id': True}]},
            {'my_orders': []}
        ]

        result = await service.sync_orders(mock_db)

        assert result['errors'] == 1
        assert result['synced'] == 0


# =============================================================================
# SYNC ORDERS BY MONTH TESTS
# =============================================================================


class TestSyncOrdersByMonth:
    """Tests for sync_orders_by_month method."""

    @pytest.mark.asyncio
    @patch('services.vinted.vinted_order_sync.create_and_wait')
    async def test_sync_orders_by_month_success(
        self, mock_create_and_wait, service, mock_db, mock_invoice_line, mock_transaction
    ):
        """Should sync orders for specific month."""
        mock_create_and_wait.side_effect = [
            # First: get invoices
            {
                'invoice_lines': [mock_invoice_line],
                'invoice_lines_pagination': {'total_pages': 1}
            },
            # Second: get conversation
            {
                'conversation': {
                    'transaction': {'id': 12345}
                }
            },
            # Third: get transaction details
            {'transaction': mock_transaction}
        ]

        # Mock order doesn't exist
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = await service.sync_orders_by_month(mock_db, year=2025, month=12)

        assert result['synced'] == 1
        assert result['month'] == '2025-12'

    @pytest.mark.asyncio
    @patch('services.vinted.vinted_order_sync.create_and_wait')
    async def test_sync_orders_by_month_filters_non_sales(
        self, mock_create_and_wait, service, mock_db
    ):
        """Should only process sales (entity_type=user_msg_thread + title=Vente)."""
        mock_create_and_wait.return_value = {
            'invoice_lines': [
                {'entity_type': 'other_type', 'title': 'Other', 'entity_id': 1},
                {'entity_type': 'user_msg_thread', 'title': 'Achat', 'entity_id': 2},
            ],
            'invoice_lines_pagination': {'total_pages': 1}
        }

        result = await service.sync_orders_by_month(mock_db, year=2025, month=12)

        assert result['synced'] == 0

    @pytest.mark.asyncio
    @patch('services.vinted.vinted_order_sync.create_and_wait')
    async def test_sync_orders_by_month_handles_pagination(
        self, mock_create_and_wait, service, mock_db, mock_invoice_line
    ):
        """Should handle pagination."""
        mock_create_and_wait.side_effect = [
            # Page 1
            {
                'invoice_lines': [mock_invoice_line],
                'invoice_lines_pagination': {'total_pages': 2}
            },
            # Conversation call
            {'conversation': {'transaction': {'id': 111}}},
            # Transaction call
            {'transaction': {'id': 111}},
            # Page 2
            {
                'invoice_lines': [],
                'invoice_lines_pagination': {'total_pages': 2}
            }
        ]

        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = await service.sync_orders_by_month(mock_db, year=2025, month=12)

        assert result['pages'] == 2


# =============================================================================
# DATA EXTRACTION TESTS
# =============================================================================


class TestExtractOrderFromTransaction:
    """Tests for _extract_order_from_transaction method."""

    def test_extract_order_complete(self, service, mock_transaction):
        """Should extract all order fields from transaction."""
        result = service._extract_order_from_transaction(
            mock_transaction,
            invoice_price=42.00,
            invoice_currency='EUR'
        )

        assert result is not None
        assert result['transaction_id'] == 12345
        assert result['buyer_id'] == 111
        assert result['buyer_login'] == 'buyer_user'
        assert result['seller_id'] == 222
        assert result['seller_login'] == 'seller_user'
        assert result['status'] == 'completed'
        assert result['total_price'] == 49.99
        assert result['shipping_price'] == 4.99
        assert result['service_fee'] == 1.50
        assert result['buyer_protection_fee'] == 2.50
        assert result['seller_revenue'] == 42.00
        assert result['tracking_number'] == 'TRACK123'
        assert result['carrier'] == 'Mondial Relay'

    def test_extract_order_pending_status(self, service):
        """Should set status to pending for status < 400."""
        transaction = {
            'id': 12345,
            'status': 200,  # pending
            'buyer': {},
            'seller': {},
            'offer': {},
            'shipment': {}
        }

        result = service._extract_order_from_transaction(transaction, None, 'EUR')

        assert result['status'] == 'pending'

    def test_extract_order_no_id_returns_none(self, service):
        """Should return None if no transaction ID."""
        transaction = {'status': 400}

        result = service._extract_order_from_transaction(transaction, None, 'EUR')

        assert result is None

    def test_extract_order_shipped_at(self, service):
        """Should set shipped_at when shipment status >= 200."""
        transaction = {
            'id': 12345,
            'status': 300,
            'buyer': {},
            'seller': {},
            'offer': {},
            'shipment': {
                'status': 200,
                'shipped_at': '2025-12-15T10:00:00Z'
            }
        }

        result = service._extract_order_from_transaction(transaction, None, 'EUR')

        assert result['shipped_at'] == '2025-12-15T10:00:00Z'

    def test_extract_order_delivered_at(self, service):
        """Should set delivered_at when shipment status >= 400."""
        transaction = {
            'id': 12345,
            'status': 400,
            'buyer': {},
            'seller': {},
            'offer': {},
            'shipment': {
                'status': 400,
                'delivered_at': '2025-12-18T14:00:00Z'
            }
        }

        result = service._extract_order_from_transaction(transaction, None, 'EUR')

        assert result['delivered_at'] == '2025-12-18T14:00:00Z'


class TestExtractProductsFromTransaction:
    """Tests for _extract_products_from_transaction method."""

    def test_extract_products_with_items(self, service, mock_transaction):
        """Should extract products from order.items."""
        products = service._extract_products_from_transaction(mock_transaction)

        assert len(products) == 1
        assert products[0]['vinted_item_id'] == 99999
        assert products[0]['title'] == "Vintage Levi's 501"
        assert products[0]['price'] == 49.99
        assert products[0]['size'] == 'W32/L34'
        assert products[0]['brand'] == "Levi's"
        assert products[0]['photo_url'] == 'https://vinted.com/photo1.jpg'

    def test_extract_products_bundle(self, service):
        """Should extract multiple products from bundle."""
        transaction = {
            'id': 12345,
            'order': {
                'items': [
                    {'id': 1, 'title': 'Item 1', 'price': {'amount': 20}},
                    {'id': 2, 'title': 'Item 2', 'price': {'amount': 30}},
                    {'id': 3, 'title': 'Item 3', 'price': {'amount': 25}}
                ]
            }
        }

        products = service._extract_products_from_transaction(transaction)

        assert len(products) == 3
        assert products[0]['title'] == 'Item 1'
        assert products[1]['title'] == 'Item 2'
        assert products[2]['title'] == 'Item 3'

    def test_extract_products_fallback_single_item(self, service):
        """Should fallback to item_id when no order.items."""
        transaction = {
            'id': 12345,
            'item_id': 55555,
            'item_title': 'Single Item',
            'order': {}
        }

        products = service._extract_products_from_transaction(transaction)

        assert len(products) == 1
        assert products[0]['vinted_item_id'] == 55555
        assert products[0]['title'] == 'Single Item'

    def test_extract_products_no_id_returns_empty(self, service):
        """Should return empty list if no transaction ID."""
        transaction = {'order': {'items': []}}

        products = service._extract_products_from_transaction(transaction)

        assert products == []

    def test_extract_products_brand_from_brand_object(self, service):
        """Should extract brand from brand object if no brand_title."""
        transaction = {
            'id': 12345,
            'order': {
                'items': [
                    {
                        'id': 1,
                        'title': 'Item',
                        'brand': {'title': 'Nike', 'name': 'Nike Inc'}
                    }
                ]
            }
        }

        products = service._extract_products_from_transaction(transaction)

        assert products[0]['brand'] == 'Nike'


# =============================================================================
# PARSE AMOUNT TESTS
# =============================================================================


class TestParseAmount:
    """Tests for _parse_amount method."""

    def test_parse_amount_dict(self, service):
        """Should parse amount from dict."""
        price_obj = {'amount': 49.99, 'currency_code': 'EUR'}

        result = service._parse_amount(price_obj)

        assert result == 49.99

    def test_parse_amount_string(self, service):
        """Should parse amount from string."""
        result = service._parse_amount("29.99")

        assert result == 29.99

    def test_parse_amount_none(self, service):
        """Should return None for None input."""
        result = service._parse_amount(None)

        assert result is None

    def test_parse_amount_invalid_dict(self, service):
        """Should return None for invalid dict."""
        result = service._parse_amount({'invalid': 'data'})

        assert result == 0.0  # dict.get('amount', 0) returns 0

    def test_parse_amount_invalid_string(self, service):
        """Should return None for invalid string."""
        result = service._parse_amount("not_a_number")

        assert result is None


# =============================================================================
# SAVE ORDER TESTS
# =============================================================================


class TestSaveOrder:
    """Tests for _save_order method."""

    @patch('services.vinted.vinted_order_sync.VintedDataExtractor')
    def test_save_order_creates_order(self, mock_extractor, service, mock_db):
        """Should create VintedOrder in database."""
        mock_extractor.parse_date.return_value = None

        order_data = {
            'transaction_id': 12345,
            'buyer_id': 111,
            'buyer_login': 'buyer',
            'seller_id': 222,
            'seller_login': 'seller',
            'status': 'completed',
            'total_price': 49.99,
            'currency': 'EUR',
            'shipping_price': 4.99,
            'service_fee': 1.50,
            'buyer_protection_fee': 2.50,
            'seller_revenue': 42.00,
            'tracking_number': 'TRACK123',
            'carrier': 'Mondial Relay'
        }

        service._save_order(mock_db, order_data, [])

        # Should add order
        mock_db.add.assert_called()

    @patch('services.vinted.vinted_order_sync.VintedDataExtractor')
    def test_save_order_creates_products(self, mock_extractor, service, mock_db):
        """Should create VintedOrderProduct entries."""
        mock_extractor.parse_date.return_value = None

        order_data = {'transaction_id': 12345, 'currency': 'EUR'}
        products_data = [
            {
                'transaction_id': 12345,
                'vinted_item_id': 99999,
                'title': 'Product 1',
                'price': 20.00
            },
            {
                'transaction_id': 12345,
                'vinted_item_id': 88888,
                'title': 'Product 2',
                'price': 30.00
            }
        ]

        service._save_order(mock_db, order_data, products_data)

        # Should add order + 2 products = 3 calls
        assert mock_db.add.call_count == 3


# =============================================================================
# NOTE (2026-01-13): TestSchemaManager class removed
# =============================================================================
# The TestSchemaManager class was removed as part of the schema_translate_map
# migration (Phase 5). The service no longer uses SchemaManager or
# commit_and_restore_path() because:
#
# 1. schema_translate_map survives COMMIT and ROLLBACK automatically
# 2. No need for explicit schema capture/restore logic
# 3. Multi-tenant schema is configured at session creation via get_user_db()
#
# Schema isolation tests are now in tests/unit/shared/test_schema_translate_map.py
