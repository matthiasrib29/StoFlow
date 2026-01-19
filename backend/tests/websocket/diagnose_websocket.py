#!/usr/bin/env python3
"""
WebSocket Diagnosis Script - Standalone diagnostic tool

This script diagnoses WebSocket connection issues without pytest.
It tests various scenarios and reports detailed results.

Run directly: python tests/websocket/diagnose_websocket.py

Author: Claude
Date: 2026-01-19
"""
import asyncio
import json
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

# Add backend to path for imports
sys.path.insert(0, '/home/maribeiro/StoFlow-fiw-websocket/backend')

import socketio
from socketio.exceptions import ConnectionError as SIOConnectionError

# Configuration
BACKEND_URL = "http://localhost:8000"
TEST_USER_ID = 1  # Default test user


@dataclass
class TestResult:
    """Result of a single test."""
    name: str
    passed: bool
    duration_ms: float
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    events: List[Dict] = field(default_factory=list)


class DiagnosticReport:
    """Collect and report diagnostic results."""

    def __init__(self):
        self.results: List[TestResult] = []
        self.start_time = time.time()

    def add_result(self, result: TestResult):
        self.results.append(result)
        status = "✅ PASS" if result.passed else "❌ FAIL"
        print(f"\n{status}: {result.name} ({result.duration_ms:.1f}ms)")
        if result.message:
            print(f"   {result.message}")
        if result.details:
            for key, value in result.details.items():
                print(f"   {key}: {value}")

    def summary(self):
        print("\n" + "=" * 60)
        print("DIAGNOSTIC SUMMARY")
        print("=" * 60)

        passed = sum(1 for r in self.results if r.passed)
        failed = len(self.results) - passed

        print(f"Total tests: {len(self.results)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Total time: {(time.time() - self.start_time):.1f}s")

        if failed > 0:
            print("\n⚠️ FAILED TESTS:")
            for r in self.results:
                if not r.passed:
                    print(f"  - {r.name}: {r.message}")

        print("=" * 60)


def get_test_token() -> str:
    """Generate a valid JWT token for testing."""
    from dotenv import load_dotenv
    load_dotenv()

    from services.auth_service import AuthService
    from shared.database import SessionLocal
    from models.public.user import User

    db = SessionLocal()
    try:
        # Get first active user or use ID 1
        user = db.query(User).filter(User.id == TEST_USER_ID, User.is_active == True).first()
        if not user:
            user = db.query(User).filter(User.is_active == True).first()
        if not user:
            raise ValueError("No active user found in database")

        print(f"Using test user: {user.id} ({user.email})")

        token = AuthService.create_access_token(
            user_id=user.id,
            role=user.role
        )
        return token, user.id
    finally:
        db.close()


class ConnectionMonitor:
    """Monitor connection events in detail."""

    def __init__(self):
        self.events: List[Dict] = []
        self.connected = False
        self.disconnected = False
        self.connect_time: Optional[float] = None
        self.disconnect_time: Optional[float] = None
        self.disconnect_reason: Optional[str] = None
        self.errors: List[str] = []

    def log(self, event: str, data: Any = None):
        timestamp = time.time()
        entry = {
            'time': timestamp,
            'time_str': datetime.fromtimestamp(timestamp).strftime('%H:%M:%S.%f')[:-3],
            'event': event,
            'data': str(data) if data else None
        }
        self.events.append(entry)
        print(f"  [{entry['time_str']}] {event}" + (f": {data}" if data else ""))

    def on_connect(self):
        self.connected = True
        self.connect_time = time.time()
        self.log("CONNECT")

    def on_disconnect(self, reason=None):
        self.disconnected = True
        self.disconnect_time = time.time()
        self.disconnect_reason = reason
        self.log("DISCONNECT", reason)

    def on_error(self, error):
        self.errors.append(str(error))
        self.log("ERROR", error)

    def connection_duration_ms(self) -> Optional[float]:
        if self.connect_time and self.disconnect_time:
            return (self.disconnect_time - self.connect_time) * 1000
        return None


