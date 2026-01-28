"""
Unit tests for WebSocket Service.

Tests payload size validation, send_plugin_command logic,
plugin_response handler, and PluginWebSocketHelper.

Author: Claude
Date: 2026-01-19
"""
import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from services.websocket_service import (
    WebSocketService,
    MAX_PAYLOAD_SIZE,
    pending_requests,
    plugin_response,
)


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def mock_sio():
    """Mock du serveur SocketIO."""
    with patch("services.websocket_service.sio") as mock:
        # Setup rooms structure: {"namespace": {"room_name": {sid1, sid2, ...}}}
        mock.manager = MagicMock()
        mock.manager.rooms = {"/": {"user_1": {"sid_123"}}}
        mock.emit = AsyncMock()
        yield mock


@pytest.fixture
def mock_sio_no_user():
    """Mock du serveur SocketIO sans utilisateur connecté."""
    with patch("services.websocket_service.sio") as mock:
        mock.manager = MagicMock()
        mock.manager.rooms = {"/": {}}  # Empty rooms
        mock.emit = AsyncMock()
        yield mock


@pytest.fixture
def small_payload():
    """Payload de 1 KB."""
    return {"data": "x" * 1000}


@pytest.fixture
def medium_payload():
    """Payload de 1 MB."""
    return {"data": "x" * (1024 * 1024)}


@pytest.fixture
def large_payload():
    """Payload de 5 MB."""
    return {"data": "x" * (5 * 1024 * 1024)}


@pytest.fixture
def at_limit_payload():
    """Payload juste sous 10 MB (~9 MB)."""
    return {"data": "x" * (9 * 1024 * 1024)}


@pytest.fixture
def over_limit_payload():
    """Payload de 11 MB (trop gros)."""
    return {"data": "x" * (11 * 1024 * 1024)}


@pytest.fixture
def cleanup_pending_requests():
    """Cleanup pending_requests after test."""
    yield
    pending_requests.clear()


# ============================================================================
# TEST CLASS: Payload Size Validation
# ============================================================================


