"""
Standalone Marketplace Job Worker

Async worker process for executing marketplace jobs.
Uses PostgreSQL LISTEN/NOTIFY for instant job notifications.

Usage:
    python -m worker.marketplace_worker --user-id=1 --workers=4

Architecture:
    - Main loop listens for NOTIFY events on 'marketplace_job' channel
    - When notified, claims jobs via FOR UPDATE SKIP LOCKED
    - Executes handlers in async context with semaphore-limited concurrency
    - Graceful shutdown on SIGTERM/SIGINT

Author: Claude
Date: 2026-01-20
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Add backend to path for imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import asyncpg
from sqlalchemy import text

from shared.database import SessionLocal
from shared.logging_setup import get_logger, setup_logging
from shared.schema_utils import configure_schema_translate_map
from worker.config import WorkerConfig
from worker.job_executor import JobExecutor
from worker.signals import GracefulShutdown

logger = get_logger(__name__)


class MarketplaceWorker:
    """
    Async marketplace job worker.

    Features:
    - PostgreSQL LISTEN/NOTIFY for instant job detection
    - Configurable concurrency via semaphore
    - Graceful shutdown with job completion
    - Fallback polling for reliability
    """

    def __init__(self, config: WorkerConfig):
        """
        Initialize worker.

        Args:
            config: Worker configuration
        """
        self.config = config
        self._shutdown = GracefulShutdown()
        self._semaphore = asyncio.Semaphore(config.max_concurrent_jobs)
        self._job_available = asyncio.Event()
        self._active_tasks: set[asyncio.Task] = set()
        self._pg_pool: asyncpg.Pool | None = None
        self._listen_conn: asyncpg.Connection | None = None

    async def run(self) -> None:
        """
        Main worker loop.

        Sets up signal handlers, LISTEN connection, and processes jobs.
        """
        logger.info(
            f"Starting MarketplaceWorker for user {self.config.user_id} "
            f"(max_concurrent={self.config.max_concurrent_jobs}, "
            f"marketplace={self.config.marketplace_filter or 'all'})"
        )

        # Setup signal handlers
        self._shutdown.setup()

        try:
            # Create asyncpg pool for LISTEN/NOTIFY
            self._pg_pool = await asyncpg.create_pool(
                self.config.db_url,
                min_size=self.config.asyncpg_pool_min_size,
                max_size=self.config.asyncpg_pool_max_size,
            )

            # Setup LISTEN connection
            await self._setup_listen()

            # Main processing loop
            await self._process_loop()

        except Exception as e:
            logger.exception(f"Worker error: {e}")
            raise
        finally:
            await self._cleanup()

    async def _setup_listen(self) -> None:
        """Setup PostgreSQL LISTEN for job notifications."""
        self._listen_conn = await self._pg_pool.acquire()

        # Set search path to user schema
        await self._listen_conn.execute(
            f"SET search_path TO {self.config.schema_name}, public"
        )

        # Add listener
        await self._listen_conn.add_listener(
            self.config.notify_channel,
            self._on_notify,
        )

        logger.info(f"Listening on channel '{self.config.notify_channel}'")

    def _on_notify(
        self,
        connection: asyncpg.Connection,
        pid: int,
        channel: str,
        payload: str,
    ) -> None:
        """
        Handle incoming NOTIFY event.

        Args:
            connection: PostgreSQL connection
            pid: Process ID that sent notification
            channel: Channel name
            payload: JSON payload
        """
        try:
            data = json.loads(payload)
            job_id = data.get("job_id")
            schema = data.get("schema")

            # Only process jobs for our user schema
            if schema == self.config.schema_name:
                logger.debug(f"Received notification for job #{job_id}")
                self._job_available.set()
            else:
                logger.debug(f"Ignoring job #{job_id} for schema {schema}")

        except Exception as e:
            logger.warning(f"Failed to parse notification: {e}")

    async def _process_loop(self) -> None:
        """Main job processing loop."""
        logger.info("Entering main processing loop")

        while not self._shutdown.is_shutting_down:
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
                logger.info("Processing loop cancelled")
                break
            except Exception as e:
                logger.exception(f"Error in processing loop: {e}")
                await asyncio.sleep(5)  # Brief pause on error

        logger.info("Exiting processing loop")

    async def _process_pending_jobs(self) -> None:
        """Claim and process all available pending jobs."""
        while not self._shutdown.is_shutting_down:
            # Check if we have capacity
            if self._semaphore.locked():
                logger.debug("Max concurrency reached, waiting...")
                return

            # Create SQLAlchemy session with tenant schema
            db = SessionLocal()
            configure_schema_translate_map(db, self.config.schema_name)
            db.execute(text(f"SET search_path TO {self.config.schema_name}, public"))

            try:
                # Create executor
                executor = JobExecutor(
                    config=self.config,
                    db=db,
                    cancel_check=lambda jid: self._shutdown.is_shutting_down,
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

                # Register job as active
                self._shutdown.register_active_job(job_id)

                # Execute job in background with semaphore
                task = asyncio.create_task(
                    self._execute_job_with_semaphore(executor, job, db)
                )
                self._active_tasks.add(task)
                task.add_done_callback(self._active_tasks.discard)

            except Exception as e:
                logger.exception(f"Error claiming job: {e}")
                db.close()
                return

    async def _execute_job_with_semaphore(
        self,
        executor: JobExecutor,
        job,
        db,
    ) -> None:
        """
        Execute job with semaphore limiting.

        Args:
            executor: Job executor instance
            job: Job to execute
            db: Database session (will be closed after execution)
        """
        job_id = job.id

        try:
            async with self._semaphore:
                result = await executor.execute_job(job)

                if result.get("success"):
                    logger.info(
                        f"Job #{job_id} completed: "
                        f"{result.get('duration_ms', 0)}ms"
                    )
                elif result.get("will_retry"):
                    logger.warning(
                        f"Job #{job_id} failed, will retry: "
                        f"{result.get('error')}"
                    )
                else:
                    logger.error(
                        f"Job #{job_id} failed permanently: "
                        f"{result.get('error')}"
                    )

        except Exception as e:
            logger.exception(f"Error executing job #{job_id}: {e}")

        finally:
            self._shutdown.unregister_active_job(job_id)
            db.close()

    async def _cleanup(self) -> None:
        """Cleanup resources on shutdown."""
        logger.info("Cleaning up worker resources...")

        # Wait for active jobs to complete
        if self._active_tasks:
            logger.info(f"Waiting for {len(self._active_tasks)} active tasks...")
            await self._shutdown.wait_for_cleanup(
                timeout=self.config.graceful_shutdown_timeout
            )

        # Close LISTEN connection
        if self._listen_conn:
            await self._listen_conn.remove_listener(
                self.config.notify_channel,
                self._on_notify,
            )
            await self._pg_pool.release(self._listen_conn)

        # Close pool
        if self._pg_pool:
            await self._pg_pool.close()

        logger.info("Worker cleanup complete")


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="StoFlow Marketplace Job Worker"
    )
    parser.add_argument(
        "--user-id",
        type=int,
        required=True,
        help="User ID for tenant isolation",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Maximum concurrent jobs (default: 4)",
    )
    parser.add_argument(
        "--marketplace",
        type=str,
        choices=["ebay", "etsy", "vinted"],
        help="Filter by marketplace (optional)",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=30.0,
        help="Fallback polling interval in seconds (default: 30)",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)",
    )
    return parser.parse_args()


async def main() -> None:
    """Main entry point."""
    args = parse_args()

    # Setup logging
    setup_logging(level=args.log_level)

    # Create config
    config = WorkerConfig.from_args(args)
    config.validate()

    # Run worker
    worker = MarketplaceWorker(config)
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
