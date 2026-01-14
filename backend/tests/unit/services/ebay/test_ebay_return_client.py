"""
Unit tests for EbayReturnClient.

Tests the Post-Order API v2 return client for searching and managing returns.

Author: Claude
Date: 2026-01-13
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from shared.exceptions import EbayAPIError


class TestEbayReturnClientMethods:
    """Tests for EbayReturnClient methods."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock EbayReturnClient without calling __init__."""
        with patch(
            "services.ebay.ebay_return_client.EbayReturnClient.__init__",
            return_value=None,
        ):
            from services.ebay.ebay_return_client import EbayReturnClient

            client = EbayReturnClient.__new__(EbayReturnClient)
            client.db = MagicMock()
            client.user_id = 1
            client.sandbox = False
            client.post_order_base = "https://api.ebay.com/post-order/v2"
            client.marketplace_id = "EBAY_FR"
            return client

    def test_search_returns_basic(self, mock_client):
        """Test basic return search."""
        mock_response = {
            "members": [
                {"returnId": "5000012345", "state": "OPEN", "status": "RETURN_REQUESTED"}
            ],
            "total": 1,
        }

        with patch.object(
            mock_client, "api_call_post_order", return_value=mock_response
        ) as mock_call:
            result = mock_client.search_returns()

            mock_call.assert_called_once()
            call_args = mock_call.call_args
            assert call_args[0][0] == "GET"
            assert call_args[0][1] == "/return/search"
            assert result["total"] == 1
            assert len(result["members"]) == 1

    def test_search_returns_with_state_filter(self, mock_client):
        """Test return search with state filter."""
        with patch.object(
            mock_client, "api_call_post_order", return_value={"members": [], "total": 0}
        ) as mock_call:
            mock_client.search_returns(return_state="OPEN")

            call_kwargs = mock_call.call_args[1]
            assert call_kwargs["params"]["return_state"] == "OPEN"

    def test_search_returns_with_order_id(self, mock_client):
        """Test return search with order_id filter."""
        with patch.object(
            mock_client, "api_call_post_order", return_value={"members": [], "total": 0}
        ) as mock_call:
            mock_client.search_returns(order_id="12-34567-89012")

            call_kwargs = mock_call.call_args[1]
            assert call_kwargs["params"]["order_id"] == "12-34567-89012"

    def test_search_returns_with_date_range(self, mock_client):
        """Test return search with date range."""
        start_date = datetime(2026, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2026, 1, 13, tzinfo=timezone.utc)

        with patch.object(
            mock_client, "api_call_post_order", return_value={"members": [], "total": 0}
        ) as mock_call:
            mock_client.search_returns(
                creation_date_range_from=start_date, creation_date_range_to=end_date
            )

            call_kwargs = mock_call.call_args[1]
            assert "creation_date_range_from" in call_kwargs["params"]
            assert "creation_date_range_to" in call_kwargs["params"]

    def test_search_returns_pagination(self, mock_client):
        """Test return search with pagination."""
        with patch.object(
            mock_client, "api_call_post_order", return_value={"members": [], "total": 0}
        ) as mock_call:
            mock_client.search_returns(limit=100, offset=50)

            call_kwargs = mock_call.call_args[1]
            assert call_kwargs["params"]["limit"] == 100
            assert call_kwargs["params"]["offset"] == 50

    def test_search_returns_limit_capped_at_200(self, mock_client):
        """Test that limit is capped at 200."""
        with patch.object(
            mock_client, "api_call_post_order", return_value={"members": [], "total": 0}
        ) as mock_call:
            mock_client.search_returns(limit=500)

            call_kwargs = mock_call.call_args[1]
            assert call_kwargs["params"]["limit"] == 200

    def test_get_return(self, mock_client):
        """Test getting return details."""
        mock_response = {
            "returnId": "5000012345",
            "state": "OPEN",
            "status": "RETURN_REQUESTED",
            "returnReason": "NOT_AS_DESCRIBED",
        }

        with patch.object(
            mock_client, "api_call_post_order", return_value=mock_response
        ) as mock_call:
            result = mock_client.get_return("5000012345")

            mock_call.assert_called_once_with("GET", "/return/5000012345")
            assert result["returnId"] == "5000012345"
            assert result["returnReason"] == "NOT_AS_DESCRIBED"

    def test_decide_return_accept(self, mock_client):
        """Test accepting a return."""
        with patch.object(
            mock_client, "api_call_post_order", return_value={}
        ) as mock_call:
            mock_client.decide_return(
                "5000012345",
                decision="ACCEPT",
                comments="Please ship the item back",
                rma_number="RMA-001",
            )

            mock_call.assert_called_once()
            call_args = mock_call.call_args
            assert call_args[0][0] == "POST"
            assert call_args[0][1] == "/return/5000012345/decide"

            payload = call_args[1]["json_data"]
            assert payload["decision"] == "ACCEPT"
            assert payload["comments"] == "Please ship the item back"
            assert payload["RMANumber"] == "RMA-001"

    def test_decide_return_decline(self, mock_client):
        """Test declining a return."""
        with patch.object(
            mock_client, "api_call_post_order", return_value={}
        ) as mock_call:
            mock_client.decide_return(
                "5000012345", decision="DECLINE", comments="Item was as described"
            )

            call_args = mock_call.call_args
            payload = call_args[1]["json_data"]
            assert payload["decision"] == "DECLINE"
            assert "RMANumber" not in payload  # RMA not added for decline

    def test_issue_refund_full(self, mock_client):
        """Test issuing a full refund."""
        with patch.object(
            mock_client, "api_call_post_order", return_value={}
        ) as mock_call:
            mock_client.issue_refund("5000012345")

            mock_call.assert_called_once()
            call_args = mock_call.call_args
            assert call_args[0][0] == "POST"
            assert call_args[0][1] == "/return/5000012345/issue_refund"

    def test_issue_refund_partial(self, mock_client):
        """Test issuing a partial refund."""
        with patch.object(
            mock_client, "api_call_post_order", return_value={}
        ) as mock_call:
            mock_client.issue_refund(
                "5000012345",
                refund_amount=25.00,
                currency="EUR",
                comments="Partial refund",
            )

            call_args = mock_call.call_args
            payload = call_args[1]["json_data"]
            assert payload["refundAmount"]["value"] == "25.0"
            assert payload["refundAmount"]["currency"] == "EUR"
            assert payload["comments"] == "Partial refund"

    def test_mark_as_received(self, mock_client):
        """Test marking return as received."""
        with patch.object(
            mock_client, "api_call_post_order", return_value={}
        ) as mock_call:
            mock_client.mark_as_received(
                "5000012345", comments="Item received in good condition"
            )

            mock_call.assert_called_once()
            call_args = mock_call.call_args
            assert call_args[0][0] == "POST"
            assert call_args[0][1] == "/return/5000012345/mark_as_received"

    def test_send_message(self, mock_client):
        """Test sending message to buyer."""
        with patch.object(
            mock_client, "api_call_post_order", return_value={}
        ) as mock_call:
            mock_client.send_message("5000012345", message="Please ship the item back")

            call_args = mock_call.call_args
            assert call_args[0][0] == "POST"
            assert call_args[0][1] == "/return/5000012345/send_message"
            assert call_args[1]["json_data"]["message"] == "Please ship the item back"

    def test_get_all_returns_single_page(self, mock_client):
        """Test getting all returns when results fit in one page."""
        mock_response = {
            "members": [
                {"returnId": "1"},
                {"returnId": "2"},
            ],
            "total": 2,
        }

        with patch.object(
            mock_client, "search_returns", return_value=mock_response
        ) as mock_search:
            result = mock_client.get_all_returns(return_state="OPEN")

            assert len(result) == 2
            mock_search.assert_called_once()

    def test_get_all_returns_multiple_pages(self, mock_client):
        """Test getting all returns with pagination."""
        # First call returns 200 items
        page1 = {"members": [{"returnId": str(i)} for i in range(200)], "total": 250}
        # Second call returns remaining 50 items
        page2 = {
            "members": [{"returnId": str(i)} for i in range(200, 250)],
            "total": 250,
        }
        # Third call returns empty (pagination complete)
        page3 = {"members": [], "total": 250}

        with patch.object(
            mock_client, "search_returns", side_effect=[page1, page2, page3]
        ):
            result = mock_client.get_all_returns()

            assert len(result) == 250

    def test_get_returns_by_date_range(self, mock_client):
        """Test getting returns by date range."""
        mock_response = {
            "members": [{"returnId": "1"}],
            "total": 1,
        }

        start_date = datetime.now(timezone.utc) - timedelta(days=7)
        end_date = datetime.now(timezone.utc)

        with patch.object(
            mock_client, "search_returns", return_value=mock_response
        ) as mock_search:
            result = mock_client.get_returns_by_date_range(start_date, end_date)

            assert len(result) == 1
            call_kwargs = mock_search.call_args[1]
            assert call_kwargs["creation_date_range_from"] == start_date
            assert call_kwargs["creation_date_range_to"] == end_date


