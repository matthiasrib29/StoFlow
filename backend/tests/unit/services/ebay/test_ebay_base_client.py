"""
Unit tests for EbayBaseClient.

Tests the OAuth2 client for eBay API interactions including:
- Credential loading from database
- Token caching and refresh
- API calls with error handling
- Rate limiting
- Sandbox vs production environments

Author: Claude
Date: 2026-01-08
"""

import base64
import time
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, Mock, patch

import pytest
import requests

from shared.exceptions import (
    EbayAPIError,
    EbayError,
    EbayOAuthError,
    MarketplaceRateLimitError,
)


class TestEbayBaseClientInit:
    """Tests for EbayBaseClient initialization and credential loading."""

    @pytest.fixture
    def mock_env_vars(self):
        """Fixture to mock environment variables."""
        with patch.dict(
            "os.environ",
            {
                "EBAY_CLIENT_ID": "test_client_id",
                "EBAY_CLIENT_SECRET": "test_client_secret",
                "EBAY_SANDBOX": "false",
            },
        ):
            yield

    @pytest.fixture
    def mock_ebay_credentials(self):
        """Create mock EbayCredentials object."""
        creds = MagicMock()
        creds.refresh_token = "test_refresh_token"
        creds.refresh_token_expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        creds.access_token = "test_access_token"
        return creds

    @pytest.fixture
    def mock_db_session(self, mock_ebay_credentials):
        """Create mock database session."""
        db = MagicMock()
        db.query.return_value.first.return_value = mock_ebay_credentials
        db.query.return_value.filter.return_value.first.return_value = None
        return db

    def test_init_loads_credentials(self, mock_env_vars, mock_db_session, mock_ebay_credentials):
        """Test that __init__ successfully loads credentials from database."""
        with patch(
            "services.ebay.ebay_base_client.EbayBaseClient._load_credentials"
        ) as mock_load:
            with patch("services.ebay.ebay_base_client.os.getenv") as mock_getenv:
                mock_getenv.side_effect = lambda key, default="": {
                    "EBAY_CLIENT_ID": "test_client_id",
                    "EBAY_CLIENT_SECRET": "test_client_secret",
                    "EBAY_SANDBOX": "false",
                }.get(key, default)

                from services.ebay.ebay_base_client import EbayBaseClient

                client = EbayBaseClient(mock_db_session, user_id=1)

                mock_load.assert_called_once()
                assert client.user_id == 1
                assert client.db == mock_db_session

    def test_init_raises_if_no_credentials(self, mock_env_vars):
        """Test that __init__ raises ValueError when no credentials found in DB."""
        mock_db = MagicMock()
        mock_db.query.return_value.first.return_value = None

        with patch("services.ebay.ebay_base_client.os.getenv") as mock_getenv:
            mock_getenv.side_effect = lambda key, default="": {
                "EBAY_CLIENT_ID": "test_client_id",
                "EBAY_CLIENT_SECRET": "test_client_secret",
                "EBAY_SANDBOX": "false",
            }.get(key, default)

            from services.ebay.ebay_base_client import EbayBaseClient

            with pytest.raises(ValueError) as exc_info:
                EbayBaseClient(mock_db, user_id=999)

            assert "n'a pas de compte eBay configuré" in str(exc_info.value)
            assert "999" in str(exc_info.value)

    def test_init_raises_if_missing_env_vars(self):
        """Test that __init__ raises ValueError when env vars are missing."""
        mock_db = MagicMock()
        mock_creds = MagicMock()
        mock_creds.refresh_token = "test_refresh_token"
        mock_creds.refresh_token_expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        mock_db.query.return_value.first.return_value = mock_creds

        with patch("services.ebay.ebay_base_client.os.getenv") as mock_getenv:
            # Missing EBAY_CLIENT_ID
            mock_getenv.side_effect = lambda key, default="": {
                "EBAY_CLIENT_ID": None,
                "EBAY_CLIENT_SECRET": "test_secret",
                "EBAY_SANDBOX": "false",
            }.get(key, default)

            from services.ebay.ebay_base_client import EbayBaseClient

            with pytest.raises(ValueError) as exc_info:
                EbayBaseClient(mock_db, user_id=1)

            assert "EBAY_CLIENT_ID" in str(exc_info.value)

    def test_init_raises_if_no_refresh_token(self):
        """Test that __init__ raises ValueError when refresh token is missing."""
        mock_db = MagicMock()
        mock_creds = MagicMock()
        mock_creds.refresh_token = None  # No refresh token
        mock_db.query.return_value.first.return_value = mock_creds

        with patch("services.ebay.ebay_base_client.os.getenv") as mock_getenv:
            mock_getenv.side_effect = lambda key, default="": {
                "EBAY_CLIENT_ID": "test_client_id",
                "EBAY_CLIENT_SECRET": "test_client_secret",
                "EBAY_SANDBOX": "false",
            }.get(key, default)

            from services.ebay.ebay_base_client import EbayBaseClient

            with pytest.raises(ValueError) as exc_info:
                EbayBaseClient(mock_db, user_id=1)

            assert "Refresh token manquant" in str(exc_info.value)


