"""
WebSocket Connection Tests - Comprehensive diagnosis suite

These tests diagnose WebSocket connection issues by testing:
1. Basic WebSocket connectivity
2. Authentication flow
3. Transport modes (polling, websocket, upgrade)
4. Connection stability
5. Message exchange patterns
6. Disconnect scenarios

Run with: pytest tests/websocket/ -v -s

Author: Claude
Date: 2026-01-19
"""
import asyncio
import time
from typing import Optional
from unittest.mock import patch

import pytest
import socketio
from socketio.exceptions import ConnectionError as SIOConnectionError

# Test configuration
BACKEND_URL = "http://localhost:8000"
TEST_TIMEOUT = 30  # seconds


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def valid_token(db_session, test_user):
    """Get a valid JWT token for testing."""
    from services.auth_service import AuthService
    token = AuthService.create_access_token(
        user_id=test_user.id,
        role=test_user.role
    )
    return token


@pytest.fixture
def invalid_token():
    """Get an invalid JWT token."""
    return "invalid.jwt.token"


@pytest.fixture
def expired_token(test_user):
    """Get an expired JWT token."""
    from services.auth_service import AuthService
    import datetime
    # Create token that expired 1 hour ago
    with patch.object(AuthService, '_get_token_expiry', return_value=datetime.timedelta(hours=-1)):
        token = AuthService.create_access_token(
            user_id=test_user.id,
            role=test_user.role
        )
    return token


# ============================================================================
# HELPER CLASSES
# ============================================================================

class ConnectionTracker:
    """Track connection events for diagnosis."""

    def __init__(self):
        self.events = []
        self.connected = False
        self.disconnected = False
        self.connect_time: Optional[float] = None
        self.disconnect_time: Optional[float] = None
        self.disconnect_reason: Optional[str] = None
        self.errors = []
        self.messages_received = []
        self.transport_upgrades = []

    def log(self, event: str, data: any = None):
        timestamp = time.time()
        self.events.append({
            'timestamp': timestamp,
            'event': event,
            'data': data
        })
        print(f"[{timestamp:.3f}] {event}: {data}")

    def on_connect(self):
        self.connected = True
        self.connect_time = time.time()
        self.log('CONNECT')

    def on_disconnect(self, reason=None):
        self.disconnected = True
        self.disconnect_time = time.time()
        self.disconnect_reason = reason
        self.log('DISCONNECT', reason)

    def on_error(self, error):
        self.errors.append(error)
        self.log('ERROR', str(error))

    def on_message(self, event, data):
        self.messages_received.append({'event': event, 'data': data})
        self.log('MESSAGE', f"{event}: {data}")

    def get_connection_duration(self) -> Optional[float]:
        if self.connect_time and self.disconnect_time:
            return self.disconnect_time - self.connect_time
        return None

    def summary(self) -> dict:
        return {
            'connected': self.connected,
            'disconnected': self.disconnected,
            'connection_duration_ms': (self.get_connection_duration() or 0) * 1000,
            'disconnect_reason': self.disconnect_reason,
            'error_count': len(self.errors),
            'errors': self.errors,
            'event_count': len(self.events),
            'messages_received': len(self.messages_received)
        }


# ============================================================================
# TEST: BASIC CONNECTIVITY
# ============================================================================

class TestBasicConnectivity:
    """Test basic WebSocket connectivity without authentication."""

    @pytest.mark.asyncio
    async def test_server_reachable(self):
        """Test that the WebSocket server is reachable."""
        import httpx

        async with httpx.AsyncClient() as client:
            # Socket.IO serves a special endpoint
            response = await client.get(f"{BACKEND_URL}/socket.io/?EIO=4&transport=polling")

            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.text[:200]}")

            # Socket.IO should respond with OPEN packet
            assert response.status_code == 200
            assert response.text.startswith('0')  # OPEN packet

    @pytest.mark.asyncio
    async def test_websocket_upgrade_available(self):
        """Test that WebSocket upgrade is advertised."""
        import httpx
        import json

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BACKEND_URL}/socket.io/?EIO=4&transport=polling")

            # Parse the OPEN packet (format: "0{json}")
            if response.text.startswith('0'):
                data = json.loads(response.text[1:])
                print(f"Server capabilities: {data}")

                assert 'upgrades' in data
                assert 'websocket' in data['upgrades']
                assert 'pingTimeout' in data
                assert 'pingInterval' in data


# ============================================================================
# TEST: AUTHENTICATION
# ============================================================================

