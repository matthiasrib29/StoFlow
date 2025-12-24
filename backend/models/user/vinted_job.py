"""
Vinted Job Model

Job orchestration for Vinted operations.
Each job represents a single operation (publish, sync, etc.) on a product.

Business Rules (2025-12-19):
- 1 Job = 1 product operation (no sub-jobs)
- Jobs are grouped by batch_id for batch operations
- Jobs contain multiple PluginTasks (HTTP requests)
- Status: pending → running → completed/failed/cancelled/expired
- Expiration: 1 hour for pending jobs
- Priority: inherited from action_type or overridden

Author: Claude
Date: 2025-12-19
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
    """Status of a Vinted job."""
    PENDING = "pending"        # Waiting to be processed
    RUNNING = "running"        # Currently being processed
    PAUSED = "paused"          # Paused by user, can be resumed
    COMPLETED = "completed"    # Successfully completed
    FAILED = "failed"          # Failed after max retries
    CANCELLED = "cancelled"    # Cancelled by user
    EXPIRED = "expired"        # Expired (pending > 1h)


class VintedJob(Base):
    """
    Vinted job for orchestrating operations.

    Table: user_{id}.vinted_jobs

    A job represents a single operation on Vinted (publish, update, delete, etc.)
    Jobs are grouped by batch_id when created from batch API calls.
    Each job can have multiple PluginTasks (HTTP requests) associated with it.
    """

    __tablename__ = "vinted_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Batch grouping (optional)
    batch_id: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        comment="Groups jobs from same batch API call"
    )

    # Action type reference (FK to vinted.action_types)
    action_type_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        comment="FK to vinted.action_types"
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
    result_data: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Job parameters (input) and result data (output)"
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
    product = relationship("Product", foreign_keys=[product_id], lazy="select")
    tasks = relationship("PluginTask", back_populates="job", lazy="select")

    def __repr__(self) -> str:
        return f"<VintedJob(id={self.id}, status={self.status}, product_id={self.product_id})>"

    @property
    def is_active(self) -> bool:
        """Check if job is still active (can be processed)."""
        return self.status in (JobStatus.PENDING, JobStatus.RUNNING, JobStatus.PAUSED)

    @property
    def is_terminal(self) -> bool:
        """Check if job has reached a terminal state."""
        return self.status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED, JobStatus.EXPIRED)
