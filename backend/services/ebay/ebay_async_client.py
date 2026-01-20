"""
eBay Async Base Client with OAuth2 and generic API calls.

Async version of EbayBaseClient using httpx for non-blocking I/O.
Designed for use in the standalone worker process.

Architecture:
- Uses httpx.AsyncClient for HTTP/2 support and connection pooling
- Async rate limiting via AsyncRateLimiter
- Token caching shared with sync client (thread-safe)
- Context manager pattern for proper resource cleanup

Author: Claude
Date: 2026-01-20
"""

import base64
import os
import time
from typing import Any, Optional

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.public.ebay_marketplace_config import MarketplaceConfig
from models.user.ebay_credentials import EbayCredentials
from shared.async_rate_limiter import AsyncRateLimiter
from shared.exceptions import (
    EbayAPIError,
    EbayError,
    EbayOAuthError,
    MarketplaceRateLimitError,
)
from shared.logging_setup import get_logger

logger = get_logger(__name__)


class EbayAsyncClient:
    """
    Async eBay client using httpx.

    Non-blocking HTTP client for use in async workers.
    Shares token cache with sync EbayBaseClient for compatibility.

    Usage:
        async with EbayAsyncClient(user_id=1) as client:
            data = await client.api_call("GET", "/sell/inventory/v1/inventory_item/SKU-123")

    Attributes:
        user_id: User ID for tenant isolation
        marketplace_id: Optional marketplace (EBAY_FR, EBAY_GB, etc.)
        sandbox: Whether to use sandbox environment
    """

    # API Base URLs
    API_BASE_SANDBOX = "https://api.sandbox.ebay.com"
    API_BASE_PRODUCTION = "https://api.ebay.com"

    # Commerce API Base URLs
    COMMERCE_API_BASE_SANDBOX = "https://apiz.sandbox.ebay.com"
    COMMERCE_API_BASE_PRODUCTION = "https://apiz.ebay.com"

    # Shared token cache with sync client (thread-safe reads)
    # Import from sync client to share cache
    _token_cache: dict[int, tuple[str, float]] = {}
    _token_max_age: int = 7000  # 1h56min

    # Rate limiter (shared per client instance)
    _rate_limiter: AsyncRateLimiter | None = None

    def __init__(
        self,
        user_id: int,
        marketplace_id: Optional[str] = None,
        sandbox: bool = False,
        timeout: float = 30.0,
    ):
        """
        Initialize async eBay client.

        Args:
            user_id: User ID for tenant isolation
            marketplace_id: Target marketplace (EBAY_FR, EBAY_GB, etc.)
            sandbox: Use sandbox environment
            timeout: Request timeout in seconds
        """
        self.user_id = user_id
        self.marketplace_id = marketplace_id
        self.sandbox = sandbox or os.getenv("EBAY_SANDBOX", "false").lower() == "true"
        self.timeout = timeout

        # API base URL
        self.api_base = self.API_BASE_SANDBOX if self.sandbox else self.API_BASE_PRODUCTION

        # HTTP client (created in __aenter__)
        self._client: httpx.AsyncClient | None = None

        # Rate limiter
        if self._rate_limiter is None:
            self._rate_limiter = AsyncRateLimiter(min_delay=0.3, max_delay=0.8)

        # Credentials (loaded lazily)
        self._credentials: EbayCredentials | None = None
        self._marketplace_config: MarketplaceConfig | None = None
        self._client_id: str | None = None
        self._client_secret: str | None = None
        self._refresh_token: str | None = None

    async def __aenter__(self) -> "EbayAsyncClient":
        """Create HTTP client on context entry."""
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            limits=httpx.Limits(
                max_connections=10,
                max_keepalive_connections=5,
            ),
            http2=True,  # Enable HTTP/2
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Close HTTP client on context exit."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _load_credentials(self, db: AsyncSession) -> None:
        """
        Load eBay credentials from database.

        Args:
            db: Async SQLAlchemy session with tenant schema

        Raises:
            ValueError: If credentials not found or incomplete
        """
        # Load credentials from user schema
        result = await db.execute(select(EbayCredentials).limit(1))
        self._credentials = result.scalar_one_or_none()

        if not self._credentials:
            raise ValueError(
                f"User {self.user_id} has no eBay account configured. "
                "Please configure credentials via /api/ebay/connect"
            )

        # Get client ID/secret from env
        self._client_id = os.getenv("EBAY_CLIENT_ID")
        self._client_secret = os.getenv("EBAY_CLIENT_SECRET")

        if not self._client_id or not self._client_secret:
            raise ValueError(
                "eBay credentials incomplete. "
                "Please configure EBAY_CLIENT_ID and EBAY_CLIENT_SECRET in .env"
            )

        if not self._credentials.refresh_token:
            raise ValueError(
                f"Refresh token missing for user {self.user_id}. "
                "Please complete OAuth flow."
            )

        self._refresh_token = self._credentials.refresh_token

        # Load marketplace config if specified
        if self.marketplace_id:
            result = await db.execute(
                select(MarketplaceConfig)
                .filter(MarketplaceConfig.marketplace_id == self.marketplace_id)
            )
            self._marketplace_config = result.scalar_one_or_none()
            if not self._marketplace_config:
                raise ValueError(f"Unknown marketplace: {self.marketplace_id}")

    async def _refresh_access_token(self) -> str:
        """
        Refresh the OAuth2 access token.

        Returns:
            New access token

        Raises:
            RuntimeError: If refresh fails
        """
        if not self._client:
            raise RuntimeError("HTTP client not initialized. Use async context manager.")

        token_url = f"{self.api_base}/identity/v1/oauth2/token"
        auth_str = f"{self._client_id}:{self._client_secret}"
        auth_b64 = base64.b64encode(auth_str.encode()).decode()

        payload = {
            "grant_type": "refresh_token",
            "refresh_token": self._refresh_token,
        }

        headers = {
            "Authorization": f"Basic {auth_b64}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        try:
            resp = await self._client.post(
                token_url,
                data=payload,
                headers=headers,
            )
            resp.raise_for_status()
            token_data = resp.json()
            return token_data["access_token"]

        except httpx.HTTPStatusError as e:
            error_msg = f"OAuth HTTP error {e.response.status_code}"
            try:
                error_data = e.response.json()
                error_msg += f": {error_data}"
            except Exception:
                error_msg += f": {e.response.text}"
            raise RuntimeError(error_msg) from e

        except Exception as e:
            raise RuntimeError(f"eBay OAuth failed: {e}") from e

    async def get_access_token(self) -> str:
        """
        Get valid access token with caching.

        Returns:
            Valid access token
        """
        # Check cache
        if self.user_id in self._token_cache:
            cached_token, timestamp = self._token_cache[self.user_id]
            token_age = time.time() - timestamp
            if token_age < self._token_max_age:
                return cached_token

        # Refresh token
        access_token = await self._refresh_access_token()

        # Cache new token
        self._token_cache[self.user_id] = (access_token, time.time())

        return access_token

    def _get_content_language(self, content_language: Optional[str] = None) -> str:
        """Get Content-Language header value."""
        if content_language:
            return content_language
        if self._marketplace_config:
            return self._marketplace_config.get_content_language()
        return "en-US"

    async def api_call(
        self,
        method: str,
        path: str,
        params: Optional[dict[str, Any]] = None,
        json_data: Optional[dict[str, Any]] = None,
        content_language: Optional[str] = None,
    ) -> Any:
        """
        Make async API call to eBay.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            path: API endpoint path
            params: Query parameters
            json_data: Request body JSON
            content_language: Content-Language header override

        Returns:
            Response JSON or None for 204/201 without content

        Raises:
            EbayAPIError: On API errors
            EbayOAuthError: On auth errors
            MarketplaceRateLimitError: On rate limit
        """
        if not self._client:
            raise RuntimeError("HTTP client not initialized. Use async context manager.")

        # Use Commerce API base for /commerce/* endpoints
        if path.startswith("/commerce/"):
            api_base = (
                self.COMMERCE_API_BASE_SANDBOX if self.sandbox
                else self.COMMERCE_API_BASE_PRODUCTION
            )
        else:
            api_base = self.api_base

        url = f"{api_base}{path}"
        token = await self.get_access_token()
        content_lang = self._get_content_language(content_language)

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Content-Language": content_lang,
        }

        # Async rate limiting
        await self._rate_limiter.wait()

        logger.debug(f"eBay API {method} {path}")

        try:
            resp = await self._client.request(
                method.upper(),
                url,
                headers=headers,
                params=params,
                json=json_data,
            )

            # Handle errors
            if not resp.is_success:
                error_data = None
                try:
                    error_data = resp.json()
                except Exception:
                    error_data = {"raw_text": resp.text[:500] if resp.text else None}

                # Rate limit
                if resp.status_code == 429:
                    retry_after = resp.headers.get("Retry-After")
                    raise MarketplaceRateLimitError(
                        platform="ebay",
                        retry_after=int(retry_after) if retry_after else None,
                        operation=method.lower(),
                    )

                # Auth errors
                if resp.status_code in (401, 403):
                    raise EbayOAuthError(
                        message=f"eBay auth failed ({resp.status_code})",
                        status_code=resp.status_code,
                        response_body=error_data,
                    )

                # Other API errors
                raise EbayAPIError(
                    message=f"eBay error {resp.status_code} on {method} {path}",
                    status_code=resp.status_code,
                    response_body=error_data,
                )

            # Success without content
            if resp.status_code in (204, 201) and not resp.text:
                return None

            # Success with JSON
            if resp.status_code in (200, 201):
                try:
                    return resp.json()
                except Exception:
                    return None

            return None

        except httpx.TimeoutException as e:
            raise EbayError(
                message=f"Timeout on {method} {path}: {e}",
                operation=method.lower(),
            ) from e
        except httpx.RequestError as e:
            raise EbayError(
                message=f"Network error on {method} {path}: {e}",
                operation=method.lower(),
            ) from e