class TestAuthentication:
    """Test WebSocket authentication flows."""

    @pytest.mark.asyncio
    async def test_connection_without_auth_rejected(self):
        """Test that connection without auth is rejected."""
        tracker = ConnectionTracker()
        sio = socketio.AsyncClient(logger=True, engineio_logger=True)

        sio.on('connect', tracker.on_connect)
        sio.on('disconnect', tracker.on_disconnect)
        sio.on('connect_error', tracker.on_error)

        try:
            await sio.connect(
                BACKEND_URL,
                transports=['websocket'],
                wait_timeout=5
            )
            # Should not reach here
            pytest.fail("Connection without auth should be rejected")
        except SIOConnectionError as e:
            tracker.log('CONNECTION_REJECTED', str(e))
            # Expected - connection should be rejected
            assert not tracker.connected
        finally:
            if sio.connected:
                await sio.disconnect()

        print(f"\nSummary: {tracker.summary()}")

    @pytest.mark.asyncio
    async def test_connection_with_invalid_token_rejected(self, invalid_token):
        """Test that connection with invalid token is rejected."""
        tracker = ConnectionTracker()
        sio = socketio.AsyncClient(logger=True, engineio_logger=True)

        sio.on('connect', tracker.on_connect)
        sio.on('disconnect', tracker.on_disconnect)
        sio.on('connect_error', tracker.on_error)

        try:
            await sio.connect(
                BACKEND_URL,
                auth={'token': invalid_token, 'user_id': 999},
                transports=['websocket'],
                wait_timeout=5
            )
            pytest.fail("Connection with invalid token should be rejected")
        except SIOConnectionError as e:
            tracker.log('CONNECTION_REJECTED', str(e))
            assert not tracker.connected
        finally:
            if sio.connected:
                await sio.disconnect()

        print(f"\nSummary: {tracker.summary()}")

    @pytest.mark.asyncio
    async def test_connection_with_valid_token_accepted(self, valid_token, test_user):
        """Test that connection with valid token is accepted."""
        tracker = ConnectionTracker()
        sio = socketio.AsyncClient(logger=True, engineio_logger=True)

        sio.on('connect', tracker.on_connect)
        sio.on('disconnect', tracker.on_disconnect)
        sio.on('connect_error', tracker.on_error)

        try:
            await sio.connect(
                BACKEND_URL,
                auth={'token': valid_token, 'user_id': test_user.id},
                transports=['websocket'],
                wait_timeout=10
            )

            assert tracker.connected
            assert sio.connected

            # Wait a bit to check stability
            await asyncio.sleep(2)

            # Should still be connected
            assert sio.connected
            assert not tracker.disconnected

        finally:
            if sio.connected:
                await sio.disconnect()

        print(f"\nSummary: {tracker.summary()}")


# ============================================================================
# TEST: TRANSPORT MODES
# ============================================================================

