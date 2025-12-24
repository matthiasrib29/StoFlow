"""
Vinted Job Stats Model

Daily analytics for Vinted job execution.
Tracks success/failure rates, average duration per action type.

Author: Claude
Date: 2025-12-19
"""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class VintedJobStats(Base):
    """
    Daily statistics for Vinted jobs.

    Table: user_{id}.vinted_job_stats

    Aggregates job execution metrics per action type per day.
    Used for analytics and monitoring.
    """

    __tablename__ = "vinted_job_stats"
    __table_args__ = (
        UniqueConstraint("action_type_id", "date", name="uq_vinted_job_stats_action_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Action type reference (FK to vinted.action_types)
    action_type_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        comment="FK to vinted.action_types"
    )

    # Date of statistics
    date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True
    )

    # Counters
    total_jobs: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    success_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    failure_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    # Average duration in milliseconds
    avg_duration_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<VintedJobStats(date={self.date}, action_type_id={self.action_type_id}, total={self.total_jobs})>"

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_jobs == 0:
            return 0.0
        return (self.success_count / self.total_jobs) * 100
