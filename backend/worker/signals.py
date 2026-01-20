"""
Signal Handling for Graceful Shutdown

Handles SIGTERM and SIGINT for clean worker shutdown.

Author: Claude
Date: 2026-01-20
"""

import asyncio
import signal
from typing import Callable, Optional

from shared.logging_setup import get_logger

logger = get_logger(__name__)


class GracefulShutdown:
    """
    Graceful shutdown handler for async workers.

    Captures SIGTERM and SIGINT signals and sets a shutdown event.
    Allows active jobs to complete before exiting.

    Usage:
        shutdown = GracefulShutdown()
        shutdown.setup()

        while not shutdown.is_shutting_down:
            # Process jobs
            ...

        # Wait for cleanup
        await shutdown.wait_for_cleanup(timeout=60.0)
    """

    def __init__(self):
        self._shutdown_event = asyncio.Event()
        self._active_jobs: set[int] = set()
        self._cleanup_callbacks: list[Callable] = []
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    @property
    def is_shutting_down(self) -> bool:
        """Check if shutdown has been requested."""
        return self._shutdown_event.is_set()

    def setup(self, loop: Optional[asyncio.AbstractEventLoop] = None) -> None:
        """
        Setup signal handlers for graceful shutdown.

        Args:
            loop: Event loop to use (defaults to running loop)
        """
        self._loop = loop or asyncio.get_running_loop()

        # Register signal handlers
        for sig in (signal.SIGTERM, signal.SIGINT):
            self._loop.add_signal_handler(
                sig,
                lambda s=sig: self._handle_signal(s)
            )

        logger.info("Signal handlers registered for graceful shutdown")

    def _handle_signal(self, sig: signal.Signals) -> None:
        """Handle incoming signal."""
        sig_name = signal.Signals(sig).name
        logger.info(f"Received {sig_name}, initiating graceful shutdown...")
        self._shutdown_event.set()

    def register_active_job(self, job_id: int) -> None:
        """Register a job as actively processing."""
        self._active_jobs.add(job_id)

    def unregister_active_job(self, job_id: int) -> None:
        """Unregister a job that has finished processing."""
        self._active_jobs.discard(job_id)

    @property
    def active_job_count(self) -> int:
        """Get number of actively processing jobs."""
        return len(self._active_jobs)

    def add_cleanup_callback(self, callback: Callable) -> None:
        """
        Add a callback to run during cleanup.

        Args:
            callback: Async or sync callable to run on cleanup
        """
        self._cleanup_callbacks.append(callback)

    async def wait_for_shutdown(self) -> None:
        """Wait until shutdown signal is received."""
        await self._shutdown_event.wait()

    async def wait_for_cleanup(self, timeout: float = 60.0) -> bool:
        """
        Wait for active jobs to complete with timeout.

        Args:
            timeout: Maximum seconds to wait for jobs

        Returns:
            True if all jobs completed, False if timeout reached
        """
        if not self._active_jobs:
            logger.info("No active jobs, cleanup complete")
            return True

        logger.info(
            f"Waiting for {len(self._active_jobs)} active jobs to complete "
            f"(timeout: {timeout}s)..."
        )

        start_time = asyncio.get_event_loop().time()
        while self._active_jobs:
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed >= timeout:
                logger.warning(
                    f"Cleanup timeout reached, {len(self._active_jobs)} jobs still active: "
                    f"{self._active_jobs}"
                )
                return False

            await asyncio.sleep(0.5)

        logger.info("All active jobs completed")

        # Run cleanup callbacks
        for callback in self._cleanup_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback()
                else:
                    callback()
            except Exception as e:
                logger.error(f"Cleanup callback error: {e}")

        return True