class TestEbayReturnModel:
    """Tests for EbayReturn model properties."""

    def test_is_open_true(self):
        """Test is_open property when state is OPEN."""
        from models.user.ebay_return import EbayReturn

        ret = EbayReturn()
        ret.state = "OPEN"
        assert ret.is_open is True

    def test_is_open_false(self):
        """Test is_open property when state is CLOSED."""
        from models.user.ebay_return import EbayReturn

        ret = EbayReturn()
        ret.state = "CLOSED"
        assert ret.is_open is False

    def test_needs_action_true(self):
        """Test needs_action property for action-needed statuses."""
        from models.user.ebay_return import EbayReturn

        ret = EbayReturn()
        ret.status = "RETURN_REQUESTED"
        assert ret.needs_action is True

        ret.status = "RETURN_ITEM_DELIVERED"
        assert ret.needs_action is True

    def test_needs_action_false(self):
        """Test needs_action property for non-action statuses."""
        from models.user.ebay_return import EbayReturn

        ret = EbayReturn()
        ret.status = "RETURN_ITEM_SHIPPED"
        assert ret.needs_action is False

    def test_is_past_deadline_true(self):
        """Test is_past_deadline when deadline has passed."""
        from models.user.ebay_return import EbayReturn

        ret = EbayReturn()
        ret.deadline_date = datetime.now(timezone.utc) - timedelta(days=1)
        assert ret.is_past_deadline is True

    def test_is_past_deadline_false(self):
        """Test is_past_deadline when deadline is in future."""
        from models.user.ebay_return import EbayReturn

        ret = EbayReturn()
        ret.deadline_date = datetime.now(timezone.utc) + timedelta(days=1)
        assert ret.is_past_deadline is False

    def test_is_past_deadline_no_deadline(self):
        """Test is_past_deadline when no deadline set."""
        from models.user.ebay_return import EbayReturn

        ret = EbayReturn()
        ret.deadline_date = None
        assert ret.is_past_deadline is False