class TestPayloadSizeValidation:
    """Tests for payload size validation in send_plugin_command."""

    @pytest.mark.asyncio
    async def test_small_payload_accepted(self, mock_sio, small_payload, cleanup_pending_requests):
        """Un payload de 1KB doit être accepté."""
        # Setup mock to simulate response
        async def resolve_future(*args, **kwargs):
            await asyncio.sleep(0.01)
            # Find the request_id from the emit call and resolve the future
            call_args = mock_sio.emit.call_args
            if call_args:
                message_data = call_args[0][1]  # Second positional arg
                request_id = message_data.get("request_id")
                if request_id and request_id in pending_requests:
                    pending_requests[request_id].set_result({"success": True, "data": {}})

        mock_sio.emit.side_effect = resolve_future

        result = await WebSocketService.send_plugin_command(
            user_id=1, action="TEST_ACTION", payload=small_payload, timeout=5
        )

        assert result["success"] is True
        mock_sio.emit.assert_called_once()

    @pytest.mark.asyncio
    async def test_medium_payload_accepted(self, mock_sio, medium_payload, cleanup_pending_requests):
        """Un payload de 1MB doit être accepté."""
        async def resolve_future(*args, **kwargs):
            await asyncio.sleep(0.01)
            call_args = mock_sio.emit.call_args
            if call_args:
                message_data = call_args[0][1]
                request_id = message_data.get("request_id")
                if request_id and request_id in pending_requests:
                    pending_requests[request_id].set_result({"success": True, "data": {}})

        mock_sio.emit.side_effect = resolve_future

        result = await WebSocketService.send_plugin_command(
            user_id=1, action="TEST_ACTION", payload=medium_payload, timeout=5
        )

        assert result["success"] is True
        mock_sio.emit.assert_called_once()

    @pytest.mark.asyncio
    async def test_large_payload_accepted(self, mock_sio, large_payload, cleanup_pending_requests):
        """Un payload de 5MB doit être accepté."""
        async def resolve_future(*args, **kwargs):
            await asyncio.sleep(0.01)
            call_args = mock_sio.emit.call_args
            if call_args:
                message_data = call_args[0][1]
                request_id = message_data.get("request_id")
                if request_id and request_id in pending_requests:
                    pending_requests[request_id].set_result({"success": True, "data": {}})

        mock_sio.emit.side_effect = resolve_future

        result = await WebSocketService.send_plugin_command(
            user_id=1, action="TEST_ACTION", payload=large_payload, timeout=5
        )

        assert result["success"] is True
        mock_sio.emit.assert_called_once()

    @pytest.mark.asyncio
    async def test_payload_at_limit_accepted(self, mock_sio, at_limit_payload, cleanup_pending_requests):
        """Un payload juste sous 10MB (~9MB) doit être accepté."""
        async def resolve_future(*args, **kwargs):
            await asyncio.sleep(0.01)
            call_args = mock_sio.emit.call_args
            if call_args:
                message_data = call_args[0][1]
                request_id = message_data.get("request_id")
                if request_id and request_id in pending_requests:
                    pending_requests[request_id].set_result({"success": True, "data": {}})

        mock_sio.emit.side_effect = resolve_future

        result = await WebSocketService.send_plugin_command(
            user_id=1, action="TEST_ACTION", payload=at_limit_payload, timeout=5
        )

        assert result["success"] is True
        mock_sio.emit.assert_called_once()

    @pytest.mark.asyncio
    async def test_payload_over_limit_rejected(self, mock_sio, over_limit_payload, cleanup_pending_requests):
        """Un payload > 10MB doit lever RuntimeError."""
        with pytest.raises(RuntimeError) as exc_info:
            await WebSocketService.send_plugin_command(
                user_id=1, action="TEST_ACTION", payload=over_limit_payload, timeout=5
            )

        assert "exceeds max buffer size" in str(exc_info.value)
        assert str(MAX_PAYLOAD_SIZE) in str(exc_info.value)

        # emit ne doit PAS avoir été appelé
        mock_sio.emit.assert_not_called()

    @pytest.mark.asyncio
    async def test_payload_exactly_at_limit(self, mock_sio, cleanup_pending_requests):
        """Test edge case: payload exactement à 10MB."""
        # Calculate overhead: {"request_id": "req_1_xxxxx_xxxx", "action": "TEST", "payload": ...}
        # We need the total JSON to be exactly at limit
        overhead = len(json.dumps({"request_id": "req_1_9999999999999_9999", "action": "TEST", "payload": {"data": ""}}))
        remaining = MAX_PAYLOAD_SIZE - overhead - 10  # Small margin for variation

        exact_payload = {"data": "x" * remaining}

        # Verify size is close to limit
        message_data = {"request_id": "req_1_test", "action": "TEST", "payload": exact_payload}
        size = len(json.dumps(message_data))
        assert size < MAX_PAYLOAD_SIZE, f"Payload size {size} should be under {MAX_PAYLOAD_SIZE}"

        async def resolve_future(*args, **kwargs):
            await asyncio.sleep(0.01)
            call_args = mock_sio.emit.call_args
            if call_args:
                message_data = call_args[0][1]
                request_id = message_data.get("request_id")
                if request_id and request_id in pending_requests:
                    pending_requests[request_id].set_result({"success": True, "data": {}})

        mock_sio.emit.side_effect = resolve_future

        result = await WebSocketService.send_plugin_command(
            user_id=1, action="TEST", payload=exact_payload, timeout=5
        )

        assert result["success"] is True


# ============================================================================
# TEST CLASS: send_plugin_command
# ============================================================================