async def test_server_reachable(report: DiagnosticReport):
    """Test 1: Check if server is reachable."""
    start = time.time()
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BACKEND_URL}/socket.io/?EIO=4&transport=polling",
                timeout=5
            )

            if response.status_code == 200 and response.text.startswith('0'):
                # Parse server config
                config = json.loads(response.text[1:])
                report.add_result(TestResult(
                    name="Server Reachable",
                    passed=True,
                    duration_ms=(time.time() - start) * 1000,
                    message="Socket.IO server responding",
                    details={
                        'upgrades': config.get('upgrades', []),
                        'pingTimeout': config.get('pingTimeout'),
                        'pingInterval': config.get('pingInterval'),
                    }
                ))
            else:
                report.add_result(TestResult(
                    name="Server Reachable",
                    passed=False,
                    duration_ms=(time.time() - start) * 1000,
                    message=f"Unexpected response: {response.status_code}",
                ))
    except Exception as e:
        report.add_result(TestResult(
            name="Server Reachable",
            passed=False,
            duration_ms=(time.time() - start) * 1000,
            message=f"Connection failed: {e}",
        ))


async def test_websocket_connection(report: DiagnosticReport, token: str, user_id: int):
    """Test 2: Basic WebSocket connection with auth."""
    start = time.time()
    monitor = ConnectionMonitor()
    sio = socketio.AsyncClient(logger=False, engineio_logger=False)

    sio.on('connect', monitor.on_connect)
    sio.on('disconnect', monitor.on_disconnect)
    sio.on('connect_error', monitor.on_error)

    try:
        print("\n  Connecting with WebSocket transport...")
        await sio.connect(
            BACKEND_URL,
            auth={'token': token, 'user_id': user_id},
            transports=['websocket'],
            wait_timeout=10
        )

        if monitor.connected:
            # Wait briefly to check for immediate disconnect
            await asyncio.sleep(2)

            if sio.connected and not monitor.disconnected:
                report.add_result(TestResult(
                    name="WebSocket Connection",
                    passed=True,
                    duration_ms=(time.time() - start) * 1000,
                    message="Connected and stable for 2s",
                    details={'socket_id': sio.sid, 'transport': sio.transport()},
                    events=monitor.events
                ))
            else:
                report.add_result(TestResult(
                    name="WebSocket Connection",
                    passed=False,
                    duration_ms=(time.time() - start) * 1000,
                    message=f"Disconnected immediately! Reason: {monitor.disconnect_reason}",
                    details={
                        'connection_duration_ms': monitor.connection_duration_ms(),
                        'disconnect_reason': monitor.disconnect_reason
                    },
                    events=monitor.events
                ))
        else:
            report.add_result(TestResult(
                name="WebSocket Connection",
                passed=False,
                duration_ms=(time.time() - start) * 1000,
                message="Failed to connect",
                details={'errors': monitor.errors},
                events=monitor.events
            ))

    except SIOConnectionError as e:
        report.add_result(TestResult(
            name="WebSocket Connection",
            passed=False,
            duration_ms=(time.time() - start) * 1000,
            message=f"Connection error: {e}",
            events=monitor.events
        ))
    finally:
        if sio.connected:
            await sio.disconnect()


async def test_polling_connection(report: DiagnosticReport, token: str, user_id: int):
    """Test 3: Polling-only connection."""
    start = time.time()
    monitor = ConnectionMonitor()
    sio = socketio.AsyncClient(logger=False, engineio_logger=False)

    sio.on('connect', monitor.on_connect)
    sio.on('disconnect', monitor.on_disconnect)
    sio.on('connect_error', monitor.on_error)

    try:
        print("\n  Connecting with Polling transport (no upgrade)...")
        await sio.connect(
            BACKEND_URL,
            auth={'token': token, 'user_id': user_id},
            transports=['polling'],
            wait_timeout=10
        )

        if monitor.connected:
            await asyncio.sleep(5)

            if sio.connected and not monitor.disconnected:
                report.add_result(TestResult(
                    name="Polling Connection",
                    passed=True,
                    duration_ms=(time.time() - start) * 1000,
                    message="Connected and stable for 5s with polling",
                    details={'socket_id': sio.sid, 'transport': sio.transport()},
                    events=monitor.events
                ))
            else:
                report.add_result(TestResult(
                    name="Polling Connection",
                    passed=False,
                    duration_ms=(time.time() - start) * 1000,
                    message=f"Disconnected! Reason: {monitor.disconnect_reason}",
                    details={'connection_duration_ms': monitor.connection_duration_ms()},
                    events=monitor.events
                ))
        else:
            report.add_result(TestResult(
                name="Polling Connection",
                passed=False,
                duration_ms=(time.time() - start) * 1000,
                message="Failed to connect",
                events=monitor.events
            ))

    except Exception as e:
        report.add_result(TestResult(
            name="Polling Connection",
            passed=False,
            duration_ms=(time.time() - start) * 1000,
            message=f"Error: {e}",
            events=monitor.events
        ))
    finally:
        if sio.connected:
            await sio.disconnect()


