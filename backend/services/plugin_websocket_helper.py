"""
Plugin WebSocket Helper - Replaces PluginTaskHelper

Provides helper functions to execute plugin actions via WebSocket.
This replaces the old PluginTask polling system.

Author: Claude
Date: 2026-01-08
Updated: 2026-01-19 - Added generic HTTP result codes
Updated: 2026-01-19 - Added automatic retry for server errors (5xx)
"""
import asyncio
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from services.plugin_task_rate_limiter import VintedRateLimiter
from services.websocket_service import WebSocketService
from shared.logging_setup import get_logger

logger = get_logger(__name__)


# ============================================================================
# GENERIC RESULT CODES FOR PLUGIN COMMUNICATION
# ============================================================================
# These codes should be used by ALL services that communicate with the plugin
# (WebSocket, HTTP calls via plugin, etc.) to provide consistent error handling.
#
# Usage:
#   from services.plugin_websocket_helper import (
#       PluginWebSocketHelper, PluginHTTPError,
#       PLUGIN_SUCCESS, PLUGIN_NOT_FOUND, PLUGIN_FORBIDDEN, etc.
#   )
# ============================================================================

PLUGIN_SUCCESS = "success"
PLUGIN_NOT_FOUND = "not_found"           # 404 - Resource not found (sold/deleted on marketplace)
PLUGIN_FORBIDDEN = "forbidden"           # 403 - Access denied (DataDome block, rate limit)
PLUGIN_UNAUTHORIZED = "unauthorized"     # 401 - Session expired, needs re-auth
PLUGIN_BAD_REQUEST = "bad_request"       # 400 - Invalid request data
PLUGIN_RATE_LIMITED = "rate_limited"     # 429 - Too many requests
PLUGIN_SERVER_ERROR = "server_error"     # 500+ - Marketplace server error
PLUGIN_TIMEOUT = "timeout"               # Request timeout
PLUGIN_DISCONNECTED = "disconnected"     # Plugin/user not connected
PLUGIN_ERROR = "error"                   # Generic/unknown error


class PluginHTTPError(Exception):
    """
    Exception raised when plugin HTTP call fails with a specific HTTP status.

    Attributes:
        status: HTTP status code (404, 403, 401, etc.)
        message: Error message
        error_data: Optional error response data from API
    """

    def __init__(self, status: int, message: str, error_data: Optional[dict] = None):
        self.status = status
        self.message = message
        self.error_data = error_data
        super().__init__(f"HTTP {status}: {message}")

    def is_not_found(self) -> bool:
        """Return True if this is a 404 Not Found error."""
        return self.status == 404

    def is_forbidden(self) -> bool:
        """Return True if this is a 403 Forbidden error."""
        return self.status == 403

    def is_unauthorized(self) -> bool:
        """Return True if this is a 401 Unauthorized error."""
        return self.status == 401

    def is_bad_request(self) -> bool:
        """Return True if this is a 400 Bad Request error."""
        return self.status == 400

    def is_rate_limited(self) -> bool:
        """Return True if this is a 429 Too Many Requests error."""
        return self.status == 429

    def is_server_error(self) -> bool:
        """Return True if this is a 5xx server error."""
        return 500 <= self.status < 600

    def get_result_code(self) -> str:
        """
        Convert HTTP status to a generic result code.

        Returns:
            str: One of PLUGIN_* constants
        """
        if self.status == 404:
            return PLUGIN_NOT_FOUND
        if self.status == 403:
            return PLUGIN_FORBIDDEN
        if self.status == 401:
            return PLUGIN_UNAUTHORIZED
        if self.status == 400:
            return PLUGIN_BAD_REQUEST
        if self.status == 429:
            return PLUGIN_RATE_LIMITED
        if 500 <= self.status < 600:
            return PLUGIN_SERVER_ERROR
        return PLUGIN_ERROR


# ============================================================================
# RETRY CONFIGURATION FOR SERVER ERRORS (5xx)
# ============================================================================
# Vinted servers can be overloaded and return 5xx errors (especially 524 from
# Cloudflare). These are often transient, so we retry after a delay.
# ============================================================================

SERVER_ERROR_RETRY_DELAY = 30  # seconds to wait before retry
SERVER_ERROR_MAX_RETRIES = 1   # number of retries (1 = 2 total attempts)