class TestEbayBaseClientSandboxVsProduction:
    """Tests for sandbox vs production URL selection."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock EbayBaseClient without calling __init__."""
        with patch(
            "services.ebay.ebay_base_client.EbayBaseClient.__init__", return_value=None
        ):
            from services.ebay.ebay_base_client import EbayBaseClient

            client = EbayBaseClient.__new__(EbayBaseClient)
            client.db = MagicMock()
            client.user_id = 1
            client.client_id = "test_client_id"
            client.client_secret = "test_client_secret"
            client.refresh_token = "test_refresh_token"
            client.refresh_token_expires_at = datetime.now(timezone.utc) + timedelta(days=30)
            client.ebay_credentials = MagicMock()
            client.marketplace_config = None
            client._token_cache = {}
            return client

    def test_sandbox_vs_production_urls(self, mock_client):
        """Test that sandbox and production use different URLs."""
        from services.ebay.ebay_base_client import EbayBaseClient

        # Test sandbox URL
        mock_client.sandbox = True
        mock_client.api_base = EbayBaseClient.API_BASE_SANDBOX
        assert mock_client.api_base == "https://api.sandbox.ebay.com"

        # Test production URL
        mock_client.sandbox = False
        mock_client.api_base = EbayBaseClient.API_BASE_PRODUCTION
        assert mock_client.api_base == "https://api.ebay.com"

    def test_commerce_api_urls(self, mock_client):
        """Test that Commerce API uses different base URLs."""
        from services.ebay.ebay_base_client import EbayBaseClient

        # Sandbox Commerce API
        assert EbayBaseClient.COMMERCE_API_BASE_SANDBOX == "https://apiz.sandbox.ebay.com"

        # Production Commerce API
        assert EbayBaseClient.COMMERCE_API_BASE_PRODUCTION == "https://apiz.ebay.com"