async def test_polling_to_websocket_upgrade(report: DiagnosticReport, token: str, user_id: int):
    """Test 4: Polling → WebSocket upgrade (THE PROBLEMATIC SCENARIO)."""
    start = time.time()
    monitor = ConnectionMonitor()
    sio = socketio.AsyncClient(logger=True, engineio_logger=True)  # Verbose logging

    transport_history = []

    sio.on('connect', monitor.on_connect)
    sio.on('disconnect', monitor.on_disconnect)
    sio.on('connect_error', monitor.on_error)

    try:
        print("\n  Connecting with Polling → WebSocket upgrade...")
        print("  (This is the scenario that was failing)")

        await sio.connect(
            BACKEND_URL,
            auth={'token': token, 'user_id': user_id},
            transports=['polling', 'websocket'],  # Start with polling, upgrade to WS
            wait_timeout=10
        )

        if monitor.connected:
            initial_transport = sio.transport()
            transport_history.append(('initial', initial_transport, time.time()))
            print(f"\n  Initial transport: {initial_transport}")

            # Monitor for 10 seconds
            for i in range(10):
                await asyncio.sleep(1)
                current_transport = sio.transport()

                if current_transport != transport_history[-1][1]:
                    transport_history.append(('changed', current_transport, time.time()))
                    print(f"  Transport changed to: {current_transport}")

                if not sio.connected:
                    print(f"  ⚠️ DISCONNECTED at second {i+1}!")
                    break

                if i % 3 == 0:
                    print(f"  Second {i+1}: transport={current_transport}, connected=True")

            if sio.connected and not monitor.disconnected:
                report.add_result(TestResult(
                    name="Polling→WebSocket Upgrade",
                    passed=True,
                    duration_ms=(time.time() - start) * 1000,
                    message="Upgrade successful, connection stable",
                    details={
                        'final_transport': sio.transport(),
                        'transport_history': transport_history
                    },
                    events=monitor.events
                ))
            else:
                report.add_result(TestResult(
                    name="Polling→WebSocket Upgrade",
                    passed=False,
                    duration_ms=(time.time() - start) * 1000,
                    message=f"⚠️ DISCONNECTED after upgrade! Reason: {monitor.disconnect_reason}",
                    details={
                        'connection_duration_ms': monitor.connection_duration_ms(),
                        'disconnect_reason': monitor.disconnect_reason,
                        'transport_history': transport_history
                    },
                    events=monitor.events
                ))
        else:
            report.add_result(TestResult(
                name="Polling→WebSocket Upgrade",
                passed=False,
                duration_ms=(time.time() - start) * 1000,
                message="Failed to connect",
                events=monitor.events
            ))

    except Exception as e:
        report.add_result(TestResult(
            name="Polling→WebSocket Upgrade",
            passed=False,
            duration_ms=(time.time() - start) * 1000,
            message=f"Error: {e}",
            events=monitor.events
        ))
    finally:
        if sio.connected:
            await sio.disconnect()