class PluginWebSocketHelper:
    """
    Helper for plugin communication via WebSocket.

    Replaces PluginTaskHelper which used PluginTask polling.
    """

    @staticmethod
    async def call_plugin(
        db: Session,
        user_id: int,
        action: str,
        payload: dict,
        timeout: int = 60,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute plugin action via WebSocket.

        Args:
            db: SQLAlchemy session (unused, for compatibility)
            user_id: User ID
            action: Plugin action (VINTED_PUBLISH, etc.)
            payload: Action payload
            timeout: Timeout in seconds
            description: Description for logs

        Returns:
            dict: Plugin response

        Raises:
            TimeoutError: If no response within timeout
            RuntimeError: If user not connected
        """
        logger.debug(f"[PluginWS] {description or action} (user={user_id})")

        result = await WebSocketService.send_plugin_command(
            user_id=user_id, action=action, payload=payload, timeout=timeout
        )

        if not result.get("success"):
            error_msg = result.get("error", "Unknown error")
            http_status = result.get("status")
            error_data = result.get("errorData")

            logger.error(f"[PluginWS] {description or action} failed: HTTP {http_status or '?'} - {error_msg}")

            # Raise specific HTTP error if status code is available
            if http_status:
                raise PluginHTTPError(
                    status=http_status,
                    message=error_msg,
                    error_data=error_data
                )

            # Fallback to generic RuntimeError for non-HTTP errors
            raise RuntimeError(error_msg)

        return result.get("data", {})

    @staticmethod
    async def call_plugin_http(
        db: Session,
        user_id: int,
        http_method: str,
        path: str,
        payload: Optional[dict] = None,
        params: Optional[dict] = None,
        timeout: int = 60,
        description: Optional[str] = None,
        retry_on_server_error: bool = True,
    ) -> Dict[str, Any]:
        """
        Execute raw HTTP call via plugin.

        Includes rate limiting to prevent Vinted ban.
        Automatically retries on server errors (5xx) with configurable delay.

        Args:
            db: SQLAlchemy session
            user_id: User ID
            http_method: GET, POST, PUT, DELETE
            path: Full URL
            payload: Request body
            params: Query parameters
            timeout: Timeout in seconds
            description: Description for logs
            retry_on_server_error: If True, retry on 5xx errors (default: True)

        Returns:
            dict: HTTP response data

        Raises:
            PluginHTTPError: On HTTP errors (after retries for 5xx)
            RuntimeError: On non-HTTP errors
        """
        last_error: Optional[PluginHTTPError] = None

        for attempt in range(SERVER_ERROR_MAX_RETRIES + 1):
            try:
                # Apply rate limiting before calling plugin (anti-ban protection)
                delay = await VintedRateLimiter.wait_before_request(path, http_method)
                logger.info(f"[PluginWS] Rate limit applied: {delay:.2f}s delay for {http_method} {path[:50]}")

                return await PluginWebSocketHelper.call_plugin(
                    db=db,
                    user_id=user_id,
                    action="VINTED_API_CALL",
                    payload={
                        "method": http_method,
                        "endpoint": path,
                        "data": payload,
                        "params": params,
                    },
                    timeout=timeout,
                    description=description,
                )

            except PluginHTTPError as e:
                # Check if this is a server error (5xx) that we should retry
                if retry_on_server_error and e.is_server_error():
                    last_error = e
                    if attempt < SERVER_ERROR_MAX_RETRIES:
                        logger.warning(
                            f"[PluginWS] Server error {e.status} for {http_method} {path[:50]}, "
                            f"waiting {SERVER_ERROR_RETRY_DELAY}s before retry "
                            f"(attempt {attempt + 1}/{SERVER_ERROR_MAX_RETRIES + 1})"
                        )
                        await asyncio.sleep(SERVER_ERROR_RETRY_DELAY)
                        continue
                    else:
                        logger.error(
                            f"[PluginWS] Server error {e.status} for {http_method} {path[:50]} "
                            f"after {SERVER_ERROR_MAX_RETRIES + 1} attempts, giving up"
                        )
                        raise
                # Non-server errors (4xx, etc.) - don't retry, raise immediately
                raise

            except RuntimeError as e:
                # Check if this is a socket disconnection error that we should retry
                error_msg = str(e).lower()
                is_socket_error = (
                    "socket has been disconnected" in error_msg
                    or "not connected" in error_msg
                    or "disconnected" in error_msg
                )
                if is_socket_error and attempt < SERVER_ERROR_MAX_RETRIES:
                    logger.warning(
                        f"[PluginWS] Socket disconnected for {http_method} {path[:50]}, "
                        f"waiting {SERVER_ERROR_RETRY_DELAY}s before retry "
                        f"(attempt {attempt + 1}/{SERVER_ERROR_MAX_RETRIES + 1})"
                    )
                    await asyncio.sleep(SERVER_ERROR_RETRY_DELAY)
                    continue
                # Non-socket errors or max retries reached - raise
                raise

        # Should not reach here, but just in case
        if last_error:
            raise last_error
        raise RuntimeError("Unexpected error in call_plugin_http retry loop")
