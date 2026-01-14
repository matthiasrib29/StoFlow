"""
Unit tests for EbayReturnService.

Tests the return service that provides business logic for return operations.

Author: Claude
Date: 2026-01-13
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest


class TestEbayReturnServiceReadOperations:
    """Tests for EbayReturnService read operations."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock()
        db.commit = MagicMock()
        db.rollback = MagicMock()
        return db

    @pytest.fixture
    def mock_service(self, mock_db):
        """Create mock EbayReturnService without calling __init__."""
        with patch(
            "services.ebay.ebay_return_service.EbayReturnService.__init__",
            return_value=None,
        ):
            from services.ebay.ebay_return_service import EbayReturnService

            service = EbayReturnService.__new__(EbayReturnService)
            service.db = mock_db
            service.user_id = 1
            service.return_client = MagicMock()
            return service

    def test_get_return(self, mock_service):
        """Test get return by internal ID."""
        mock_return = MagicMock()
        mock_return.id = 1
        mock_return.return_id = "5000012345"

        with patch(
            "services.ebay.ebay_return_service.EbayReturnRepository"
        ) as mock_repo:
            mock_repo.get_by_id.return_value = mock_return

            result = mock_service.get_return(1)

            assert result == mock_return
            mock_repo.get_by_id.assert_called_once_with(mock_service.db, 1)

    def test_get_return_by_ebay_id(self, mock_service):
        """Test get return by eBay return ID."""
        mock_return = MagicMock()
        mock_return.return_id = "5000012345"

        with patch(
            "services.ebay.ebay_return_service.EbayReturnRepository"
        ) as mock_repo:
            mock_repo.get_by_ebay_return_id.return_value = mock_return

            result = mock_service.get_return_by_ebay_id("5000012345")

            assert result == mock_return

    def test_list_returns(self, mock_service):
        """Test list returns with filters."""
        mock_returns = [MagicMock(), MagicMock()]

        with patch(
            "services.ebay.ebay_return_service.EbayReturnRepository"
        ) as mock_repo:
            mock_repo.list_returns.return_value = (mock_returns, 2)

            result, total = mock_service.list_returns(state="OPEN", limit=50)

            assert len(result) == 2
            assert total == 2
            mock_repo.list_returns.assert_called_once()

    def test_get_returns_needing_action(self, mock_service):
        """Test get returns needing action."""
        mock_returns = [MagicMock(), MagicMock()]

        with patch(
            "services.ebay.ebay_return_service.EbayReturnRepository"
        ) as mock_repo:
            mock_repo.list_needs_action.return_value = mock_returns

            result = mock_service.get_returns_needing_action()

            assert len(result) == 2

    def test_get_returns_past_deadline(self, mock_service):
        """Test get returns past deadline."""
        mock_returns = [MagicMock()]

        with patch(
            "services.ebay.ebay_return_service.EbayReturnRepository"
        ) as mock_repo:
            mock_repo.list_past_deadline.return_value = mock_returns

            result = mock_service.get_returns_past_deadline()

            assert len(result) == 1

    def test_get_return_statistics(self, mock_service):
        """Test get return statistics."""
        with patch(
            "services.ebay.ebay_return_service.EbayReturnRepository"
        ) as mock_repo:
            mock_repo.count_by_state.side_effect = [5, 10]  # open, closed
            mock_repo.count_needs_action.return_value = 3
            mock_repo.count_past_deadline.return_value = 1

            result = mock_service.get_return_statistics()

            assert result["open"] == 5
            assert result["closed"] == 10
            assert result["needs_action"] == 3
            assert result["past_deadline"] == 1


