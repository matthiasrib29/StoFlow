"""
Unit tests for EbayCancellationClient.

Tests the Post-Order API v2 cancellation client for searching and managing cancellations.

Author: Claude
Date: 2026-01-14
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest


class TestEbayCancellationClientMethods:
    """Tests for EbayCancellationClient methods."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock EbayCancellationClient without calling __init__."""
        with patch(
            "services.ebay.ebay_cancellation_client.EbayCancellationClient.__init__",
            return_value=None,
        ):
            from services.ebay.ebay_cancellation_client import EbayCancellationClient

            client = EbayCancellationClient.__new__(EbayCancellationClient)
            client.db = MagicMock()
            client.user_id = 1
            client.sandbox = False
            client.post_order_base = "https://api.ebay.com/post-order/v2"
            client.marketplace_id = "EBAY_FR"
            return client

    def test_search_cancellations_basic(self, mock_client):
        """Test basic cancellation search."""
        mock_response = {
            "cancellations": [
                {
                    "cancelId": "5000012345",
                    "cancelState": "CLOSED",
                    "cancelStatus": "CANCEL_CLOSED_WITH_REFUND",
                }
            ],
            "total": 1,
        }

        with patch.object(
            mock_client, "api_call_post_order", return_value=mock_response
        ) as mock_call:
            result = mock_client.search_cancellations()

            mock_call.assert_called_once()
            call_args = mock_call.call_args
            assert call_args[0][0] == "GET"
            assert call_args[0][1] == "/cancellation/search"
            assert result["total"] == 1
            assert len(result["cancellations"]) == 1

    def test_search_cancellations_with_order_id(self, mock_client):
        """Test cancellation search with order_id filter."""
        with patch.object(
            mock_client, "api_call_post_order", return_value={"cancellations": [], "total": 0}
        ) as mock_call:
            mock_client.search_cancellations(order_id="123456789012")

            call_kwargs = mock_call.call_args[1]
            assert call_kwargs["params"]["legacy_order_id"] == "123456789012"

    def test_search_cancellations_with_cancel_id(self, mock_client):
        """Test cancellation search with cancel_id filter."""
        with patch.object(
            mock_client, "api_call_post_order", return_value={"cancellations": [], "total": 0}
        ) as mock_call:
            mock_client.search_cancellations(cancel_id="5000012345")

            call_kwargs = mock_call.call_args[1]
            assert call_kwargs["params"]["cancel_id"] == "5000012345"

    def test_search_cancellations_with_role(self, mock_client):
        """Test cancellation search with role filter."""
        with patch.object(
            mock_client, "api_call_post_order", return_value={"cancellations": [], "total": 0}
        ) as mock_call:
            mock_client.search_cancellations(role="SELLER")

            call_kwargs = mock_call.call_args[1]
            assert call_kwargs["params"]["role"] == "SELLER"

    def test_search_cancellations_with_date_range(self, mock_client):
        """Test cancellation search with date range."""
        start_date = datetime(2026, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2026, 1, 14, tzinfo=timezone.utc)

        with patch.object(
            mock_client, "api_call_post_order", return_value={"cancellations": [], "total": 0}
        ) as mock_call:
            mock_client.search_cancellations(
                creation_date_range_from=start_date, creation_date_range_to=end_date
            )

            call_kwargs = mock_call.call_args[1]
            assert "creation_date_range_from" in call_kwargs["params"]
            assert "creation_date_range_to" in call_kwargs["params"]

    def test_search_cancellations_pagination(self, mock_client):
        """Test cancellation search with pagination."""
        with patch.object(
            mock_client, "api_call_post_order", return_value={"cancellations": [], "total": 0}
        ) as mock_call:
            mock_client.search_cancellations(limit=100, offset=50)

            call_kwargs = mock_call.call_args[1]
            assert call_kwargs["params"]["limit"] == 100
            assert call_kwargs["params"]["offset"] == 50

    def test_search_cancellations_limit_capped_at_200(self, mock_client):
        """Test that limit is capped at 200."""
        with patch.object(
            mock_client, "api_call_post_order", return_value={"cancellations": [], "total": 0}
        ) as mock_call:
            mock_client.search_cancellations(limit=500)

            call_kwargs = mock_call.call_args[1]
            assert call_kwargs["params"]["limit"] == 200

    def test_get_cancellation(self, mock_client):
        """Test getting cancellation details."""
        mock_response = {
            "cancelId": "5000012345",
            "cancelState": "CLOSED",
            "cancelStatus": "CANCEL_CLOSED_WITH_REFUND",
            "cancelReason": "BUYER_ASKED_CANCEL",
        }

        with patch.object(
            mock_client, "api_call_post_order", return_value=mock_response
        ) as mock_call:
            result = mock_client.get_cancellation("5000012345")

            mock_call.assert_called_once_with("GET", "/cancellation/5000012345")
            assert result["cancelId"] == "5000012345"
            assert result["cancelReason"] == "BUYER_ASKED_CANCEL"

    def test_check_eligibility(self, mock_client):
        """Test checking order eligibility for cancellation."""
        mock_response = {
            "eligible": True,
            "eligibilityStatus": "ELIGIBLE",
            "legacyOrderId": "123456789012",
        }

        with patch.object(
            mock_client, "api_call_post_order", return_value=mock_response
        ) as mock_call:
            result = mock_client.check_eligibility("123456789012")

            mock_call.assert_called_once()
            call_args = mock_call.call_args
            assert call_args[0][0] == "POST"
            assert call_args[0][1] == "/cancellation/check_eligibility"
            assert call_args[1]["json_data"]["legacyOrderId"] == "123456789012"
            assert result["eligible"] is True

    def test_create_cancellation(self, mock_client):
        """Test creating a seller-initiated cancellation."""
        mock_response = {
            "cancelId": "5000012345",
            "cancelStatus": "CANCEL_PENDING",
        }

        with patch.object(
            mock_client, "api_call_post_order", return_value=mock_response
        ) as mock_call:
            result = mock_client.create_cancellation(
                order_id="123456789012",
                reason="OUT_OF_STOCK",
                comments="Item sold on another platform",
            )

            mock_call.assert_called_once()
            call_args = mock_call.call_args
            assert call_args[0][0] == "POST"
            assert call_args[0][1] == "/cancellation/"

            payload = call_args[1]["json_data"]
            assert payload["legacyOrderId"] == "123456789012"
            assert payload["cancelReason"] == "OUT_OF_STOCK"
            assert result["cancelId"] == "5000012345"

    def test_approve_cancellation(self, mock_client):
        """Test approving a buyer's cancellation request."""
        with patch.object(
            mock_client, "api_call_post_order", return_value={}
        ) as mock_call:
            mock_client.approve_cancellation(
                "5000012345", comments="Approved at buyer's request"
            )

            mock_call.assert_called_once()
            call_args = mock_call.call_args
            assert call_args[0][0] == "POST"
            assert call_args[0][1] == "/cancellation/5000012345/approve"

    def test_reject_cancellation_already_shipped(self, mock_client):
        """Test rejecting cancellation because already shipped."""
        shipped_date = datetime.now(timezone.utc)

        with patch.object(
            mock_client, "api_call_post_order", return_value={}
        ) as mock_call:
            mock_client.reject_cancellation(
                "5000012345",
                reason="ALREADY_SHIPPED",
                tracking_number="1Z999AA10123456784",
                carrier="UPS",
                shipped_date=shipped_date,
                comments="Item already shipped",
            )

            mock_call.assert_called_once()
            call_args = mock_call.call_args
            assert call_args[0][0] == "POST"
            assert call_args[0][1] == "/cancellation/5000012345/reject"

            payload = call_args[1]["json_data"]
            assert payload["rejectReason"] == "ALREADY_SHIPPED"
            assert payload["trackingNumber"] == "1Z999AA10123456784"
            assert payload["shipmentCarrier"] == "UPS"

    def test_reject_cancellation_other_reason(self, mock_client):
        """Test rejecting cancellation for other reason."""
        with patch.object(
            mock_client, "api_call_post_order", return_value={}
        ) as mock_call:
            mock_client.reject_cancellation(
                "5000012345",
                reason="OTHER_SELLER_REJECT_REASON",
                comments="Cannot cancel, processing already started",
            )

            call_args = mock_call.call_args
            payload = call_args[1]["json_data"]
            assert payload["rejectReason"] == "OTHER_SELLER_REJECT_REASON"
            assert "trackingNumber" not in payload

    def test_get_all_cancellations_single_page(self, mock_client):
        """Test getting all cancellations when results fit in one page."""
        mock_response = {
            "cancellations": [
                {"cancelId": "1"},
                {"cancelId": "2"},
            ],
            "total": 2,
        }

        with patch.object(
            mock_client, "search_cancellations", return_value=mock_response
        ) as mock_search:
            result = mock_client.get_all_cancellations(role="SELLER")

            assert len(result) == 2
            mock_search.assert_called_once()

    def test_get_all_cancellations_multiple_pages(self, mock_client):
        """Test getting all cancellations with pagination."""
        # First call returns 200 items
        page1 = {
            "cancellations": [{"cancelId": str(i)} for i in range(200)],
            "total": 250,
        }
        # Second call returns remaining 50 items
        page2 = {
            "cancellations": [{"cancelId": str(i)} for i in range(200, 250)],
            "total": 250,
        }
        # Third call returns empty (pagination complete)
        page3 = {"cancellations": [], "total": 250}

        with patch.object(
            mock_client, "search_cancellations", side_effect=[page1, page2, page3]
        ):
            result = mock_client.get_all_cancellations()

            assert len(result) == 250

    def test_get_cancellations_by_date_range(self, mock_client):
        """Test getting cancellations by date range."""
        mock_response = {
            "cancellations": [{"cancelId": "1"}],
            "total": 1,
        }

        start_date = datetime.now(timezone.utc) - timedelta(days=7)
        end_date = datetime.now(timezone.utc)

        with patch.object(
            mock_client, "search_cancellations", return_value=mock_response
        ) as mock_search:
            result = mock_client.get_cancellations_by_date_range(start_date, end_date)

            assert len(result) == 1
            call_kwargs = mock_search.call_args[1]
            assert call_kwargs["creation_date_range_from"] == start_date
            assert call_kwargs["creation_date_range_to"] == end_date

    def test_get_pending_cancellations(self, mock_client):
        """Test getting pending cancellations."""
        all_cancels = [
            {"cancelId": "1", "cancelStatus": "CANCEL_REQUESTED"},
            {"cancelId": "2", "cancelStatus": "CANCEL_PENDING"},
            {"cancelId": "3", "cancelStatus": "CANCEL_CLOSED_WITH_REFUND"},
            {"cancelId": "4", "cancelStatus": "CANCEL_REJECTED"},
        ]

        with patch.object(
            mock_client, "get_all_cancellations", return_value=all_cancels
        ):
            result = mock_client.get_pending_cancellations()

            assert len(result) == 2
            assert all(
                c["cancelStatus"] in ["CANCEL_REQUESTED", "CANCEL_PENDING"]
                for c in result
            )


