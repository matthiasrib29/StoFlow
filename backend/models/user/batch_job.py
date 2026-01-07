"""
Batch Job Model

Groups multiple MarketplaceJobs into a single batch operation.
Provides progress tracking and batch-level status management.

Author: Claude
Date: 2026-01-06
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.database import Base


class BatchJobStatus(str, Enum):
    """Status of a batch job."""
    PENDING = "pending"              # Not started yet
    RUNNING = "running"              # Some jobs are running
    COMPLETED = "completed"          # All jobs completed successfully
    PARTIALLY_FAILED = "partially_failed"  # Some succeeded, some failed
    FAILED = "failed"                # All jobs failed
    CANCELLED = "cancelled"          # Batch was cancelled


class BatchJob(Base):
    """
    Batch job for grouping multiple marketplace operations.

    Table: user_{id}.batch_jobs

    A batch job represents a bulk operation (e.g., publish 200 products).
    It groups N MarketplaceJobs and tracks overall progress.
    """

    __tablename__ = "batch_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Batch identifier (UUID-like)
    batch_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
        comment="Unique batch identifier (format: action_timestamp_uuid)"
    )

    # Marketplace and action
    marketplace: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Target marketplace (vinted, ebay, etsy)"
    )

    action_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Action type (publish, update, delete, link_product, sync)"
    )

    # Progress counters
    total_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Total number of jobs in this batch"
    )

    completed_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of successfully completed jobs"
    )

    failed_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of failed jobs"
    )

    cancelled_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of cancelled jobs"
    )

    # Status
    status: Mapped[BatchJobStatus] = mapped_column(
        SQLEnum(
            BatchJobStatus,
            values_callable=lambda x: [e.value for e in x]
        ),
        default=BatchJobStatus.PENDING,
        nullable=False,
        index=True
    )

    # Priority (1=CRITICAL, 2=HIGH, 3=NORMAL, 4=LOW)
    priority: Mapped[int] = mapped_column(
        Integer,
        default=3,
        nullable=False,
        index=True,
        comment="1=CRITICAL, 2=HIGH, 3=NORMAL, 4=LOW"
    )

    # Metadata
    created_by_user_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("public.users.id", ondelete="SET NULL"),
        nullable=True,
        comment="User who created this batch"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When first job started processing"
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When batch finished (all jobs terminal)"
    )

    # Relationships
    jobs = relationship(
        "MarketplaceJob",
        back_populates="batch_job",
        lazy="select",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<BatchJob(id={self.id}, batch_id={self.batch_id}, status={self.status}, progress={self.progress_percent}%)>"

    @property
    def progress_percent(self) -> float:
        """
        Calculate progress percentage based on completed jobs.

        Returns:
            Progress percentage (0-100)
        """
        if self.total_count == 0:
            return 0.0
        return round((self.completed_count / self.total_count) * 100, 1)

    @property
    def is_active(self) -> bool:
        """
        Check if batch is still active (not terminal).

        Returns:
            True if batch is pending or running
        """
        return self.status in (BatchJobStatus.PENDING, BatchJobStatus.RUNNING)

    @property
    def is_terminal(self) -> bool:
        """
        Check if batch has reached a terminal state.

        Returns:
            True if batch is completed, failed, partially_failed, or cancelled
        """
        return self.status in (
            BatchJobStatus.COMPLETED,
            BatchJobStatus.FAILED,
            BatchJobStatus.PARTIALLY_FAILED,
            BatchJobStatus.CANCELLED
        )

    @property
    def pending_count(self) -> int:
        """
        Calculate number of pending jobs.

        Returns:
            Number of jobs not yet processed
        """
        return self.total_count - (self.completed_count + self.failed_count + self.cancelled_count)
