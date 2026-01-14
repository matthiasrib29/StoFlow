"""
Unit tests for EbayPostOrderClient.

Tests the Post-Order API v2 client for cancellations, returns, and inquiries.

Author: Claude
Date: 2026-01-13
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
import requests

from shared.exceptions import (
    EbayAPIError,
    EbayError,
    EbayOAuthError,
    MarketplaceRateLimitError,
)


class TestEbayPostOrderClientInit:
    """Tests for EbayPostOrderClient initialization."""

    @pytest.fixture
    def mock_ebay_credentials(self):
        """Create mock EbayCredentials object."""
        creds = MagicMock()
        creds.refresh_token = "test_refresh_token"
        creds.refresh_token_expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        return creds

    @pytest.fixture
    def mock_db_session(self, mock_ebay_credentials):
        """Create mock database session."""
        db = MagicMock()
        db.query.return_value.first.return_value = mock_ebay_credentials
        db.query.return_value.filter.return_value.first.return_value = None
        return db

    def test_init_sets_post_order_base_production(self, mock_db_session):
        """Test that production URL is set when sandbox=False."""
        with patch("services.ebay.ebay_base_client.os.getenv") as mock_getenv:
            mock_getenv.side_effect = lambda key, default="": {
                "EBAY_CLIENT_ID": "test_client_id",
                "EBAY_CLIENT_SECRET": "test_client_secret",
                "EBAY_SANDBOX": "false",
            }.get(key, default)

            from services.ebay.ebay_post_order_client import EbayPostOrderClient

            client = EbayPostOrderClient(mock_db_session, user_id=1, sandbox=False)

            assert client.post_order_base == "https://api.ebay.com/post-order/v2"
            assert client.sandbox is False

    def test_init_sets_post_order_base_sandbox(self, mock_db_session):
        """Test that sandbox URL is set when sandbox=True."""
        with patch("services.ebay.ebay_base_client.os.getenv") as mock_getenv:
            mock_getenv.side_effect = lambda key, default="": {
                "EBAY_CLIENT_ID": "test_client_id",
                "EBAY_CLIENT_SECRET": "test_client_secret",
                "EBAY_SANDBOX": "true",
            }.get(key, default)

            from services.ebay.ebay_post_order_client import EbayPostOrderClient

            client = EbayPostOrderClient(mock_db_session, user_id=1, sandbox=True)

            assert client.post_order_base == "https://api.sandbox.ebay.com/post-order/v2"
            assert client.sandbox is True


class TestApiCallPostOrder:
    """Tests for api_call_post_order method."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock EbayPostOrderClient without calling __init__."""
        with patch(
            "services.ebay.ebay_post_order_client.EbayPostOrderClient.__init__",
            return_value=None,
        ):
            from services.ebay.ebay_post_order_client import EbayPostOrderClient

            client = EbayPostOrderClient.__new__(EbayPostOrderClient)
            client.db = MagicMock()
            client.user_id = 1
            client.sandbox = False
            client.post_order_base = "https://api.ebay.com/post-order/v2"
            client.marketplace_id = "EBAY_FR"
            return client

    @pytest.fixture
    def mock_rate_limiter(self):
        """Create a mock RateLimiter."""
        limiter = MagicMock()
        limiter.wait = MagicMock()
        return limiter

    def test_api_call_post_order_success(self, mock_client, mock_rate_limiter):
        """Test successful API call returns JSON response."""
        mock_client._post_order_rate_limiter = mock_rate_limiter

        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "cancellations": [{"cancelId": "123", "status": "CANCEL_REQUESTED"}]
        }

        with patch.object(mock_client, "get_access_token", return_value="test_token"):
            with patch(
                "services.ebay.ebay_post_order_client.requests.request"
            ) as mock_request:
                mock_request.return_value = mock_response

                result = mock_client.api_call_post_order(
                    "GET", "/cancellation/search", params={"order_id": "12-34567-89012"}
                )

                assert result == {
                    "cancellations": [{"cancelId": "123", "status": "CANCEL_REQUESTED"}]
                }
                mock_rate_limiter.wait.assert_called_once()
                mock_request.assert_called_once()

                # Verify correct URL (first positional arg is method, second is URL)
                call_args = mock_request.call_args
                url = call_args[0][1]  # args[1] is URL
                assert url == "https://api.ebay.com/post-order/v2/cancellation/search"

    def test_api_call_post_order_headers(self, mock_client, mock_rate_limiter):
        """Test that correct headers are sent."""
        mock_client._post_order_rate_limiter = mock_rate_limiter

        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "value"}

        with patch.object(mock_client, "get_access_token", return_value="test_token"):
            with patch(
                "services.ebay.ebay_post_order_client.requests.request"
            ) as mock_request:
                mock_request.return_value = mock_response

                mock_client.api_call_post_order("GET", "/return/123")

                call_kwargs = mock_request.call_args[1]
                assert call_kwargs["headers"]["Authorization"] == "Bearer test_token"
                assert call_kwargs["headers"]["Content-Type"] == "application/json"
                assert call_kwargs["headers"]["Accept"] == "application/json"
                assert call_kwargs["headers"]["X-EBAY-C-MARKETPLACE-ID"] == "EBAY_FR"

    def test_api_call_post_order_with_json_body(self, mock_client, mock_rate_limiter):
        """Test that JSON body is correctly sent."""
        mock_client._post_order_rate_limiter = mock_rate_limiter

        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}

        with patch.object(mock_client, "get_access_token", return_value="test_token"):
            with patch(
                "services.ebay.ebay_post_order_client.requests.request"
            ) as mock_request:
                mock_request.return_value = mock_response

                mock_client.api_call_post_order(
                    "POST",
                    "/cancellation/ABC123/approve",
                    json_data={"reason": "BUYER_ASKED_CANCEL"},
                )

                call_kwargs = mock_request.call_args[1]
                assert call_kwargs["json"] == {"reason": "BUYER_ASKED_CANCEL"}

    def test_api_call_post_order_handles_rate_limit(
        self, mock_client, mock_rate_limiter
    ):
        """Test that 429 response raises MarketplaceRateLimitError."""
        mock_client._post_order_rate_limiter = mock_rate_limiter

        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "60"}
        mock_response.json.return_value = {"error": "rate_limit_exceeded"}

        with patch.object(mock_client, "get_access_token", return_value="test_token"):
            with patch(
                "services.ebay.ebay_post_order_client.requests.request"
            ) as mock_request:
                mock_request.return_value = mock_response

                with pytest.raises(MarketplaceRateLimitError) as exc_info:
                    mock_client.api_call_post_order("GET", "/cancellation/search")

                assert exc_info.value.platform == "ebay"
                assert exc_info.value.retry_after == 60

    def test_api_call_post_order_handles_401(self, mock_client, mock_rate_limiter):
        """Test that 401 response raises EbayOAuthError."""
        mock_client._post_order_rate_limiter = mock_rate_limiter

        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 401
        mock_response.json.return_value = {"error": "invalid_token"}

        with patch.object(mock_client, "get_access_token", return_value="test_token"):
            with patch(
                "services.ebay.ebay_post_order_client.requests.request"
            ) as mock_request:
                mock_request.return_value = mock_response

                with pytest.raises(EbayOAuthError) as exc_info:
                    mock_client.api_call_post_order("GET", "/cancellation/search")

                assert exc_info.value.status_code == 401
                assert "Post-Order API auth failed" in str(exc_info.value.message)

    def test_api_call_post_order_handles_403(self, mock_client, mock_rate_limiter):
        """Test that 403 response raises EbayOAuthError."""
        mock_client._post_order_rate_limiter = mock_rate_limiter

        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 403
        mock_response.json.return_value = {"error": "forbidden"}

        with patch.object(mock_client, "get_access_token", return_value="test_token"):
            with patch(
                "services.ebay.ebay_post_order_client.requests.request"
            ) as mock_request:
                mock_request.return_value = mock_response

                with pytest.raises(EbayOAuthError) as exc_info:
                    mock_client.api_call_post_order("GET", "/cancellation/search")

                assert exc_info.value.status_code == 403

    def test_api_call_post_order_handles_500(self, mock_client, mock_rate_limiter):
        """Test that 500 response raises EbayAPIError."""
        mock_client._post_order_rate_limiter = mock_rate_limiter

        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_response.json.return_value = {"error": "internal_error"}

        with patch.object(mock_client, "get_access_token", return_value="test_token"):
            with patch(
                "services.ebay.ebay_post_order_client.requests.request"
            ) as mock_request:
                mock_request.return_value = mock_response

                with pytest.raises(EbayAPIError) as exc_info:
                    mock_client.api_call_post_order("GET", "/cancellation/search")

                assert exc_info.value.status_code == 500
                assert "Post-Order API error 500" in str(exc_info.value.message)

    def test_api_call_post_order_handles_204_no_content(
        self, mock_client, mock_rate_limiter
    ):
        """Test that 204 response returns None."""
        mock_client._post_order_rate_limiter = mock_rate_limiter

        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 204
        mock_response.text = ""

        with patch.object(mock_client, "get_access_token", return_value="test_token"):
            with patch(
                "services.ebay.ebay_post_order_client.requests.request"
            ) as mock_request:
                mock_request.return_value = mock_response

                result = mock_client.api_call_post_order(
                    "POST", "/cancellation/ABC123/approve"
                )

                assert result is None

    def test_api_call_post_order_handles_timeout(self, mock_client, mock_rate_limiter):
        """Test that timeout raises EbayError."""
        mock_client._post_order_rate_limiter = mock_rate_limiter

        with patch.object(mock_client, "get_access_token", return_value="test_token"):
            with patch(
                "services.ebay.ebay_post_order_client.requests.request"
            ) as mock_request:
                mock_request.side_effect = requests.exceptions.Timeout(
                    "Connection timed out"
                )

                with pytest.raises(EbayError) as exc_info:
                    mock_client.api_call_post_order("GET", "/cancellation/search")

                assert "Timeout" in str(exc_info.value.message)
                assert "Post-Order" in str(exc_info.value.message)

    def test_api_call_post_order_handles_network_error(
        self, mock_client, mock_rate_limiter
    ):
        """Test that network errors raise EbayError."""
        mock_client._post_order_rate_limiter = mock_rate_limiter

        with patch.object(mock_client, "get_access_token", return_value="test_token"):
            with patch(
                "services.ebay.ebay_post_order_client.requests.request"
            ) as mock_request:
                mock_request.side_effect = requests.exceptions.ConnectionError(
                    "Connection refused"
                )

                with pytest.raises(EbayError) as exc_info:
                    mock_client.api_call_post_order("GET", "/cancellation/search")

                assert "Network error" in str(exc_info.value.message)
                assert "Post-Order" in str(exc_info.value.message)

    def test_api_call_post_order_default_marketplace(self, mock_rate_limiter):
        """Test that default marketplace EBAY_FR is used when not specified."""
        with patch(
            "services.ebay.ebay_post_order_client.EbayPostOrderClient.__init__",
            return_value=None,
        ):
            from services.ebay.ebay_post_order_client import EbayPostOrderClient

            client = EbayPostOrderClient.__new__(EbayPostOrderClient)
            client.db = MagicMock()
            client.user_id = 1
            client.sandbox = False
            client.post_order_base = "https://api.ebay.com/post-order/v2"
            client.marketplace_id = None  # Not specified
            client._post_order_rate_limiter = mock_rate_limiter

            mock_response = MagicMock()
            mock_response.ok = True
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": "value"}

            with patch.object(client, "get_access_token", return_value="test_token"):
                with patch(
                    "services.ebay.ebay_post_order_client.requests.request"
                ) as mock_request:
                    mock_request.return_value = mock_response

                    client.api_call_post_order("GET", "/cancellation/search")

                    call_kwargs = mock_request.call_args[1]
                    # Default should be EBAY_FR
                    assert call_kwargs["headers"]["X-EBAY-C-MARKETPLACE-ID"] == "EBAY_FR"


