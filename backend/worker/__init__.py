"""
StoFlow Marketplace Worker Package

Job processing system with two modes:
1. Integrated (recommended): JobDispatcher runs inside FastAPI backend
2. Standalone: MarketplaceWorker runs as separate process (legacy)

Components:
- config.py: Worker configuration (for standalone mode)
- dispatcher_config.py: Dispatcher configuration (for integrated mode)
- client_worker.py: Per-tenant worker (used by dispatcher)
- dispatcher.py: Multi-tenant job dispatcher (integrated mode)
- signals.py: Graceful shutdown handling
- job_executor.py: Async job execution logic
- marketplace_worker.py: Standalone worker entry point (legacy)
- scheduler.py: Periodic tasks (replaces Celery Beat)

Usage (integrated - recommended):
    # Automatically started by FastAPI lifespan when DISPATCHER_ENABLED=true

Usage (standalone - legacy):
    python -m worker.marketplace_worker --user-id=1 --workers=4

Author: Claude
Date: 2026-01-21
"""

__all__ = [
    # Integrated mode (recommended)
    "JobDispatcher",
    "DispatcherConfig",
    "ClientWorker",
    # Standalone mode (legacy)
    "WorkerConfig",
    "MarketplaceWorker",
    # Shared
    "JobExecutor",
    "MarketplaceScheduler",
]
