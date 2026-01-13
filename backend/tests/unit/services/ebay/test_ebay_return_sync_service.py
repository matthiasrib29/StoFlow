"""
Unit tests for EbayReturnSyncService.

Tests the sync service that fetches returns from eBay API and stores in local DB.

Author: Claude
Date: 2026-01-13
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest


class TestEbayReturnSyncService:
    """Tests for EbayReturnSyncService."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock()
        db.commit = MagicMock()
        db.rollback = MagicMock()
        return db

    @pytest.fixture
    def mock_service(self, mock_db):
        """Create mock EbayReturnSyncService without calling __init__."""
        with patch(
            "services.ebay.ebay_return_sync_service.EbayReturnSyncService.__init__",
            return_value=None,
        ):
            from services.ebay.ebay_return_sync_service import EbayReturnSyncService

            service = EbayReturnSyncService.__new__(EbayReturnSyncService)
            service.db = mock_db
            service.user_id = 1
            service.return_client = MagicMock()
            return service

    def test_sync_returns_basic(self, mock_service):
        """Test basic return sync."""
        api_returns = [
            {
                "returnId": "5000012345",
                "orderId": "12-34567-89012",
                "state": "OPEN",
                "status": "RETURN_REQUESTED",
            }
        ]

        mock_service.return_client.get_returns_by_date_range.return_value = api_returns

        with patch(
            "services.ebay.ebay_return_sync_service.EbayReturnRepository"
        ) as mock_repo:
            mock_repo.get_by_ebay_return_id.return_value = None
            mock_repo.create.return_value = MagicMock()

            result = mock_service.sync_returns(days_back=30)

            assert result["created"] == 1
            assert result["updated"] == 0
            assert result["total_fetched"] == 1
            mock_service.db.commit.assert_called_once()

    def test_sync_returns_update_existing(self, mock_service):
        """Test sync updates existing returns."""
        api_returns = [
            {
                "returnId": "5000012345",
                "state": "OPEN",
                "status": "RETURN_ITEM_SHIPPED",
            }
        ]

        mock_service.return_client.get_returns_by_date_range.return_value = api_returns

        with patch(
            "services.ebay.ebay_return_sync_service.EbayReturnRepository"
        ) as mock_repo:
            existing_return = MagicMock()
            existing_return.return_id = "5000012345"
            mock_repo.get_by_ebay_return_id.return_value = existing_return
            mock_repo.update.return_value = existing_return

            result = mock_service.sync_returns(days_back=30)

            assert result["created"] == 0
            assert result["updated"] == 1

    def test_sync_returns_invalid_days_back(self, mock_service):
        """Test sync raises error for invalid days_back."""
        with pytest.raises(ValueError, match="days_back must be between 1 and 120"):
            mock_service.sync_returns(days_back=0)

        with pytest.raises(ValueError, match="days_back must be between 1 and 120"):
            mock_service.sync_returns(days_back=150)

    def test_sync_returns_handles_errors(self, mock_service):
        """Test sync handles individual return processing errors."""
        api_returns = [
            {"returnId": "5000012345", "state": "OPEN"},
            {},  # Missing returnId - will error
            {"returnId": "5000012347", "state": "OPEN"},
        ]

        mock_service.return_client.get_returns_by_date_range.return_value = api_returns

        with patch(
            "services.ebay.ebay_return_sync_service.EbayReturnRepository"
        ) as mock_repo:
            mock_repo.get_by_ebay_return_id.return_value = None
            mock_repo.create.return_value = MagicMock()

            result = mock_service.sync_returns(days_back=30)

            assert result["created"] == 2
            assert result["errors"] == 1

    def test_sync_open_returns(self, mock_service):
        """Test convenience method for syncing open returns."""
        with patch.object(mock_service, "sync_returns") as mock_sync:
            mock_sync.return_value = {"created": 1, "updated": 0}

            result = mock_service.sync_open_returns()

            mock_sync.assert_called_once_with(return_state="OPEN", days_back=90)

    def test_map_api_return_to_model(self, mock_service):
        """Test API return mapping to model fields."""
        api_return = {
            "returnId": "5000012345",
            "orderId": "12-34567-89012",
            "state": "OPEN",
            "status": "RETURN_REQUESTED",
            "returnType": "RETURN",
            "returnReason": "NOT_AS_DESCRIBED",
            "returnReasonDescription": "Item color is different",
            "refundAmount": {"value": "50.00", "currency": "EUR"},
            "refundStatus": "PENDING",
            "buyer": {"username": "buyer123"},
            "buyerComments": "Please refund",
            "sellerComments": None,
            "RMANumber": "RMA-001",
            "returnShipment": {
                "shipmentTracking": {
                    "trackingNumber": "1Z999AA10123456784",
                    "carrier": "UPS",
                }
            },
            "creationDate": "2026-01-10T10:00:00.000Z",
            "closedDate": None,
            "sellerResponseDue": {"deadline": "2026-01-15T10:00:00.000Z"},
        }

        result = mock_service._map_api_return_to_model(api_return)

        assert result["return_id"] == "5000012345"
        assert result["order_id"] == "12-34567-89012"
        assert result["state"] == "OPEN"
        assert result["status"] == "RETURN_REQUESTED"
        assert result["return_type"] == "RETURN"
        assert result["reason"] == "NOT_AS_DESCRIBED"
        assert result["reason_detail"] == "Item color is different"
        assert result["refund_amount"] == 50.0
        assert result["refund_currency"] == "EUR"
        assert result["buyer_username"] == "buyer123"
        assert result["return_tracking_number"] == "1Z999AA10123456784"
        assert result["return_carrier"] == "UPS"
        assert result["rma_number"] == "RMA-001"
        assert result["creation_date"] is not None
        assert result["deadline_date"] is not None
        assert result["raw_data"] == api_return

    def test_parse_date_valid(self, mock_service):
        """Test date parsing with valid ISO 8601 string."""
        date_str = "2026-01-13T10:30:00.000Z"

        result = mock_service._parse_date(date_str)

        assert result is not None
        assert result.year == 2026
        assert result.month == 1
        assert result.day == 13

    def test_parse_date_none(self, mock_service):
        """Test date parsing with None."""
        result = mock_service._parse_date(None)
        assert result is None

    def test_parse_date_invalid(self, mock_service):
        """Test date parsing with invalid string."""
        result = mock_service._parse_date("invalid-date")
        assert result is None

    def test_parse_float_valid(self, mock_service):
        """Test float parsing with valid string."""
        assert mock_service._parse_float("50.00") == 50.0
        assert mock_service._parse_float("0.99") == 0.99

    def test_parse_float_none(self, mock_service):
        """Test float parsing with None."""
        result = mock_service._parse_float(None)
        assert result is None

    def test_parse_float_invalid(self, mock_service):
        """Test float parsing with invalid string."""
        result = mock_service._parse_float("not-a-number")
        assert result is None
