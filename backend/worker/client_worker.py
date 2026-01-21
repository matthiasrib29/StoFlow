"""
Client Worker for Multi-Tenant Job Dispatcher

Worker that processes jobs for a single tenant (user).
Uses double semaphore pattern for fair resource allocation.

Author: Claude
Date: 2026-01-21
"""

import asyncio
from datetime import datetime, timezone
from typing import TYPE_CHECKING

import asyncpg

from shared.database import get_tenant_session
from shared.logging_setup import get_logger
from worker.config import WorkerConfig
from worker.job_executor import JobExecutor

if TYPE_CHECKING:
    from worker.dispatcher_config import DispatcherConfig

logger = get_logger(__name__)


class ClientWorker:
    """
    Worker for a single tenant (user).

    Processes jobs from the tenant's schema with:
    - Local semaphore (per_client_max_concurrent)
    - Global semaphore (shared across all tenants)
    - NOTIFY-based wake-up for instant job processing
    - Polling fallback for reliability

    Usage:
        worker = ClientWorker(user_id=1, config=config, global_semaphore=sem, pg_pool=pool)
        await worker.start()
        # ... when done ...
        await worker.stop()
    """

    def __init__(
        self,
        user_id: int,
        config: "DispatcherConfig",
        global_semaphore: asyncio.Semaphore,
        pg_pool: asyncpg.Pool,
    ):
        """
        Initialize client worker.

        Args:
            user_id: User ID for tenant isolation
            config: Dispatcher configuration
            global_semaphore: Shared semaphore for global concurrency limit
            pg_pool: Shared asyncpg connection pool
        """
        self.user_id = user_id
        self.schema_name = f"user_{user_id}"
        self.config = config
        self._global_semaphore = global_semaphore
        self._local_semaphore = asyncio.Semaphore(config.per_client_max_concurrent)
        self._pg_pool = pg_pool

        # Control signals
        self._job_available = asyncio.Event()
        self._shutdown_event = asyncio.Event()

        # Tracking
        self._active_tasks: set[asyncio.Task] = set()
        self._last_activity = datetime.now(timezone.utc)
        self._created_at = datetime.now(timezone.utc)
        self._task: asyncio.Task | None = None
        self._is_running = False

    async def start(self) -> None:
        """Start the worker's processing loop."""
        if self._is_running:
            logger.warning(f"[ClientWorker:{self.user_id}] Already running")
            return

        logger.info(
            f"[ClientWorker:{self.user_id}] Starting "
            f"(schema={self.schema_name}, max_concurrent={self.config.per_client_max_concurrent})"
        )

        self._is_running = True
        self._shutdown_event.clear()
        self._task = asyncio.create_task(self._run())

    async def stop(self, timeout: float = 60.0) -> None:
        """
        Stop the worker gracefully.

        Args:
            timeout: Max seconds to wait for active jobs to complete
        """
        if not self._is_running:
            return

        logger.info(
            f"[ClientWorker:{self.user_id}] Stopping "
            f"({len(self._active_tasks)} active tasks)"
        )

        self._shutdown_event.set()
        self._job_available.set()  # Wake up the loop

        # Wait for active tasks to complete
        if self._active_tasks:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*self._active_tasks, return_exceptions=True),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                logger.warning(
                    f"[ClientWorker:{self.user_id}] Timeout waiting for tasks, "
                    f"cancelling {len(self._active_tasks)} remaining"
                )
                for task in self._active_tasks:
                    task.cancel()

        # Cancel the main task
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        self._is_running = False
        logger.info(f"[ClientWorker:{self.user_id}] Stopped")

    async def _run(self) -> None:
        """Main processing loop."""
        logger.debug(f"[ClientWorker:{self.user_id}] Entering main loop")

        while not self._shutdown_event.is_set():
            try:
                # Process available jobs
                await self._process_pending_jobs()

                # Wait for notification or timeout (fallback polling)
                self._job_available.clear()
                try:
                    await asyncio.wait_for(
                        self._job_available.wait(),
                        timeout=self.config.poll_interval,
                    )
                except asyncio.TimeoutError:
                    # Timeout = fallback polling
                    pass

            except asyncio.CancelledError:
                logger.debug(f"[ClientWorker:{self.user_id}] Loop cancelled")
                break
            except Exception as e:
                logger.exception(f"[ClientWorker:{self.user_id}] Error in loop: {e}")
                await asyncio.sleep(5)  # Brief pause on error

        logger.debug(f"[ClientWorker:{self.user_id}] Exiting main loop")

    async def _process_pending_jobs(self) -> None:
        """Claim and process all available pending jobs."""
        while not self._shutdown_event.is_set():
            # Check if we have local capacity
            if self._local_semaphore.locked():
                logger.debug(
                    f"[ClientWorker:{self.user_id}] Local semaphore full, waiting"
                )
                return

            # Check if global capacity available
            if self._global_semaphore.locked():
                logger.debug(
                    f"[ClientWorker:{self.user_id}] Global semaphore full, waiting"
                )
                return

            # Create SQLAlchemy session with tenant schema properly configured
            db = get_tenant_session(self.user_id)

            try:
                # Create worker config for executor
                worker_config = WorkerConfig(
                    user_id=self.user_id,
                    max_concurrent_jobs=self.config.per_client_max_concurrent,
                    poll_interval=self.config.poll_interval,
                )

                # Create executor
                executor = JobExecutor(
                    config=worker_config,
                    db=db,
                    cancel_check=lambda _: self._shutdown_event.is_set(),
                )

                # Expire old jobs periodically
                executor.expire_old_jobs()
                executor.force_cancel_stale_jobs()

                # Claim next job
                job = executor.claim_next_job()
                if not job:
                    db.close()
                    return  # No more jobs

                job_id = job.id
                self._last_activity = datetime.now(timezone.utc)

                logger.debug(
                    f"[ClientWorker:{self.user_id}] Claimed job #{job_id}"
                )

                # Execute job in background with double semaphore
                task = asyncio.create_task(
                    self._execute_with_semaphores(executor, job, db)
                )
                self._active_tasks.add(task)
                task.add_done_callback(self._active_tasks.discard)

            except Exception as e:
                logger.exception(
                    f"[ClientWorker:{self.user_id}] Error claiming job: {e}"
                )
                db.close()
                return

    async def _execute_with_semaphores(
        self,
        executor: JobExecutor,
        job,
        db,
    ) -> None:
        """
        Execute job with double semaphore pattern.

        Order is important:
        1. Acquire global semaphore first (protects DB)
        2. Then acquire local semaphore (ensures fairness)

        Args:
            executor: Job executor instance
            job: Job to execute
            db: Database session (will be closed after execution)
        """
        job_id = job.id

        try:
            # Double semaphore: global first, then local
            async with self._global_semaphore:
                async with self._local_semaphore:
                    result = await executor.execute_job(job)

                    if result.get("success"):
                        logger.info(
                            f"[ClientWorker:{self.user_id}] Job #{job_id} completed: "
                            f"{result.get('duration_ms', 0)}ms"
                        )
                    elif result.get("will_retry"):
                        logger.warning(
                            f"[ClientWorker:{self.user_id}] Job #{job_id} failed, will retry: "
                            f"{result.get('error')}"
                        )
                    elif result.get("status") == "cancelled":
                        logger.info(
                            f"[ClientWorker:{self.user_id}] Job #{job_id} cancelled"
                        )
                    else:
                        logger.error(
                            f"[ClientWorker:{self.user_id}] Job #{job_id} failed permanently: "
                            f"{result.get('error')}"
                        )

        except asyncio.CancelledError:
            logger.info(
                f"[ClientWorker:{self.user_id}] Job #{job_id} interrupted by shutdown"
            )
            raise

        except Exception as e:
            logger.exception(
                f"[ClientWorker:{self.user_id}] Error executing job #{job_id}: {e}"
            )

        finally:
            db.close()

    def notify_job_available(self) -> None:
        """Signal that a new job is available for processing."""
        self._job_available.set()
        self._last_activity = datetime.now(timezone.utc)

    @property
    def is_idle(self) -> bool:
        """
        Check if worker has been idle for longer than the configured timeout.

        Returns:
            True if idle timeout exceeded
        """
        idle_seconds = (
            datetime.now(timezone.utc) - self._last_activity
        ).total_seconds()
        idle_threshold = self.config.worker_idle_timeout_hours * 3600
        return idle_seconds > idle_threshold

    @property
    def is_old(self) -> bool:
        """
        Check if worker has exceeded its maximum age.

        Returns:
            True if max age exceeded
        """
        age_seconds = (
            datetime.now(timezone.utc) - self._created_at
        ).total_seconds()
        age_threshold = self.config.worker_max_age_hours * 3600
        return age_seconds > age_threshold

    @property
    def active_job_count(self) -> int:
        """Get number of currently active jobs."""
        return len(self._active_tasks)

    @property
    def is_running(self) -> bool:
        """Check if worker is running."""
        return self._is_running

    def get_status(self) -> dict:
        """
        Get worker status for monitoring.

        Returns:
            Status dict with worker information
        """
        now = datetime.now(timezone.utc)
        return {
            "user_id": self.user_id,
            "schema": self.schema_name,
            "is_running": self._is_running,
            "active_jobs": self.active_job_count,
            "is_idle": self.is_idle,
            "is_old": self.is_old,
            "created_at": self._created_at.isoformat(),
            "last_activity": self._last_activity.isoformat(),
            "age_hours": round((now - self._created_at).total_seconds() / 3600, 2),
            "idle_hours": round((now - self._last_activity).total_seconds() / 3600, 2),
        }