class TestEbayReturnServiceActionOperations:
    """Tests for EbayReturnService action operations."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock()
        db.commit = MagicMock()
        db.rollback = MagicMock()
        return db

    @pytest.fixture
    def mock_service(self, mock_db):
        """Create mock EbayReturnService without calling __init__."""
        with patch(
            "services.ebay.ebay_return_service.EbayReturnService.__init__",
            return_value=None,
        ):
            from services.ebay.ebay_return_service import EbayReturnService

            service = EbayReturnService.__new__(EbayReturnService)
            service.db = mock_db
            service.user_id = 1
            service.return_client = MagicMock()
            return service

    @pytest.fixture
    def mock_return(self):
        """Create mock return object."""
        return_obj = MagicMock()
        return_obj.id = 1
        return_obj.return_id = "5000012345"
        return_obj.status = "RETURN_REQUESTED"
        return_obj.state = "OPEN"
        return return_obj

    def test_accept_return(self, mock_service, mock_return):
        """Test accept return."""
        with patch(
            "services.ebay.ebay_return_service.EbayReturnRepository"
        ) as mock_repo:
            mock_repo.get_by_id.return_value = mock_return

            result = mock_service.accept_return(
                return_id=1,
                comments="Shipping label sent",
                rma_number="RMA-001",
            )

            assert result["success"] is True
            assert result["return_id"] == "5000012345"
            assert result["new_status"] == "RETURN_ACCEPTED"
            mock_service.return_client.decide_return.assert_called_once_with(
                return_id="5000012345",
                decision="ACCEPT",
                comments="Shipping label sent",
                rma_number="RMA-001",
            )
            mock_service.db.commit.assert_called_once()

    def test_accept_return_not_found(self, mock_service):
        """Test accept return raises error when not found."""
        with patch(
            "services.ebay.ebay_return_service.EbayReturnRepository"
        ) as mock_repo:
            mock_repo.get_by_id.return_value = None

            with pytest.raises(ValueError, match="Return 999 not found"):
                mock_service.accept_return(return_id=999)

    def test_decline_return(self, mock_service, mock_return):
        """Test decline return."""
        with patch(
            "services.ebay.ebay_return_service.EbayReturnRepository"
        ) as mock_repo:
            mock_repo.get_by_id.return_value = mock_return

            result = mock_service.decline_return(
                return_id=1,
                comments="Item was as described",
            )

            assert result["success"] is True
            assert result["new_status"] == "RETURN_DECLINED"
            mock_service.return_client.decide_return.assert_called_once_with(
                return_id="5000012345",
                decision="DECLINE",
                comments="Item was as described",
            )

    def test_decline_return_requires_comments(self, mock_service, mock_return):
        """Test decline return requires comments."""
        with pytest.raises(ValueError, match="Comments are required"):
            mock_service.decline_return(return_id=1, comments="")

    def test_issue_refund_full(self, mock_service, mock_return):
        """Test issue full refund."""
        with patch(
            "services.ebay.ebay_return_service.EbayReturnRepository"
        ) as mock_repo:
            mock_repo.get_by_id.return_value = mock_return

            result = mock_service.issue_refund(return_id=1)

            assert result["success"] is True
            assert result["refund_status"] == "REFUND_ISSUED"
            mock_service.return_client.issue_refund.assert_called_once_with(
                return_id="5000012345",
                refund_amount=None,
                currency=None,
                comments=None,
            )

    def test_issue_refund_partial(self, mock_service, mock_return):
        """Test issue partial refund."""
        with patch(
            "services.ebay.ebay_return_service.EbayReturnRepository"
        ) as mock_repo:
            mock_repo.get_by_id.return_value = mock_return

            result = mock_service.issue_refund(
                return_id=1,
                refund_amount=25.00,
                currency="EUR",
                comments="Partial refund for damage",
            )

            assert result["success"] is True
            mock_service.return_client.issue_refund.assert_called_once_with(
                return_id="5000012345",
                refund_amount=25.00,
                currency="EUR",
                comments="Partial refund for damage",
            )

    def test_mark_as_received(self, mock_service, mock_return):
        """Test mark return as received."""
        with patch(
            "services.ebay.ebay_return_service.EbayReturnRepository"
        ) as mock_repo:
            mock_repo.get_by_id.return_value = mock_return

            result = mock_service.mark_as_received(
                return_id=1,
                comments="Item in good condition",
            )

            assert result["success"] is True
            assert result["new_status"] == "RETURN_ITEM_RECEIVED"
            mock_service.return_client.mark_as_received.assert_called_once()

    def test_send_message(self, mock_service, mock_return):
        """Test send message to buyer."""
        with patch(
            "services.ebay.ebay_return_service.EbayReturnRepository"
        ) as mock_repo:
            mock_repo.get_by_id.return_value = mock_return

            result = mock_service.send_message(
                return_id=1,
                message="Please ship the item back",
            )

            assert result["success"] is True
            mock_service.return_client.send_message.assert_called_once_with(
                return_id="5000012345",
                message="Please ship the item back",
            )

    def test_send_message_requires_message(self, mock_service):
        """Test send message requires non-empty message."""
        with pytest.raises(ValueError, match="Message cannot be empty"):
            mock_service.send_message(return_id=1, message="")

    def test_action_rollback_on_error(self, mock_service, mock_return):
        """Test actions rollback on API error."""
        with patch(
            "services.ebay.ebay_return_service.EbayReturnRepository"
        ) as mock_repo:
            mock_repo.get_by_id.return_value = mock_return
            mock_service.return_client.decide_return.side_effect = Exception(
                "API Error"
            )

            with pytest.raises(RuntimeError, match="Failed to accept return"):
                mock_service.accept_return(return_id=1)

            mock_service.db.rollback.assert_called_once()
