"""
Temporal workflow orchestration module for StoFlow.

This module provides:
- TemporalConfig: Configuration for Temporal connection
- get_temporal_client: Factory for Temporal client
- TemporalWorkerManager: Worker lifecycle management
"""

from temporal.config import TemporalConfig, get_temporal_config
from temporal.client import get_temporal_client, close_temporal_client
from temporal.worker import TemporalWorkerManager

__all__ = [
    "TemporalConfig",
    "get_temporal_config",
    "get_temporal_client",
    "close_temporal_client",
    "TemporalWorkerManager",
]
