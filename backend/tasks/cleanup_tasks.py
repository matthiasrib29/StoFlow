"""
Celery tasks for cleanup and maintenance operations.
"""
from datetime import datetime, timedelta, timezone
from typing import Any

from celery import shared_task
from celery.utils.log import get_task_logger
from sqlalchemy import and_, text

from shared.database import SessionLocal

logger = get_task_logger(__name__)


@shared_task(
    bind=True,
    name="tasks.cleanup_tasks.cleanup_old_task_records",
    max_retries=1,
)
def cleanup_old_task_records(self, days: int = 30) -> dict[str, Any]:
    """
    Clean up old Celery task records from the database.

    This task is called by Celery beat every hour.

    Args:
        days: Number of days to keep task records (default: 30)

    Returns:
        Dict with cleanup statistics
    """
    logger.info(f"Cleaning up task records older than {days} days")

    db = SessionLocal()
    try:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        # Delete old completed/failed task records
        result = db.execute(
            text("""
                DELETE FROM public.celery_task_records
                WHERE status IN ('SUCCESS', 'FAILURE', 'REVOKED')
                AND completed_at < :cutoff_date
            """),
            {"cutoff_date": cutoff_date},
        )
        deleted_count = result.rowcount
        db.commit()

        logger.info(f"Cleaned up {deleted_count} old task records")
        return {
            "deleted_count": deleted_count,
            "cutoff_date": cutoff_date.isoformat(),
        }

    except Exception as exc:
        logger.error(f"Failed to cleanup task records: {exc}", exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()


@shared_task(
    bind=True,
    name="tasks.cleanup_tasks.cleanup_expired_jobs",
    max_retries=1,
)
def cleanup_expired_jobs(self) -> dict[str, Any]:
    """
    Clean up expired marketplace jobs.

    This task marks old PENDING jobs as EXPIRED.
    Called periodically to prevent jobs from sitting in queue forever.

    Returns:
        Dict with cleanup statistics
    """
    logger.info("Cleaning up expired marketplace jobs")

    from models.public.user import User

    db = SessionLocal()
    try:
        # Get all users
        users = db.query(User).filter(User.is_active == True).all()

        total_expired = 0
        errors = []

        for user in users:
            try:
                # Set user schema
                schema_name = f"user_{user.id}"
                user_db = db.execution_options(
                    schema_translate_map={"tenant": schema_name}
                )

                # Expire old PENDING jobs (older than 1 hour)
                cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
                result = user_db.execute(
                    text("""
                        UPDATE marketplace_jobs
                        SET status = 'EXPIRED',
                            error_message = 'Job expired after 1 hour',
                            completed_at = NOW()
                        WHERE status = 'PENDING'
                        AND created_at < :cutoff
                    """),
                    {"cutoff": cutoff},
                )
                expired_count = result.rowcount
                total_expired += expired_count

                if expired_count > 0:
                    logger.info(
                        f"Expired {expired_count} jobs for user {user.id}"
                    )

            except Exception as e:
                errors.append(f"User {user.id}: {str(e)}")
                logger.error(f"Error expiring jobs for user {user.id}: {e}")

        db.commit()

        result = {
            "total_expired": total_expired,
            "users_processed": len(users),
            "errors": errors,
        }
        logger.info(f"Job cleanup completed: {result}")
        return result

    except Exception as exc:
        logger.error(f"Failed to cleanup expired jobs: {exc}", exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()


@shared_task(
    bind=True,
    name="tasks.cleanup_tasks.cleanup_stale_running_jobs",
    max_retries=1,
)
def cleanup_stale_running_jobs(self, timeout_minutes: int = 30) -> dict[str, Any]:
    """
    Clean up stale RUNNING jobs that haven't completed.

    Jobs stuck in RUNNING state for too long are marked as FAILED.

    Args:
        timeout_minutes: Minutes after which a running job is considered stale

    Returns:
        Dict with cleanup statistics
    """
    logger.info(f"Cleaning up jobs stuck in RUNNING for > {timeout_minutes} minutes")

    from models.public.user import User

    db = SessionLocal()
    try:
        users = db.query(User).filter(User.is_active == True).all()

        total_failed = 0
        errors = []

        for user in users:
            try:
                schema_name = f"user_{user.id}"
                user_db = db.execution_options(
                    schema_translate_map={"tenant": schema_name}
                )

                cutoff = datetime.now(timezone.utc) - timedelta(minutes=timeout_minutes)
                result = user_db.execute(
                    text("""
                        UPDATE marketplace_jobs
                        SET status = 'FAILED',
                            error_message = 'Job timed out (stuck in RUNNING)',
                            completed_at = NOW()
                        WHERE status = 'RUNNING'
                        AND started_at < :cutoff
                    """),
                    {"cutoff": cutoff},
                )
                failed_count = result.rowcount
                total_failed += failed_count

                if failed_count > 0:
                    logger.warning(
                        f"Marked {failed_count} stale jobs as FAILED for user {user.id}"
                    )

            except Exception as e:
                errors.append(f"User {user.id}: {str(e)}")
                logger.error(f"Error cleaning stale jobs for user {user.id}: {e}")

        db.commit()

        result = {
            "total_failed": total_failed,
            "users_processed": len(users),
            "errors": errors,
        }
        logger.info(f"Stale job cleanup completed: {result}")
        return result

    except Exception as exc:
        logger.error(f"Failed to cleanup stale jobs: {exc}", exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()


@shared_task(
    bind=True,
    name="tasks.cleanup_tasks.cleanup_redis_cache",
    max_retries=1,
)
def cleanup_redis_cache(self, pattern: str = "stoflow:cache:*") -> dict[str, Any]:
    """
    Clean up expired Redis cache entries.

    Args:
        pattern: Redis key pattern to clean (default: stoflow:cache:*)

    Returns:
        Dict with cleanup statistics
    """
    logger.info(f"Cleaning up Redis cache with pattern: {pattern}")

    import redis
    from shared.config import settings

    try:
        r = redis.from_url(settings.redis_url)

        # Get all keys matching pattern
        keys = list(r.scan_iter(match=pattern))
        deleted_count = 0

        # Delete keys in batches
        batch_size = 100
        for i in range(0, len(keys), batch_size):
            batch = keys[i:i + batch_size]
            if batch:
                deleted_count += r.delete(*batch)

        result = {
            "pattern": pattern,
            "keys_found": len(keys),
            "deleted_count": deleted_count,
        }
        logger.info(f"Redis cache cleanup completed: {result}")
        return result

    except Exception as exc:
        logger.error(f"Failed to cleanup Redis cache: {exc}", exc_info=True)
        raise
