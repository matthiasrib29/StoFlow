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
from services.auth_service import AuthService
from shared.database import SessionLocal
from models.public.user import User

logger = get_logger(__name__)

# Create SocketIO server
# Note: cors_allowed_origins="*" in dev, specific origins in prod (env-based)
# DEBUG 2026-01-19: Added logger=True to debug 403 connection rejections
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",  # Allow all origins in dev (TODO: configure via env)
    logger=True,  # Enable Socket.IO debug logging
    engineio_logger=True,  # Enable Engine.IO debug logging
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
    """
    Client WebSocket connection with JWT authentication.

    Security (2026-01-12):
    - JWT token MUST be provided and valid
    - Token type MUST be "access"
    - User MUST be active in database
    - Rejects if token invalid, expired, or user inactive

    Auth format:
    {
        "token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
        "user_id": 123  # Optional, for validation only
    }

    Returns:
        bool: True if authenticated, False otherwise
    """
    logger.info(f"[WebSocket] ═══ CONNECTION ATTEMPT ═══")
    logger.info(f"[WebSocket] SID: {sid}")
    logger.info(f"[WebSocket] Auth type: {type(auth).__name__}, has auth: {auth is not None}")

    # 1. Extract token from auth dict
    if not auth or not isinstance(auth, dict):
        logger.info(f"[WebSocket] Connection rejected: no auth dict (sid={sid}, auth={auth})")
        return False

    token = auth.get("token")
    claimed_user_id = auth.get("user_id")  # Optional, for logging
    logger.info(f"[WebSocket] Token present: {bool(token)}, claimed_user_id: {claimed_user_id}")

    if not token:
        logger.info(f"[WebSocket] Connection rejected: no token (sid={sid}, keys={list(auth.keys()) if auth else None})")
        return False

    # 2. Verify JWT token
    logger.debug(f"[WebSocket] Verifying token (first 20 chars): {token[:20] if token else 'N/A'}...")
    payload = AuthService.verify_token(token, token_type="access")
    if not payload:
        logger.warning(f"[WebSocket] Connection rejected: invalid token (sid={sid})")
        return False
    logger.info(f"[WebSocket] Token verified, payload user_id: {payload.get('user_id')}")

    # 3. Extract user_id from verified token (trusted source)
    user_id = payload.get("user_id")
    if not user_id:
        logger.warning(f"[WebSocket] Connection rejected: no user_id in token (sid={sid})")
        return False

    # 4. Security check: verify user is active in database
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            logger.warning(
                f"[WebSocket] Connection rejected: user not found "
                f"(user_id={user_id}, sid={sid})"
            )
            return False

        if not user.is_active:
            logger.warning(
                f"[WebSocket] Connection rejected: user inactive "
                f"(user_id={user_id}, sid={sid})"
            )
            return False
    finally:
        db.close()

    # 5. Log warning if claimed user_id doesn't match token
    if claimed_user_id and claimed_user_id != user_id:
        logger.warning(
            f"[WebSocket] User ID mismatch: claimed={claimed_user_id}, "
            f"token={user_id} (sid={sid})"
        )

    # 6. Authentication successful - join user room
    await sio.enter_room(sid, f"user_{user_id}")
    logger.info(f"[WebSocket] ✓ SUCCESS: User {user_id} joined room 'user_{user_id}' (sid={sid})")
    logger.info(f"[WebSocket] ═══ CONNECTION ESTABLISHED ═══")

    return True


@sio.event
async def disconnect(sid):
    """Client disconnected."""
    logger.info(f"[WebSocket] ═══ DISCONNECTION ═══ (sid={sid})")


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

    # Return ACK to frontend (Socket.IO acknowledgement pattern)
    return {"status": "ok", "request_id": request_id}


# Export
__all__ = ["sio", "WebSocketService"]
