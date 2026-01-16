"""
Base Marketplace Handler

Abstract base class for all marketplace job handlers.
Replaces BaseJobHandler with multi-marketplace support.

Provides common utilities for:
- Creating MarketplaceTasks
- Executing plugin HTTP tasks (Vinted)
- Executing direct HTTP requests (eBay, Etsy)
- Database operations
- File operations

Author: Claude
Date: 2026-01-07
"""

import httpx
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from models.user.marketplace_job import MarketplaceJob
from models.user.marketplace_task import (
    MarketplaceTask,
    MarketplaceTaskType,
    TaskStatus,
)
from services.plugin_websocket_helper import PluginWebSocketHelper  # WebSocket architecture (2026-01-12)
from shared.config import settings
from shared.logging_setup import get_logger

logger = get_logger(__name__)


class BaseMarketplaceHandler(ABC):
    """
    Base class for all marketplace job handlers.

    Each handler implements execute() for a specific action.
    Supports multiple marketplaces (Vinted, eBay, Etsy).

    Usage:
        handler = PublishJobHandler(db, job_id=123)
        result = await handler.execute()
    """

    # Action code (to be defined in subclasses)
    ACTION_CODE: str = "base"

    def __init__(self, db: Session, job_id: int):
        """
        Initialize the handler.

        Args:
            db: SQLAlchemy session (user schema)
            job_id: MarketplaceJob ID to execute
        """
        self.db = db
        self.job_id = job_id
        self.user_id = None  # Set by MarketplaceJobProcessor for WebSocket (2026-01-12)

        # Load the job
        self.job = (
            self.db.query(MarketplaceJob).filter(MarketplaceJob.id == job_id).first()
        )
        if not self.job:
            raise ValueError(f"MarketplaceJob with id={job_id} not found")

        # Extract common fields for convenience
        self.marketplace = self.job.marketplace
        self.product_id = self.job.product_id

    @abstractmethod
    async def execute(self) -> dict[str, Any]:
        """
        Execute the job.

        Must be implemented by subclasses.

        Returns:
            dict: {
                "success": bool,
                "error": str | None,
                ...additional fields
            }
        """
        pass

    # =========================================================================
    # TASK CREATION
    # =========================================================================

    async def create_task(
        self,
        task_type: MarketplaceTaskType | str,
        description: str,
        product_id: int | None = None,
        http_method: str | None = None,
        path: str | None = None,
        payload: dict | None = None,
        platform: str | None = None,
    ) -> MarketplaceTask:
        """
        Create a child task for this job.

        Args:
            task_type: Type of task (plugin_http, direct_http, db_operation, file_operation)
            description: Human-readable description (e.g., "Upload image 1/5")
            product_id: Product ID (optional, defaults to job.product_id)
            http_method: HTTP method (POST, PUT, GET, DELETE) - for HTTP tasks
            path: API path (e.g., /api/v2/photos) - for HTTP tasks
            payload: Request payload - for HTTP tasks
            platform: Platform identifier (e.g., "vinted") - for plugin_http tasks

        Returns:
            Created MarketplaceTask instance
        """
        # Convert string to enum if needed
        if isinstance(task_type, str):
            task_type = MarketplaceTaskType(task_type)

        task = MarketplaceTask(
            job_id=self.job_id,
            task_type=task_type,
            description=description,
            status=TaskStatus.PENDING,
            product_id=product_id or self.product_id,
            http_method=http_method,
            path=path,
            payload=payload,
            platform=platform or self.marketplace,
            created_at=datetime.now(timezone.utc),
        )

        self.db.add(task)
        self.db.flush()  # Get task.id without committing

        self.log_debug(f"Task #{task.id} created: {description}")

        return task

    # =========================================================================
    # TASK EXECUTION
    # =========================================================================

    async def execute_plugin_task(
        self, task: MarketplaceTask, timeout: int = 60
    ) -> dict[str, Any]:
        """
        Execute a plugin HTTP task (Vinted only).

        Uses the browser plugin to make HTTP requests with DataDome bypass.
        This is the Strategy Pattern implementation for Vinted's communication.

        Communication Flow:
        1. Backend → WebSocket → Frontend → Plugin → Vinted API
        2. Backend ← WebSocket ← Frontend ← Plugin ← Vinted API

        Why WebSocket for Vinted:
        - Vinted uses DataDome anti-bot protection
        - Direct HTTP requests from backend are blocked
        - Plugin runs in browser context with valid cookies/headers
        - WebSocket provides real-time bidirectional communication

        Granular Commit Strategy:
        - Commits after marking task as PROCESSING (visibility)
        - Commits after marking task as SUCCESS/FAILED (progress tracking)
        - Enables frontend to poll for real-time updates

        Args:
            task: MarketplaceTask of type plugin_http
            timeout: Timeout in seconds (default: 60)

        Returns:
            dict: Plugin response with marketplace-specific data
                Example: {"vinted_id": 987, "url": "https://..."}

        Raises:
            ValueError: If task is not plugin_http type
            TimeoutError: If plugin doesn't respond within timeout
            Exception: Any error from plugin or Vinted API
        """
        if task.task_type != MarketplaceTaskType.PLUGIN_HTTP:
            raise ValueError(
                f"Task #{task.id} is not a plugin_http task (type={task.task_type.value})"
            )

        self.log_debug(f"Executing plugin task #{task.id}: {task.description}")

        # Mark task as processing
        # Commit immediately for real-time progress tracking
        task.status = TaskStatus.PROCESSING
        task.started_at = datetime.now(timezone.utc)
        self.db.commit()

        try:
            # Call plugin via WebSocket (2026-01-12)
            # PluginWebSocketHelper handles:
            # - Finding user's WebSocket connection by user_id
            # - Sending command to frontend via Socket.IO
            # - Waiting for response with configurable timeout
            # - Raising TimeoutError if no response
            result = await PluginWebSocketHelper.call_plugin_http(
                db=self.db,
                user_id=self.user_id,  # Required: identifies WebSocket connection
                http_method=task.http_method,  # POST, PUT, GET, DELETE
                path=task.path,  # Vinted API path (e.g., /api/v2/items)
                payload=task.payload,  # Request body
                timeout=timeout,  # Default 60s
                description=task.description,  # Human-readable description for logs
            )

            # Mark task as success
            # Commit immediately for real-time progress tracking
            task.status = TaskStatus.SUCCESS
            task.result = result
            task.completed_at = datetime.now(timezone.utc)
            self.db.commit()

            self.log_debug(f"Plugin task #{task.id} completed successfully")

            return result

        except Exception as e:
            # Mark task as failed
            # Commit immediately so retry logic can see the failure
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            task.completed_at = datetime.now(timezone.utc)
            self.db.commit()

            self.log_error(f"Plugin task #{task.id} failed: {e}")
            raise

    async def execute_direct_http(
        self, task: MarketplaceTask, headers: dict | None = None, timeout: int = 30
    ) -> dict[str, Any]:
        """
        Execute a direct HTTP request from backend (eBay, Etsy, Vinted CDN).

        Makes HTTP request directly without plugin using httpx async client.
        This is the Strategy Pattern implementation for eBay/Etsy communication.

        Communication Flow:
        Backend → httpx → eBay/Etsy API (OAuth 2.0)

        Why Direct HTTP for eBay/Etsy:
        - No anti-bot protection (unlike Vinted)
        - OAuth 2.0 access tokens provide authentication
        - Direct communication is faster (no WebSocket overhead)
        - Simpler architecture (no plugin dependency)

        Granular Commit Strategy:
        - Same as execute_plugin_task()
        - Commits after each status change for real-time visibility

        Args:
            task: MarketplaceTask of type direct_http
            headers: Optional HTTP headers (e.g., Authorization bearer token)
            timeout: Timeout in seconds (default: 30, shorter than plugin)

        Returns:
            dict: HTTP response JSON from marketplace API
                Example: {"sku": "SKU123", "status": "PUBLISHED"}

        Raises:
            ValueError: If task is not direct_http type
            httpx.HTTPStatusError: If response status is 4xx or 5xx
            httpx.TimeoutException: If request exceeds timeout
            httpx.RequestError: Any other HTTP error
        """
        if task.task_type != MarketplaceTaskType.DIRECT_HTTP:
            raise ValueError(
                f"Task #{task.id} is not a direct_http task (type={task.task_type.value})"
            )

        self.log_debug(f"Executing direct HTTP task #{task.id}: {task.description}")

        # Mark task as processing
        # Commit immediately for real-time progress tracking
        task.status = TaskStatus.PROCESSING
        task.started_at = datetime.now(timezone.utc)
        self.db.commit()

        try:
            # Use httpx async client for non-blocking I/O
            # Timeout is shorter than plugin (30s vs 60s) since no browser overhead
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.request(
                    method=task.http_method,  # POST, PUT, GET, DELETE, PATCH
                    url=task.path,  # Full URL (e.g., https://api.ebay.com/sell/...)
                    json=task.payload,  # Request body (serialized to JSON)
                    headers=headers,  # Auth headers (e.g., Authorization: Bearer ...)
                )
                # Raise exception for 4xx/5xx status codes
                response.raise_for_status()

                # Parse JSON response
                result = response.json()

                # Mark task as success
                # Commit immediately for real-time progress tracking
                task.status = TaskStatus.SUCCESS
                task.result = result
                task.completed_at = datetime.now(timezone.utc)
                self.db.commit()

                self.log_debug(f"Direct HTTP task #{task.id} completed successfully")

                return result

        except Exception as e:
            # Mark task as failed
            # Commit immediately so retry logic can see the failure
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            task.completed_at = datetime.now(timezone.utc)
            self.db.commit()

            self.log_error(f"Direct HTTP task #{task.id} failed: {e}")
            raise

    # =========================================================================
    # COMPATIBILITY LAYER (for existing handlers)
    # =========================================================================

    async def call_plugin(
        self,
        http_method: str,
        path: str,
        payload: dict,
        product_id: int | None = None,
        timeout: int = 60,
        description: str = "",
    ) -> dict[str, Any]:
        """
        Helper for calling the plugin (backward compatibility).

        Creates a plugin_http task and executes it.

        Args:
            http_method: GET, POST, PUT, DELETE
            path: API path (e.g., /api/v2/items)
            payload: Request body
            product_id: Product ID for tracking
            timeout: Timeout in seconds
            description: Description for logs

        Returns:
            dict: Plugin response
        """
        # Create task
        task = await self.create_task(
            task_type=MarketplaceTaskType.PLUGIN_HTTP,
            description=description or f"{http_method} {path}",
            product_id=product_id,
            http_method=http_method,
            path=path,
            payload=payload,
            platform=self.marketplace,
        )

        # Execute task
        return await self.execute_plugin_task(task, timeout=timeout)

    # =========================================================================
    # LOGGING HELPERS
    # =========================================================================

    def log_start(self, message: str):
        """Log start of operation."""
        logger.info(f"[{self.ACTION_CODE.upper()}] {message}")

    def log_success(self, message: str):
        """Log successful operation."""
        logger.info(f"[{self.ACTION_CODE.upper()}] ✓ {message}")

    def log_error(self, message: str, exc_info: bool = False):
        """Log error."""
        logger.error(
            f"[{self.ACTION_CODE.upper()}] ✗ {message}", exc_info=exc_info
        )

    def log_debug(self, message: str):
        """Log debug info."""
        logger.debug(f"[{self.ACTION_CODE.upper()}] {message}")

    def log_warning(self, message: str):
        """Log warning."""
        logger.warning(f"[{self.ACTION_CODE.upper()}] ⚠ {message}")
