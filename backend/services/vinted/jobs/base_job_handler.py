"""
Base Job Handler - Classe abstraite pour tous les handlers de jobs Vinted

Fournit l'interface commune et les utilitaires partagés.

Author: Claude
Date: 2025-12-19
"""

from abc import ABC, abstractmethod
from typing import Any

from sqlalchemy.orm import Session

from models.user.vinted_job import VintedJob
from services.plugin_task_helper import create_and_wait
from shared.logging_setup import get_logger

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

    @abstractmethod
    async def execute(self, job: VintedJob) -> dict[str, Any]:
        """
        Execute the action.

        Args:
            job: The VintedJob to execute

        Returns:
            dict: {"success": bool, ...}
        """
        pass

    async def call_plugin(
        self,
        http_method: str,
        path: str,
        payload: dict,
        product_id: int | None = None,
        timeout: int = 60,
        description: str = ""
    ) -> dict[str, Any]:
        """
        Helper pour appeler le plugin.

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
        return await create_and_wait(
            self.db,
            http_method=http_method,
            path=path,
            payload=payload,
            platform="vinted",
            product_id=product_id,
            job_id=self.job_id,
            timeout=timeout,
            description=description
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
