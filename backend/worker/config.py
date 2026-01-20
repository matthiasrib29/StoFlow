"""
Worker Configuration

Centralized configuration for the marketplace job worker.

Author: Claude
Date: 2026-01-20
"""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class WorkerConfig:
    """
    Configuration for marketplace job worker.

    Attributes:
        user_id: User ID for tenant isolation
        max_concurrent_jobs: Maximum parallel jobs (semaphore limit)
        marketplace_filter: Optional marketplace filter (ebay, etsy, vinted)
        poll_interval: Fallback polling interval in seconds
        graceful_shutdown_timeout: Max seconds to wait for jobs on shutdown
        db_url: PostgreSQL connection URL (from env)
        log_level: Logging level
    """

    user_id: int
    max_concurrent_jobs: int = 4
    marketplace_filter: Optional[str] = None
    poll_interval: float = 30.0
    graceful_shutdown_timeout: float = 60.0
    log_level: str = "INFO"

    # Database settings (from environment)
    db_url: str = field(default_factory=lambda: os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/stoflow"
    ))

    # Async pool settings
    asyncpg_pool_min_size: int = 2
    asyncpg_pool_max_size: int = 10

    # Job processing settings
    job_timeout: float = 600.0  # 10 minutes max per job
    retry_delay: float = 5.0  # Delay between retries
    max_retries: int = 3

    # LISTEN/NOTIFY channel
    notify_channel: str = "marketplace_job"

    @property
    def schema_name(self) -> str:
        """Get tenant schema name for this user."""
        return f"user_{self.user_id}"

    @classmethod
    def from_args(cls, args) -> "WorkerConfig":
        """
        Create config from argparse namespace.

        Args:
            args: argparse.Namespace with CLI arguments

        Returns:
            WorkerConfig instance
        """
        return cls(
            user_id=args.user_id,
            max_concurrent_jobs=args.workers,
            marketplace_filter=args.marketplace if hasattr(args, 'marketplace') else None,
            poll_interval=getattr(args, 'poll_interval', 30.0),
            log_level=getattr(args, 'log_level', 'INFO'),
        )

    def validate(self) -> None:
        """
        Validate configuration values.

        Raises:
            ValueError: If configuration is invalid
        """
        if self.user_id <= 0:
            raise ValueError(f"Invalid user_id: {self.user_id}")

        if self.max_concurrent_jobs < 1 or self.max_concurrent_jobs > 32:
            raise ValueError(
                f"max_concurrent_jobs must be between 1 and 32, got {self.max_concurrent_jobs}"
            )

        if self.marketplace_filter and self.marketplace_filter not in ("ebay", "etsy", "vinted"):
            raise ValueError(
                f"Invalid marketplace_filter: {self.marketplace_filter}. "
                f"Must be one of: ebay, etsy, vinted"
            )

        if not self.db_url:
            raise ValueError("DATABASE_URL environment variable not set")
