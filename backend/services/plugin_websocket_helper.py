"""
Plugin WebSocket Helper - Replaces PluginTaskHelper

Provides helper functions to execute plugin actions via WebSocket.
This replaces the old PluginTask polling system.

Author: Claude
Date: 2026-01-08
"""
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from services.websocket_service import WebSocketService
from shared.logging_setup import get_logger

logger = get_logger(__name__)


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
            logger.error(f"[PluginWS] {description or action} failed: {error_msg}")
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
    ) -> Dict[str, Any]:
        """
        Execute raw HTTP call via plugin.

        Args:
            db: SQLAlchemy session
            user_id: User ID
            http_method: GET, POST, PUT, DELETE
            path: Full URL
            payload: Request body
            params: Query parameters
            timeout: Timeout in seconds
            description: Description for logs

        Returns:
            dict: HTTP response data
        """
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
