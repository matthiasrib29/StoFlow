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
# FIX 2026-01-19: Increased ping_timeout to prevent disconnections during long API calls
# FIX 2026-01-19: Increased max_http_buffer_size to 10MB to prevent disconnects on large payloads
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",  # Allow all origins in dev (TODO: configure via env)
    logger=True,  # Enable Socket.IO debug logging
    engineio_logger=True,  # Enable Engine.IO debug logging
    ping_timeout=120,  # Wait 120s for pong before disconnect (default: 20s)
    ping_interval=25,  # Send ping every 25s (default: 25s)
    max_http_buffer_size=10 * 1024 * 1024,  # 10MB (default: 1MB) - prevents disconnect on large messages
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

        logger.info(f"[WebSocket] ═══ COMMAND START ═══")
        logger.info(f"[WebSocket] Request ID: {request_id}")
        logger.info(f"[WebSocket] Action: {action}")
        logger.info(f"[WebSocket] User ID: {user_id}")
        logger.info(f"[WebSocket] Timeout: {timeout}s")
        logger.debug(f"[WebSocket] Payload: {str(payload)[:200]}...")

        # Check if user connected
        room = f"user_{user_id}"
        room_sids = sio.manager.rooms.get("/", {}).get(room, set())

        logger.info(f"[WebSocket] Room '{room}' has {len(room_sids)} connected clients: {room_sids}")

        if not room_sids:
            logger.error(f"[WebSocket] ✗ No clients in room '{room}'")
            raise RuntimeError(f"User {user_id} not connected via WebSocket")

        # Create future for response
        future = asyncio.get_event_loop().create_future()
        pending_requests[request_id] = future
        logger.info(f"[WebSocket] Pending requests count: {len(pending_requests)}")

        try:
            # Emit command to user's room
            logger.info(f"[WebSocket] → Emitting 'plugin_command' to room '{room}'...")
            await sio.emit(
                "plugin_command",
                {"request_id": request_id, "action": action, "payload": payload},
                room=room,
            )
            emit_time = time.time()
            logger.info(f"[WebSocket] ✓ Emit completed in {(emit_time - start_time)*1000:.1f}ms")
            logger.info(f"[WebSocket] Waiting for response (timeout={timeout}s)...")

            # Wait for response
            result = await asyncio.wait_for(future, timeout=timeout)

            response_time = time.time()
            logger.info(f"[WebSocket] ✓ Response received in {(response_time - start_time)*1000:.1f}ms")
            logger.info(f"[WebSocket] Response success: {result.get('success')}")
            logger.debug(f"[WebSocket] Response data keys: {list(result.get('data', {}).keys()) if result.get('data') else 'N/A'}")
            logger.info(f"[WebSocket] ═══ COMMAND SUCCESS ═══")
            return result

        except asyncio.TimeoutError:
            elapsed = time.time() - start_time
            logger.error(f"[WebSocket] ✗ TIMEOUT after {elapsed:.1f}s")
            logger.error(f"[WebSocket] Request ID that timed out: {request_id}")
            logger.error(f"[WebSocket] Pending requests at timeout: {list(pending_requests.keys())}")
            logger.info(f"[WebSocket] ═══ COMMAND FAILED (TIMEOUT) ═══")
            raise TimeoutError(f"Plugin command timeout after {timeout}s")

        finally:
            was_pending = request_id in pending_requests
            pending_requests.pop(request_id, None)
            logger.debug(f"[WebSocket] Cleaned up request {request_id} (was_pending={was_pending})")


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
    receive_time = time.time()
    request_id = data.get("request_id")

    logger.info(f"[WebSocket] ═══ RESPONSE RECEIVED ═══")
    logger.info(f"[WebSocket] SID: {sid}")
    logger.info(f"[WebSocket] Request ID: {request_id}")
    logger.info(f"[WebSocket] Success: {data.get('success')}")
    logger.info(f"[WebSocket] Has error: {bool(data.get('error'))}")
    logger.info(f"[WebSocket] Has data: {bool(data.get('data'))}")
    logger.debug(f"[WebSocket] Data keys: {list(data.get('data', {}).keys()) if data.get('data') else 'N/A'}")
    logger.info(f"[WebSocket] Current pending requests: {list(pending_requests.keys())}")

    if not request_id:
        logger.warning("[WebSocket] ✗ Response missing request_id!")
        return

    future = pending_requests.get(request_id)

    if not future:
        logger.warning(f"[WebSocket] ✗ No pending request found for {request_id}")
        logger.warning(f"[WebSocket] Available pending requests: {list(pending_requests.keys())}")
        return

    if future.done():
        logger.warning(f"[WebSocket] ✗ Future already done for {request_id}")
        return

    # Resolve the future
    future.set_result(data)
    logger.info(f"[WebSocket] ✓ Future resolved for {request_id}")
    logger.info(f"[WebSocket] ═══ RESPONSE PROCESSED ═══")

    # Return ACK to frontend (Socket.IO acknowledgement pattern)
    return {"status": "ok", "request_id": request_id}


# Export
__all__ = ["sio", "WebSocketService"]
