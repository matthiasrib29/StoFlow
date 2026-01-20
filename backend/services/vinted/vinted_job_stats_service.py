"""
Vinted Job Stats Service

Service for tracking and retrieving job statistics.

Business Rules:
- Daily statistics per action type
- Rolling average for job duration
- Success rate calculation

Created: 2026-01-06
Author: Claude
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from models.user.marketplace_job import MarketplaceJob
from models.user.marketplace_job_stats import MarketplaceJobStats
from models.vinted.vinted_action_type import VintedActionType
from shared.logging import get_logger

logger = get_logger(__name__)


class VintedJobStatsService:
    """Service for Vinted job statistics."""

    @staticmethod
    def update_job_stats(db: Session, job: MarketplaceJob, success: bool) -> None:
        """
        Update daily statistics for a completed job.

        Args:
            db: SQLAlchemy Session
            job: Completed MarketplaceJob
            success: Whether job succeeded
        """
        today = datetime.now(timezone.utc).date()

        # Get or create stats record
        stats = (
            db.query(MarketplaceJobStats)
            .filter(
                MarketplaceJobStats.action_type_id == job.action_type_id,
                MarketplaceJobStats.marketplace == 'vinted',
                MarketplaceJobStats.date == today,
            )
            .first()
        )

        if not stats:
            stats = MarketplaceJobStats(
                marketplace='vinted',
                action_type_id=job.action_type_id,
                date=today,
                total_jobs=0,
                success_count=0,
                failure_count=0,
            )
            db.add(stats)

        stats.total_jobs += 1
        if success:
            stats.success_count += 1
        else:
            stats.failure_count += 1

        # Calculate average duration
        if job.started_at and job.completed_at:
            duration_ms = int((job.completed_at - job.started_at).total_seconds() * 1000)
            if stats.avg_duration_ms is None:
                stats.avg_duration_ms = duration_ms
            else:
                # Rolling average
                stats.avg_duration_ms = int(
                    (stats.avg_duration_ms * (stats.total_jobs - 1) + duration_ms)
                    / stats.total_jobs
                )

        db.commit()

    @staticmethod
    def get_stats(
        db: Session,
        days: int = 7,
        action_type_resolver: Optional[callable] = None,
    ) -> list[dict]:
        """
        Get job statistics for the last N days.

        Args:
            db: SQLAlchemy Session
            days: Number of days to look back
            action_type_resolver: Optional function to resolve action_type_id to VintedActionType

        Returns:
            List of daily stats with action type info
        """
        start_date = datetime.now(timezone.utc).date() - timedelta(days=days)

        stats_records = (
            db.query(MarketplaceJobStats)
            .filter(
                MarketplaceJobStats.marketplace == 'vinted',
                MarketplaceJobStats.date >= start_date
            )
            .order_by(MarketplaceJobStats.date.desc())
            .all()
        )

        # ===== PERFORMANCE FIX (Phase 3.4 - 2026-01-12): Avoid N+1 queries =====
        # Load all action types in a single query (instead of one query per stat)
        if not action_type_resolver:
            action_type_ids = {stat.action_type_id for stat in stats_records}
            action_types = (
                db.query(VintedActionType)
                .filter(VintedActionType.id.in_(action_type_ids))
                .all()
            )
            action_type_resolver = {at.id: at for at in action_types}.get

        result = []
        for stat in stats_records:
            action_type = action_type_resolver(stat.action_type_id)

            result.append({
                "date": stat.date.isoformat(),
                "action_code": action_type.code if action_type else "unknown",
                "action_name": action_type.name if action_type else "Unknown",
                "total_jobs": stat.total_jobs,
                "success_count": stat.success_count,
                "failure_count": stat.failure_count,
                "success_rate": stat.success_rate,
                "avg_duration_ms": stat.avg_duration_ms,
            })

        return result

    @staticmethod
    def get_daily_summary(db: Session, date: Optional[datetime] = None) -> dict:
        """
        Get summary of all job types for a specific day.

        Args:
            db: SQLAlchemy Session
            date: Date to get summary for (default: today)

        Returns:
            Dict with total stats and per-action breakdown
        """
        if date is None:
            date = datetime.now(timezone.utc).date()
        elif isinstance(date, datetime):
            date = date.date()

        stats_records = (
            db.query(MarketplaceJobStats)
            .filter(
                MarketplaceJobStats.marketplace == 'vinted',
                MarketplaceJobStats.date == date
            )
            .all()
        )

        if not stats_records:
            return {
                "date": date.isoformat(),
                "total_jobs": 0,
                "success_count": 0,
                "failure_count": 0,
                "success_rate": 0.0,
                "by_action": [],
            }

        total_jobs = sum(s.total_jobs for s in stats_records)
        success_count = sum(s.success_count for s in stats_records)
        failure_count = sum(s.failure_count for s in stats_records)

        by_action = []
        for stat in stats_records:
            action_type = (
                db.query(VintedActionType)
                .filter(VintedActionType.id == stat.action_type_id)
                .first()
            )
            by_action.append({
                "action_code": action_type.code if action_type else "unknown",
                "total_jobs": stat.total_jobs,
                "success_count": stat.success_count,
                "failure_count": stat.failure_count,
                "success_rate": stat.success_rate,
            })

        return {
            "date": date.isoformat(),
            "total_jobs": total_jobs,
            "success_count": success_count,
            "failure_count": failure_count,
            "success_rate": round(success_count / total_jobs * 100, 1) if total_jobs > 0 else 0.0,
            "by_action": by_action,
        }


__all__ = ["VintedJobStatsService"]