async def test_long_connection_stability(report: DiagnosticReport, token: str, user_id: int):
    """Test 5: Long connection stability (30 seconds)."""
    start = time.time()
    monitor = ConnectionMonitor()
    sio = socketio.AsyncClient(logger=False, engineio_logger=False)

    sio.on('connect', monitor.on_connect)
    sio.on('disconnect', monitor.on_disconnect)
    sio.on('connect_error', monitor.on_error)

    try:
        print("\n  Testing 30-second connection stability...")

        await sio.connect(
            BACKEND_URL,
            auth={'token': token, 'user_id': user_id},
            transports=['websocket'],
            wait_timeout=10
        )

        if monitor.connected:
            disconnect_at = None
            for i in range(30):
                await asyncio.sleep(1)
                if not sio.connected:
                    disconnect_at = i + 1
                    break
                if i % 10 == 0:
                    print(f"  Second {i+1}: connected ✓")

            if disconnect_at:
                report.add_result(TestResult(
                    name="30s Stability Test",
                    passed=False,
                    duration_ms=(time.time() - start) * 1000,
                    message=f"Disconnected after {disconnect_at} seconds",
                    details={
                        'disconnect_reason': monitor.disconnect_reason,
                        'disconnected_at_second': disconnect_at
                    },
                    events=monitor.events
                ))
            else:
                report.add_result(TestResult(
                    name="30s Stability Test",
                    passed=True,
                    duration_ms=(time.time() - start) * 1000,
                    message="Connection stable for 30 seconds",
                    events=monitor.events
                ))
        else:
            report.add_result(TestResult(
                name="30s Stability Test",
                passed=False,
                duration_ms=(time.time() - start) * 1000,
                message="Failed to connect",
                events=monitor.events
            ))

    except Exception as e:
        report.add_result(TestResult(
            name="30s Stability Test",
            passed=False,
            duration_ms=(time.time() - start) * 1000,
            message=f"Error: {e}",
            events=monitor.events
        ))
    finally:
        if sio.connected:
            await sio.disconnect()


async def test_emit_message(report: DiagnosticReport, token: str, user_id: int):
    """Test 6: Emit a message and stay connected."""
    start = time.time()
    monitor = ConnectionMonitor()
    sio = socketio.AsyncClient(logger=False, engineio_logger=False)

    sio.on('connect', monitor.on_connect)
    sio.on('disconnect', monitor.on_disconnect)
    sio.on('connect_error', monitor.on_error)

    try:
        print("\n  Testing message emission...")

        await sio.connect(
            BACKEND_URL,
            auth={'token': token, 'user_id': user_id},
            transports=['websocket'],
            wait_timeout=10
        )

        if monitor.connected:
            # Emit a test message
            print("  Emitting plugin_response...")
            await sio.emit('plugin_response', {
                'request_id': 'test_diag_' + str(int(time.time())),
                'success': True,
                'data': {'diagnostic': 'test'},
                'error': None
            })

            # Check if still connected after emit
            await asyncio.sleep(2)

            if sio.connected and not monitor.disconnected:
                report.add_result(TestResult(
                    name="Message Emission",
                    passed=True,
                    duration_ms=(time.time() - start) * 1000,
                    message="Emitted message, still connected",
                    events=monitor.events
                ))
            else:
                report.add_result(TestResult(
                    name="Message Emission",
                    passed=False,
                    duration_ms=(time.time() - start) * 1000,
                    message=f"Disconnected after emit! Reason: {monitor.disconnect_reason}",
                    details={'connection_duration_ms': monitor.connection_duration_ms()},
                    events=monitor.events
                ))
        else:
            report.add_result(TestResult(
                name="Message Emission",
                passed=False,
                duration_ms=(time.time() - start) * 1000,
                message="Failed to connect",
                events=monitor.events
            ))

    except Exception as e:
        report.add_result(TestResult(
            name="Message Emission",
            passed=False,
            duration_ms=(time.time() - start) * 1000,
            message=f"Error: {e}",
            events=monitor.events
        ))
    finally:
        if sio.connected:
            await sio.disconnect()


async def main():
    """Run all diagnostic tests."""
    print("=" * 60)
    print("WEBSOCKET DIAGNOSTIC SUITE")
    print(f"Target: {BACKEND_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    report = DiagnosticReport()

    # Get auth token
    print("\n📝 Getting test token...")
    try:
        token, user_id = get_test_token()
        print(f"   Token obtained for user {user_id}")
    except Exception as e:
        print(f"❌ Failed to get token: {e}")
        print("   Make sure the backend database is running and has users")
        return

    # Run tests
    print("\n" + "-" * 60)
    print("RUNNING DIAGNOSTIC TESTS")
    print("-" * 60)

    await test_server_reachable(report)
    await test_websocket_connection(report, token, user_id)
    await test_polling_connection(report, token, user_id)
    await test_polling_to_websocket_upgrade(report, token, user_id)
    await test_long_connection_stability(report, token, user_id)
    await test_emit_message(report, token, user_id)

    # Summary
    report.summary()


if __name__ == '__main__':
    asyncio.run(main())
