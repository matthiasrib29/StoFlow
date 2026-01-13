"""
Marketplace Task Model

Tasks for marketplace operations (plugin-based or direct execution).

Business Rules (Updated: 2026-01-07):
- Supports multiple task types: plugin_http, direct_http, db_operation, file_operation
- plugin_http: HTTP request via browser plugin (Vinted DataDome bypass)
- direct_http: Direct HTTP request from backend (eBay, Etsy, Vinted CDN)
- db_operation: Database operation
- file_operation: File upload/download (R2, S3)

Author: Claude
Date: 2026-01-07
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import JSON, DateTime, Enum as SQLEnum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.database import Base


class MarketplaceTaskType(str, Enum):
    """Type of marketplace task."""
    PLUGIN_HTTP = "plugin_http"        # HTTP request via browser plugin
    DIRECT_HTTP = "direct_http"        # Direct HTTP request from backend
    DB_OPERATION = "db_operation"      # Database operation
    FILE_OPERATION = "file_operation"  # File upload/download


class TaskStatus(str, Enum):
    """Status of a task."""
    PENDING = "pending"          # Waiting for execution
    PROCESSING = "processing"    # Currently being executed
    SUCCESS = "success"          # Successfully completed
    FAILED = "failed"            # Execution failed
    TIMEOUT = "timeout"          # Execution timed out
    CANCELLED = "cancelled"      # Cancelled by user


class MarketplaceTask(Base):
    """
    Task for marketplace operations.

    Table: user_{id}.marketplace_tasks

    A task represents a single atomic operation (HTTP request, DB operation, etc.)
    within a MarketplaceJob. Each job can have multiple tasks.
    """
    __tablename__ = "marketplace_tasks"
    __table_args__ = {"schema": "tenant"}  # Placeholder for schema_translate_map

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Task type
    task_type: Mapped[MarketplaceTaskType] = mapped_column(
        SQLEnum(
            MarketplaceTaskType,
            values_callable=lambda x: [e.value for e in x]
        ),
        default=MarketplaceTaskType.PLUGIN_HTTP,
        nullable=False,
        index=True,
        comment="Type of task (plugin_http, direct_http, db_operation, file_operation)"
    )

    # Human-readable description
    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Human-readable description (e.g., 'Upload image 1/5', 'Create listing')"
    )

    # Status
    status: Mapped[TaskStatus] = mapped_column(
        SQLEnum(
            TaskStatus,
            values_callable=lambda x: [e.value for e in x]
        ),
        default=TaskStatus.PENDING,
        nullable=False,
        index=True
    )

    # Payload JSON (data for executing the task)
    payload: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Task execution parameters (product_id, title, price, etc.)"
    )

    # Result JSON (output after execution)
    result: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Task result data (vinted_id, url, error, etc.)"
    )

    # Error message
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Optional relations
    product_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )

    # Job reference (parent MarketplaceJob)
    job_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("marketplace_jobs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Parent MarketplaceJob for this task"
    )

    # HTTP request information (for plugin_http and direct_http tasks)
    platform: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        comment="Target platform (vinted, ebay, etsy)"
    )

    http_method: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        comment="HTTP method (POST, PUT, DELETE, GET)"
    )

    path: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="API path (e.g., /api/v2/photos)"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When task execution started"
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When task finished (success or failure)"
    )

    # Retry
    retry_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of execution attempts"
    )

    # Note: max_retries is configured at the MarketplaceJob level, not per task

    # Relationship to job (one-way, MarketplaceJob.tasks points to PluginTask)
    job = relationship("MarketplaceJob", foreign_keys=[job_id], lazy="select")

    def __repr__(self) -> str:
        desc = self.description or f"{self.task_type.value}"
        return f"<MarketplaceTask(id={self.id}, {desc}, status={self.status})>"

    @property
    def is_plugin_task(self) -> bool:
        """Check if this task requires plugin execution."""
        return self.task_type == MarketplaceTaskType.PLUGIN_HTTP

    @property
    def is_active(self) -> bool:
        """Check if task is still active (not terminal)."""
        return self.status in (TaskStatus.PENDING, TaskStatus.PROCESSING)

    @property
    def is_terminal(self) -> bool:
        """Check if task has reached a terminal state."""
        return self.status in (TaskStatus.SUCCESS, TaskStatus.FAILED, TaskStatus.TIMEOUT, TaskStatus.CANCELLED)
