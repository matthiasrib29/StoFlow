"""
Unit tests for EbayTradingClient.

Tests the eBay Trading API XML client for seller information retrieval including:
- GetUser API calls
- XML request building
- XML response parsing
- Error handling
- Safe mode operations

Author: Claude
Date: 2026-01-08
"""

from unittest.mock import MagicMock, Mock, patch

import pytest
import requests


class TestEbayTradingClientInit:
    """Tests for EbayTradingClient initialization."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock EbayTradingClient without calling __init__."""
        with patch(
            "services.ebay.ebay_trading_client.EbayTradingClient.__init__",
            return_value=None,
        ):
            from services.ebay.ebay_trading_client import EbayTradingClient

            client = EbayTradingClient.__new__(EbayTradingClient)
            client.db = MagicMock()
            client.user_id = 1
            client.sandbox = False
            return client

    def test_class_constants(self):
        """Test that class URL constants are correct."""
        from services.ebay.ebay_trading_client import EbayTradingClient

        assert EbayTradingClient.TRADING_API_URL_PRODUCTION == "https://api.ebay.com/ws/api.dll"
        assert EbayTradingClient.TRADING_API_URL_SANDBOX == "https://api.sandbox.ebay.com/ws/api.dll"

    def test_inherits_from_ebay_base_client(self):
        """Test that EbayTradingClient inherits from EbayBaseClient."""
        from services.ebay.ebay_base_client import EbayBaseClient
        from services.ebay.ebay_trading_client import EbayTradingClient

        assert issubclass(EbayTradingClient, EbayBaseClient)


class TestBuildGetUserRequest:
    """Tests for _build_get_user_request method."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock EbayTradingClient for testing XML building."""
        with patch(
            "services.ebay.ebay_trading_client.EbayTradingClient.__init__",
            return_value=None,
        ):
            from services.ebay.ebay_trading_client import EbayTradingClient

            client = EbayTradingClient.__new__(EbayTradingClient)
            return client

    def test_build_get_user_request_without_user_id(self, mock_client):
        """Test building request without user ID returns authenticated user request."""
        xml_request = mock_client._build_get_user_request()

        assert '<?xml version="1.0" encoding="utf-8"?>' in xml_request
        assert "<GetUserRequest" in xml_request
        assert "xmlns=\"urn:ebay:apis:eBLBaseComponents\"" in xml_request
        assert "<DetailLevel>ReturnAll</DetailLevel>" in xml_request
        assert "<UserID>" not in xml_request or "</UserID>" in xml_request

    def test_build_get_user_request_with_user_id(self, mock_client):
        """Test building request with user ID includes UserID element."""
        xml_request = mock_client._build_get_user_request("test_user_123")

        assert '<?xml version="1.0" encoding="utf-8"?>' in xml_request
        assert "<GetUserRequest" in xml_request
        assert "<UserID>test_user_123</UserID>" in xml_request
        assert "<DetailLevel>ReturnAll</DetailLevel>" in xml_request

    def test_build_get_user_request_xml_structure(self, mock_client):
        """Test that XML structure is valid and complete."""
        xml_request = mock_client._build_get_user_request()

        assert "<GetUserRequest" in xml_request
        assert "</GetUserRequest>" in xml_request
        assert "<RequesterCredentials>" in xml_request
        assert "</RequesterCredentials>" in xml_request
        assert "<eBayAuthToken>" in xml_request


