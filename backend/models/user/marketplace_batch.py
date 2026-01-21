"""
Marketplace Batch Model

Groups multiple MarketplaceJobs into a single batch operation.
Provides progress tracking and batch-level status management.

Renamed from BatchJob to MarketplaceBatch for consistency with MarketplaceJob and MarketplaceTask.

Author: Claude
Date: 2026-01-06
Updated: 2026-01-20 - Renamed BatchJob → MarketplaceBatch
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.database import Base


class MarketplaceBatchStatus(str, Enum):
    """Status of a marketplace batch."""
    PENDING = "pending"              # Not started yet
    RUNNING = "running"              # Some jobs are running
    COMPLETED = "completed"          # All jobs completed successfully
    PARTIALLY_FAILED = "partially_failed"  # Some succeeded, some failed
    FAILED = "failed"                # All jobs failed
    CANCELLED = "cancelled"          # Batch was cancelled


# Backward compatibility alias (deprecated)
BatchJobStatus = MarketplaceBatchStatus


class MarketplaceBatch(Base):
    """
    Marketplace batch for grouping multiple marketplace operations.

    Table: user_{id}.marketplace_batches

    A batch represents a bulk operation (e.g., publish 200 products).
    It groups N MarketplaceJobs and tracks overall progress.
    """

    __tablename__ = "marketplace_batches"
    __table_args__ = {"schema": "tenant"}  # Placeholder for schema_translate_map

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
    status: Mapped[MarketplaceBatchStatus] = mapped_column(
        SQLEnum(
            MarketplaceBatchStatus,
            values_callable=lambda x: [e.value for e in x]
        ),
        default=MarketplaceBatchStatus.PENDING,
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

    # Relationships - lazy="raise" to prevent N+1 queries
    jobs = relationship(
        "MarketplaceJob",
        back_populates="marketplace_batch",
        lazy="raise",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<MarketplaceBatch(id={self.id}, batch_id={self.batch_id}, status={self.status}, progress={self.progress_percent}%)>"

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
        return self.status in (MarketplaceBatchStatus.PENDING, MarketplaceBatchStatus.RUNNING)

    @property
    def is_terminal(self) -> bool:
        """
        Check if batch has reached a terminal state.

        Returns:
            True if batch is completed, failed, partially_failed, or cancelled
        """
        return self.status in (
            MarketplaceBatchStatus.COMPLETED,
            MarketplaceBatchStatus.FAILED,
            MarketplaceBatchStatus.PARTIALLY_FAILED,
            MarketplaceBatchStatus.CANCELLED
        )

    @property
    def pending_count(self) -> int:
        """
        Calculate number of pending jobs.

        Returns:
            Number of jobs not yet processed
        """
        return self.total_count - (self.completed_count + self.failed_count + self.cancelled_count)


# Backward compatibility alias (deprecated)
BatchJob = MarketplaceBatch
