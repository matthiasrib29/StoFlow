"""
Plugin WebSocket Helper - Replaces PluginTaskHelper

Provides helper functions to execute plugin actions via WebSocket.
This replaces the old PluginTask polling system.

Author: Claude
Date: 2026-01-08
"""
from typing import Any, Dict, Optional
from urllib.parse import urlencode

from sqlalchemy.orm import Session

from services.plugin_task_rate_limiter import VintedRateLimiter
from services.websocket_service import WebSocketService
from shared.logging import get_logger

logger = get_logger(__name__)


# Generic result codes for plugin communication

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


class PluginWebSocketHelper:
    """
    Helper for plugin communication via WebSocket.

    Replaces PluginTaskHelper which used PluginTask polling.
    """

    @staticmethod
    async def call_plugin(
        db: Session,
        user_id: int,
        http_method: str,
        path: str,
        payload: Optional[dict] = None,
        params: Optional[dict] = None,
        timeout: int = 60,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute Vinted API call via plugin.

        Single entry point — always uses VINTED_API_CALL action
        with rate limiting.

        Args:
            db: SQLAlchemy session
            user_id: User ID
            http_method: GET, POST, PUT, DELETE
            path: Full URL or API path
            payload: Request body
            params: Query parameters
            timeout: Timeout in seconds
            description: Description for logs

        Returns:
            dict: HTTP response data

        Raises:
            PluginHTTPError: On HTTP errors
            RuntimeError: On non-HTTP errors
        """
        # Apply rate limiting before calling plugin (anti-ban protection)
        delay = await VintedRateLimiter.for_user(user_id).wait_before_request(path, http_method)
        if delay > 0:
            logger.debug(f"[PluginWS] Rate limit: {delay:.2f}s for {http_method} {path[:50]}")

        # Build complete endpoint URL with query params embedded.
        # The plugin content script doesn't handle params separately,
        # so we encode them directly into the URL.
        endpoint = path
        if params:
            separator = "&" if "?" in path else "?"
            endpoint = f"{path}{separator}{urlencode(params, doseq=True)}"

        return await PluginWebSocketHelper._send_to_plugin(
            db=db,
            user_id=user_id,
            action="VINTED_API_CALL",
            payload={
                "method": http_method,
                "endpoint": endpoint,
                "data": payload,
            },
            timeout=timeout,
            description=description,
        )

    @staticmethod
    async def _send_to_plugin(
        db: Session,
        user_id: int,
        action: str,
        payload: dict,
        timeout: int = 60,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Internal: send raw action to plugin via WebSocket.

        Do not call directly — use call_plugin() instead.
        """
        result = await WebSocketService.send_plugin_command(
            user_id=user_id, action=action, payload=payload, timeout=timeout
        )

        if not result.get("success"):
            error_msg = result.get("error", "Unknown error")
            http_status = result.get("status")
            error_data = result.get("errorData")

            logger.error(f"[PluginWS] {description or action} failed: HTTP {http_status or '?'} - {error_msg}")

            if http_status:
                raise PluginHTTPError(
                    status=http_status,
                    message=error_msg,
                    error_data=error_data
                )

            raise RuntimeError(error_msg)

        return result.get("data", {})
