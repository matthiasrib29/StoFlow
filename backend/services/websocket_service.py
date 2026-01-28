"""
WebSocket Service - Real-time communication Backend ↔ Frontend

Provides WebSocket infrastructure for plugin command execution.
Replaces the old PluginTask polling system.

Author: Claude
Date: 2026-01-08
"""
import asyncio
import json
import random
import time
from typing import Any, Dict, Optional

import socketio

from shared.logging import get_logger
from services.auth_service import AuthService
from shared.database import SessionLocal
from models.public.user import User

logger = get_logger(__name__)

# Buffer size limit - must match max_http_buffer_size
MAX_PAYLOAD_SIZE = 10 * 1024 * 1024  # 10MB

# Create SocketIO server
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",  # Allow all origins in dev (TODO: configure via env)
    logger=False,
    engineio_logger=False,
    ping_timeout=120,  # Wait 120s for pong before disconnect (default: 20s)
    ping_interval=25,  # Send ping every 25s (default: 25s)
    max_http_buffer_size=MAX_PAYLOAD_SIZE,
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
        start_time = time.time()

        logger.debug(f"[WebSocket] Command {action} for user {user_id} (req={request_id})")

        # Validate payload size before sending
        message_data = {"request_id": request_id, "action": action, "payload": payload}
        payload_size = len(json.dumps(message_data))
        if payload_size > MAX_PAYLOAD_SIZE:
            logger.error(
                f"[WebSocket] PAYLOAD TOO LARGE: {payload_size} bytes "
                f"(max: {MAX_PAYLOAD_SIZE} bytes) for action {action}"
            )
            raise RuntimeError(
                f"Payload size ({payload_size} bytes) exceeds max buffer size ({MAX_PAYLOAD_SIZE} bytes)"
            )

        # Check if user connected
        room = f"user_{user_id}"
        room_sids = sio.manager.rooms.get("/", {}).get(room, set())

        if not room_sids:
            logger.error(f"[WebSocket] User {user_id} not connected (no clients in room)")
            raise RuntimeError(f"User {user_id} not connected via WebSocket")

        # Create future for response
        future = asyncio.get_event_loop().create_future()
        pending_requests[request_id] = future

        try:
            # Emit command to user's room
            await sio.emit("plugin_command", message_data, room=room)

            # Wait for response
            result = await asyncio.wait_for(future, timeout=timeout)

            elapsed = time.time() - start_time
            logger.debug(f"[WebSocket] {action} completed in {elapsed*1000:.1f}ms (success={result.get('success')})")
            return result

        except asyncio.TimeoutError:
            elapsed = time.time() - start_time
            logger.error(f"[WebSocket] TIMEOUT after {elapsed:.1f}s for {action} (req={request_id})", exc_info=True)
            raise TimeoutError(f"Plugin command timeout after {timeout}s")

        finally:
            pending_requests.pop(request_id, None)


# ===== EVENT HANDLERS =====


@sio.event
async def connect(sid, environ, auth):
    """
    Client WebSocket connection with JWT authentication.

    Security:
    - JWT token MUST be provided and valid
    - Token type MUST be "access"
    - User MUST be active in database
    """
    # 1. Extract token from auth dict
    if not auth or not isinstance(auth, dict):
        logger.debug(f"[WebSocket] Connection rejected: no auth (sid={sid})")
        return False

    token = auth.get("token")
    claimed_user_id = auth.get("user_id")

    if not token:
        logger.debug(f"[WebSocket] Connection rejected: no token (sid={sid})")
        return False

    # 2. Verify JWT token
    payload = AuthService.verify_token(token, token_type="access")
    if not payload:
        logger.warning(f"[WebSocket] Connection rejected: invalid token (sid={sid})")
        return False

    # 3. Extract user_id from verified token
    user_id = payload.get("user_id")
    if not user_id:
        logger.warning(f"[WebSocket] Connection rejected: no user_id in token (sid={sid})")
        return False

    # 4. Verify user is active in database
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            logger.warning(f"[WebSocket] Connection rejected: user {user_id} not found/inactive")
            return False
    finally:
        db.close()

    # 5. Log warning if claimed user_id doesn't match token
    if claimed_user_id and claimed_user_id != user_id:
        logger.warning(f"[WebSocket] User ID mismatch: claimed={claimed_user_id}, token={user_id}")

    # 6. Success - join user room
    await sio.enter_room(sid, f"user_{user_id}")
    logger.info(f"[WebSocket] User {user_id} connected (sid={sid})")

    return True


@sio.event
async def disconnect(sid):
    """Client disconnected."""
    logger.debug(f"[WebSocket] Client disconnected (sid={sid})")


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
        logger.warning("[WebSocket] Response missing request_id")
        return

    future = pending_requests.get(request_id)

    if not future:
        logger.warning(f"[WebSocket] No pending request for {request_id}")
        return

    if future.done():
        logger.warning(f"[WebSocket] Future already resolved for {request_id}")
        return

    # Resolve the future
    future.set_result(data)

    # Return ACK to frontend
    return {"status": "ok", "request_id": request_id}


# Export
__all__ = ["sio", "WebSocketService", "MAX_PAYLOAD_SIZE"]
