"""
Temporal configuration module.

Provides configuration for connecting to Temporal server.
"""

import os
from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class TemporalConfig(BaseSettings):
    """Configuration for Temporal workflow orchestration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Temporal Server Connection
    temporal_host: str = Field(
        default="localhost:7233",
        description="Temporal server address (host:port)"
    )
    temporal_namespace: str = Field(
        default="stoflow",
        description="Temporal namespace for StoFlow workflows"
    )

    # Task Queue Configuration
    temporal_task_queue: str = Field(
        default="stoflow-sync-queue",
        description="Default task queue for sync workflows"
    )

    # Worker Configuration
    temporal_worker_identity: Optional[str] = Field(
        default=None,
        description="Worker identity (auto-generated if not set)"
    )
    temporal_max_concurrent_workflow_tasks: int = Field(
        default=10,
        description="Max concurrent workflow task executions"
    )
    temporal_max_concurrent_activities: int = Field(
        default=50,
        description="Max concurrent activity executions (sliding window)"
    )

    # Retry Configuration (defaults)
    temporal_default_retry_max_attempts: int = Field(
        default=3,
        description="Default max retry attempts for activities"
    )
    temporal_default_retry_initial_interval_seconds: int = Field(
        default=1,
        description="Initial retry interval in seconds"
    )
    temporal_default_retry_max_interval_seconds: int = Field(
        default=60,
        description="Maximum retry interval in seconds"
    )
    temporal_default_retry_backoff_coefficient: float = Field(
        default=2.0,
        description="Retry backoff multiplier"
    )

    # Timeouts
    temporal_workflow_execution_timeout_hours: int = Field(
        default=24,
        description="Max workflow execution time in hours"
    )
    temporal_workflow_run_timeout_hours: int = Field(
        default=1,
        description="Max single workflow run time in hours"
    )
    temporal_activity_start_to_close_timeout_minutes: int = Field(
        default=10,
        description="Activity execution timeout in minutes"
    )
    temporal_activity_schedule_to_close_timeout_minutes: int = Field(
        default=30,
        description="Activity schedule to close timeout in minutes"
    )

    # Feature Flags
    temporal_enabled: bool = Field(
        default=True,
        description="Enable Temporal workflows (can disable for fallback)"
    )

    @property
    def worker_identity(self) -> str:
        """Get worker identity, auto-generate if not set."""
        if self.temporal_worker_identity:
            return self.temporal_worker_identity
        import socket
        hostname = socket.gethostname()
        pid = os.getpid()
        return f"stoflow-worker-{hostname}-{pid}"


@lru_cache()
def get_temporal_config() -> TemporalConfig:
    """Get cached Temporal configuration instance."""
    return TemporalConfig()


# Global instance for easy import
temporal_config = get_temporal_config()