class TestPostOrderTypes:
    """Tests for post_order_types enums."""

    def test_cancellation_status_values(self):
        """Test CancellationStatus enum values."""
        from services.ebay.post_order_types import CancellationStatus

        assert CancellationStatus.CANCEL_REQUESTED.value == "CANCEL_REQUESTED"
        assert CancellationStatus.CANCEL_PENDING.value == "CANCEL_PENDING"
        assert (
            CancellationStatus.CANCEL_CLOSED_WITH_REFUND.value
            == "CANCEL_CLOSED_WITH_REFUND"
        )

    def test_return_status_values(self):
        """Test ReturnStatus enum values."""
        from services.ebay.post_order_types import ReturnStatus

        assert ReturnStatus.RETURN_REQUESTED.value == "RETURN_REQUESTED"
        assert ReturnStatus.RETURN_ITEM_SHIPPED.value == "RETURN_ITEM_SHIPPED"
        assert ReturnStatus.RETURN_CLOSED.value == "RETURN_CLOSED"

    def test_inquiry_status_values(self):
        """Test InquiryStatus enum values."""
        from services.ebay.post_order_types import InquiryStatus

        assert InquiryStatus.OPEN.value == "OPEN"
        assert InquiryStatus.CLOSED.value == "CLOSED"
        assert InquiryStatus.ESCALATED.value == "ESCALATED"

    def test_payment_dispute_status_values(self):
        """Test PaymentDisputeStatus enum values."""
        from services.ebay.post_order_types import PaymentDisputeStatus

        assert PaymentDisputeStatus.OPEN.value == "OPEN"
        assert PaymentDisputeStatus.WAITING_FOR_SELLER.value == "WAITING_FOR_SELLER"
        assert PaymentDisputeStatus.CLOSED.value == "CLOSED"

    def test_refund_status_values(self):
        """Test RefundStatus enum values."""
        from services.ebay.post_order_types import RefundStatus

        assert RefundStatus.PENDING.value == "PENDING"
        assert RefundStatus.COMPLETED.value == "COMPLETED"
        assert RefundStatus.FAILED.value == "FAILED"

    def test_enums_are_str_based(self):
        """Test that enums are str-based for JSON serialization."""
        from services.ebay.post_order_types import (
            CancellationStatus,
            RefundStatus,
            ReturnStatus,
        )

        # str-based enums can be used directly in JSON
        assert isinstance(CancellationStatus.CANCEL_REQUESTED.value, str)
        assert isinstance(ReturnStatus.RETURN_REQUESTED.value, str)
        assert isinstance(RefundStatus.PENDING.value, str)

        # They should also be comparable to strings
        assert CancellationStatus.CANCEL_REQUESTED == "CANCEL_REQUESTED"
