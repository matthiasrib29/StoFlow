"""
Centralized HTTP Client

Provides configured HTTP client with:
- Consistent timeout configuration
- Retry logic with exponential backoff
- Error handling
- Resource management
- Rate limiting (RateLimiter class for backwards compatibility)

Created: 2026-01-08
Author: Claude
"""

import asyncio
import random
import time
from typing import Any, Dict, Optional

import httpx
from httpx import Response, TimeoutException, ConnectError, ReadError

from shared.config import get_settings
from shared.logging_setup import get_logger

logger = get_logger(__name__)
settings = get_settings()


class RateLimiter:
    """
    Simple rate limiter with configurable delay.

    Used by eBay and Etsy clients for backwards compatibility.
    For new code, prefer using HTTPClient with retry logic.

    Attributes:
        min_delay: Minimum delay between requests (seconds)
        max_delay: Maximum delay between requests (seconds)
        last_request_time: Timestamp of last request
    """

    def __init__(self, min_delay: float = 0.3, max_delay: float = 0.8):
        """
        Initialize the rate limiter.

        Args:
            min_delay: Minimum delay between requests (default: 0.3s)
            max_delay: Maximum delay between requests (default: 0.8s)
        """
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.last_request_time = 0.0

    def wait(self) -> None:
        """Wait for the necessary delay before the next request."""
        now = time.time()
        elapsed = now - self.last_request_time

        if elapsed < self.min_delay:
            delay = random.uniform(self.min_delay, self.max_delay)
            time.sleep(delay)

        self.last_request_time = time.time()


