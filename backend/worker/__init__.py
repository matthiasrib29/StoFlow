"""
StoFlow Marketplace Worker Package

Standalone async worker for processing marketplace jobs.
Replaces Celery with a custom PostgreSQL LISTEN/NOTIFY based system.

Components:
- config.py: Worker configuration
- signals.py: Graceful shutdown handling
- job_executor.py: Async job execution logic
- marketplace_worker.py: Main worker entry point
- scheduler.py: Periodic tasks (replaces Celery Beat)

Usage:
    python -m worker.marketplace_worker --user-id=1 --workers=4

Author: Claude
Date: 2026-01-20
"""

__all__ = [
    "WorkerConfig",
    "MarketplaceWorker",
    "JobExecutor",
    "MarketplaceScheduler",
]