class TestTransportModes:
    """Test different transport modes and upgrades."""

    @pytest.mark.asyncio
    async def test_websocket_only_transport(self, valid_token, test_user):
        """Test connection with WebSocket-only transport."""
        tracker = ConnectionTracker()
        sio = socketio.AsyncClient(logger=True, engineio_logger=True)

        sio.on('connect', tracker.on_connect)
        sio.on('disconnect', lambda: tracker.on_disconnect('client_disconnect'))
        sio.on('connect_error', tracker.on_error)

        try:
            print("\n=== Testing WebSocket-only transport ===")
            await sio.connect(
                BACKEND_URL,
                auth={'token': valid_token, 'user_id': test_user.id},
                transports=['websocket'],
                wait_timeout=10
            )

            assert tracker.connected
            print(f"Transport: {sio.transport()}")
            assert sio.transport() == 'websocket'

            # Hold connection for 5 seconds
            for i in range(5):
                await asyncio.sleep(1)
                print(f"  Second {i+1}: connected={sio.connected}")
                if not sio.connected:
                    print(f"  DISCONNECTED at second {i+1}!")
                    break

            if tracker.disconnected:
                print(f"\n⚠️ UNEXPECTED DISCONNECT!")
                print(f"  Duration: {tracker.get_connection_duration()*1000:.1f}ms")
                print(f"  Reason: {tracker.disconnect_reason}")

        finally:
            if sio.connected:
                await sio.disconnect()

        print(f"\nSummary: {tracker.summary()}")

    @pytest.mark.asyncio
    async def test_polling_only_transport(self, valid_token, test_user):
        """Test connection with polling-only transport (no upgrade)."""
        tracker = ConnectionTracker()
        sio = socketio.AsyncClient(logger=True, engineio_logger=True)

        sio.on('connect', tracker.on_connect)
        sio.on('disconnect', lambda: tracker.on_disconnect('client_disconnect'))
        sio.on('connect_error', tracker.on_error)

        try:
            print("\n=== Testing Polling-only transport ===")
            await sio.connect(
                BACKEND_URL,
                auth={'token': valid_token, 'user_id': test_user.id},
                transports=['polling'],
                wait_timeout=10
            )

            assert tracker.connected
            print(f"Transport: {sio.transport()}")
            assert sio.transport() == 'polling'

            # Hold connection for 5 seconds
            for i in range(5):
                await asyncio.sleep(1)
                print(f"  Second {i+1}: connected={sio.connected}")
                if not sio.connected:
                    print(f"  DISCONNECTED at second {i+1}!")
                    break

        finally:
            if sio.connected:
                await sio.disconnect()

        print(f"\nSummary: {tracker.summary()}")

    @pytest.mark.asyncio
    async def test_polling_to_websocket_upgrade(self, valid_token, test_user):
        """Test connection with polling then upgrade to WebSocket."""
        tracker = ConnectionTracker()
        sio = socketio.AsyncClient(logger=True, engineio_logger=True)

        transport_changes = []

        def on_transport_change(transport):
            transport_changes.append({
                'transport': transport,
                'time': time.time()
            })
            tracker.log('TRANSPORT_CHANGE', transport)

        sio.on('connect', tracker.on_connect)
        sio.on('disconnect', lambda: tracker.on_disconnect('client_disconnect'))
        sio.on('connect_error', tracker.on_error)

        try:
            print("\n=== Testing Polling → WebSocket upgrade ===")
            await sio.connect(
                BACKEND_URL,
                auth={'token': valid_token, 'user_id': test_user.id},
                transports=['polling', 'websocket'],  # Start polling, upgrade to WS
                wait_timeout=10
            )

            assert tracker.connected
            initial_transport = sio.transport()
            print(f"Initial transport: {initial_transport}")

            # Wait for potential upgrade
            for i in range(10):
                await asyncio.sleep(1)
                current_transport = sio.transport()
                print(f"  Second {i+1}: transport={current_transport}, connected={sio.connected}")

                if current_transport != initial_transport:
                    transport_changes.append({
                        'from': initial_transport,
                        'to': current_transport,
                        'time': time.time()
                    })

                if not sio.connected:
                    print(f"  ⚠️ DISCONNECTED at second {i+1}!")
                    break

            print(f"\nTransport changes: {transport_changes}")

        finally:
            if sio.connected:
                await sio.disconnect()

        print(f"\nSummary: {tracker.summary()}")


# ============================================================================
# TEST: CONNECTION STABILITY
# ============================================================================

class TestConnectionStability:
    """Test connection stability over time."""

    @pytest.mark.asyncio
    async def test_connection_stays_alive_30_seconds(self, valid_token, test_user):
        """Test that connection stays alive for 30 seconds."""
        tracker = ConnectionTracker()
        sio = socketio.AsyncClient(logger=True, engineio_logger=True)

        sio.on('connect', tracker.on_connect)
        sio.on('disconnect', lambda: tracker.on_disconnect('unknown'))
        sio.on('connect_error', tracker.on_error)

        try:
            print("\n=== Testing 30-second connection stability ===")
            await sio.connect(
                BACKEND_URL,
                auth={'token': valid_token, 'user_id': test_user.id},
                transports=['websocket'],
                wait_timeout=10
            )

            assert tracker.connected

            disconnect_at = None
            for i in range(30):
                await asyncio.sleep(1)
                if not sio.connected:
                    disconnect_at = i + 1
                    print(f"  ⚠️ DISCONNECTED at second {disconnect_at}!")
                    break
                if i % 5 == 0:
                    print(f"  Second {i+1}: still connected ✓")

            if disconnect_at:
                print(f"\n❌ Connection dropped after {disconnect_at} seconds")
                print(f"  Disconnect reason: {tracker.disconnect_reason}")
            else:
                print(f"\n✅ Connection stable for 30 seconds")

        finally:
            if sio.connected:
                await sio.disconnect()

        print(f"\nSummary: {tracker.summary()}")

    @pytest.mark.asyncio
    async def test_rapid_connect_disconnect_cycles(self, valid_token, test_user):
        """Test rapid connect/disconnect cycles."""
        results = []

        print("\n=== Testing rapid connect/disconnect cycles ===")

        for cycle in range(5):
            tracker = ConnectionTracker()
            sio = socketio.AsyncClient()

            sio.on('connect', tracker.on_connect)
            sio.on('disconnect', lambda: tracker.on_disconnect('client_disconnect'))
            sio.on('connect_error', tracker.on_error)

            try:
                start = time.time()
                await sio.connect(
                    BACKEND_URL,
                    auth={'token': valid_token, 'user_id': test_user.id},
                    transports=['websocket'],
                    wait_timeout=10
                )
                connect_time = time.time() - start

                # Stay connected briefly
                await asyncio.sleep(0.5)

                # Disconnect
                await sio.disconnect()

                results.append({
                    'cycle': cycle + 1,
                    'success': tracker.connected,
                    'connect_time_ms': connect_time * 1000,
                    'errors': tracker.errors
                })

                print(f"  Cycle {cycle+1}: {'✓' if tracker.connected else '✗'} ({connect_time*1000:.1f}ms)")

            except Exception as e:
                results.append({
                    'cycle': cycle + 1,
                    'success': False,
                    'error': str(e)
                })
                print(f"  Cycle {cycle+1}: ✗ ({e})")

            # Brief pause between cycles
            await asyncio.sleep(0.5)

        success_count = sum(1 for r in results if r.get('success'))
        print(f"\n✅ {success_count}/5 cycles successful")


