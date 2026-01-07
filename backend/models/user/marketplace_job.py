"""
Marketplace Job Model

Job orchestration for marketplace operations (Vinted, eBay, Etsy).
Each job represents a single operation (publish, sync, etc.) on a product.

Business Rules (Updated: 2026-01-07):
- 1 Job = 1 product operation
- Jobs can be grouped into BatchJobs via batch_job_id FK
- Jobs contain multiple MarketplaceTasks
- Status: pending → running → completed/failed/cancelled/expired
- Expiration: 1 hour for pending jobs
- Priority: inherited from action_type or overridden

Author: Claude
Date: 2026-01-07
"""

from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.database import Base


class JobStatus(str, Enum):
    """Status of a marketplace job."""
    PENDING = "pending"        # Waiting to be processed
    RUNNING = "running"        # Currently being processed
    PAUSED = "paused"          # Paused by user, can be resumed
    COMPLETED = "completed"    # Successfully completed
    FAILED = "failed"          # Failed after max retries
    CANCELLED = "cancelled"    # Cancelled by user
    EXPIRED = "expired"        # Expired (pending > 1h)


class MarketplaceJob(Base):
    """
    Marketplace job for orchestrating operations.

    Table: user_{id}.marketplace_jobs

    A job represents a single operation on a marketplace (publish, update, delete, etc.)
    Jobs can be grouped into BatchJobs when created from batch API calls.
    Each job can have multiple MarketplaceTasks associated with it.
    """

    __tablename__ = "marketplace_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Marketplace identifier
    marketplace: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="vinted",
        index=True,
        comment="Target marketplace (vinted, ebay, etsy)"
    )

    # Batch reference (NEW - FK to BatchJob)
    batch_job_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("batch_jobs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Parent BatchJob (for batch operations)"
    )

    # Batch ID string (DEPRECATED - keep for backward compatibility)
    batch_id: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        comment="DEPRECATED: Use batch_job_id instead. Groups jobs from same batch API call"
    )

    # Action type reference (FK to vinted.action_types)
    action_type_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        comment="FK to action_types table (marketplace-specific)"
    )

    # Product reference (optional, for product-specific jobs)
    product_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Product being processed (if applicable)"
    )

    # Status
    status: Mapped[JobStatus] = mapped_column(
        SQLEnum(
            JobStatus,
            values_callable=lambda x: [e.value for e in x]
        ),
        default=JobStatus.PENDING,
        nullable=False,
        index=True
    )

    # Priority (can override action_type default)
    priority: Mapped[int] = mapped_column(
        Integer,
        default=3,
        nullable=False,
        index=True,
        comment="1=CRITICAL, 2=HIGH, 3=NORMAL, 4=LOW"
    )

    # Job parameters/result data
    input_data: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Job input parameters"
    )

    result_data: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Job result data (output)"
    )

    # Error tracking
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    retry_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    max_retries: Mapped[int] = mapped_column(
        Integer,
        default=3,
        nullable=False
    )

    # Timestamps
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When job started processing"
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When job finished (success or failure)"
    )

    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When pending job expires (created_at + 1h)"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )

    # Relationships
    batch_job = relationship("BatchJob", back_populates="jobs", lazy="select")
    product = relationship("Product", foreign_keys=[product_id], lazy="select")
    tasks = relationship("MarketplaceTask", back_populates="job", lazy="select")

    def __repr__(self) -> str:
        return f"<MarketplaceJob(id={self.id}, marketplace={self.marketplace}, status={self.status}, product_id={self.product_id})>"

    @property
    def is_active(self) -> bool:
        """Check if job is still active (can be processed)."""
        return self.status in (JobStatus.PENDING, JobStatus.RUNNING, JobStatus.PAUSED)

    @property
    def is_terminal(self) -> bool:
        """Check if job has reached a terminal state."""
        return self.status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED, JobStatus.EXPIRED)

    @property
    def is_vinted(self) -> bool:
        """Check if this is a Vinted job."""
        return self.marketplace == "vinted"

    @property
    def is_ebay(self) -> bool:
        """Check if this is an eBay job."""
        return self.marketplace == "ebay"

    @property
    def is_etsy(self) -> bool:
        """Check if this is an Etsy job."""
        return self.marketplace == "etsy"