class TestRefreshAccessToken:
    """Tests for _refresh_access_token method."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock EbayBaseClient for testing refresh."""
        with patch(
            "services.ebay.ebay_base_client.EbayBaseClient.__init__", return_value=None
        ):
            from services.ebay.ebay_base_client import EbayBaseClient

            client = EbayBaseClient.__new__(EbayBaseClient)
            client.db = MagicMock()
            client.user_id = 1
            client.client_id = "test_client_id"
            client.client_secret = "test_client_secret"
            client.refresh_token = "test_refresh_token"
            client.refresh_token_expires_at = datetime.now(timezone.utc) + timedelta(days=30)
            client.ebay_credentials = MagicMock()
            client.sandbox = False
            client.api_base = "https://api.ebay.com"
            client._token_cache = {}
            return client

    def test_refresh_access_token_success(self, mock_client):
        """Test successful access token refresh."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "new_access_token",
            "token_type": "Bearer",
            "expires_in": 7200,
        }
        mock_response.raise_for_status = MagicMock()

        with patch("services.ebay.ebay_base_client.requests.post") as mock_post:
            mock_post.return_value = mock_response

            result = mock_client._refresh_access_token()

            assert result == "new_access_token"
            mock_post.assert_called_once()

            # Verify correct URL and headers
            call_args = mock_post.call_args
            assert "identity/v1/oauth2/token" in call_args[0][0]
            assert "Authorization" in call_args[1]["headers"]
            assert call_args[1]["data"]["grant_type"] == "refresh_token"

    def test_refresh_access_token_updates_token_rotation(self, mock_client):
        """Test that new refresh token is saved when eBay rotates it."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "refresh_token_expires_in": 47304000,
            "token_type": "Bearer",
            "expires_in": 7200,
        }
        mock_response.raise_for_status = MagicMock()

        with patch("services.ebay.ebay_base_client.requests.post") as mock_post:
            mock_post.return_value = mock_response

            result = mock_client._refresh_access_token()

            assert result == "new_access_token"
            # Verify refresh token was updated in credentials
            assert mock_client.ebay_credentials.refresh_token == "new_refresh_token"
            mock_client.db.commit.assert_called_once()
            # Verify local instance was updated
            assert mock_client.refresh_token == "new_refresh_token"

    def test_refresh_access_token_raises_on_http_error(self, mock_client):
        """Test that HTTP errors raise RuntimeError."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"error": "invalid_grant"}
        mock_response.text = "Unauthorized"
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=mock_response
        )

        with patch("services.ebay.ebay_base_client.requests.post") as mock_post:
            mock_post.return_value = mock_response

            with pytest.raises(RuntimeError) as exc_info:
                mock_client._refresh_access_token()

            assert "Erreur OAuth HTTP 401" in str(exc_info.value)


class TestCheckRefreshTokenExpiry:
    """Tests for _check_refresh_token_expiry method."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock EbayBaseClient for testing expiry checks."""
        with patch(
            "services.ebay.ebay_base_client.EbayBaseClient.__init__", return_value=None
        ):
            from services.ebay.ebay_base_client import EbayBaseClient

            client = EbayBaseClient.__new__(EbayBaseClient)
            client.user_id = 1
            return client

    def test_check_refresh_token_expiry_not_expired(self, mock_client):
        """Test that valid refresh token does not raise."""
        mock_client.refresh_token_expires_at = datetime.now(timezone.utc) + timedelta(days=30)

        # Should not raise
        mock_client._check_refresh_token_expiry()

    def test_check_refresh_token_expiry_raises_if_expired(self, mock_client):
        """Test that expired refresh token raises RuntimeError."""
        mock_client.refresh_token_expires_at = datetime.now(timezone.utc) - timedelta(days=1)

        with pytest.raises(RuntimeError) as exc_info:
            mock_client._check_refresh_token_expiry()

        assert "refresh token expired" in str(exc_info.value)
        assert "reconnect" in str(exc_info.value).lower()

    def test_check_refresh_token_expiry_none_is_ok(self, mock_client):
        """Test that None expiry (legacy) does not raise."""
        mock_client.refresh_token_expires_at = None

        # Should not raise (legacy token)
        mock_client._check_refresh_token_expiry()