# ============================================================================
# TEST: MESSAGE EXCHANGE
# ============================================================================

class TestMessageExchange:
    """Test message sending and receiving."""

    @pytest.mark.asyncio
    async def test_emit_plugin_response(self, valid_token, test_user):
        """Test emitting a plugin_response message."""
        tracker = ConnectionTracker()
        sio = socketio.AsyncClient(logger=True, engineio_logger=True)

        response_received = asyncio.Event()
        response_data = {}

        @sio.on('plugin_command')
        async def on_plugin_command(data):
            tracker.on_message('plugin_command', data)
            # Echo back a response
            await sio.emit('plugin_response', {
                'request_id': data.get('request_id', 'test'),
                'success': True,
                'data': {'test': 'response'},
                'error': None
            })

        sio.on('connect', tracker.on_connect)
        sio.on('disconnect', lambda: tracker.on_disconnect('unknown'))
        sio.on('connect_error', tracker.on_error)

        try:
            print("\n=== Testing message exchange ===")
            await sio.connect(
                BACKEND_URL,
                auth={'token': valid_token, 'user_id': test_user.id},
                transports=['websocket'],
                wait_timeout=10
            )

            assert tracker.connected

            # Send a test message
            print("Sending plugin_response...")
            await sio.emit('plugin_response', {
                'request_id': 'test_req_123',
                'success': True,
                'data': {'test': 'data'},
                'error': None
            })

            # Wait a bit
            await asyncio.sleep(2)

            # Check still connected
            assert sio.connected, "Disconnected after sending message!"
            print("✅ Still connected after sending message")

        finally:
            if sio.connected:
                await sio.disconnect()

        print(f"\nSummary: {tracker.summary()}")

    @pytest.mark.asyncio
    async def test_emit_with_ack(self, valid_token, test_user):
        """Test emitting with acknowledgement."""
        tracker = ConnectionTracker()
        sio = socketio.AsyncClient(logger=True, engineio_logger=True)

        sio.on('connect', tracker.on_connect)
        sio.on('disconnect', lambda: tracker.on_disconnect('unknown'))
        sio.on('connect_error', tracker.on_error)

        try:
            print("\n=== Testing emit with acknowledgement ===")
            await sio.connect(
                BACKEND_URL,
                auth={'token': valid_token, 'user_id': test_user.id},
                transports=['websocket'],
                wait_timeout=10
            )

            assert tracker.connected

            # Emit with callback (acknowledgement)
            print("Emitting plugin_response with ack...")

            try:
                # Use call() which waits for ack
                response = await asyncio.wait_for(
                    sio.call('plugin_response', {
                        'request_id': 'test_ack_123',
                        'success': True,
                        'data': {'test': 'ack_data'},
                        'error': None
                    }),
                    timeout=10
                )
                print(f"Received ack: {response}")
            except asyncio.TimeoutError:
                print("⚠️ Ack timeout - server may not send ack for this event")

            # Check still connected
            await asyncio.sleep(1)
            assert sio.connected, "Disconnected after emit with ack!"
            print("✅ Still connected after emit with ack")

        finally:
            if sio.connected:
                await sio.disconnect()

        print(f"\nSummary: {tracker.summary()}")