class TestParseGetUserResponse:
    """Tests for _parse_get_user_response method."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock EbayTradingClient for testing XML parsing."""
        with patch(
            "services.ebay.ebay_trading_client.EbayTradingClient.__init__",
            return_value=None,
        ):
            from services.ebay.ebay_trading_client import EbayTradingClient

            client = EbayTradingClient.__new__(EbayTradingClient)
            return client

    def test_parse_get_user_response_success(self, mock_client):
        """Test successful parsing of GetUser response."""
        xml_response = """<?xml version="1.0" encoding="UTF-8"?>
        <GetUserResponse xmlns="urn:ebay:apis:eBLBaseComponents">
            <Ack>Success</Ack>
            <User>
                <UserID>test_seller</UserID>
                <Email>seller@example.com</Email>
                <RegistrationDate>2020-01-15T10:30:00.000Z</RegistrationDate>
                <Site>US</Site>
                <Status>Confirmed</Status>
                <FeedbackScore>1500</FeedbackScore>
                <PositiveFeedbackPercent>99.5</PositiveFeedbackPercent>
            </User>
        </GetUserResponse>"""

        result = mock_client._parse_get_user_response(xml_response)

        assert result["user_id"] == "test_seller"
        assert result["username"] == "test_seller"
        assert result["email"] == "seller@example.com"
        assert result["site"] == "US"
        assert result["status"] == "Confirmed"
        assert result["feedback_score"] == 1500
        assert result["positive_feedback_percent"] == 99.5

    def test_parse_get_user_response_with_seller_info(self, mock_client):
        """Test parsing response with SellerInfo element."""
        xml_response = """<?xml version="1.0" encoding="UTF-8"?>
        <GetUserResponse xmlns="urn:ebay:apis:eBLBaseComponents">
            <Ack>Success</Ack>
            <User>
                <UserID>pro_seller</UserID>
                <Email>pro@example.com</Email>
                <RegistrationDate>2018-05-10T08:00:00.000Z</RegistrationDate>
                <Site>FR</Site>
                <Status>Confirmed</Status>
                <FeedbackScore>5000</FeedbackScore>
                <PositiveFeedbackPercent>100.0</PositiveFeedbackPercent>
                <SellerInfo>
                    <SellerLevel>TopRated</SellerLevel>
                    <TopRatedSeller>true</TopRatedSeller>
                </SellerInfo>
            </User>
        </GetUserResponse>"""

        result = mock_client._parse_get_user_response(xml_response)

        assert result["user_id"] == "pro_seller"
        assert result["seller_level"] == "TopRated"
        assert result["top_rated_seller"] is True

    def test_parse_get_user_response_not_top_rated(self, mock_client):
        """Test parsing response with TopRatedSeller=false."""
        xml_response = """<?xml version="1.0" encoding="UTF-8"?>
        <GetUserResponse xmlns="urn:ebay:apis:eBLBaseComponents">
            <Ack>Success</Ack>
            <User>
                <UserID>basic_seller</UserID>
                <Email>basic@example.com</Email>
                <Site>US</Site>
                <Status>Confirmed</Status>
                <FeedbackScore>100</FeedbackScore>
                <PositiveFeedbackPercent>98.0</PositiveFeedbackPercent>
                <SellerInfo>
                    <SellerLevel>Standard</SellerLevel>
                    <TopRatedSeller>false</TopRatedSeller>
                </SellerInfo>
            </User>
        </GetUserResponse>"""

        result = mock_client._parse_get_user_response(xml_response)

        assert result["seller_level"] == "Standard"
        assert result["top_rated_seller"] is False

    def test_parse_get_user_response_failure(self, mock_client):
        """Test parsing error response raises RuntimeError."""
        xml_response = """<?xml version="1.0" encoding="UTF-8"?>
        <GetUserResponse xmlns="urn:ebay:apis:eBLBaseComponents">
            <Ack>Failure</Ack>
            <Errors>
                <ShortMessage>Invalid token</ShortMessage>
                <LongMessage>The authentication token is invalid.</LongMessage>
            </Errors>
        </GetUserResponse>"""

        with pytest.raises(RuntimeError) as exc_info:
            mock_client._parse_get_user_response(xml_response)

        assert "GetUser failed" in str(exc_info.value)
        assert "Invalid token" in str(exc_info.value)

    def test_parse_get_user_response_no_user_element(self, mock_client):
        """Test parsing response without User element raises RuntimeError."""
        xml_response = """<?xml version="1.0" encoding="UTF-8"?>
        <GetUserResponse xmlns="urn:ebay:apis:eBLBaseComponents">
            <Ack>Success</Ack>
        </GetUserResponse>"""

        with pytest.raises(RuntimeError) as exc_info:
            mock_client._parse_get_user_response(xml_response)

        assert "No User element" in str(exc_info.value)

    def test_parse_get_user_response_warning_ack(self, mock_client):
        """Test parsing response with Warning Ack still succeeds."""
        xml_response = """<?xml version="1.0" encoding="UTF-8"?>
        <GetUserResponse xmlns="urn:ebay:apis:eBLBaseComponents">
            <Ack>Warning</Ack>
            <User>
                <UserID>warning_user</UserID>
                <Email>warn@example.com</Email>
                <Site>US</Site>
                <Status>Confirmed</Status>
                <FeedbackScore>500</FeedbackScore>
                <PositiveFeedbackPercent>97.0</PositiveFeedbackPercent>
            </User>
        </GetUserResponse>"""

        result = mock_client._parse_get_user_response(xml_response)

        assert result["user_id"] == "warning_user"
        assert result["feedback_score"] == 500

    def test_parse_get_user_response_missing_optional_fields(self, mock_client):
        """Test parsing response with missing optional fields uses defaults."""
        xml_response = """<?xml version="1.0" encoding="UTF-8"?>
        <GetUserResponse xmlns="urn:ebay:apis:eBLBaseComponents">
            <Ack>Success</Ack>
            <User>
                <UserID>minimal_user</UserID>
            </User>
        </GetUserResponse>"""

        result = mock_client._parse_get_user_response(xml_response)

        assert result["user_id"] == "minimal_user"
        assert result["email"] == ""
        assert result["site"] == ""
        assert result["feedback_score"] == 0
        assert result["positive_feedback_percent"] == 0.0


