"""
Base Job Handler - Classe abstraite pour tous les handlers de jobs Vinted

Fournit l'interface commune et les utilitaires partagés.

Author: Claude
Date: 2025-12-19
Updated: 2026-01-08 - Migrated to WebSocket communication
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, List, Optional

from sqlalchemy.orm import Session

from models.user.marketplace_job import MarketplaceJob
from models.user.marketplace_task import MarketplaceTask, TaskStatus
from services.plugin_websocket_helper import PluginWebSocketHelper
from shared.logging import get_logger

logger = get_logger(__name__)


class BaseJobHandler(ABC):
    """
    Classe de base pour tous les handlers de jobs Vinted.

    Chaque handler implémente execute() pour une action spécifique.

    Usage:
        handler = PublishJobHandler(db, shop_id=123, job_id=1)
        result = await handler.execute(product_id=456)
    """

    # Code de l'action (à définir dans les sous-classes)
    ACTION_CODE: str = "base"

    def __init__(
        self,
        db: Session,
        shop_id: int | None = None,
        job_id: int | None = None
    ):
        """
        Initialize the handler.

        Args:
            db: SQLAlchemy session (user schema)
            shop_id: Vinted shop ID
            job_id: Parent job ID for task tracking
        """
        self.db = db
        self.shop_id = shop_id
        self.job_id = job_id
        self.user_id: Optional[int] = None  # Must be set before execute()

        # TaskOrchestrator instance for task management (lazy import to avoid circular import)
        from services.marketplace.task_orchestrator import TaskOrchestrator
        self.orchestrator = TaskOrchestrator(db)

    @abstractmethod
    async def execute(self, job: MarketplaceJob) -> dict[str, Any]:
        """
        Execute the action.

        Args:
            job: The MarketplaceJob to execute

        Returns:
            dict: {"success": bool, ...}
        """
        pass

    @abstractmethod
    def create_tasks(self, job: MarketplaceJob) -> List[str]:
        """
        Define the list of task names for this job type.

        Each handler must implement this to define its execution steps.
        TaskOrchestrator will create MarketplaceTask objects from these names.

        Args:
            job: The MarketplaceJob to create tasks for

        Returns:
            List of task names in execution order (e.g., ["Validate product", "Upload image 1/3", "Publish listing"])

        Example:
            def create_tasks(self, job: MarketplaceJob) -> List[str]:
                # For a publish job with 3 images
                return [
                    "Validate product data",
                    "Upload image 1/3",
                    "Upload image 2/3",
                    "Upload image 3/3",
                    "Create Vinted listing"
                ]
        """
        pass

    def execute_with_tasks(
        self,
        job: MarketplaceJob,
        handlers: dict[str, Callable[[MarketplaceTask], dict]]
    ) -> dict[str, Any]:
        """
        Execute job using TaskOrchestrator with retry intelligence.

        This is a helper method that handlers CAN use (but are not required to).
        It provides automatic task creation, execution tracking, and retry intelligence.

        Workflow:
        1. Create tasks using handler's create_tasks() method
        2. Execute tasks in order with TaskOrchestrator
        3. Skip completed tasks on retry
        4. Stop on first failure

        Args:
            job: MarketplaceJob to execute
            handlers: Dict mapping task name -> handler function
                     Each handler receives a MarketplaceTask and returns result dict

        Returns:
            dict: {
                "success": bool,
                "tasks_completed": int,
                "tasks_total": int,
                "error": str | None
            }

        Example:
            async def execute(self, job: MarketplaceJob) -> dict[str, Any]:
                # Define handlers for each task
                handlers = {
                    "Validate product data": self._validate_product,
                    "Upload image 1/3": lambda task: self._upload_image(task, 0),
                    "Upload image 2/3": lambda task: self._upload_image(task, 1),
                    "Upload image 3/3": lambda task: self._upload_image(task, 2),
                    "Create Vinted listing": self._create_listing,
                }

                # Execute with automatic retry intelligence
                return await self.execute_with_tasks(job, handlers)
        """
        # 1. Create tasks if not already created
        existing_tasks = self.db.query(MarketplaceTask).filter(
            MarketplaceTask.job_id == job.id
        ).all()

        if not existing_tasks:
            task_names = self.create_tasks(job)
            tasks = self.orchestrator.create_tasks(job, task_names)
            self.log_debug(f"Created {len(tasks)} tasks for job #{job.id}")
        else:
            tasks = existing_tasks
            self.log_debug(f"Found {len(tasks)} existing tasks for job #{job.id}")

        # 2. Execute tasks with retry intelligence
        success = self.orchestrator.execute_job_with_tasks(job, tasks, handlers)

        # 3. Count completed tasks
        completed = sum(1 for t in tasks if t.status == TaskStatus.SUCCESS)

        # 4. Return result
        if success:
            return {
                "success": True,
                "tasks_completed": completed,
                "tasks_total": len(tasks)
            }
        else:
            # Find first failed task for error message
            failed_task = next((t for t in tasks if t.status == TaskStatus.FAILED), None)
            return {
                "success": False,
                "tasks_completed": completed,
                "tasks_total": len(tasks),
                "error": failed_task.error_message if failed_task else "Unknown error"
            }

    async def call_plugin(
        self,
        http_method: str,
        path: str,
        payload: dict | None = None,
        params: dict | None = None,
        product_id: int | None = None,
        timeout: int = 60,
        description: str = ""
    ) -> dict[str, Any]:
        """
        Helper pour appeler le plugin via WebSocket (Vinted uniquement).

        Args:
            http_method: GET, POST, PUT, DELETE
            path: API path (e.g., /api/v2/items)
            payload: Request body
            params: Query parameters
            product_id: Product ID for tracking
            timeout: Timeout in seconds
            description: Description for logs

        Returns:
            dict: Plugin response

        Raises:
            RuntimeError: If user_id not set
        """
        if not self.user_id:
            raise RuntimeError("user_id must be set before calling plugin")

        return await PluginWebSocketHelper.call_plugin_http(
            db=self.db,
            user_id=self.user_id,
            http_method=http_method,
            path=path,
            payload=payload,
            params=params,
            timeout=timeout,
            description=description or f"{self.ACTION_CODE} - {http_method} {path}"
        )

    async def call_http(
        self,
        base_url: str,
        http_method: str,
        path: str,
        headers: dict,
        payload: Optional[dict] = None,
        params: Optional[dict] = None,
        timeout: int = 60,
        description: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Helper pour appeler API marketplace directement (eBay, Etsy).

        This method makes direct HTTP requests to marketplace APIs using OAuth tokens.
        Used by eBay and Etsy handlers (not Vinted, which uses WebSocket via plugin).

        Args:
            base_url: API base URL (e.g., 'https://api.ebay.com')
            http_method: GET, POST, PUT, DELETE
            path: API path (e.g., '/sell/inventory/v1/inventory_item')
            headers: HTTP headers (Authorization, Content-Type, etc.)
            payload: Request body (will be serialized to JSON)
            params: Query parameters
            timeout: Timeout in seconds
            description: Description for logs

        Returns:
            dict: API response (parsed JSON)

        Raises:
            httpx.HTTPStatusError: If request fails (4xx, 5xx)
            httpx.TimeoutException: If request times out
            httpx.RequestError: If request cannot be sent

        Example:
            result = await self.call_http(
                base_url="https://api.ebay.com",
                http_method="POST",
                path="/sell/inventory/v1/inventory_item/SKU123",
                headers={"Authorization": f"Bearer {token}"},
                payload={"availability": {"shipToLocationAvailability": {...}}}
            )
        """
        from services.marketplace_http_helper import MarketplaceHttpHelper

        return await MarketplaceHttpHelper.call_api(
            base_url=base_url,
            http_method=http_method,
            path=path,
            headers=headers,
            payload=payload,
            params=params,
            timeout=timeout,
            description=description or f"{self.ACTION_CODE} - {http_method} {path}"
        )

    def log_start(self, message: str):
        """Log start of operation."""
        logger.info(f"[{self.ACTION_CODE.upper()}] {message}")

    def log_success(self, message: str):
        """Log successful operation."""
        logger.info(f"[{self.ACTION_CODE.upper()}] ✓ {message}")

    def log_error(self, message: str, exc_info: bool = False):
        """Log error."""
        logger.error(
            f"[{self.ACTION_CODE.upper()}] ✗ {message}",
            exc_info=exc_info
        )

    def log_debug(self, message: str):
        """Log debug info."""
        logger.debug(f"[{self.ACTION_CODE.upper()}] {message}")
