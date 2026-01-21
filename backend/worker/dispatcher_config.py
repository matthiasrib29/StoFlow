"""
Job Dispatcher Configuration

Configuration for the multi-tenant job dispatcher.

Author: Claude
Date: 2026-01-21
"""

import os
from dataclasses import dataclass, field


@dataclass
class DispatcherConfig:
    """
    Configuration for the JobDispatcher.

    The dispatcher manages multiple ClientWorkers (one per active tenant)
    and ensures fair resource allocation across all tenants.

    Attributes:
        global_max_concurrent: Maximum total concurrent jobs across all tenants
        per_client_max_concurrent: Maximum concurrent jobs per tenant
        asyncpg_pool_min_size: Minimum connections in asyncpg pool
        asyncpg_pool_max_size: Maximum connections in asyncpg pool
        worker_idle_timeout_hours: Remove idle workers after this duration
        worker_max_age_hours: Force restart workers after this duration
        poll_interval: Fallback polling interval in seconds
        notify_channel: PostgreSQL LISTEN/NOTIFY channel name
        job_timeout: Maximum job execution time in seconds
        graceful_shutdown_timeout: Max wait time for jobs on shutdown
        db_url: PostgreSQL connection URL
    """

    # Semaphore limits
    global_max_concurrent: int = 150      # Protection DB globale
    per_client_max_concurrent: int = 30   # Par client

    # Connection pool (partagé)
    asyncpg_pool_min_size: int = 2
    asyncpg_pool_max_size: int = 5

    # Worker lifecycle
    worker_idle_timeout_hours: float = 2.0   # Janitor cleanup
    worker_max_age_hours: float = 24.0       # Force restart

    # Polling
    poll_interval: float = 30.0
    notify_channel: str = "marketplace_job"

    # Timeouts
    job_timeout: float = 600.0               # 10 min max
    graceful_shutdown_timeout: float = 60.0

    # Database
    db_url: str = field(default_factory=lambda: os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/stoflow"
    ))

    @classmethod
    def from_settings(cls) -> "DispatcherConfig":
        """
        Create config from application settings.

        Returns:
            DispatcherConfig instance with values from settings
        """
        # Import here to avoid circular dependency
        from shared.config import settings

        return cls(
            global_max_concurrent=settings.dispatcher_global_max_concurrent,
            per_client_max_concurrent=settings.dispatcher_per_client_max_concurrent,
            worker_idle_timeout_hours=settings.dispatcher_worker_idle_timeout_hours,
            worker_max_age_hours=settings.dispatcher_worker_max_age_hours,
            poll_interval=settings.dispatcher_poll_interval,
            db_url=str(settings.database_url),
        )

    def validate(self) -> None:
        """
        Validate configuration values.

        Raises:
            ValueError: If configuration is invalid
        """
        if self.global_max_concurrent < 1:
            raise ValueError(
                f"global_max_concurrent must be >= 1, got {self.global_max_concurrent}"
            )

        if self.per_client_max_concurrent < 1:
            raise ValueError(
                f"per_client_max_concurrent must be >= 1, got {self.per_client_max_concurrent}"
            )

        if self.per_client_max_concurrent > self.global_max_concurrent:
            raise ValueError(
                f"per_client_max_concurrent ({self.per_client_max_concurrent}) "
                f"cannot exceed global_max_concurrent ({self.global_max_concurrent})"
            )

        if self.worker_idle_timeout_hours <= 0:
            raise ValueError(
                f"worker_idle_timeout_hours must be > 0, got {self.worker_idle_timeout_hours}"
            )

        if self.worker_max_age_hours <= 0:
            raise ValueError(
                f"worker_max_age_hours must be > 0, got {self.worker_max_age_hours}"
            )

        if not self.db_url:
            raise ValueError("DATABASE_URL environment variable not set")