class TestGetAccessToken:
    """Tests for get_access_token method with caching."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock EbayBaseClient for testing token retrieval."""
        with patch(
            "services.ebay.ebay_base_client.EbayBaseClient.__init__", return_value=None
        ):
            from services.ebay.ebay_base_client import EbayBaseClient

            client = EbayBaseClient.__new__(EbayBaseClient)
            client.db = MagicMock()
            client.user_id = 1
            client.client_id = "test_client_id"
            client.client_secret = "test_client_secret"
            client.refresh_token = "test_refresh_token"
            client.refresh_token_expires_at = datetime.now(timezone.utc) + timedelta(days=30)
            client.ebay_credentials = MagicMock()
            client.sandbox = False
            client.api_base = "https://api.ebay.com"
            # Clear class-level cache for test isolation
            EbayBaseClient._token_cache = {}
            client._token_max_age = 7000
            return client

    def test_get_access_token_uses_cache(self, mock_client):
        """Test that cached token is returned without refresh."""
        from services.ebay.ebay_base_client import EbayBaseClient

        # Pre-populate cache with valid token
        EbayBaseClient._token_cache[1] = ("cached_token", time.time())

        with patch.object(mock_client, "_refresh_access_token") as mock_refresh:
            result = mock_client.get_access_token()

            assert result == "cached_token"
            mock_refresh.assert_not_called()

    def test_get_access_token_refreshes_expired(self, mock_client):
        """Test that expired cached token triggers refresh."""
        from services.ebay.ebay_base_client import EbayBaseClient

        # Pre-populate cache with expired token (old timestamp)
        EbayBaseClient._token_cache[1] = ("old_token", time.time() - 8000)

        with patch.object(
            mock_client, "_refresh_access_token", return_value="new_token"
        ) as mock_refresh:
            result = mock_client.get_access_token()

            assert result == "new_token"
            mock_refresh.assert_called_once()

    def test_get_access_token_refreshes_if_not_cached(self, mock_client):
        """Test that missing cache entry triggers refresh."""
        from services.ebay.ebay_base_client import EbayBaseClient

        # Ensure cache is empty for this user
        EbayBaseClient._token_cache.pop(1, None)

        with patch.object(
            mock_client, "_refresh_access_token", return_value="fresh_token"
        ) as mock_refresh:
            result = mock_client.get_access_token()

            assert result == "fresh_token"
            mock_refresh.assert_called_once()
            # Verify token was cached
            assert 1 in EbayBaseClient._token_cache
            assert EbayBaseClient._token_cache[1][0] == "fresh_token"


