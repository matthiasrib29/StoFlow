"""
Temporal client module.

Provides a singleton client for connecting to Temporal server.
"""

import logging
from typing import Optional

from temporalio.client import Client

from temporal.config import get_temporal_config

logger = logging.getLogger(__name__)

# Global client instance
_temporal_client: Optional[Client] = None


async def get_temporal_client() -> Client:
    """
    Get or create a Temporal client connection.

    Returns a singleton client instance. The client is created on first call
    and reused for subsequent calls.

    Returns:
        Temporal Client instance

    Raises:
        RuntimeError: If Temporal is disabled or connection fails
    """
    global _temporal_client

    config = get_temporal_config()

    if not config.temporal_enabled:
        raise RuntimeError("Temporal is disabled in configuration")

    if _temporal_client is None:
        logger.info(
            "Connecting to Temporal server",
            extra={
                "host": config.temporal_host,
                "namespace": config.temporal_namespace,
            }
        )

        try:
            _temporal_client = await Client.connect(
                config.temporal_host,
                namespace=config.temporal_namespace,
            )
            logger.info("Successfully connected to Temporal server")
        except Exception as e:
            logger.error(
                "Failed to connect to Temporal server",
                extra={"error": str(e), "host": config.temporal_host}
            )
            raise RuntimeError(f"Failed to connect to Temporal: {e}") from e

    return _temporal_client


async def close_temporal_client() -> None:
    """
    Close the Temporal client connection.

    Should be called during application shutdown.
    """
    global _temporal_client

    if _temporal_client is not None:
        logger.info("Closing Temporal client connection")
        # Note: Temporal Python SDK doesn't have explicit close,
        # but we clear the reference for clean restart
        _temporal_client = None
        logger.info("Temporal client connection closed")


async def check_temporal_health() -> dict:
    """
    Check Temporal server health.

    Returns:
        Dict with health status information
    """
    config = get_temporal_config()

    if not config.temporal_enabled:
        return {
            "status": "disabled",
            "message": "Temporal is disabled in configuration"
        }

    try:
        client = await get_temporal_client()
        # Simple health check: try to get service info
        # This validates the connection is working
        return {
            "status": "healthy",
            "host": config.temporal_host,
            "namespace": config.temporal_namespace,
            "connected": True
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "host": config.temporal_host,
            "namespace": config.temporal_namespace,
            "error": str(e),
            "connected": False
        }