class HTTPClient:
    """
    Centralized HTTP client with timeout and retry configuration.

    Usage:
        async with HTTPClient() as client:
            response = await client.get("https://example.com")
            data = response.json()

    Or with retry:
        async with HTTPClient() as client:
            response = await client.get_with_retry("https://example.com", max_retries=3)
    """

    def __init__(
        self,
        timeout_connect: Optional[float] = None,
        timeout_read: Optional[float] = None,
        timeout_write: Optional[float] = None,
        timeout_pool: Optional[float] = None,
        max_retries: Optional[int] = None,
        backoff_factor: Optional[float] = None,
    ):
        """
        Initialize HTTP client with timeout configuration.

        Args:
            timeout_connect: Connection timeout (default from settings)
            timeout_read: Read timeout (default from settings)
            timeout_write: Write timeout (default from settings)
            timeout_pool: Pool timeout (default from settings)
            max_retries: Maximum retry attempts (default from settings)
            backoff_factor: Exponential backoff factor (default from settings)
        """
        self.timeout_connect = timeout_connect or settings.http_timeout_connect
        self.timeout_read = timeout_read or settings.http_timeout_read
        self.timeout_write = timeout_write or settings.http_timeout_write
        self.timeout_pool = timeout_pool or settings.http_timeout_pool
        self.max_retries = max_retries or settings.http_max_retries
        self.backoff_factor = backoff_factor or settings.http_retry_backoff_factor

        # Create timeout configuration
        self.timeout = httpx.Timeout(
            connect=self.timeout_connect,
            read=self.timeout_read,
            write=self.timeout_write,
            pool=self.timeout_pool,
        )

        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self._client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def get(self, url: str, **kwargs) -> Response:
        """
        Perform GET request.

        Args:
            url: Request URL
            **kwargs: Additional arguments passed to httpx.get()

        Returns:
            httpx.Response object

        Raises:
            httpx.HTTPError: On HTTP errors
        """
        if not self._client:
            raise RuntimeError("HTTPClient must be used as async context manager")
        return await self._client.get(url, **kwargs)

    async def post(self, url: str, **kwargs) -> Response:
        """
        Perform POST request.

        Args:
            url: Request URL
            **kwargs: Additional arguments passed to httpx.post()

        Returns:
            httpx.Response object

        Raises:
            httpx.HTTPError: On HTTP errors
        """
        if not self._client:
            raise RuntimeError("HTTPClient must be used as async context manager")
        return await self._client.post(url, **kwargs)

    async def put(self, url: str, **kwargs) -> Response:
        """
        Perform PUT request.

        Args:
            url: Request URL
            **kwargs: Additional arguments passed to httpx.put()

        Returns:
            httpx.Response object

        Raises:
            httpx.HTTPError: On HTTP errors
        """
        if not self._client:
            raise RuntimeError("HTTPClient must be used as async context manager")
        return await self._client.put(url, **kwargs)

    async def delete(self, url: str, **kwargs) -> Response:
        """
        Perform DELETE request.

        Args:
            url: Request URL
            **kwargs: Additional arguments passed to httpx.delete()

        Returns:
            httpx.Response object

        Raises:
            httpx.HTTPError: On HTTP errors
        """
        if not self._client:
            raise RuntimeError("HTTPClient must be used as async context manager")
        return await self._client.delete(url, **kwargs)

    async def request(self, method: str, url: str, **kwargs) -> Response:
        """
        Perform generic HTTP request.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            url: Request URL
            **kwargs: Additional arguments passed to httpx.request()

        Returns:
            httpx.Response object

        Raises:
            httpx.HTTPError: On HTTP errors
        """
        if not self._client:
            raise RuntimeError("HTTPClient must be used as async context manager")
        return await self._client.request(method, url, **kwargs)

    async def get_with_retry(
        self,
        url: str,
        max_retries: Optional[int] = None,
        backoff_factor: Optional[float] = None,
        **kwargs
    ) -> Response:
        """
        Perform GET request with exponential backoff retry.

        Args:
            url: Request URL
            max_retries: Maximum retry attempts (overrides default)
            backoff_factor: Exponential backoff factor (overrides default)
            **kwargs: Additional arguments passed to httpx.get()

        Returns:
            httpx.Response object

        Raises:
            httpx.HTTPError: After all retries exhausted
        """
        return await self._request_with_retry(
            "GET", url, max_retries, backoff_factor, **kwargs
        )

    async def post_with_retry(
        self,
        url: str,
        max_retries: Optional[int] = None,
        backoff_factor: Optional[float] = None,
        **kwargs
    ) -> Response:
        """
        Perform POST request with exponential backoff retry.

        Args:
            url: Request URL
            max_retries: Maximum retry attempts (overrides default)
            backoff_factor: Exponential backoff factor (overrides default)
            **kwargs: Additional arguments passed to httpx.post()

        Returns:
            httpx.Response object

        Raises:
            httpx.HTTPError: After all retries exhausted
        """
        return await self._request_with_retry(
            "POST", url, max_retries, backoff_factor, **kwargs
        )

    async def _request_with_retry(
        self,
        method: str,
        url: str,
        max_retries: Optional[int] = None,
        backoff_factor: Optional[float] = None,
        **kwargs
    ) -> Response:
        """
        Perform HTTP request with exponential backoff retry.

        Args:
            method: HTTP method
            url: Request URL
            max_retries: Maximum retry attempts (overrides default)
            backoff_factor: Exponential backoff factor (overrides default)
            **kwargs: Additional arguments passed to httpx.request()

        Returns:
            httpx.Response object

        Raises:
            httpx.HTTPError: After all retries exhausted
        """
        retries = max_retries if max_retries is not None else self.max_retries
        backoff = backoff_factor if backoff_factor is not None else self.backoff_factor

        last_exception = None

        for attempt in range(retries):
            try:
                response = await self.request(method, url, **kwargs)
                response.raise_for_status()
                return response

            except (TimeoutException, ConnectError, ReadError) as e:
                last_exception = e

                if attempt < retries - 1:
                    delay = backoff * (2 ** attempt)  # Exponential backoff
                    logger.warning(
                        f"[HTTPClient] Request failed (attempt {attempt+1}/{retries}): "
                        f"{type(e).__name__}: {e}. Retrying in {delay}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"[HTTPClient] Request failed after {retries} attempts: "
                        f"{type(e).__name__}: {e}"
                    )

            except httpx.HTTPStatusError as e:
                # Don't retry on 4xx client errors (except 429 rate limit)
                if 400 <= e.response.status_code < 500 and e.response.status_code != 429:
                    logger.error(
                        f"[HTTPClient] Client error {e.response.status_code}: {e}"
                    )
                    raise

                last_exception = e

                if attempt < retries - 1:
                    delay = backoff * (2 ** attempt)
                    logger.warning(
                        f"[HTTPClient] Request failed with status {e.response.status_code} "
                        f"(attempt {attempt+1}/{retries}). Retrying in {delay}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"[HTTPClient] Request failed after {retries} attempts: "
                        f"Status {e.response.status_code}"
                    )

        # All retries exhausted
        if last_exception:
            raise last_exception

        raise RuntimeError("Request failed without exception (should not happen)")


# Convenience function for one-off requests
async def fetch(
    url: str,
    method: str = "GET",
    with_retry: bool = False,
    max_retries: Optional[int] = None,
    timeout: Optional[float] = None,
    **kwargs
) -> Response:
    """
    Perform one-off HTTP request without context manager.

    Args:
        url: Request URL
        method: HTTP method (default GET)
        with_retry: Enable retry logic (default False)
        max_retries: Maximum retry attempts (only if with_retry=True)
        timeout: Custom timeout (overrides all timeouts)
        **kwargs: Additional arguments passed to httpx.request()

    Returns:
        httpx.Response object

    Raises:
        httpx.HTTPError: On HTTP errors

    Usage:
        response = await fetch("https://example.com/api/data")
        data = response.json()

        # With retry
        response = await fetch(
            "https://example.com/api/data",
            with_retry=True,
            max_retries=5
        )
    """
    timeout_config = None
    if timeout is not None:
        # Use same timeout for all operations
        timeout_config = httpx.Timeout(timeout)

    async with HTTPClient() as client:
        if timeout_config:
            client._client._timeout = timeout_config

        if with_retry:
            return await client._request_with_retry(
                method, url, max_retries, **kwargs
            )
        else:
            return await client.request(method, url, **kwargs)


__all__ = [
    "RateLimiter",
    "HTTPClient",
    "fetch",
]