class TestApiCall:
    """Tests for api_call method."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock EbayBaseClient for testing API calls."""
        with patch(
            "services.ebay.ebay_base_client.EbayBaseClient.__init__", return_value=None
        ):
            from services.ebay.ebay_base_client import EbayBaseClient

            client = EbayBaseClient.__new__(EbayBaseClient)
            client.db = MagicMock()
            client.user_id = 1
            client.sandbox = False
            client.api_base = "https://api.ebay.com"
            client.marketplace_config = None
            EbayBaseClient._token_cache = {}
            return client

    @pytest.fixture
    def mock_rate_limiter(self):
        """Create a mock RateLimiter."""
        limiter = MagicMock()
        limiter.wait = MagicMock()
        return limiter

    def test_api_call_success(self, mock_client, mock_rate_limiter):
        """Test successful API call returns JSON response."""
        mock_client._rate_limiter = mock_rate_limiter

        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.json.return_value = {"sku": "TEST-123", "data": "value"}

        with patch.object(mock_client, "get_access_token", return_value="test_token"):
            with patch("services.ebay.ebay_base_client.requests.request") as mock_request:
                mock_request.return_value = mock_response

                result = mock_client.api_call("GET", "/sell/inventory/v1/inventory_item/TEST-123")

                assert result == {"sku": "TEST-123", "data": "value"}
                mock_rate_limiter.wait.assert_called_once()
                mock_request.assert_called_once()

                # Verify correct headers
                call_kwargs = mock_request.call_args[1]
                assert call_kwargs["headers"]["Authorization"] == "Bearer test_token"
                assert call_kwargs["headers"]["Content-Type"] == "application/json"

    def test_api_call_handles_rate_limit(self, mock_client, mock_rate_limiter):
        """Test that 429 response raises MarketplaceRateLimitError."""
        mock_client._rate_limiter = mock_rate_limiter

        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "60"}
        mock_response.json.return_value = {"error": "rate_limit_exceeded"}

        with patch.object(mock_client, "get_access_token", return_value="test_token"):
            with patch("services.ebay.ebay_base_client.requests.request") as mock_request:
                mock_request.return_value = mock_response

                with pytest.raises(MarketplaceRateLimitError) as exc_info:
                    mock_client.api_call("GET", "/sell/inventory/v1/inventory_item")

                assert exc_info.value.platform == "ebay"
                assert exc_info.value.retry_after == 60

    def test_api_call_handles_401_raises_oauth_error(self, mock_client, mock_rate_limiter):
        """Test that 401 response raises EbayOAuthError."""
        mock_client._rate_limiter = mock_rate_limiter

        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 401
        mock_response.json.return_value = {"error": "invalid_token"}

        with patch.object(mock_client, "get_access_token", return_value="test_token"):
            with patch("services.ebay.ebay_base_client.requests.request") as mock_request:
                mock_request.return_value = mock_response

                with pytest.raises(EbayOAuthError) as exc_info:
                    mock_client.api_call("GET", "/sell/inventory/v1/inventory_item")

                assert exc_info.value.status_code == 401
                assert "401" in str(exc_info.value.message)

    def test_api_call_handles_403_raises_oauth_error(self, mock_client, mock_rate_limiter):
        """Test that 403 response raises EbayOAuthError."""
        mock_client._rate_limiter = mock_rate_limiter

        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 403
        mock_response.json.return_value = {"error": "forbidden"}

        with patch.object(mock_client, "get_access_token", return_value="test_token"):
            with patch("services.ebay.ebay_base_client.requests.request") as mock_request:
                mock_request.return_value = mock_response

                with pytest.raises(EbayOAuthError) as exc_info:
                    mock_client.api_call("GET", "/sell/inventory/v1/inventory_item")

                assert exc_info.value.status_code == 403

    def test_api_call_handles_other_errors(self, mock_client, mock_rate_limiter):
        """Test that other HTTP errors raise EbayAPIError."""
        mock_client._rate_limiter = mock_rate_limiter

        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_response.json.return_value = {"error": "internal_error"}

        with patch.object(mock_client, "get_access_token", return_value="test_token"):
            with patch("services.ebay.ebay_base_client.requests.request") as mock_request:
                mock_request.return_value = mock_response

                with pytest.raises(EbayAPIError) as exc_info:
                    mock_client.api_call("GET", "/sell/inventory/v1/inventory_item")

                assert exc_info.value.status_code == 500

    def test_api_call_handles_204_no_content(self, mock_client, mock_rate_limiter):
        """Test that 204 response returns None."""
        mock_client._rate_limiter = mock_rate_limiter

        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 204
        mock_response.text = ""

        with patch.object(mock_client, "get_access_token", return_value="test_token"):
            with patch("services.ebay.ebay_base_client.requests.request") as mock_request:
                mock_request.return_value = mock_response

                result = mock_client.api_call("DELETE", "/sell/inventory/v1/inventory_item/SKU")

                assert result is None

    def test_api_call_handles_201_without_body(self, mock_client, mock_rate_limiter):
        """Test that 201 response without body returns None."""
        mock_client._rate_limiter = mock_rate_limiter

        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 201
        mock_response.text = ""

        with patch.object(mock_client, "get_access_token", return_value="test_token"):
            with patch("services.ebay.ebay_base_client.requests.request") as mock_request:
                mock_request.return_value = mock_response

                result = mock_client.api_call("POST", "/sell/inventory/v1/inventory_item")

                assert result is None

    def test_api_call_handles_timeout(self, mock_client, mock_rate_limiter):
        """Test that timeout raises EbayError."""
        mock_client._rate_limiter = mock_rate_limiter

        with patch.object(mock_client, "get_access_token", return_value="test_token"):
            with patch("services.ebay.ebay_base_client.requests.request") as mock_request:
                mock_request.side_effect = requests.exceptions.Timeout("Connection timed out")

                with pytest.raises(EbayError) as exc_info:
                    mock_client.api_call("GET", "/sell/inventory/v1/inventory_item")

                assert "Timeout" in str(exc_info.value.message)

    def test_api_call_handles_network_error(self, mock_client, mock_rate_limiter):
        """Test that network errors raise EbayError."""
        mock_client._rate_limiter = mock_rate_limiter

        with patch.object(mock_client, "get_access_token", return_value="test_token"):
            with patch("services.ebay.ebay_base_client.requests.request") as mock_request:
                mock_request.side_effect = requests.exceptions.ConnectionError(
                    "Connection refused"
                )

                with pytest.raises(EbayError) as exc_info:
                    mock_client.api_call("GET", "/sell/inventory/v1/inventory_item")

                assert "Erreur réseau" in str(exc_info.value.message)

    def test_api_call_uses_commerce_api_base_for_commerce_endpoints(
        self, mock_client, mock_rate_limiter
    ):
        """Test that /commerce/* endpoints use Commerce API base URL."""
        mock_client._rate_limiter = mock_rate_limiter

        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "value"}

        with patch.object(mock_client, "get_access_token", return_value="test_token"):
            with patch("services.ebay.ebay_base_client.requests.request") as mock_request:
                mock_request.return_value = mock_response

                mock_client.api_call("GET", "/commerce/catalog/v1_beta/product")

                # Verify the Commerce API base URL was used
                call_args = mock_request.call_args
                # URL is passed as positional arg or in kwargs
                url = call_args.kwargs.get("url") or call_args.args[1] if len(call_args.args) > 1 else str(call_args)
                assert "apiz.ebay.com" in url

    def test_api_call_with_marketplace_content_language(self, mock_client, mock_rate_limiter):
        """Test that Content-Language is set from marketplace config."""
        mock_client._rate_limiter = mock_rate_limiter

        # Setup marketplace config
        mock_marketplace = MagicMock()
        mock_marketplace.get_content_language.return_value = "fr-FR"
        mock_client.marketplace_config = mock_marketplace

        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "value"}

        with patch.object(mock_client, "get_access_token", return_value="test_token"):
            with patch("services.ebay.ebay_base_client.requests.request") as mock_request:
                mock_request.return_value = mock_response

                mock_client.api_call("GET", "/sell/inventory/v1/inventory_item")

                call_kwargs = mock_request.call_args[1]
                assert call_kwargs["headers"]["Content-Language"] == "fr-FR"

    def test_api_call_default_content_language(self, mock_client, mock_rate_limiter):
        """Test that default Content-Language is en-US."""
        mock_client._rate_limiter = mock_rate_limiter
        mock_client.marketplace_config = None

        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "value"}

        with patch.object(mock_client, "get_access_token", return_value="test_token"):
            with patch("services.ebay.ebay_base_client.requests.request") as mock_request:
                mock_request.return_value = mock_response

                mock_client.api_call("GET", "/sell/inventory/v1/inventory_item")

                call_kwargs = mock_request.call_args[1]
                assert call_kwargs["headers"]["Content-Language"] == "en-US"


