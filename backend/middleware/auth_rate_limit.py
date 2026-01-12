"""
Auth Rate Limiter - Protection contre brute force sur endpoints auth.

Implémentation en mémoire (dict-based) pour développement.
Pour production : migrer vers Redis pour clustering multi-serveur.

Security Phase 1.3 (2026-01-12)

Author: Claude
Date: 2026-01-12
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Tuple

from fastapi import HTTPException, Request, status

from shared.logging_setup import get_logger

logger = get_logger(__name__)


class AuthRateLimiter:
    """
    Rate limiter for authentication endpoints.

    Tracks requests per IP address with per-endpoint limits.
    In-memory implementation with automatic cleanup.

    Thread-safe via asyncio.Lock.

    Production Note:
        For multi-server deployments, migrate to Redis:
        - Replace _storage dict with Redis
        - Use Redis INCR + EXPIRE commands
        - Enable clustering for high availability
    """

    # Rate limits per endpoint (max_attempts, window_minutes)
    LIMITS = {
        "login": (5, 15),               # 5 attempts per 15 minutes
        "register": (3, 60),            # 3 accounts per hour
        "refresh": (10, 5),             # 10 refreshes per 5 minutes
        "resend_verification": (3, 60), # 3 emails per hour
        "verify_email": (10, 60),       # 10 verifications per hour
    }

    def __init__(self):
        """Initialize rate limiter with in-memory storage."""
        # Storage: {endpoint:{ip:[(timestamp, count)]}}
        self._storage: Dict[str, Dict[str, list]] = {}
        self._lock = asyncio.Lock()
        self._cleanup_interval = 300  # Cleanup every 5 minutes
        self._last_cleanup = time.time()

    async def check_rate_limit(self, request: Request, endpoint: str) -> None:
        """
        Check if request exceeds rate limit.

        Args:
            request: FastAPI request object
            endpoint: Endpoint identifier (login, register, etc.)

        Raises:
            HTTPException: 429 if rate limit exceeded
        """
        if endpoint not in self.LIMITS:
            # No limit configured for this endpoint
            return

        max_attempts, window_minutes = self.LIMITS[endpoint]

        # Get client IP (handle proxy headers)
        client_ip = self._get_client_ip(request)

        # Lock for thread-safety
        async with self._lock:
            # Periodic cleanup of old entries
            await self._cleanup_old_entries()

            # Initialize storage for endpoint if needed
            if endpoint not in self._storage:
                self._storage[endpoint] = {}

            # Get current timestamp
            now = time.time()
            window_start = now - (window_minutes * 60)

            # Get or initialize IP entry
            if client_ip not in self._storage[endpoint]:
                self._storage[endpoint][client_ip] = []

            # Filter out expired attempts
            self._storage[endpoint][client_ip] = [
                (ts, count) for ts, count in self._storage[endpoint][client_ip]
                if ts > window_start
            ]

            # Count recent attempts
            recent_attempts = sum(
                count for _, count in self._storage[endpoint][client_ip]
            )

            if recent_attempts >= max_attempts:
                # Rate limit exceeded
                retry_after = int(window_minutes * 60)
                logger.warning(
                    f"Rate limit exceeded for {endpoint} from {client_ip}: "
                    f"{recent_attempts}/{max_attempts} attempts"
                )
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": "rate_limit_exceeded",
                        "message": f"Too many {endpoint} attempts. Try again in {retry_after} seconds.",
                        "retry_after": retry_after,
                    },
                    headers={"Retry-After": str(retry_after)},
                )

            # Record this attempt
            self._storage[endpoint][client_ip].append((now, 1))

            logger.debug(
                f"Rate limit check passed for {endpoint} from {client_ip}: "
                f"{recent_attempts + 1}/{max_attempts} attempts"
            )

    def _get_client_ip(self, request: Request) -> str:
        """
        Extract client IP from request.

        Handles proxy headers (X-Forwarded-For, X-Real-IP).

        Args:
            request: FastAPI request object

        Returns:
            Client IP address
        """
        # Check proxy headers first
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # X-Forwarded-For can contain multiple IPs (client, proxy1, proxy2)
            # Take the first one (original client)
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()

        # Fallback to direct connection
        if request.client:
            return request.client.host

        return "unknown"

    async def _cleanup_old_entries(self) -> None:
        """
        Cleanup old entries from storage.

        Runs periodically to prevent memory growth.
        """
        now = time.time()

        # Only cleanup every N seconds
        if now - self._last_cleanup < self._cleanup_interval:
            return

        logger.debug("Running rate limiter cleanup...")

        removed_count = 0
        for endpoint in list(self._storage.keys()):
            for client_ip in list(self._storage[endpoint].keys()):
                # Remove IPs with no recent attempts
                if not self._storage[endpoint][client_ip]:
                    del self._storage[endpoint][client_ip]
                    removed_count += 1

            # Remove endpoints with no IPs
            if not self._storage[endpoint]:
                del self._storage[endpoint]

        self._last_cleanup = now

        if removed_count > 0:
            logger.debug(f"Cleaned up {removed_count} old rate limit entries")

    async def reset_for_ip(self, client_ip: str, endpoint: str = None) -> None:
        """
        Reset rate limit for a specific IP (admin function).

        Args:
            client_ip: IP address to reset
            endpoint: Specific endpoint to reset (or None for all)
        """
        async with self._lock:
            if endpoint:
                if endpoint in self._storage and client_ip in self._storage[endpoint]:
                    del self._storage[endpoint][client_ip]
                    logger.info(f"Reset rate limit for {client_ip} on {endpoint}")
            else:
                for ep in self._storage:
                    if client_ip in self._storage[ep]:
                        del self._storage[ep][client_ip]
                logger.info(f"Reset all rate limits for {client_ip}")


# Singleton instance
_auth_rate_limiter: AuthRateLimiter = None


def get_auth_rate_limiter() -> AuthRateLimiter:
    """
    Get the auth rate limiter singleton.

    Returns:
        AuthRateLimiter instance
    """
    global _auth_rate_limiter

    if _auth_rate_limiter is None:
        _auth_rate_limiter = AuthRateLimiter()
        logger.info("AuthRateLimiter initialized (in-memory)")

    return _auth_rate_limiter