class TestEbayCancellationModel:
    """Tests for EbayCancellation model properties."""

    def test_is_closed_true(self):
        """Test is_closed property when state is CLOSED."""
        from models.user.ebay_cancellation import EbayCancellation

        cancel = EbayCancellation()
        cancel.cancel_state = "CLOSED"
        assert cancel.is_closed is True

    def test_is_closed_false(self):
        """Test is_closed property when state is not CLOSED."""
        from models.user.ebay_cancellation import EbayCancellation

        cancel = EbayCancellation()
        cancel.cancel_state = None
        assert cancel.is_closed is False

    def test_is_pending_true(self):
        """Test is_pending property for pending statuses."""
        from models.user.ebay_cancellation import EbayCancellation

        cancel = EbayCancellation()
        cancel.cancel_status = "CANCEL_REQUESTED"
        assert cancel.is_pending is True

        cancel.cancel_status = "CANCEL_PENDING"
        assert cancel.is_pending is True

    def test_is_pending_false(self):
        """Test is_pending property for non-pending statuses."""
        from models.user.ebay_cancellation import EbayCancellation

        cancel = EbayCancellation()
        cancel.cancel_status = "CANCEL_CLOSED_WITH_REFUND"
        assert cancel.is_pending is False

    def test_needs_action_true(self):
        """Test needs_action when buyer-initiated and pending."""
        from models.user.ebay_cancellation import EbayCancellation

        cancel = EbayCancellation()
        cancel.cancel_status = "CANCEL_REQUESTED"
        cancel.requestor_role = "BUYER"
        assert cancel.needs_action is True

    def test_needs_action_false_seller_initiated(self):
        """Test needs_action when seller-initiated (no action needed)."""
        from models.user.ebay_cancellation import EbayCancellation

        cancel = EbayCancellation()
        cancel.cancel_status = "CANCEL_REQUESTED"
        cancel.requestor_role = "SELLER"
        assert cancel.needs_action is False

    def test_needs_action_false_not_pending(self):
        """Test needs_action when not pending."""
        from models.user.ebay_cancellation import EbayCancellation

        cancel = EbayCancellation()
        cancel.cancel_status = "CANCEL_CLOSED_WITH_REFUND"
        cancel.requestor_role = "BUYER"
        assert cancel.needs_action is False

    def test_was_approved_true(self):
        """Test was_approved for approved statuses."""
        from models.user.ebay_cancellation import EbayCancellation

        cancel = EbayCancellation()
        cancel.cancel_status = "CANCEL_CLOSED_WITH_REFUND"
        assert cancel.was_approved is True

        cancel.cancel_status = "CANCEL_CLOSED_UNKNOWN_REFUND"
        assert cancel.was_approved is True

    def test_was_approved_false(self):
        """Test was_approved for rejected status."""
        from models.user.ebay_cancellation import EbayCancellation

        cancel = EbayCancellation()
        cancel.cancel_status = "CANCEL_REJECTED"
        assert cancel.was_approved is False

    def test_was_rejected_true(self):
        """Test was_rejected property."""
        from models.user.ebay_cancellation import EbayCancellation

        cancel = EbayCancellation()
        cancel.cancel_status = "CANCEL_REJECTED"
        assert cancel.was_rejected is True

    def test_was_rejected_false(self):
        """Test was_rejected property for approved status."""
        from models.user.ebay_cancellation import EbayCancellation

        cancel = EbayCancellation()
        cancel.cancel_status = "CANCEL_CLOSED_WITH_REFUND"
        assert cancel.was_rejected is False

    def test_is_past_response_due_true(self):
        """Test is_past_response_due when deadline has passed."""
        from models.user.ebay_cancellation import EbayCancellation

        cancel = EbayCancellation()
        cancel.response_due_date = datetime.now(timezone.utc) - timedelta(days=1)
        assert cancel.is_past_response_due is True

    def test_is_past_response_due_false(self):
        """Test is_past_response_due when deadline is in future."""
        from models.user.ebay_cancellation import EbayCancellation

        cancel = EbayCancellation()
        cancel.response_due_date = datetime.now(timezone.utc) + timedelta(days=1)
        assert cancel.is_past_response_due is False

    def test_is_past_response_due_no_deadline(self):
        """Test is_past_response_due when no deadline set."""
        from models.user.ebay_cancellation import EbayCancellation

        cancel = EbayCancellation()
        cancel.response_due_date = None
        assert cancel.is_past_response_due is False
