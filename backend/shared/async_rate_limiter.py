"""
Async Rate Limiter for HTTP Clients

Non-blocking rate limiter for use with httpx async client.

Author: Claude
Date: 2026-01-20
"""

import asyncio
import random
import time
from typing import Optional


class AsyncRateLimiter:
    """
    Asynchronous rate limiter for API calls.

    Ensures a minimum delay between requests with optional jitter
    to avoid thundering herd problems.

    Usage:
        limiter = AsyncRateLimiter(min_delay=0.3, max_delay=0.8)

        async def make_request():
            await limiter.wait()  # Non-blocking wait
            return await client.get(url)

    Attributes:
        min_delay: Minimum seconds between requests
        max_delay: Maximum seconds between requests (for jitter)
        burst_limit: Maximum requests allowed in burst (optional)
        burst_window: Time window for burst limit in seconds
    """

    def __init__(
        self,
        min_delay: float = 0.3,
        max_delay: float = 0.8,
        burst_limit: Optional[int] = None,
        burst_window: float = 1.0,
    ):
        """
        Initialize rate limiter.

        Args:
            min_delay: Minimum delay between requests in seconds
            max_delay: Maximum delay (with jitter) in seconds
            burst_limit: Optional max requests per burst_window
            burst_window: Time window for burst counting
        """
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.burst_limit = burst_limit
        self.burst_window = burst_window

        self._last_request: float = 0.0
        self._lock = asyncio.Lock()
        self._request_times: list[float] = []

    async def wait(self) -> None:
        """
        Wait until a request can be made, respecting rate limits.

        This method is non-blocking and uses asyncio.sleep().
        Thread-safe via asyncio.Lock().
        """
        async with self._lock:
            now = time.monotonic()

            # Check burst limit if configured
            if self.burst_limit:
                self._cleanup_old_requests(now)
                if len(self._request_times) >= self.burst_limit:
                    # Wait until oldest request exits the window
                    oldest = self._request_times[0]
                    wait_time = (oldest + self.burst_window) - now
                    if wait_time > 0:
                        await asyncio.sleep(wait_time)
                        now = time.monotonic()

            # Check minimum delay
            elapsed = now - self._last_request
            if elapsed < self.min_delay:
                # Add jitter to avoid synchronized requests
                delay = random.uniform(self.min_delay, self.max_delay)
                await asyncio.sleep(delay - elapsed)
                now = time.monotonic()

            # Record this request
            self._last_request = now
            if self.burst_limit:
                self._request_times.append(now)

    def _cleanup_old_requests(self, now: float) -> None:
        """Remove request times outside the burst window."""
        cutoff = now - self.burst_window
        self._request_times = [t for t in self._request_times if t > cutoff]

    async def wait_with_backoff(self, attempt: int, base_delay: float = 1.0) -> None:
        """
        Wait with exponential backoff for retries.

        Args:
            attempt: Current retry attempt (0-indexed)
            base_delay: Base delay in seconds
        """
        if attempt == 0:
            return

        # Exponential backoff with jitter
        delay = base_delay * (2 ** (attempt - 1))
        jitter = random.uniform(0, delay * 0.1)
        total_delay = min(delay + jitter, 60.0)  # Cap at 60 seconds

        await asyncio.sleep(total_delay)

    def reset(self) -> None:
        """Reset the rate limiter state."""
        self._last_request = 0.0
        self._request_times.clear()


class TokenBucketLimiter:
    """
    Token bucket rate limiter for sustained throughput.

    Allows bursting up to bucket capacity, then limits to refill rate.
    Better for APIs with explicit rate limits (e.g., "100 requests/minute").

    Usage:
        # 100 requests per minute, burst up to 10
        limiter = TokenBucketLimiter(rate=100/60, capacity=10)

        async def make_request():
            await limiter.acquire()
            return await client.get(url)
    """

    def __init__(self, rate: float, capacity: int = 1):
        """
        Initialize token bucket.

        Args:
            rate: Token refill rate per second
            capacity: Maximum tokens (burst capacity)
        """
        self.rate = rate
        self.capacity = capacity
        self._tokens = float(capacity)
        self._last_update = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: int = 1) -> None:
        """
        Acquire tokens, waiting if necessary.

        Args:
            tokens: Number of tokens to acquire
        """
        async with self._lock:
            await self._wait_for_tokens(tokens)
            self._tokens -= tokens

    async def _wait_for_tokens(self, needed: int) -> None:
        """Wait until enough tokens are available."""
        while True:
            now = time.monotonic()
            elapsed = now - self._last_update
            self._last_update = now

            # Refill tokens
            self._tokens = min(
                self.capacity,
                self._tokens + elapsed * self.rate
            )

            if self._tokens >= needed:
                return

            # Calculate wait time for needed tokens
            deficit = needed - self._tokens
            wait_time = deficit / self.rate
            await asyncio.sleep(wait_time)