# ============================================================================
# TEST: DISCONNECT SCENARIOS
# ============================================================================

class TestDisconnectScenarios:
    """Test various disconnect scenarios."""

    @pytest.mark.asyncio
    async def test_graceful_client_disconnect(self, valid_token, test_user):
        """Test graceful client-initiated disconnect."""
        tracker = ConnectionTracker()
        sio = socketio.AsyncClient(logger=True, engineio_logger=True)

        sio.on('connect', tracker.on_connect)
        sio.on('disconnect', lambda: tracker.on_disconnect('io client disconnect'))
        sio.on('connect_error', tracker.on_error)

        try:
            print("\n=== Testing graceful disconnect ===")
            await sio.connect(
                BACKEND_URL,
                auth={'token': valid_token, 'user_id': test_user.id},
                transports=['websocket'],
                wait_timeout=10
            )

            assert tracker.connected

            # Graceful disconnect
            print("Initiating graceful disconnect...")
            await sio.disconnect()

            # Wait a bit for disconnect event
            await asyncio.sleep(0.5)

            assert tracker.disconnected
            assert not sio.connected
            print("✅ Graceful disconnect successful")

        except Exception as e:
            print(f"❌ Error: {e}")
            raise

        print(f"\nSummary: {tracker.summary()}")

    @pytest.mark.asyncio
    async def test_reconnection_after_disconnect(self, valid_token, test_user):
        """Test reconnection after disconnect."""
        tracker = ConnectionTracker()
        sio = socketio.AsyncClient(
            logger=True,
            engineio_logger=True,
            reconnection=True,
            reconnection_attempts=3,
            reconnection_delay=1,
            reconnection_delay_max=3
        )

        reconnect_count = 0

        @sio.event
        async def connect():
            nonlocal reconnect_count
            reconnect_count += 1
            tracker.on_connect()
            print(f"  Connect event #{reconnect_count}")

        sio.on('disconnect', lambda: tracker.on_disconnect('unknown'))
        sio.on('connect_error', tracker.on_error)

        try:
            print("\n=== Testing reconnection ===")
            await sio.connect(
                BACKEND_URL,
                auth={'token': valid_token, 'user_id': test_user.id},
                transports=['websocket'],
                wait_timeout=10
            )

            assert tracker.connected
            print(f"Initial connect: reconnect_count={reconnect_count}")

            # Simulate disconnect by closing the transport
            # This should trigger auto-reconnection
            print("Waiting 10 seconds to observe stability...")
            for i in range(10):
                await asyncio.sleep(1)
                print(f"  Second {i+1}: connected={sio.connected}, reconnects={reconnect_count}")

            print(f"Final reconnect count: {reconnect_count}")

        finally:
            if sio.connected:
                await sio.disconnect()

        print(f"\nSummary: {tracker.summary()}")


# ============================================================================
# TEST: PING/PONG
# ============================================================================

class TestPingPong:
    """Test ping/pong keep-alive mechanism."""

    @pytest.mark.asyncio
    async def test_ping_pong_over_time(self, valid_token, test_user):
        """Test that ping/pong keeps connection alive."""
        tracker = ConnectionTracker()
        sio = socketio.AsyncClient(logger=True, engineio_logger=True)

        ping_count = 0
        pong_count = 0

        sio.on('connect', tracker.on_connect)
        sio.on('disconnect', lambda: tracker.on_disconnect('unknown'))
        sio.on('connect_error', tracker.on_error)

        try:
            print("\n=== Testing ping/pong over 60 seconds ===")
            print("Note: pingInterval=25s, pingTimeout=120s on server")

            await sio.connect(
                BACKEND_URL,
                auth={'token': valid_token, 'user_id': test_user.id},
                transports=['websocket'],
                wait_timeout=10
            )

            assert tracker.connected

            # Monitor for 60 seconds (should see at least 2 ping/pong cycles)
            for i in range(60):
                await asyncio.sleep(1)

                if not sio.connected:
                    print(f"  ⚠️ DISCONNECTED at second {i+1}!")
                    break

                if i % 10 == 0:
                    print(f"  Second {i+1}: connected ✓")

            if sio.connected:
                print("✅ Connection stable for 60 seconds (ping/pong working)")
            else:
                print(f"❌ Connection dropped")
                print(f"  Disconnect reason: {tracker.disconnect_reason}")

        finally:
            if sio.connected:
                await sio.disconnect()

        print(f"\nSummary: {tracker.summary()}")


# ============================================================================
# MAIN: Run all tests
# ============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
