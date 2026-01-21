"""
Multi-Tenant Job Dispatcher

Central dispatcher that manages ClientWorkers for each active tenant.
Integrated into FastAPI backend process via lifespan.

Architecture:
    - Single global semaphore (150) protects the database
    - Per-client semaphores (30 each) ensure fairness
    - LISTEN/NOTIFY for instant job detection
    - Janitor task cleans up idle workers

Author: Claude
Date: 2026-01-21
"""

import asyncio
import json
import re
from datetime import datetime, timezone
from typing import Optional

import asyncpg

from shared.logging_setup import get_logger
from worker.client_worker import ClientWorker
from worker.dispatcher_config import DispatcherConfig

logger = get_logger(__name__)


class JobDispatcher:
    """
    Central dispatcher for multi-tenant job processing.

    Features:
    - Creates/manages ClientWorker per active tenant
    - PostgreSQL LISTEN/NOTIFY for instant job routing
    - Global semaphore for database protection
    - Janitor task for cleanup of idle/old workers

    Usage (in FastAPI lifespan):
        config = DispatcherConfig.from_settings()
        dispatcher = JobDispatcher(config)
        await dispatcher.start()
        # ... app runs ...
        await dispatcher.stop()
    """

    def __init__(self, config: DispatcherConfig):
        """
        Initialize job dispatcher.

        Args:
            config: Dispatcher configuration
        """
        self.config = config
        self._workers: dict[int, ClientWorker] = {}
        self._workers_lock = asyncio.Lock()
        self._global_semaphore = asyncio.Semaphore(config.global_max_concurrent)
        self._pg_pool: Optional[asyncpg.Pool] = None
        self._listen_conn: Optional[asyncpg.Connection] = None
        self._shutdown_event = asyncio.Event()
        self._janitor_task: Optional[asyncio.Task] = None
        self._is_running = False

    async def start(self) -> None:
        """
        Start the dispatcher.

        Called by FastAPI lifespan on startup.
        """
        if self._is_running:
            logger.warning("[JobDispatcher] Already running")
            return

        logger.info(
            f"[JobDispatcher] Starting (global_max={self.config.global_max_concurrent}, "
            f"per_client_max={self.config.per_client_max_concurrent})"
        )

        try:
            # Validate config
            self.config.validate()

            # Create asyncpg pool for LISTEN/NOTIFY
            self._pg_pool = await asyncpg.create_pool(
                self.config.db_url,
                min_size=self.config.asyncpg_pool_min_size,
                max_size=self.config.asyncpg_pool_max_size,
            )
            logger.debug("[JobDispatcher] Created asyncpg pool")

            # Setup LISTEN connection
            await self._setup_listen()

            # Bootstrap workers for users with pending jobs
            await self._bootstrap_workers()

            # Start janitor task
            self._janitor_task = asyncio.create_task(self._janitor_loop())

            self._is_running = True
            logger.info("[JobDispatcher] Started successfully")

        except Exception as e:
            logger.exception(f"[JobDispatcher] Failed to start: {e}")
            await self._cleanup()
            raise

    async def stop(self) -> None:
        """
        Stop the dispatcher gracefully.

        Called by FastAPI lifespan on shutdown.
        """
        if not self._is_running:
            return

        logger.info(
            f"[JobDispatcher] Stopping ({len(self._workers)} active workers)"
        )

        self._shutdown_event.set()

        # Stop janitor
        if self._janitor_task and not self._janitor_task.done():
            self._janitor_task.cancel()
            try:
                await self._janitor_task
            except asyncio.CancelledError:
                pass

        # Stop all workers gracefully
        async with self._workers_lock:
            stop_tasks = [
                worker.stop(timeout=self.config.graceful_shutdown_timeout)
                for worker in self._workers.values()
            ]
            if stop_tasks:
                await asyncio.gather(*stop_tasks, return_exceptions=True)
            self._workers.clear()

        await self._cleanup()
        self._is_running = False
        logger.info("[JobDispatcher] Stopped")

    async def _cleanup(self) -> None:
        """Cleanup resources."""
        # Close LISTEN connection
        if self._listen_conn:
            try:
                await self._listen_conn.remove_listener(
                    self.config.notify_channel,
                    self._on_notify,
                )
                await self._pg_pool.release(self._listen_conn)
            except Exception as e:
                logger.warning(f"[JobDispatcher] Error closing LISTEN conn: {e}")
            self._listen_conn = None

        # Close pool
        if self._pg_pool:
            try:
                await self._pg_pool.close()
            except Exception as e:
                logger.warning(f"[JobDispatcher] Error closing pool: {e}")
            self._pg_pool = None

    async def _setup_listen(self) -> None:
        """Setup PostgreSQL LISTEN for job notifications."""
        self._listen_conn = await self._pg_pool.acquire()

        # Add listener
        await self._listen_conn.add_listener(
            self.config.notify_channel,
            self._on_notify,
        )

        logger.info(
            f"[JobDispatcher] Listening on channel '{self.config.notify_channel}'"
        )

    def _on_notify(
        self,
        connection: asyncpg.Connection,
        pid: int,
        channel: str,
        payload: str,
    ) -> None:
        """
        Handle incoming NOTIFY event.

        Routes the notification to the appropriate ClientWorker.

        Args:
            connection: PostgreSQL connection
            pid: Process ID that sent notification
            channel: Channel name
            payload: JSON payload with job_id and schema
        """
        try:
            data = json.loads(payload)
            job_id = data.get("job_id")
            schema = data.get("schema")

            logger.debug(
                f"[JobDispatcher] Received notification: job #{job_id}, schema={schema}"
            )

            # Extract user_id from schema (e.g., "user_123" -> 123)
            user_id = self._extract_user_id(schema)
            if user_id is None:
                logger.warning(
                    f"[JobDispatcher] Could not extract user_id from schema: {schema}"
                )
                return

            # Ensure worker exists and notify it
            # Use create_task to avoid blocking the callback
            asyncio.create_task(self._route_notification(user_id))

        except json.JSONDecodeError as e:
            logger.warning(f"[JobDispatcher] Invalid notification payload: {e}")
        except Exception as e:
            logger.exception(f"[JobDispatcher] Error handling notification: {e}")

    def _extract_user_id(self, schema: str) -> Optional[int]:
        """
        Extract user ID from schema name.

        Args:
            schema: Schema name (e.g., "user_123")

        Returns:
            User ID or None if extraction fails
        """
        if not schema:
            return None

        match = re.match(r"^user_(\d+)$", schema)
        if match:
            return int(match.group(1))
        return None

    async def _route_notification(self, user_id: int) -> None:
        """
        Route notification to appropriate worker.

        Creates worker if it doesn't exist.

        Args:
            user_id: User ID to route to
        """
        try:
            worker = await self._ensure_worker_exists(user_id)
            worker.notify_job_available()
        except Exception as e:
            logger.exception(
                f"[JobDispatcher] Error routing notification to user {user_id}: {e}"
            )

    async def _ensure_worker_exists(self, user_id: int) -> ClientWorker:
        """
        Get or create worker for user.

        Args:
            user_id: User ID

        Returns:
            ClientWorker for the user
        """
        async with self._workers_lock:
            if user_id not in self._workers:
                logger.info(f"[JobDispatcher] Creating ClientWorker for user {user_id}")

                worker = ClientWorker(
                    user_id=user_id,
                    config=self.config,
                    global_semaphore=self._global_semaphore,
                    pg_pool=self._pg_pool,
                )
                await worker.start()
                self._workers[user_id] = worker

            return self._workers[user_id]

    async def _bootstrap_workers(self) -> None:
        """
        Create workers for users with pending jobs at startup.

        Scans all user schemas for pending marketplace jobs.
        """
        logger.info("[JobDispatcher] Bootstrapping workers for pending jobs...")

        try:
            async with self._pg_pool.acquire() as conn:
                # Get all user schemas
                schemas = await conn.fetch(
                    """
                    SELECT schema_name
                    FROM information_schema.schemata
                    WHERE schema_name LIKE 'user_%'
                    ORDER BY schema_name
                    """
                )

                users_with_jobs = []

                for row in schemas:
                    schema = row["schema_name"]
                    user_id = self._extract_user_id(schema)
                    if user_id is None:
                        continue

                    # Check for pending jobs in this schema
                    try:
                        count = await conn.fetchval(
                            f"""
                            SELECT COUNT(*)
                            FROM {schema}.marketplace_jobs
                            WHERE status = 'pending'
                            """
                        )
                        if count > 0:
                            users_with_jobs.append((user_id, count))
                    except asyncpg.UndefinedTableError:
                        # Schema exists but no marketplace_jobs table
                        continue
                    except Exception as e:
                        logger.warning(
                            f"[JobDispatcher] Error checking schema {schema}: {e}"
                        )

                # Create workers for users with pending jobs
                for user_id, job_count in users_with_jobs:
                    logger.info(
                        f"[JobDispatcher] User {user_id} has {job_count} pending jobs"
                    )
                    await self._ensure_worker_exists(user_id)

                logger.info(
                    f"[JobDispatcher] Bootstrap complete: "
                    f"{len(users_with_jobs)} workers created"
                )

        except Exception as e:
            logger.exception(f"[JobDispatcher] Bootstrap error: {e}")

    async def _janitor_loop(self) -> None:
        """
        Janitor task that cleans up idle/old workers.

        Runs every 5 minutes:
        - Removes workers idle for > worker_idle_timeout_hours with no active jobs
        - Force restarts workers older than worker_max_age_hours
        """
        janitor_interval = 300  # 5 minutes

        logger.info("[JobDispatcher] Janitor started")

        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(janitor_interval)

                if self._shutdown_event.is_set():
                    break

                await self._janitor_cleanup()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"[JobDispatcher] Janitor error: {e}")

        logger.info("[JobDispatcher] Janitor stopped")

    async def _janitor_cleanup(self) -> None:
        """Perform janitor cleanup."""
        async with self._workers_lock:
            to_remove: list[int] = []

            for user_id, worker in self._workers.items():
                # Remove idle workers with no active jobs
                if worker.is_idle and worker.active_job_count == 0:
                    logger.info(
                        f"[JobDispatcher] Janitor: removing idle worker for user {user_id}"
                    )
                    to_remove.append(user_id)
                    continue

                # Force restart old workers (memory leak protection)
                if worker.is_old:
                    logger.info(
                        f"[JobDispatcher] Janitor: restarting old worker for user {user_id}"
                    )
                    to_remove.append(user_id)
                    continue

            # Stop and remove workers
            for user_id in to_remove:
                worker = self._workers.pop(user_id)
                await worker.stop(timeout=30)

            if to_remove:
                logger.info(
                    f"[JobDispatcher] Janitor: cleaned up {len(to_remove)} workers, "
                    f"{len(self._workers)} remaining"
                )

    def get_status(self) -> dict:
        """
        Get dispatcher status for monitoring.

        Returns:
            Status dict with dispatcher and worker information
        """
        now = datetime.now(timezone.utc)

        # Calculate global semaphore usage
        # Note: Semaphore doesn't expose current count directly,
        # so we count active jobs across all workers
        total_active_jobs = sum(w.active_job_count for w in self._workers.values())

        return {
            "is_running": self._is_running,
            "config": {
                "global_max_concurrent": self.config.global_max_concurrent,
                "per_client_max_concurrent": self.config.per_client_max_concurrent,
                "worker_idle_timeout_hours": self.config.worker_idle_timeout_hours,
                "worker_max_age_hours": self.config.worker_max_age_hours,
                "poll_interval": self.config.poll_interval,
            },
            "workers_count": len(self._workers),
            "total_active_jobs": total_active_jobs,
            "global_semaphore_available": self.config.global_max_concurrent - total_active_jobs,
            "workers": [w.get_status() for w in self._workers.values()],
            "timestamp": now.isoformat(),
        }
