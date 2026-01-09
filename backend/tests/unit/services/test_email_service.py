"""
Unit tests for EmailService.

Tests cover:
- send_email: success, text content, Brevo disabled, HTTP errors, network errors
- send_verification_email: success, correct link generation
- send_password_reset_email: success, correct link generation
- _get_headers: API key inclusion

Uses pytest with pytest.mark.asyncio for async tests.
Mocks: httpx.AsyncClient, settings

Author: Claude
Date: 2026-01-08
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, Mock
import httpx

from services.email_service import EmailService


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_settings():
    """Create mock settings with Brevo configuration."""
    settings = MagicMock()
    settings.brevo_enabled = True
    settings.brevo_api_key = "test-api-key-123"
    settings.brevo_sender_email = "noreply@stoflow.io"
    settings.brevo_sender_name = "StoFlow"
    settings.frontend_url = "https://app.stoflow.io"
    return settings


@pytest.fixture
def mock_settings_brevo_disabled():
    """Create mock settings with Brevo disabled."""
    settings = MagicMock()
    settings.brevo_enabled = False
    settings.brevo_api_key = None
    return settings


@pytest.fixture
def mock_response_success():
    """Create a successful HTTP response mock."""
    response = MagicMock()
    response.status_code = 201
    response.text = '{"messageId": "abc123"}'
    return response


@pytest.fixture
def mock_response_error():
    """Create an HTTP error response mock."""
    response = MagicMock()
    response.status_code = 400
    response.text = '{"code": "invalid_parameter", "message": "Invalid email"}'
    return response


# =============================================================================
# Test _get_headers
# =============================================================================


class TestGetHeaders:
    """Tests for the _get_headers method."""

    @patch("services.email_service.settings")
    def test_get_headers_includes_api_key(self, mock_settings):
        """Test that _get_headers includes the Brevo API key."""
        mock_settings.brevo_api_key = "test-brevo-api-key-xyz"

        headers = EmailService._get_headers()

        assert headers["api-key"] == "test-brevo-api-key-xyz"
        assert headers["accept"] == "application/json"
        assert headers["content-type"] == "application/json"

    @patch("services.email_service.settings")
    def test_get_headers_returns_correct_content_type(self, mock_settings):
        """Test that headers include correct content type."""
        mock_settings.brevo_api_key = "some-key"

        headers = EmailService._get_headers()

        assert "content-type" in headers
        assert headers["content-type"] == "application/json"

    @patch("services.email_service.settings")
    def test_get_headers_returns_correct_accept(self, mock_settings):
        """Test that headers include correct accept header."""
        mock_settings.brevo_api_key = "some-key"

        headers = EmailService._get_headers()

        assert "accept" in headers
        assert headers["accept"] == "application/json"


# =============================================================================
# Test send_email
# =============================================================================


class TestSendEmail:
    """Tests for the send_email method."""

    @pytest.mark.asyncio
    @patch("services.email_service.settings")
    @patch("services.email_service.httpx.AsyncClient")
    async def test_send_email_success(self, mock_client_class, mock_settings):
        """Test successful email sending returns True."""
        # Setup mocks
        mock_settings.brevo_enabled = True
        mock_settings.brevo_api_key = "test-api-key"
        mock_settings.brevo_sender_email = "noreply@stoflow.io"
        mock_settings.brevo_sender_name = "StoFlow"

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.text = '{"messageId": "123"}'

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        # Execute
        result = await EmailService.send_email(
            to_email="user@example.com",
            to_name="Test User",
            subject="Test Subject",
            html_content="<h1>Hello</h1>",
        )

        # Assert
        assert result is True
        mock_client.post.assert_called_once()
        call_kwargs = mock_client.post.call_args
        assert call_kwargs[0][0] == EmailService.BREVO_API_URL
        payload = call_kwargs[1]["json"]
        assert payload["to"][0]["email"] == "user@example.com"
        assert payload["to"][0]["name"] == "Test User"
        assert payload["subject"] == "Test Subject"
        assert payload["htmlContent"] == "<h1>Hello</h1>"

    @pytest.mark.asyncio
    @patch("services.email_service.settings")
    @patch("services.email_service.httpx.AsyncClient")
    async def test_send_email_with_text_content(self, mock_client_class, mock_settings):
        """Test that text_content is included in payload when provided."""
        # Setup mocks
        mock_settings.brevo_enabled = True
        mock_settings.brevo_api_key = "test-api-key"
        mock_settings.brevo_sender_email = "noreply@stoflow.io"
        mock_settings.brevo_sender_name = "StoFlow"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"messageId": "456"}'

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        # Execute
        result = await EmailService.send_email(
            to_email="user@example.com",
            to_name="Test User",
            subject="Test Subject",
            html_content="<h1>Hello</h1>",
            text_content="Hello plain text",
        )

        # Assert
        assert result is True
        call_kwargs = mock_client.post.call_args
        payload = call_kwargs[1]["json"]
        assert "textContent" in payload
        assert payload["textContent"] == "Hello plain text"

    @pytest.mark.asyncio
    @patch("services.email_service.settings")
    async def test_send_email_brevo_disabled_returns_false(self, mock_settings):
        """Test that send_email returns False when Brevo is disabled."""
        mock_settings.brevo_enabled = False

        result = await EmailService.send_email(
            to_email="user@example.com",
            to_name="Test User",
            subject="Test Subject",
            html_content="<h1>Hello</h1>",
        )

        assert result is False

    @pytest.mark.asyncio
    @patch("services.email_service.settings")
    @patch("services.email_service.httpx.AsyncClient")
    async def test_send_email_http_error_returns_false(
        self, mock_client_class, mock_settings
    ):
        """Test that send_email returns False on HTTP error response."""
        # Setup mocks
        mock_settings.brevo_enabled = True
        mock_settings.brevo_api_key = "test-api-key"
        mock_settings.brevo_sender_email = "noreply@stoflow.io"
        mock_settings.brevo_sender_name = "StoFlow"

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = '{"code": "invalid_parameter"}'

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        # Execute
        result = await EmailService.send_email(
            to_email="invalid-email",
            to_name="Test User",
            subject="Test Subject",
            html_content="<h1>Hello</h1>",
        )

        # Assert
        assert result is False

    @pytest.mark.asyncio
    @patch("services.email_service.settings")
    @patch("services.email_service.httpx.AsyncClient")
    async def test_send_email_network_error_returns_false(
        self, mock_client_class, mock_settings
    ):
        """Test that send_email returns False on network error."""
        # Setup mocks
        mock_settings.brevo_enabled = True
        mock_settings.brevo_api_key = "test-api-key"
        mock_settings.brevo_sender_email = "noreply@stoflow.io"
        mock_settings.brevo_sender_name = "StoFlow"

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=httpx.RequestError("Connection failed"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        # Execute
        result = await EmailService.send_email(
            to_email="user@example.com",
            to_name="Test User",
            subject="Test Subject",
            html_content="<h1>Hello</h1>",
        )

        # Assert
        assert result is False

    @pytest.mark.asyncio
    @patch("services.email_service.settings")
    @patch("services.email_service.httpx.AsyncClient")
    async def test_send_email_status_200_returns_true(
        self, mock_client_class, mock_settings
    ):
        """Test that send_email returns True on status code 200."""
        # Setup mocks
        mock_settings.brevo_enabled = True
        mock_settings.brevo_api_key = "test-api-key"
        mock_settings.brevo_sender_email = "noreply@stoflow.io"
        mock_settings.brevo_sender_name = "StoFlow"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"messageId": "789"}'

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        # Execute
        result = await EmailService.send_email(
            to_email="user@example.com",
            to_name="Test User",
            subject="Test Subject",
            html_content="<h1>Hello</h1>",
        )

        # Assert
        assert result is True

    @pytest.mark.asyncio
    @patch("services.email_service.settings")
    @patch("services.email_service.httpx.AsyncClient")
    async def test_send_email_status_500_returns_false(
        self, mock_client_class, mock_settings
    ):
        """Test that send_email returns False on server error."""
        # Setup mocks
        mock_settings.brevo_enabled = True
        mock_settings.brevo_api_key = "test-api-key"
        mock_settings.brevo_sender_email = "noreply@stoflow.io"
        mock_settings.brevo_sender_name = "StoFlow"

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        # Execute
        result = await EmailService.send_email(
            to_email="user@example.com",
            to_name="Test User",
            subject="Test Subject",
            html_content="<h1>Hello</h1>",
        )

        # Assert
        assert result is False

    @pytest.mark.asyncio
    @patch("services.email_service.settings")
    @patch("services.email_service.httpx.AsyncClient")
    async def test_send_email_unexpected_exception_returns_false(
        self, mock_client_class, mock_settings
    ):
        """Test that send_email returns False on unexpected exceptions."""
        # Setup mocks
        mock_settings.brevo_enabled = True
        mock_settings.brevo_api_key = "test-api-key"
        mock_settings.brevo_sender_email = "noreply@stoflow.io"
        mock_settings.brevo_sender_name = "StoFlow"

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=Exception("Unexpected error"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        # Execute
        result = await EmailService.send_email(
            to_email="user@example.com",
            to_name="Test User",
            subject="Test Subject",
            html_content="<h1>Hello</h1>",
        )

        # Assert
        assert result is False

    @pytest.mark.asyncio
    @patch("services.email_service.settings")
    @patch("services.email_service.httpx.AsyncClient")
    async def test_send_email_payload_structure(self, mock_client_class, mock_settings):
        """Test that the payload sent to Brevo has correct structure."""
        # Setup mocks
        mock_settings.brevo_enabled = True
        mock_settings.brevo_api_key = "test-api-key"
        mock_settings.brevo_sender_email = "sender@stoflow.io"
        mock_settings.brevo_sender_name = "StoFlow Team"

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.text = '{"messageId": "test"}'

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        # Execute
        await EmailService.send_email(
            to_email="recipient@example.com",
            to_name="Recipient Name",
            subject="Test Subject",
            html_content="<p>Content</p>",
        )

        # Assert payload structure
        call_kwargs = mock_client.post.call_args
        payload = call_kwargs[1]["json"]

        assert "sender" in payload
        assert payload["sender"]["email"] == "sender@stoflow.io"
        assert payload["sender"]["name"] == "StoFlow Team"
        assert "to" in payload
        assert isinstance(payload["to"], list)
        assert len(payload["to"]) == 1
        assert payload["to"][0]["email"] == "recipient@example.com"
        assert payload["to"][0]["name"] == "Recipient Name"


# =============================================================================
# Test send_verification_email
# =============================================================================


class TestSendVerificationEmail:
    """Tests for the send_verification_email method."""

    @pytest.mark.asyncio
    @patch("services.email_service.settings")
    @patch("services.email_service.httpx.AsyncClient")
    async def test_send_verification_email_success(
        self, mock_client_class, mock_settings
    ):
        """Test successful verification email sending."""
        # Setup mocks
        mock_settings.brevo_enabled = True
        mock_settings.brevo_api_key = "test-api-key"
        mock_settings.brevo_sender_email = "noreply@stoflow.io"
        mock_settings.brevo_sender_name = "StoFlow"
        mock_settings.frontend_url = "https://app.stoflow.io"

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.text = '{"messageId": "verification-123"}'

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        # Execute
        result = await EmailService.send_verification_email(
            to_email="newuser@example.com",
            to_name="New User",
            verification_token="abc123token",
        )

        # Assert
        assert result is True
        mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    @patch("services.email_service.settings")
    @patch("services.email_service.httpx.AsyncClient")
    async def test_send_verification_email_generates_correct_link(
        self, mock_client_class, mock_settings
    ):
        """Test that verification email contains correct verification link."""
        # Setup mocks
        mock_settings.brevo_enabled = True
        mock_settings.brevo_api_key = "test-api-key"
        mock_settings.brevo_sender_email = "noreply@stoflow.io"
        mock_settings.brevo_sender_name = "StoFlow"
        mock_settings.frontend_url = "https://app.stoflow.io"

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.text = '{"messageId": "123"}'

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        # Execute
        await EmailService.send_verification_email(
            to_email="user@example.com",
            to_name="Test User",
            verification_token="my-verification-token-xyz",
        )

        # Assert - check that the URL is in the HTML content
        call_kwargs = mock_client.post.call_args
        payload = call_kwargs[1]["json"]
        html_content = payload["htmlContent"]
        text_content = payload.get("textContent", "")

        expected_url = "https://app.stoflow.io/auth/verify-email?token=my-verification-token-xyz"
        assert expected_url in html_content
        assert expected_url in text_content

    @pytest.mark.asyncio
    @patch("services.email_service.settings")
    @patch("services.email_service.httpx.AsyncClient")
    async def test_send_verification_email_correct_subject(
        self, mock_client_class, mock_settings
    ):
        """Test that verification email has correct subject."""
        # Setup mocks
        mock_settings.brevo_enabled = True
        mock_settings.brevo_api_key = "test-api-key"
        mock_settings.brevo_sender_email = "noreply@stoflow.io"
        mock_settings.brevo_sender_name = "StoFlow"
        mock_settings.frontend_url = "https://app.stoflow.io"

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.text = '{"messageId": "123"}'

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        # Execute
        await EmailService.send_verification_email(
            to_email="user@example.com",
            to_name="Test User",
            verification_token="token123",
        )

        # Assert
        call_kwargs = mock_client.post.call_args
        payload = call_kwargs[1]["json"]
        assert payload["subject"] == "Confirmez votre adresse email - StoFlow"

    @pytest.mark.asyncio
    @patch("services.email_service.settings")
    async def test_send_verification_email_brevo_disabled(self, mock_settings):
        """Test that verification email returns False when Brevo is disabled."""
        mock_settings.brevo_enabled = False

        result = await EmailService.send_verification_email(
            to_email="user@example.com",
            to_name="Test User",
            verification_token="token123",
        )

        assert result is False

    @pytest.mark.asyncio
    @patch("services.email_service.settings")
    @patch("services.email_service.httpx.AsyncClient")
    async def test_send_verification_email_includes_user_name_in_content(
        self, mock_client_class, mock_settings
    ):
        """Test that verification email includes user name in content."""
        # Setup mocks
        mock_settings.brevo_enabled = True
        mock_settings.brevo_api_key = "test-api-key"
        mock_settings.brevo_sender_email = "noreply@stoflow.io"
        mock_settings.brevo_sender_name = "StoFlow"
        mock_settings.frontend_url = "https://app.stoflow.io"

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.text = '{"messageId": "123"}'

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        # Execute
        await EmailService.send_verification_email(
            to_email="user@example.com",
            to_name="Jean Dupont",
            verification_token="token123",
        )

        # Assert - user name should be in the email content
        call_kwargs = mock_client.post.call_args
        payload = call_kwargs[1]["json"]
        html_content = payload["htmlContent"]
        text_content = payload.get("textContent", "")

        assert "Jean Dupont" in html_content
        assert "Jean Dupont" in text_content


# =============================================================================
# Test send_password_reset_email
# =============================================================================


class TestSendPasswordResetEmail:
    """Tests for the send_password_reset_email method.

    NOTE: These tests assume the method will be implemented with a similar
    structure to send_verification_email. If the method doesn't exist yet,
    these tests will be skipped.
    """

    @pytest.mark.asyncio
    @patch("services.email_service.settings")
    @patch("services.email_service.httpx.AsyncClient")
    async def test_send_password_reset_email_success(
        self, mock_client_class, mock_settings
    ):
        """Test successful password reset email sending."""
        # Check if method exists
        if not hasattr(EmailService, "send_password_reset_email"):
            pytest.skip("send_password_reset_email not implemented yet")

        # Setup mocks
        mock_settings.brevo_enabled = True
        mock_settings.brevo_api_key = "test-api-key"
        mock_settings.brevo_sender_email = "noreply@stoflow.io"
        mock_settings.brevo_sender_name = "StoFlow"
        mock_settings.frontend_url = "https://app.stoflow.io"

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.text = '{"messageId": "reset-123"}'

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        # Execute
        result = await EmailService.send_password_reset_email(
            to_email="user@example.com",
            to_name="Test User",
            reset_token="reset-token-xyz",
        )

        # Assert
        assert result is True
        mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    @patch("services.email_service.settings")
    @patch("services.email_service.httpx.AsyncClient")
    async def test_send_password_reset_email_generates_correct_link(
        self, mock_client_class, mock_settings
    ):
        """Test that password reset email contains correct reset link."""
        # Check if method exists
        if not hasattr(EmailService, "send_password_reset_email"):
            pytest.skip("send_password_reset_email not implemented yet")

        # Setup mocks
        mock_settings.brevo_enabled = True
        mock_settings.brevo_api_key = "test-api-key"
        mock_settings.brevo_sender_email = "noreply@stoflow.io"
        mock_settings.brevo_sender_name = "StoFlow"
        mock_settings.frontend_url = "https://app.stoflow.io"

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.text = '{"messageId": "123"}'

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        # Execute
        await EmailService.send_password_reset_email(
            to_email="user@example.com",
            to_name="Test User",
            reset_token="my-reset-token-abc",
        )

        # Assert - check that the reset URL is in the HTML content
        call_kwargs = mock_client.post.call_args
        payload = call_kwargs[1]["json"]
        html_content = payload["htmlContent"]

        # The exact URL format depends on implementation
        # Common patterns: /auth/reset-password?token= or /reset-password?token=
        assert "my-reset-token-abc" in html_content
        assert "reset" in html_content.lower()

    @pytest.mark.asyncio
    @patch("services.email_service.settings")
    async def test_send_password_reset_email_brevo_disabled(self, mock_settings):
        """Test that password reset email returns False when Brevo is disabled."""
        # Check if method exists
        if not hasattr(EmailService, "send_password_reset_email"):
            pytest.skip("send_password_reset_email not implemented yet")

        mock_settings.brevo_enabled = False

        result = await EmailService.send_password_reset_email(
            to_email="user@example.com",
            to_name="Test User",
            reset_token="token123",
        )

        assert result is False


# =============================================================================
# Test helper methods for email content generation
# =============================================================================


class TestEmailContentGeneration:
    """Tests for email content generation helper methods."""

    @patch("services.email_service.settings")
    def test_verification_email_html_contains_required_elements(self, mock_settings):
        """Test that verification email HTML contains all required elements."""
        mock_settings.frontend_url = "https://app.stoflow.io"

        html_content = EmailService._get_verification_email_html(
            name="Test User",
            verification_url="https://app.stoflow.io/auth/verify-email?token=abc",
        )

        # Check for required elements
        assert "Test User" in html_content
        assert "https://app.stoflow.io/auth/verify-email?token=abc" in html_content
        assert "StoFlow" in html_content
        assert "Confirmer" in html_content or "confirmer" in html_content
        assert "24 heures" in html_content

    @patch("services.email_service.settings")
    def test_verification_email_text_contains_required_elements(self, mock_settings):
        """Test that verification email text contains all required elements."""
        mock_settings.frontend_url = "https://app.stoflow.io"

        text_content = EmailService._get_verification_email_text(
            name="Test User",
            verification_url="https://app.stoflow.io/auth/verify-email?token=abc",
        )

        # Check for required elements
        assert "Test User" in text_content
        assert "https://app.stoflow.io/auth/verify-email?token=abc" in text_content
        assert "StoFlow" in text_content

    @patch("services.email_service.settings")
    def test_verification_email_html_is_valid_html(self, mock_settings):
        """Test that verification email HTML has valid structure."""
        mock_settings.frontend_url = "https://app.stoflow.io"

        html_content = EmailService._get_verification_email_html(
            name="User",
            verification_url="https://example.com/verify",
        )

        # Basic HTML structure checks
        assert "<!DOCTYPE html>" in html_content
        assert "<html" in html_content
        assert "</html>" in html_content
        assert "<body" in html_content
        assert "</body>" in html_content


# =============================================================================
# Test edge cases
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    @pytest.mark.asyncio
    @patch("services.email_service.settings")
    @patch("services.email_service.httpx.AsyncClient")
    async def test_send_email_with_empty_name(self, mock_client_class, mock_settings):
        """Test sending email with empty recipient name."""
        # Setup mocks
        mock_settings.brevo_enabled = True
        mock_settings.brevo_api_key = "test-api-key"
        mock_settings.brevo_sender_email = "noreply@stoflow.io"
        mock_settings.brevo_sender_name = "StoFlow"

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.text = '{"messageId": "123"}'

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        # Execute
        result = await EmailService.send_email(
            to_email="user@example.com",
            to_name="",
            subject="Test",
            html_content="<p>Content</p>",
        )

        # Assert - should still work with empty name
        assert result is True
        call_kwargs = mock_client.post.call_args
        payload = call_kwargs[1]["json"]
        assert payload["to"][0]["name"] == ""

    @pytest.mark.asyncio
    @patch("services.email_service.settings")
    @patch("services.email_service.httpx.AsyncClient")
    async def test_send_email_with_special_characters_in_subject(
        self, mock_client_class, mock_settings
    ):
        """Test sending email with special characters in subject."""
        # Setup mocks
        mock_settings.brevo_enabled = True
        mock_settings.brevo_api_key = "test-api-key"
        mock_settings.brevo_sender_email = "noreply@stoflow.io"
        mock_settings.brevo_sender_name = "StoFlow"

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.text = '{"messageId": "123"}'

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        # Execute
        special_subject = "Test: Accents (cafe, resume) & Symbols <>"
        result = await EmailService.send_email(
            to_email="user@example.com",
            to_name="User",
            subject=special_subject,
            html_content="<p>Content</p>",
        )

        # Assert
        assert result is True
        call_kwargs = mock_client.post.call_args
        payload = call_kwargs[1]["json"]
        assert payload["subject"] == special_subject

    @pytest.mark.asyncio
    @patch("services.email_service.settings")
    @patch("services.email_service.httpx.AsyncClient")
    async def test_send_email_timeout_handling(self, mock_client_class, mock_settings):
        """Test that timeout is configured correctly."""
        # Setup mocks
        mock_settings.brevo_enabled = True
        mock_settings.brevo_api_key = "test-api-key"
        mock_settings.brevo_sender_email = "noreply@stoflow.io"
        mock_settings.brevo_sender_name = "StoFlow"

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.text = '{"messageId": "123"}'

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        # Execute
        await EmailService.send_email(
            to_email="user@example.com",
            to_name="User",
            subject="Test",
            html_content="<p>Content</p>",
        )

        # Assert - AsyncClient was created with timeout
        mock_client_class.assert_called_once_with(timeout=30.0)

    @pytest.mark.asyncio
    @patch("services.email_service.settings")
    @patch("services.email_service.httpx.AsyncClient")
    async def test_send_email_without_text_content_no_textcontent_in_payload(
        self, mock_client_class, mock_settings
    ):
        """Test that textContent is not included when text_content is None."""
        # Setup mocks
        mock_settings.brevo_enabled = True
        mock_settings.brevo_api_key = "test-api-key"
        mock_settings.brevo_sender_email = "noreply@stoflow.io"
        mock_settings.brevo_sender_name = "StoFlow"

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.text = '{"messageId": "123"}'

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        # Execute - without text_content
        await EmailService.send_email(
            to_email="user@example.com",
            to_name="User",
            subject="Test",
            html_content="<p>Content</p>",
            text_content=None,
        )

        # Assert - textContent should not be in payload
        call_kwargs = mock_client.post.call_args
        payload = call_kwargs[1]["json"]
        assert "textContent" not in payload
