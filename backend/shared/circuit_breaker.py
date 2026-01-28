"""
Circuit Breaker for marketplace API calls.

Prevents cascading failures when a marketplace API is down by temporarily
stopping requests after repeated failures.

States:
    CLOSED  -> API is healthy, requests pass through
    OPEN    -> API is unhealthy, requests are rejected immediately
    HALF_OPEN -> Testing recovery, limited requests allowed

Issue #20 - Business Logic Audit.
"""
import threading
import time
from enum import Enum

from shared.logging import get_logger

logger = get_logger(__name__)


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """
    Thread-safe circuit breaker for marketplace API resilience.

    Usage:
        cb = get_circuit_breaker("ebay")
        if not cb.can_execute():
            # Re-queue the job, circuit is open
            return

        try:
            result = call_ebay_api(...)
            cb.record_success()
        except Exception as e:
            cb.record_failure()
            raise
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        success_threshold: int = 2,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: float = 0.0
        self._lock = threading.Lock()

    @property
    def state(self) -> CircuitState:
        with self._lock:
            if self._state == CircuitState.OPEN:
                # Check if recovery timeout has elapsed
                if time.time() - self._last_failure_time >= self.recovery_timeout:
                    self._state = CircuitState.HALF_OPEN
                    self._success_count = 0
                    logger.info(
                        f"[CircuitBreaker:{self.name}] OPEN -> HALF_OPEN "
                        f"(recovery timeout elapsed)"
                    )
            return self._state

    def can_execute(self) -> bool:
        """Check if a request can proceed through the circuit."""
        return self.state != CircuitState.OPEN

    def record_success(self) -> None:
        """Record a successful API call."""
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.success_threshold:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    self._success_count = 0
                    logger.info(
                        f"[CircuitBreaker:{self.name}] HALF_OPEN -> CLOSED "
                        f"(recovered after {self.success_threshold} successes)"
                    )
            elif self._state == CircuitState.CLOSED:
                # Reset failure count on success
                self._failure_count = 0

    def record_failure(self) -> None:
        """Record a failed API call."""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()

            if self._state == CircuitState.HALF_OPEN:
                # Any failure in half-open goes back to open
                self._state = CircuitState.OPEN
                self._success_count = 0
                logger.warning(
                    f"[CircuitBreaker:{self.name}] HALF_OPEN -> OPEN "
                    f"(failure during recovery)"
                )
            elif (
                self._state == CircuitState.CLOSED
                and self._failure_count >= self.failure_threshold
            ):
                self._state = CircuitState.OPEN
                logger.warning(
                    f"[CircuitBreaker:{self.name}] CLOSED -> OPEN "
                    f"(threshold {self.failure_threshold} reached)"
                )


# Global registry of circuit breakers (one per marketplace)
_circuit_breakers: dict[str, CircuitBreaker] = {}
_registry_lock = threading.Lock()


def get_circuit_breaker(marketplace: str) -> CircuitBreaker:
    """
    Get or create a circuit breaker for a marketplace.

    Args:
        marketplace: Marketplace name (e.g., "vinted", "ebay", "etsy")

    Returns:
        CircuitBreaker instance for the marketplace
    """
    with _registry_lock:
        if marketplace not in _circuit_breakers:
            _circuit_breakers[marketplace] = CircuitBreaker(name=marketplace)
        return _circuit_breakers[marketplace]
