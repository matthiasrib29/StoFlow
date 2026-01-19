"""
Task Metrics Service

Service for logging and tracking task-level execution metrics.

Business Rules:
- Logs task execution times with structured format
- Tracks slow tasks (>5000ms) with WARNING level
- Provides start/complete logging methods
- Tracks daily task statistics (success/failure/duration)
- Provides failure rate alerting

Created: 2026-01-19
Author: Claude (Phase 12-01)
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from models.user.marketplace_task import MarketplaceTask, TaskStatus
from models.user.marketplace_task_stats import MarketplaceTaskStats
from shared.logging_setup import get_logger

logger = get_logger(__name__)

# Threshold for slow task warning (in milliseconds)
SLOW_TASK_THRESHOLD_MS = 5000

# Default failure rate alert threshold (20%)
DEFAULT_FAILURE_THRESHOLD = 0.2


class TaskMetricsService:
    """
    Service for task execution metrics and logging.

    Provides structured logging for task execution times and status changes.
    Integrates with MarketplaceJobProcessor for observability.

    Log Format:
        [TaskMetrics] task_id={id} job_id={job_id} type={task_type} status={status} duration_ms={ms}

    Usage:
        metrics = TaskMetricsService()
        metrics.log_task_start(task)
        # ... task execution ...
        metrics.log_task_complete(task)
    """

    @staticmethod
    def log_task_start(task: MarketplaceTask) -> None:
        """
        Log task execution start.

        Logs at INFO level with structured format including task metadata.

        Args:
            task: The MarketplaceTask that is starting execution
        """
        logger.info(
            f"[TaskMetrics] task_id={task.id} job_id={task.job_id} "
            f"type={task.task_type.value} status=started "
            f"description=\"{task.description or 'N/A'}\""
        )

    @staticmethod
    def log_task_complete(task: MarketplaceTask) -> None:
        """
        Log task execution completion with duration.

        Calculates duration from task.started_at and task.completed_at.
        Logs at WARNING level if duration exceeds SLOW_TASK_THRESHOLD_MS.

        Args:
            task: The completed MarketplaceTask with started_at and completed_at set
        """
        duration_ms = TaskMetricsService._calculate_duration_ms(task)
        status = task.status.value if task.status else "unknown"

        log_message = (
            f"[TaskMetrics] task_id={task.id} job_id={task.job_id} "
            f"type={task.task_type.value} status={status} "
            f"duration_ms={duration_ms}"
        )

        # Log at WARNING level for slow tasks
        if duration_ms is not None and duration_ms > SLOW_TASK_THRESHOLD_MS:
            logger.warning(f"{log_message} (SLOW TASK)")
        else:
            logger.info(log_message)

    @staticmethod
    def _calculate_duration_ms(task: MarketplaceTask) -> Optional[int]:
        """
        Calculate task execution duration in milliseconds.

        Args:
            task: Task with started_at and completed_at timestamps

        Returns:
            Duration in milliseconds, or None if timestamps are missing
        """
        if task.started_at and task.completed_at:
            # Handle timezone-aware and naive datetimes
            started = task.started_at
            completed = task.completed_at

            # Ensure both are timezone-aware for comparison
            if started.tzinfo is None:
                started = started.replace(tzinfo=timezone.utc)
            if completed.tzinfo is None:
                completed = completed.replace(tzinfo=timezone.utc)

            duration_seconds = (completed - started).total_seconds()
            return int(duration_seconds * 1000)
        return None

    @staticmethod
    def get_task_duration_ms(task: MarketplaceTask) -> Optional[int]:
        """
        Public method to get task duration for external use.

        Args:
            task: Task with timestamps

        Returns:
            Duration in milliseconds, or None if not calculable
        """
        return TaskMetricsService._calculate_duration_ms(task)

    # =========================================================================
    # TASK STATS METHODS (Phase 12-01 Task 2)
    # =========================================================================

    @staticmethod
    def update_task_stats(db: Session, task: MarketplaceTask, success: bool) -> None:
        """
        Update daily statistics for a completed task.

        Creates or updates MarketplaceTaskStats record for today.
        Follows the same rolling average pattern as VintedJobStatsService.

        Args:
            db: SQLAlchemy Session (user schema)
            task: Completed MarketplaceTask
            success: Whether task succeeded
        """
        today = datetime.now(timezone.utc).date()
        task_type = task.task_type.value
        marketplace = task.platform or "unknown"

        # Get or create stats record for today
        stats = (
            db.query(MarketplaceTaskStats)
            .filter(
                MarketplaceTaskStats.task_type == task_type,
                MarketplaceTaskStats.marketplace == marketplace,
                MarketplaceTaskStats.date == today,
            )
            .first()
        )

        if not stats:
            stats = MarketplaceTaskStats(
                task_type=task_type,
                marketplace=marketplace,
                date=today,
                total_tasks=0,
                success_count=0,
                failure_count=0,
            )
            db.add(stats)

        # Update counters
        stats.total_tasks += 1
        if success:
            stats.success_count += 1
        else:
            stats.failure_count += 1

        # Calculate rolling average duration (same pattern as VintedJobStatsService)
        duration_ms = TaskMetricsService._calculate_duration_ms(task)
        if duration_ms is not None:
            if stats.avg_duration_ms is None:
                stats.avg_duration_ms = duration_ms
            else:
                # Rolling average: (old_avg * (n-1) + new_value) / n
                stats.avg_duration_ms = int(
                    (stats.avg_duration_ms * (stats.total_tasks - 1) + duration_ms)
                    / stats.total_tasks
                )

        db.commit()

        logger.debug(
            f"[TaskStats] Updated stats: {marketplace}/{task_type} "
            f"total={stats.total_tasks} success_rate={stats.success_rate:.1f}%"
        )

    @staticmethod
    def get_task_stats(
        db: Session,
        days: int = 7,
        marketplace: Optional[str] = None,
        task_type: Optional[str] = None,
    ) -> list[dict]:
        """
        Get task statistics for the last N days.

        Args:
            db: SQLAlchemy Session
            days: Number of days to look back (default: 7)
            marketplace: Optional filter by marketplace (vinted, ebay, etsy)
            task_type: Optional filter by task type

        Returns:
            List of daily stats dicts with keys:
            - date, task_type, marketplace, total_tasks, success_count,
              failure_count, success_rate, avg_duration_ms
        """
        start_date = datetime.now(timezone.utc).date() - timedelta(days=days)

        query = db.query(MarketplaceTaskStats).filter(
            MarketplaceTaskStats.date >= start_date
        )

        if marketplace:
            query = query.filter(MarketplaceTaskStats.marketplace == marketplace)
        if task_type:
            query = query.filter(MarketplaceTaskStats.task_type == task_type)

        stats_records = query.order_by(MarketplaceTaskStats.date.desc()).all()

        return [
            {
                "date": stat.date.isoformat(),
                "task_type": stat.task_type,
                "marketplace": stat.marketplace,
                "total_tasks": stat.total_tasks,
                "success_count": stat.success_count,
                "failure_count": stat.failure_count,
                "success_rate": round(stat.success_rate, 1),
                "failure_rate": round(stat.failure_rate, 1),
                "avg_duration_ms": stat.avg_duration_ms,
            }
            for stat in stats_records
        ]


__all__ = ["TaskMetricsService", "SLOW_TASK_THRESHOLD_MS", "DEFAULT_FAILURE_THRESHOLD"]
