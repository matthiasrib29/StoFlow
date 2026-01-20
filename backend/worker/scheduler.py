"""
Marketplace Job Scheduler

Replaces Celery Beat for periodic tasks.
Uses APScheduler with async support.

Usage:
    python -m worker.scheduler

Tasks:
- sync_all_orders: Every 15 minutes (sync orders from all marketplaces)
- cleanup_old_jobs: Every hour (remove old completed/failed jobs)
- expire_stale_jobs: Every 5 minutes (expire pending jobs > 1 hour)

Author: Claude
Date: 2026-01-20
"""

import argparse
import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add backend to path for imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import text

from shared.database import SessionLocal
from shared.logging_setup import get_logger, setup_logging
from shared.schema_utils import configure_schema_translate_map
from worker.signals import GracefulShutdown

logger = get_logger(__name__)


class MarketplaceScheduler:
    """
    Periodic task scheduler using APScheduler.

    Replaces Celery Beat for scheduled tasks.
    Runs async jobs in the event loop.
    """

    def __init__(self):
        """Initialize scheduler."""
        self.scheduler = AsyncIOScheduler()
        self._shutdown = GracefulShutdown()

    def setup_jobs(self) -> None:
        """Register all periodic jobs."""
        # Sync orders every 15 minutes
        self.scheduler.add_job(
            self._sync_all_orders,
            trigger=IntervalTrigger(minutes=15),
            id='sync_orders',
            replace_existing=True,
            name='Sync marketplace orders',
        )

        # Cleanup old jobs every hour
        self.scheduler.add_job(
            self._cleanup_old_jobs,
            trigger=IntervalTrigger(hours=1),
            id='cleanup_jobs',
            replace_existing=True,
            name='Cleanup old job records',
        )

        # Expire stale pending jobs every 5 minutes
        self.scheduler.add_job(
            self._expire_stale_jobs,
            trigger=IntervalTrigger(minutes=5),
            id='expire_stale_jobs',
            replace_existing=True,
            name='Expire stale pending jobs',
        )

        logger.info(
            f"Registered {len(self.scheduler.get_jobs())} scheduled jobs"
        )

    async def run(self) -> None:
        """Run the scheduler."""
        logger.info("Starting MarketplaceScheduler")

        # Setup signal handlers
        self._shutdown.setup()

        # Setup and start scheduler
        self.setup_jobs()
        self.scheduler.start()

        # Wait for shutdown
        await self._shutdown.wait_for_shutdown()

        # Cleanup
        logger.info("Shutting down scheduler...")
        self.scheduler.shutdown(wait=True)
        logger.info("Scheduler stopped")

    async def _sync_all_orders(self) -> None:
        """
        Sync orders from all marketplaces for all users.

        Creates sync_orders jobs for each user with marketplace connections.
        """
        logger.info("[Scheduler] Starting sync_all_orders task")

        db = SessionLocal()
        try:
            # Get all users with marketplace connections
            from models.public.user import User
            from models.user.ebay_credentials import EbayCredentials

            users = db.query(User).filter(User.is_active == True).all()

            for user in users:
                user_id = user.id
                schema_name = f"user_{user_id}"

                try:
                    # Create user-scoped session
                    user_db = SessionLocal()
                    configure_schema_translate_map(user_db, schema_name)
                    user_db.execute(text(f"SET search_path TO {schema_name}, public"))

                    # Check if user has eBay credentials
                    ebay_creds = user_db.query(EbayCredentials).first()

                    if ebay_creds:
                        # Create sync_orders job for eBay
                        from services.marketplace.marketplace_job_service import MarketplaceJobService

                        job_service = MarketplaceJobService(user_db)
                        job = job_service.create_job(
                            marketplace="ebay",
                            action_code="sync_orders",
                            input_data={},
                        )
                        user_db.commit()

                        logger.info(
                            f"[Scheduler] Created sync_orders job #{job.id} for user {user_id}"
                        )

                    user_db.close()

                except Exception as e:
                    logger.warning(f"[Scheduler] Failed to create sync job for user {user_id}: {e}")

            logger.info("[Scheduler] sync_all_orders task completed")

        except Exception as e:
            logger.exception(f"[Scheduler] sync_all_orders task failed: {e}")

        finally:
            db.close()

    async def _cleanup_old_jobs(self) -> None:
        """
        Clean up old completed/failed job records.

        Removes jobs older than 7 days to prevent table bloat.
        """
        logger.info("[Scheduler] Starting cleanup_old_jobs task")

        db = SessionLocal()
        try:
            # Get all user schemas
            result = db.execute(text("""
                SELECT schema_name
                FROM information_schema.schemata
                WHERE schema_name LIKE 'user_%'
            """))
            schemas = [row[0] for row in result]

            cutoff = datetime.now(timezone.utc) - timedelta(days=7)
            total_deleted = 0

            for schema in schemas:
                try:
                    result = db.execute(
                        text(f"""
                            DELETE FROM {schema}.marketplace_jobs
                            WHERE status IN ('completed', 'failed', 'cancelled', 'expired')
                            AND created_at < :cutoff
                        """),
                        {"cutoff": cutoff}
                    )
                    deleted = result.rowcount
                    total_deleted += deleted

                    if deleted > 0:
                        logger.debug(f"[Scheduler] Deleted {deleted} old jobs from {schema}")

                except Exception as e:
                    logger.warning(f"[Scheduler] Failed to cleanup jobs in {schema}: {e}")

            db.commit()

            logger.info(f"[Scheduler] cleanup_old_jobs completed: deleted {total_deleted} records")

        except Exception as e:
            logger.exception(f"[Scheduler] cleanup_old_jobs task failed: {e}")

        finally:
            db.close()

    async def _expire_stale_jobs(self) -> None:
        """
        Expire pending jobs that have been waiting too long.

        Jobs pending for more than 1 hour are marked as expired.
        """
        logger.info("[Scheduler] Starting expire_stale_jobs task")

        db = SessionLocal()
        try:
            # Get all user schemas
            result = db.execute(text("""
                SELECT schema_name
                FROM information_schema.schemata
                WHERE schema_name LIKE 'user_%'
            """))
            schemas = [row[0] for row in result]

            cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
            total_expired = 0

            for schema in schemas:
                try:
                    result = db.execute(
                        text(f"""
                            UPDATE {schema}.marketplace_jobs
                            SET status = 'expired'
                            WHERE status = 'pending'
                            AND created_at < :cutoff
                        """),
                        {"cutoff": cutoff}
                    )
                    expired = result.rowcount
                    total_expired += expired

                    if expired > 0:
                        logger.debug(f"[Scheduler] Expired {expired} stale jobs in {schema}")

                except Exception as e:
                    logger.warning(f"[Scheduler] Failed to expire jobs in {schema}: {e}")

            db.commit()

            if total_expired > 0:
                logger.info(f"[Scheduler] expire_stale_jobs completed: expired {total_expired} jobs")

        except Exception as e:
            logger.exception(f"[Scheduler] expire_stale_jobs task failed: {e}")

        finally:
            db.close()


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="StoFlow Marketplace Job Scheduler"
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

    # Run scheduler
    scheduler = MarketplaceScheduler()
    await scheduler.run()


if __name__ == "__main__":
    asyncio.run(main())
