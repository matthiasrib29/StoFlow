"""
SQLAlchemy model for Celery task records.

This model tracks Celery task execution metadata for monitoring
and debugging purposes.
"""
from datetime import datetime
from typing import Any

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from shared.database import Base


class CeleryTaskRecord(Base):
    """
    Model for tracking Celery task execution.

    Stores metadata about task execution including status, timing,
    results, and errors.
    """

    __tablename__ = "celery_task_records"
    __table_args__ = {"schema": "public"}

    # Primary key is the Celery task UUID
    id = Column(String(36), primary_key=True, comment="Celery task UUID")

    # Task identification
    name = Column(
        String(255),
        nullable=False,
        comment="Task name (e.g., tasks.marketplace_tasks.publish_product)",
    )
    status = Column(
        String(50),
        nullable=False,
        default="PENDING",
        comment="Task status: PENDING, STARTED, SUCCESS, FAILURE, RETRY, REVOKED",
    )

    # Task context
    marketplace = Column(
        String(50),
        nullable=True,
        comment="Marketplace: vinted, ebay, etsy",
    )
    action_code = Column(
        String(50),
        nullable=True,
        comment="Action: publish, update, delete, sync, sync_orders",
    )
    product_id = Column(
        Integer,
        nullable=True,
        comment="Product ID if applicable",
    )
    user_id = Column(
        Integer,
        ForeignKey("public.users.id", ondelete="CASCADE"),
        nullable=False,
        comment="User who initiated the task",
    )

    # Task arguments and result
    args = Column(JSONB, nullable=True, comment="Task arguments (JSON)")
    kwargs = Column(JSONB, nullable=True, comment="Task keyword arguments (JSON)")
    result = Column(JSONB, nullable=True, comment="Task result (JSON)")
    error = Column(Text, nullable=True, comment="Error message if failed")
    traceback = Column(Text, nullable=True, comment="Error traceback if failed")

    # Retry tracking
    retries = Column(Integer, default=0, comment="Number of retry attempts")
    max_retries = Column(Integer, default=3, comment="Maximum retry attempts")

    # Scheduling
    eta = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Scheduled execution time",
    )
    expires = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Task expiration time",
    )

    # Execution context
    worker = Column(
        String(255),
        nullable=True,
        comment="Worker hostname that processed the task",
    )
    queue = Column(String(255), nullable=True, comment="Queue name")

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    runtime_seconds = Column(
        Float,
        nullable=True,
        comment="Task execution time in seconds",
    )

    # Relationships
    user = relationship("User", back_populates="celery_tasks")

    def __repr__(self) -> str:
        return (
            f"<CeleryTaskRecord(id={self.id}, name={self.name}, "
            f"status={self.status}, user_id={self.user_id})>"
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status,
            "marketplace": self.marketplace,
            "action_code": self.action_code,
            "product_id": self.product_id,
            "user_id": self.user_id,
            "result": self.result,
            "error": self.error,
            "retries": self.retries,
            "max_retries": self.max_retries,
            "worker": self.worker,
            "queue": self.queue,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "runtime_seconds": self.runtime_seconds,
        }