class TestGetUser:
    """Tests for get_user method."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock EbayTradingClient for testing get_user."""
        with patch(
            "services.ebay.ebay_trading_client.EbayTradingClient.__init__",
            return_value=None,
        ):
            from services.ebay.ebay_trading_client import EbayTradingClient

            client = EbayTradingClient.__new__(EbayTradingClient)
            client.db = MagicMock()
            client.user_id = 1
            client.sandbox = False
            return client

    def test_get_user_success_production(self, mock_client):
        """Test successful get_user call in production mode."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.text = """<?xml version="1.0" encoding="UTF-8"?>
        <GetUserResponse xmlns="urn:ebay:apis:eBLBaseComponents">
            <Ack>Success</Ack>
            <User>
                <UserID>test_seller</UserID>
                <Email>seller@example.com</Email>
                <Site>US</Site>
                <Status>Confirmed</Status>
                <FeedbackScore>1000</FeedbackScore>
                <PositiveFeedbackPercent>99.0</PositiveFeedbackPercent>
            </User>
        </GetUserResponse>"""

        with patch.object(mock_client, "get_access_token", return_value="test_token"):
            with patch("services.ebay.ebay_trading_client.requests.post") as mock_post:
                mock_post.return_value = mock_response

                result = mock_client.get_user()

                assert result["user_id"] == "test_seller"
                assert result["feedback_score"] == 1000

                # Verify correct URL for production
                call_args = mock_post.call_args
                assert "https://api.ebay.com/ws/api.dll" in call_args[0][0]

                # Verify correct headers
                headers = call_args[1]["headers"]
                assert headers["X-EBAY-API-CALL-NAME"] == "GetUser"
                assert headers["X-EBAY-API-IAF-TOKEN"] == "test_token"
                assert headers["Content-Type"] == "text/xml"

    def test_get_user_success_sandbox(self, mock_client):
        """Test successful get_user call in sandbox mode."""
        mock_client.sandbox = True

        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.text = """<?xml version="1.0" encoding="UTF-8"?>
        <GetUserResponse xmlns="urn:ebay:apis:eBLBaseComponents">
            <Ack>Success</Ack>
            <User>
                <UserID>sandbox_seller</UserID>
                <Site>US</Site>
                <Status>Confirmed</Status>
                <FeedbackScore>0</FeedbackScore>
                <PositiveFeedbackPercent>0.0</PositiveFeedbackPercent>
            </User>
        </GetUserResponse>"""

        with patch.object(mock_client, "get_access_token", return_value="sandbox_token"):
            with patch("services.ebay.ebay_trading_client.requests.post") as mock_post:
                mock_post.return_value = mock_response

                result = mock_client.get_user()

                # Verify correct URL for sandbox
                call_args = mock_post.call_args
                assert "https://api.sandbox.ebay.com/ws/api.dll" in call_args[0][0]

    def test_get_user_with_specific_user_id(self, mock_client):
        """Test get_user with specific user ID parameter."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.text = """<?xml version="1.0" encoding="UTF-8"?>
        <GetUserResponse xmlns="urn:ebay:apis:eBLBaseComponents">
            <Ack>Success</Ack>
            <User>
                <UserID>specific_user</UserID>
                <Site>US</Site>
                <Status>Confirmed</Status>
                <FeedbackScore>500</FeedbackScore>
                <PositiveFeedbackPercent>95.0</PositiveFeedbackPercent>
            </User>
        </GetUserResponse>"""

        with patch.object(mock_client, "get_access_token", return_value="test_token"):
            with patch("services.ebay.ebay_trading_client.requests.post") as mock_post:
                mock_post.return_value = mock_response

                result = mock_client.get_user("specific_user")

                # Verify XML request contains the specific user ID
                call_args = mock_post.call_args
                xml_data = call_args[1]["data"]
                assert "<UserID>specific_user</UserID>" in xml_data

    def test_get_user_http_error(self, mock_client):
        """Test get_user raises RuntimeError on HTTP error."""
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        with patch.object(mock_client, "get_access_token", return_value="test_token"):
            with patch("services.ebay.ebay_trading_client.requests.post") as mock_post:
                mock_post.return_value = mock_response

                with pytest.raises(RuntimeError) as exc_info:
                    mock_client.get_user()

                assert "Trading API error" in str(exc_info.value)
                assert "500" in str(exc_info.value)

    def test_get_user_api_failure_response(self, mock_client):
        """Test get_user raises RuntimeError on API Failure response."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.text = """<?xml version="1.0" encoding="UTF-8"?>
        <GetUserResponse xmlns="urn:ebay:apis:eBLBaseComponents">
            <Ack>Failure</Ack>
            <Errors>
                <ShortMessage>User not found</ShortMessage>
            </Errors>
        </GetUserResponse>"""

        with patch.object(mock_client, "get_access_token", return_value="test_token"):
            with patch("services.ebay.ebay_trading_client.requests.post") as mock_post:
                mock_post.return_value = mock_response

                with pytest.raises(RuntimeError) as exc_info:
                    mock_client.get_user()

                assert "GetUser failed" in str(exc_info.value)


class TestGetUserSafe:
    """Tests for get_user_safe method."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock EbayTradingClient for testing get_user_safe."""
        with patch(
            "services.ebay.ebay_trading_client.EbayTradingClient.__init__",
            return_value=None,
        ):
            from services.ebay.ebay_trading_client import EbayTradingClient

            client = EbayTradingClient.__new__(EbayTradingClient)
            client.db = MagicMock()
            client.user_id = 1
            client.sandbox = False
            return client

    def test_get_user_safe_success(self, mock_client):
        """Test get_user_safe returns user data on success."""
        expected_user = {
            "user_id": "test_user",
            "username": "test_user",
            "email": "test@example.com",
            "feedback_score": 100,
        }

        with patch.object(mock_client, "get_user", return_value=expected_user):
            result = mock_client.get_user_safe()

            assert result == expected_user

    def test_get_user_safe_returns_none_on_runtime_error(self, mock_client):
        """Test get_user_safe returns None on RuntimeError."""
        with patch.object(
            mock_client, "get_user", side_effect=RuntimeError("API error")
        ):
            result = mock_client.get_user_safe()

            assert result is None

    def test_get_user_safe_returns_none_on_request_exception(self, mock_client):
        """Test get_user_safe returns None on requests exception."""
        with patch.object(
            mock_client,
            "get_user",
            side_effect=requests.exceptions.RequestException("Network error"),
        ):
            result = mock_client.get_user_safe()

            assert result is None

    def test_get_user_safe_returns_none_on_timeout(self, mock_client):
        """Test get_user_safe returns None on timeout."""
        with patch.object(
            mock_client,
            "get_user",
            side_effect=requests.exceptions.Timeout("Request timed out"),
        ):
            result = mock_client.get_user_safe()

            assert result is None

    def test_get_user_safe_returns_none_on_connection_error(self, mock_client):
        """Test get_user_safe returns None on connection error."""
        with patch.object(
            mock_client,
            "get_user",
            side_effect=requests.exceptions.ConnectionError("Connection refused"),
        ):
            result = mock_client.get_user_safe()

            assert result is None