class TestNormalizeScopes:
    """Tests for _normalize_scopes method."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock EbayBaseClient for testing scope normalization."""
        with patch(
            "services.ebay.ebay_base_client.EbayBaseClient.__init__", return_value=None
        ):
            from services.ebay.ebay_base_client import EbayBaseClient

            client = EbayBaseClient.__new__(EbayBaseClient)
            client.SCOPES = EbayBaseClient.SCOPES
            return client

    def test_normalize_scopes_none_returns_api_scope(self, mock_client):
        """Test that None scopes returns api_scope."""
        result = mock_client._normalize_scopes(None)

        assert "https://api.ebay.com/oauth/api_scope" in result

    def test_normalize_scopes_string_input(self, mock_client):
        """Test that string input is normalized."""
        result = mock_client._normalize_scopes("sell.inventory")

        assert "https://api.ebay.com/oauth/api_scope/sell.inventory" in result

    def test_normalize_scopes_list_input(self, mock_client):
        """Test that list input is normalized."""
        result = mock_client._normalize_scopes(["sell.inventory", "sell.account"])

        assert "https://api.ebay.com/oauth/api_scope/sell.inventory" in result
        assert "https://api.ebay.com/oauth/api_scope/sell.account" in result

    def test_normalize_scopes_full_url_preserved(self, mock_client):
        """Test that full URLs are preserved."""
        full_url = "https://api.ebay.com/oauth/api_scope/custom"
        result = mock_client._normalize_scopes([full_url])

        assert full_url in result

    def test_normalize_scopes_removes_duplicates(self, mock_client):
        """Test that duplicate scopes are removed."""
        result = mock_client._normalize_scopes(["sell.inventory", "sell.inventory"])

        # Should only appear once
        assert result.count("sell.inventory") == 1