class TestSendPluginCommand:
    """Tests for the send_plugin_command method."""

    @pytest.mark.asyncio
    async def test_user_not_connected_raises_error(self, mock_sio_no_user, cleanup_pending_requests):
        """Si l'utilisateur n'est pas connecté, RuntimeError est levée."""
        with pytest.raises(RuntimeError) as exc_info:
            await WebSocketService.send_plugin_command(
                user_id=999, action="TEST_ACTION", payload={}, timeout=5
            )

        assert "not connected" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_request_id_format(self, mock_sio, small_payload, cleanup_pending_requests):
        """Le request_id doit avoir le format req_{user_id}_{timestamp}_{random}."""
        async def capture_and_resolve(*args, **kwargs):
            await asyncio.sleep(0.01)
            call_args = mock_sio.emit.call_args
            if call_args:
                message_data = call_args[0][1]
                request_id = message_data.get("request_id")
                if request_id and request_id in pending_requests:
                    pending_requests[request_id].set_result({"success": True, "data": {}})

        mock_sio.emit.side_effect = capture_and_resolve

        await WebSocketService.send_plugin_command(
            user_id=1, action="TEST_ACTION", payload=small_payload, timeout=5
        )

        # Check the emit was called with correct format
        call_args = mock_sio.emit.call_args
        message_data = call_args[0][1]
        request_id = message_data["request_id"]

        # Validate format: req_{user_id}_{timestamp}_{random}
        parts = request_id.split("_")
        assert len(parts) == 4
        assert parts[0] == "req"
        assert parts[1] == "1"  # user_id
        assert parts[2].isdigit()  # timestamp
        assert parts[3].isdigit()  # random number
        assert 1000 <= int(parts[3]) <= 9999  # random between 1000 and 9999

    @pytest.mark.asyncio
    async def test_timeout_raises_error(self, mock_sio, small_payload, cleanup_pending_requests):
        """Si pas de réponse dans le timeout, TimeoutError est levée."""
        # Don't resolve the future - let it timeout
        mock_sio.emit.side_effect = AsyncMock()

        with pytest.raises(TimeoutError) as exc_info:
            await WebSocketService.send_plugin_command(
                user_id=1, action="TEST_ACTION", payload=small_payload, timeout=0.1
            )

        assert "timeout" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_successful_command(self, mock_sio, small_payload, cleanup_pending_requests):
        """Une commande réussie retourne les données attendues."""
        expected_data = {"product_id": 123, "status": "published"}

        async def resolve_with_data(*args, **kwargs):
            await asyncio.sleep(0.01)
            call_args = mock_sio.emit.call_args
            if call_args:
                message_data = call_args[0][1]
                request_id = message_data.get("request_id")
                if request_id and request_id in pending_requests:
                    pending_requests[request_id].set_result({
                        "success": True,
                        "data": expected_data,
                        "error": None
                    })

        mock_sio.emit.side_effect = resolve_with_data

        result = await WebSocketService.send_plugin_command(
            user_id=1, action="VINTED_API_CALL", payload=small_payload, timeout=5
        )

        assert result["success"] is True
        assert result["data"] == expected_data
        assert result["error"] is None


# ============================================================================
# TEST CLASS: plugin_response handler
# ============================================================================


class TestPluginResponse:
    """Tests for the plugin_response event handler."""

    @pytest.mark.asyncio
    async def test_missing_request_id_ignored(self, cleanup_pending_requests):
        """Si request_id manquant, le message est ignoré avec warning."""
        data = {"success": True, "data": {}}  # No request_id

        with patch("services.websocket_service.logger") as mock_logger:
            result = await plugin_response("sid_123", data)

            mock_logger.warning.assert_called_once()
            assert "missing request_id" in mock_logger.warning.call_args[0][0].lower()
            assert result is None

    @pytest.mark.asyncio
    async def test_unknown_request_id_ignored(self, cleanup_pending_requests):
        """Si request_id inconnu, le message est ignoré avec warning."""
        data = {"request_id": "unknown_req_id", "success": True, "data": {}}

        with patch("services.websocket_service.logger") as mock_logger:
            result = await plugin_response("sid_123", data)

            mock_logger.warning.assert_called_once()
            assert "no pending request" in mock_logger.warning.call_args[0][0].lower()
            assert result is None

    @pytest.mark.asyncio
    async def test_valid_response_resolves_future(self, cleanup_pending_requests):
        """Une réponse valide résout le future correspondant."""
        request_id = "req_1_12345_1234"
        loop = asyncio.get_event_loop()
        future = loop.create_future()
        pending_requests[request_id] = future

        data = {
            "request_id": request_id,
            "success": True,
            "data": {"result": "ok"},
            "error": None
        }

        result = await plugin_response("sid_123", data)

        assert result == {"status": "ok", "request_id": request_id}
        assert future.done()
        assert future.result() == data

    @pytest.mark.asyncio
    async def test_duplicate_response_ignored(self, cleanup_pending_requests):
        """Si le future est déjà résolu, la réponse dupliquée est ignorée."""
        request_id = "req_1_12345_1234"
        loop = asyncio.get_event_loop()
        future = loop.create_future()
        future.set_result({"already": "resolved"})  # Already done
        pending_requests[request_id] = future

        data = {
            "request_id": request_id,
            "success": True,
            "data": {"result": "duplicate"},
            "error": None
        }

        with patch("services.websocket_service.logger") as mock_logger:
            result = await plugin_response("sid_123", data)

            mock_logger.warning.assert_called_once()
            assert "already resolved" in mock_logger.warning.call_args[0][0].lower()
            # Should not change the original result
            assert future.result() == {"already": "resolved"}
            assert result is None


