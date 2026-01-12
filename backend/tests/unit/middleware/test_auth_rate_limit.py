"""
Unit tests for auth rate limiter.

Tests rate limiting protection on authentication endpoints.

Author: Claude
Date: 2026-01-12
"""

import asyncio
import pytest
from fastapi import HTTPException, Request
from unittest.mock import Mock

from middleware.auth_rate_limit import AuthRateLimiter


class TestAuthRateLimiter:
    """Test auth rate limiter functionality."""

    @pytest.fixture
    def rate_limiter(self):
        """Create a fresh rate limiter for each test."""
        return AuthRateLimiter()

    @pytest.fixture
    def mock_request(self):
        """Create a mock FastAPI request."""
        mock = Mock(spec=Request)
        mock.client = Mock()
        mock.client.host = "192.168.1.100"
        mock.headers = {}
        return mock

    @pytest.mark.asyncio
    async def test_login_rate_limit_allows_under_limit(self, rate_limiter, mock_request):
        """Requests under the limit should pass."""
        # Login limit: 5 attempts per 15 minutes
        for i in range(5):
            # Should not raise exception
            await rate_limiter.check_rate_limit(mock_request, "login")

    @pytest.mark.asyncio
    async def test_login_rate_limit_blocks_over_limit(self, rate_limiter, mock_request):
        """6th login attempt should be blocked."""
        # Login limit: 5 attempts per 15 minutes

        # First 5 should pass
        for i in range(5):
            await rate_limiter.check_rate_limit(mock_request, "login")

        # 6th should raise 429
        with pytest.raises(HTTPException) as exc_info:
            await rate_limiter.check_rate_limit(mock_request, "login")

        assert exc_info.value.status_code == 429
        assert "rate_limit_exceeded" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_different_ips_have_separate_limits(self, rate_limiter):
        """Different IPs should have independent rate limits."""
        # Create two different IPs
        mock_request1 = Mock(spec=Request)
        mock_request1.client = Mock()
        mock_request1.client.host = "192.168.1.100"
        mock_request1.headers = {}

        mock_request2 = Mock(spec=Request)
        mock_request2.client = Mock()
        mock_request2.client.host = "192.168.1.200"
        mock_request2.headers = {}

        # Max out IP1's limit
        for i in range(5):
            await rate_limiter.check_rate_limit(mock_request1, "login")

        # IP1 should be blocked
        with pytest.raises(HTTPException):
            await rate_limiter.check_rate_limit(mock_request1, "login")

        # IP2 should still work
        await rate_limiter.check_rate_limit(mock_request2, "login")

    @pytest.mark.asyncio
    async def test_different_endpoints_have_separate_limits(self, rate_limiter, mock_request):
        """Different endpoints should have independent rate limits."""
        # Max out login limit (5 attempts)
        for i in range(5):
            await rate_limiter.check_rate_limit(mock_request, "login")

        # Login should be blocked
        with pytest.raises(HTTPException):
            await rate_limiter.check_rate_limit(mock_request, "login")

        # Register should still work (3 attempts limit)
        await rate_limiter.check_rate_limit(mock_request, "register")

    @pytest.mark.asyncio
    async def test_register_rate_limit_blocks_spam_accounts(self, rate_limiter, mock_request):
        """Register endpoint should have 3 attempts per hour."""
        # Register limit: 3 attempts per 60 minutes

        # First 3 should pass
        for i in range(3):
            await rate_limiter.check_rate_limit(mock_request, "register")

        # 4th should raise 429
        with pytest.raises(HTTPException) as exc_info:
            await rate_limiter.check_rate_limit(mock_request, "register")

        assert exc_info.value.status_code == 429
        assert "register" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_refresh_rate_limit_prevents_token_exhaustion(self, rate_limiter, mock_request):
        """Refresh endpoint should have 10 attempts per 5 minutes."""
        # Refresh limit: 10 attempts per 5 minutes

        # First 10 should pass
        for i in range(10):
            await rate_limiter.check_rate_limit(mock_request, "refresh")

        # 11th should raise 429
        with pytest.raises(HTTPException) as exc_info:
            await rate_limiter.check_rate_limit(mock_request, "refresh")

        assert exc_info.value.status_code == 429
        assert "refresh" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_rate_limit_returns_retry_after_header(self, rate_limiter, mock_request):
        """Rate limit response should include Retry-After header."""
        # Max out login limit
        for i in range(5):
            await rate_limiter.check_rate_limit(mock_request, "login")

        # Check exception has retry_after
        with pytest.raises(HTTPException) as exc_info:
            await rate_limiter.check_rate_limit(mock_request, "login")

        assert "retry_after" in exc_info.value.detail
        assert exc_info.value.detail["retry_after"] > 0

    @pytest.mark.asyncio
    async def test_get_client_ip_from_x_forwarded_for(self, rate_limiter):
        """Should extract IP from X-Forwarded-For header."""
        mock_request = Mock(spec=Request)
        mock_request.headers = {"X-Forwarded-For": "10.0.0.1, 192.168.1.1"}
        mock_request.client = Mock()
        mock_request.client.host = "192.168.1.100"

        # Should use first IP from X-Forwarded-For
        client_ip = rate_limiter._get_client_ip(mock_request)
        assert client_ip == "10.0.0.1"

    @pytest.mark.asyncio
    async def test_get_client_ip_from_x_real_ip(self, rate_limiter):
        """Should extract IP from X-Real-IP header."""
        mock_request = Mock(spec=Request)
        mock_request.headers = {"X-Real-IP": "10.0.0.2"}
        mock_request.client = Mock()
        mock_request.client.host = "192.168.1.100"

        # Should use X-Real-IP
        client_ip = rate_limiter._get_client_ip(mock_request)
        assert client_ip == "10.0.0.2"

    @pytest.mark.asyncio
    async def test_reset_for_ip_clears_limits(self, rate_limiter, mock_request):
        """Reset should clear rate limits for an IP."""
        # Max out login limit
        for i in range(5):
            await rate_limiter.check_rate_limit(mock_request, "login")

        # Should be blocked
        with pytest.raises(HTTPException):
            await rate_limiter.check_rate_limit(mock_request, "login")

        # Reset limits
        await rate_limiter.reset_for_ip("192.168.1.100", "login")

        # Should work again
        await rate_limiter.check_rate_limit(mock_request, "login")

    @pytest.mark.asyncio
    async def test_no_limit_for_unconfigured_endpoint(self, rate_limiter, mock_request):
        """Endpoints without limits should not be rate limited."""
        # Call many times - should not raise exception
        for i in range(100):
            await rate_limiter.check_rate_limit(mock_request, "unknown_endpoint")
