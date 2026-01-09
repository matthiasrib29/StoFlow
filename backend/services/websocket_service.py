"""
WebSocket Service - Real-time communication Backend ↔ Frontend

Provides WebSocket infrastructure for plugin command execution.
Replaces the old PluginTask polling system.

Author: Claude
Date: 2026-01-08
"""
import asyncio
import random
import time
from typing import Any, Dict, Optional

import socketio

from shared.logging_setup import get_logger

logger = get_logger(__name__)

# Create SocketIO server
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:3003",
        "https://app.stoflow.com",
    ],
)

# Store pending requests awaiting responses
pending_requests: Dict[str, asyncio.Future] = {}


class WebSocketService:
    """
    Service for real-time WebSocket communication with frontend.

    Usage:
        # Send command to plugin via frontend
        result = await WebSocketService.send_plugin_command(
            user_id=123,
            action="VINTED_PUBLISH",
            payload={...},
            timeout=60
        )
    """

    @staticmethod
    async def send_plugin_command(
        user_id: int, action: str, payload: dict, timeout: int = 60
    ) -> Dict[str, Any]:
        """
        Send a command to the plugin via WebSocket.

        Args:
            user_id: User ID (for room targeting)
            action: Plugin action (VINTED_PUBLISH, VINTED_UPDATE, etc.)
            payload: Action payload
            timeout: Timeout in seconds

        Returns:
            dict: Plugin response

        Raises:
            TimeoutError: If no response within timeout
            RuntimeError: If user not connected
        """
        request_id = (
            f"req_{user_id}_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
        )

        # Check if user connected
        room = f"user_{user_id}"
        room_sids = sio.manager.rooms.get("/", {}).get(room, set())

        if not room_sids:
            raise RuntimeError(f"User {user_id} not connected via WebSocket")

        # Create future for response
        future = asyncio.get_event_loop().create_future()
        pending_requests[request_id] = future

        try:
            # Emit command to user's room
            await sio.emit(
                "plugin_command",
                {"request_id": request_id, "action": action, "payload": payload},
                room=room,
            )

            logger.debug(f"[WebSocket] Sent command {action} to user {user_id}")

            # Wait for response
            result = await asyncio.wait_for(future, timeout=timeout)
            return result

        except asyncio.TimeoutError:
            logger.error(f"[WebSocket] Command {action} timeout for user {user_id}")
            raise TimeoutError(f"Plugin command timeout after {timeout}s")

        finally:
            pending_requests.pop(request_id, None)


# ===== EVENT HANDLERS =====


@sio.event
async def connect(sid, environ, auth):
    """Client connected."""
    user_id = auth.get("user_id") if auth else None

    if not user_id:
        logger.warning("[WebSocket] Connection rejected: no user_id")
        return False

    # Join user-specific room
    await sio.enter_room(sid, f"user_{user_id}")
    logger.info(f"[WebSocket] User {user_id} connected (sid={sid})")
    return True


@sio.event
async def disconnect(sid):
    """Client disconnected."""
    logger.info(f"[WebSocket] Client disconnected (sid={sid})")


@sio.event
async def plugin_response(sid, data):
    """
    Receive plugin command response from frontend.

    Data format:
    {
        'request_id': 'req_123_...',
        'success': true,
        'data': {...},
        'error': null
    }
    """
    request_id = data.get("request_id")

    if not request_id:
        logger.warning("[WebSocket] Received response without request_id")
        return

    future = pending_requests.get(request_id)
    if not future or future.done():
        logger.warning(f"[WebSocket] No pending request for {request_id}")
        return

    # Resolve the future
    future.set_result(data)
    logger.debug(f"[WebSocket] Received response for {request_id}")


# Export
__all__ = ["sio", "WebSocketService"]