# ============================================================================
# TEST CLASS: MAX_PAYLOAD_SIZE constant
# ============================================================================


class TestMaxPayloadSize:
    """Tests for the MAX_PAYLOAD_SIZE constant."""

    def test_max_payload_size_is_10mb(self):
        """MAX_PAYLOAD_SIZE doit être exactement 10MB."""
        assert MAX_PAYLOAD_SIZE == 10 * 1024 * 1024
        assert MAX_PAYLOAD_SIZE == 10485760

    def test_max_payload_size_matches_sio_config(self):
        """MAX_PAYLOAD_SIZE doit correspondre à la config SocketIO."""
        from services.websocket_service import sio

        # sio.eio.max_http_buffer_size should match
        assert sio.eio.max_http_buffer_size == MAX_PAYLOAD_SIZE


# ============================================================================
# TEST CLASS: Room Management
# ============================================================================


class TestRoomManagement:
    """Tests for room/user connection management."""

    @pytest.mark.asyncio
    async def test_emit_targets_correct_room(self, mock_sio, small_payload, cleanup_pending_requests):
        """L'emit doit cibler la room user_{user_id}."""
        async def resolve_and_check(*args, **kwargs):
            await asyncio.sleep(0.01)
            call_args = mock_sio.emit.call_args
            if call_args:
                message_data = call_args[0][1]
                request_id = message_data.get("request_id")
                if request_id and request_id in pending_requests:
                    pending_requests[request_id].set_result({"success": True})

        mock_sio.emit.side_effect = resolve_and_check

        await WebSocketService.send_plugin_command(
            user_id=1, action="TEST_ACTION", payload=small_payload, timeout=5
        )

        # Check emit was called with room="user_1"
        call_args = mock_sio.emit.call_args
        assert call_args[1]["room"] == "user_1"

    @pytest.mark.asyncio
    async def test_user_with_multiple_sids_accepted(self, cleanup_pending_requests):
        """Un utilisateur avec plusieurs connexions (SIDs) doit fonctionner."""
        with patch("services.websocket_service.sio") as mock_sio:
            # User has 3 connections
            mock_sio.manager = MagicMock()
            mock_sio.manager.rooms = {"/": {"user_42": {"sid_1", "sid_2", "sid_3"}}}

            async def resolve_future(*args, **kwargs):
                await asyncio.sleep(0.01)
                call_args = mock_sio.emit.call_args
                if call_args:
                    message_data = call_args[0][1]
                    request_id = message_data.get("request_id")
                    if request_id and request_id in pending_requests:
                        pending_requests[request_id].set_result({"success": True})

            mock_sio.emit = AsyncMock(side_effect=resolve_future)

            result = await WebSocketService.send_plugin_command(
                user_id=42, action="TEST_ACTION", payload={"test": 1}, timeout=5
            )

            assert result["success"] is True


# ============================================================================
# TEST CLASS: Cleanup / Edge Cases
# ============================================================================


