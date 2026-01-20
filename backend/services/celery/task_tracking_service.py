"""
Task Tracking Service for Celery tasks.

Provides CRUD operations and queries for CeleryTaskRecord.
"""
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session

from models.public.celery_task_record import CeleryTaskRecord
from shared.logging_setup import get_logger

logger = get_logger(__name__)


class TaskTrackingService:
    """
    Service for tracking Celery task execution.

    Provides methods to create, update, and query task records.
    """

    def __init__(self, db: Session):
        """
        Initialize the service.

        Args:
            db: SQLAlchemy session
        """
        self.db = db

    def create_task_record(
        self,
        task_id: str,
        name: str,
        user_id: int,
        args: list | None = None,
        kwargs: dict | None = None,
        marketplace: str | None = None,
        action_code: str | None = None,
        product_id: int | None = None,
        queue: str | None = None,
        eta: datetime | None = None,
        expires: datetime | None = None,
        max_retries: int = 3,
    ) -> CeleryTaskRecord:
        """
        Create a new task record.

        Args:
            task_id: Celery task UUID
            name: Task name
            user_id: User ID
            args: Task arguments
            kwargs: Task keyword arguments
            marketplace: Marketplace (vinted, ebay, etsy)
            action_code: Action code (publish, update, etc.)
            product_id: Product ID if applicable
            queue: Queue name
            eta: Scheduled execution time
            expires: Task expiration time
            max_retries: Maximum retry attempts

        Returns:
            Created CeleryTaskRecord
        """
        record = CeleryTaskRecord(
            id=task_id,
            name=name,
            status="PENDING",
            user_id=user_id,
            args=args,
            kwargs=kwargs,
            marketplace=marketplace,
            action_code=action_code,
            product_id=product_id,
            queue=queue,
            eta=eta,
            expires=expires,
            max_retries=max_retries,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)

        logger.info(
            f"Created task record: id={task_id}, name={name}, user_id={user_id}"
        )
        return record

    def update_task_started(
        self,
        task_id: str,
        worker: str | None = None,
    ) -> CeleryTaskRecord | None:
        """
        Update task record when task starts.

        Args:
            task_id: Celery task UUID
            worker: Worker hostname

        Returns:
            Updated record or None if not found
        """
        record = self.get_task_record(task_id)
        if not record:
            return None

        record.status = "STARTED"
        record.started_at = datetime.now(timezone.utc)
        record.worker = worker
        self.db.commit()

        logger.debug(f"Task started: id={task_id}, worker={worker}")
        return record

    def update_task_success(
        self,
        task_id: str,
        result: Any = None,
    ) -> CeleryTaskRecord | None:
        """
        Update task record on success.

        Args:
            task_id: Celery task UUID
            result: Task result

        Returns:
            Updated record or None if not found
        """
        record = self.get_task_record(task_id)
        if not record:
            return None

        now = datetime.now(timezone.utc)
        record.status = "SUCCESS"
        record.result = result if isinstance(result, dict) else {"value": result}
        record.completed_at = now
        if record.started_at:
            record.runtime_seconds = (now - record.started_at).total_seconds()
        self.db.commit()

        logger.info(f"Task succeeded: id={task_id}")
        return record

    def update_task_failure(
        self,
        task_id: str,
        error: str,
        traceback: str | None = None,
    ) -> CeleryTaskRecord | None:
        """
        Update task record on failure.

        Args:
            task_id: Celery task UUID
            error: Error message
            traceback: Error traceback

        Returns:
            Updated record or None if not found
        """
        record = self.get_task_record(task_id)
        if not record:
            return None

        now = datetime.now(timezone.utc)
        record.status = "FAILURE"
        record.error = error
        record.traceback = traceback
        record.completed_at = now
        if record.started_at:
            record.runtime_seconds = (now - record.started_at).total_seconds()
        self.db.commit()

        logger.error(f"Task failed: id={task_id}, error={error}")
        return record

    def update_task_retry(
        self,
        task_id: str,
        retries: int,
        error: str | None = None,
    ) -> CeleryTaskRecord | None:
        """
        Update task record on retry.

        Args:
            task_id: Celery task UUID
            retries: Current retry count
            error: Error that caused retry

        Returns:
            Updated record or None if not found
        """
        record = self.get_task_record(task_id)
        if not record:
            return None

        record.status = "RETRY"
        record.retries = retries
        if error:
            record.error = error
        self.db.commit()

        logger.info(f"Task retrying: id={task_id}, retries={retries}")
        return record

    def update_task_revoked(
        self,
        task_id: str,
    ) -> CeleryTaskRecord | None:
        """
        Update task record when revoked.

        Args:
            task_id: Celery task UUID

        Returns:
            Updated record or None if not found
        """
        record = self.get_task_record(task_id)
        if not record:
            return None

        record.status = "REVOKED"
        record.completed_at = datetime.now(timezone.utc)
        self.db.commit()

        logger.info(f"Task revoked: id={task_id}")
        return record

    def get_task_record(self, task_id: str) -> CeleryTaskRecord | None:
        """
        Get a task record by ID.

        Args:
            task_id: Celery task UUID

        Returns:
            Task record or None
        """
        return (
            self.db.query(CeleryTaskRecord)
            .filter(CeleryTaskRecord.id == task_id)
            .first()
        )

    def get_tasks_for_user(
        self,
        user_id: int,
        status: str | None = None,
        marketplace: str | None = None,
        action_code: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[CeleryTaskRecord]:
        """
        Get tasks for a specific user.

        Args:
            user_id: User ID
            status: Filter by status
            marketplace: Filter by marketplace
            action_code: Filter by action code
            limit: Maximum number of records
            offset: Number of records to skip

        Returns:
            List of task records
        """
        query = self.db.query(CeleryTaskRecord).filter(
            CeleryTaskRecord.user_id == user_id
        )

        if status:
            query = query.filter(CeleryTaskRecord.status == status)
        if marketplace:
            query = query.filter(CeleryTaskRecord.marketplace == marketplace)
        if action_code:
            query = query.filter(CeleryTaskRecord.action_code == action_code)

        return (
            query.order_by(desc(CeleryTaskRecord.created_at))
            .limit(limit)
            .offset(offset)
            .all()
        )

    def get_task_count_for_user(
        self,
        user_id: int,
        status: str | None = None,
    ) -> int:
        """
        Get task count for a user.

        Args:
            user_id: User ID
            status: Filter by status

        Returns:
            Task count
        """
        query = self.db.query(func.count(CeleryTaskRecord.id)).filter(
            CeleryTaskRecord.user_id == user_id
        )
        if status:
            query = query.filter(CeleryTaskRecord.status == status)
        return query.scalar() or 0

    def get_task_stats(
        self,
        user_id: int,
        days: int = 7,
    ) -> dict[str, Any]:
        """
        Get task statistics for a user.

        Args:
            user_id: User ID
            days: Number of days to include

        Returns:
            Dict with statistics
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        # Get counts by status
        status_counts = (
            self.db.query(
                CeleryTaskRecord.status,
                func.count(CeleryTaskRecord.id).label("count"),
            )
            .filter(
                CeleryTaskRecord.user_id == user_id,
                CeleryTaskRecord.created_at >= cutoff,
            )
            .group_by(CeleryTaskRecord.status)
            .all()
        )

        # Get counts by marketplace
        marketplace_counts = (
            self.db.query(
                CeleryTaskRecord.marketplace,
                func.count(CeleryTaskRecord.id).label("count"),
            )
            .filter(
                CeleryTaskRecord.user_id == user_id,
                CeleryTaskRecord.created_at >= cutoff,
                CeleryTaskRecord.marketplace.isnot(None),
            )
            .group_by(CeleryTaskRecord.marketplace)
            .all()
        )

        # Get average runtime
        avg_runtime = (
            self.db.query(func.avg(CeleryTaskRecord.runtime_seconds))
            .filter(
                CeleryTaskRecord.user_id == user_id,
                CeleryTaskRecord.created_at >= cutoff,
                CeleryTaskRecord.runtime_seconds.isnot(None),
            )
            .scalar()
        )

        return {
            "period_days": days,
            "by_status": {row.status: row.count for row in status_counts},
            "by_marketplace": {
                row.marketplace: row.count for row in marketplace_counts
            },
            "avg_runtime_seconds": round(avg_runtime, 2) if avg_runtime else None,
            "total": sum(row.count for row in status_counts),
        }

    def delete_old_records(self, days: int = 30) -> int:
        """
        Delete old completed/failed task records.

        Args:
            days: Number of days to keep

        Returns:
            Number of deleted records
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        deleted = (
            self.db.query(CeleryTaskRecord)
            .filter(
                CeleryTaskRecord.status.in_(["SUCCESS", "FAILURE", "REVOKED"]),
                CeleryTaskRecord.completed_at < cutoff,
            )
            .delete(synchronize_session=False)
        )
        self.db.commit()

        logger.info(f"Deleted {deleted} old task records")
        return deleted
