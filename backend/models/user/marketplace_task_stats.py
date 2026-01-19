"""
Marketplace Task Stats Model

Daily analytics for task execution across all marketplaces.
Tracks success/failure rates, average duration per task type.

Author: Claude
Date: 2026-01-19 (Phase 12-01)
"""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class MarketplaceTaskStats(Base):
    """
    Daily statistics for marketplace tasks.

    Table: user_{id}.marketplace_task_stats

    Aggregates task execution metrics per task_type and marketplace per day.
    Used for analytics, monitoring, and failure rate alerting.

    Follows the same pattern as VintedJobStats but at the task level.
    """

    __tablename__ = "marketplace_task_stats"
    __table_args__ = (
        UniqueConstraint(
            "task_type", "marketplace", "date",
            name="uq_marketplace_task_stats_type_marketplace_date"
        ),
        {"schema": "tenant"},  # Placeholder for schema_translate_map
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Task type (plugin_http, direct_http, db_operation, file_operation)
    task_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Type of task (plugin_http, direct_http, db_operation, file_operation)"
    )

    # Marketplace identifier
    marketplace: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Target marketplace (vinted, ebay, etsy)"
    )

    # Date of statistics
    date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True
    )

    # Counters
    total_tasks: Mapped[int] = mapped_column(
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

    # Average duration in milliseconds (rolling average)
    avg_duration_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Rolling average task duration in milliseconds"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<MarketplaceTaskStats(date={self.date}, "
            f"marketplace={self.marketplace}, task_type={self.task_type}, "
            f"total={self.total_tasks})>"
        )

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage (0-100)."""
        if self.total_tasks == 0:
            return 0.0
        return (self.success_count / self.total_tasks) * 100

    @property
    def failure_rate(self) -> float:
        """Calculate failure rate as percentage (0-100)."""
        if self.total_tasks == 0:
            return 0.0
        return (self.failure_count / self.total_tasks) * 100