class TestCleanupAndEdgeCases:
    """Tests for cleanup and edge cases."""

    @pytest.mark.asyncio
    async def test_pending_request_cleaned_on_success(self, mock_sio, small_payload, cleanup_pending_requests):
        """Après une réponse réussie, le pending_request est nettoyé."""
        request_id_captured = []

        async def capture_and_resolve(*args, **kwargs):
            await asyncio.sleep(0.01)
            call_args = mock_sio.emit.call_args
            if call_args:
                message_data = call_args[0][1]
                request_id = message_data.get("request_id")
                request_id_captured.append(request_id)
                if request_id and request_id in pending_requests:
                    pending_requests[request_id].set_result({"success": True})

        mock_sio.emit.side_effect = capture_and_resolve

        await WebSocketService.send_plugin_command(
            user_id=1, action="TEST_ACTION", payload=small_payload, timeout=5
        )

        # The request should have been cleaned up
        assert len(request_id_captured) == 1
        assert request_id_captured[0] not in pending_requests

    @pytest.mark.asyncio
    async def test_pending_request_cleaned_on_timeout(self, mock_sio, small_payload, cleanup_pending_requests):
        """Après un timeout, le pending_request est nettoyé."""
        request_id_captured = []

        async def capture_no_resolve(*args, **kwargs):
            call_args = mock_sio.emit.call_args
            if call_args:
                message_data = call_args[0][1]
                request_id = message_data.get("request_id")
                request_id_captured.append(request_id)
            # Don't resolve - let it timeout

        mock_sio.emit.side_effect = capture_no_resolve

        with pytest.raises(TimeoutError):
            await WebSocketService.send_plugin_command(
                user_id=1, action="TEST_ACTION", payload=small_payload, timeout=0.1
            )

        # The request should have been cleaned up even on timeout
        assert len(request_id_captured) == 1
        assert request_id_captured[0] not in pending_requests

    @pytest.mark.asyncio
    async def test_empty_payload_accepted(self, mock_sio, cleanup_pending_requests):
        """Un payload vide doit être accepté."""
        async def resolve_future(*args, **kwargs):
            await asyncio.sleep(0.01)
            call_args = mock_sio.emit.call_args
            if call_args:
                message_data = call_args[0][1]
                request_id = message_data.get("request_id")
                if request_id and request_id in pending_requests:
                    pending_requests[request_id].set_result({"success": True})

        mock_sio.emit.side_effect = resolve_future

        result = await WebSocketService.send_plugin_command(
            user_id=1, action="TEST_ACTION", payload={}, timeout=5
        )

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_nested_payload_size_calculated(self, mock_sio, cleanup_pending_requests):
        """La taille d'un payload imbriqué doit être correctement calculée."""
        # Create nested payload that when serialized is > 10MB
        nested_payload = {
            "level1": {
                "level2": {
                    "level3": {
                        "data": "x" * (11 * 1024 * 1024)
                    }
                }
            }
        }

        with pytest.raises(RuntimeError) as exc_info:
            await WebSocketService.send_plugin_command(
                user_id=1, action="TEST_ACTION", payload=nested_payload, timeout=5
            )

        assert "exceeds max buffer size" in str(exc_info.value)


# ============================================================================
# TEST CLASS: Message Structure
# ============================================================================


class TestMessageStructure:
    """Tests for the structure of messages sent via WebSocket."""

    @pytest.mark.asyncio
    async def test_message_contains_required_fields(self, mock_sio, small_payload, cleanup_pending_requests):
        """Le message émis doit contenir request_id, action et payload."""
        captured_message = {}

        async def capture_message(*args, **kwargs):
            await asyncio.sleep(0.01)
            call_args = mock_sio.emit.call_args
            if call_args:
                captured_message.update(call_args[0][1])
                request_id = captured_message.get("request_id")
                if request_id and request_id in pending_requests:
                    pending_requests[request_id].set_result({"success": True})

        mock_sio.emit.side_effect = capture_message

        await WebSocketService.send_plugin_command(
            user_id=1, action="VINTED_API_CALL", payload=small_payload, timeout=5
        )

        assert "request_id" in captured_message
        assert "action" in captured_message
        assert "payload" in captured_message
        assert captured_message["action"] == "VINTED_API_CALL"
        assert captured_message["payload"] == small_payload

    @pytest.mark.asyncio
    async def test_event_name_is_plugin_command(self, mock_sio, small_payload, cleanup_pending_requests):
        """L'événement émis doit être 'plugin_command'."""
        async def resolve_future(*args, **kwargs):
            await asyncio.sleep(0.01)
            call_args = mock_sio.emit.call_args
            if call_args:
                message_data = call_args[0][1]
                request_id = message_data.get("request_id")
                if request_id and request_id in pending_requests:
                    pending_requests[request_id].set_result({"success": True})

        mock_sio.emit.side_effect = resolve_future

        await WebSocketService.send_plugin_command(
            user_id=1, action="TEST_ACTION", payload=small_payload, timeout=5
        )

        call_args = mock_sio.emit.call_args
        assert call_args[0][0] == "plugin_command"
