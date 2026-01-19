"""
Publish Job Handler - Publication de produits sur Vinted

Delegates business logic to VintedPublicationService.
Handler is responsible for orchestration and logging only.

Author: Claude
Date: 2025-12-19
Updated: 2026-01-15 - Migrated to service delegation pattern
"""

from models.user.marketplace_job import MarketplaceJob
from services.vinted.vinted_publication_service import VintedPublicationService
from services.vinted.vinted_job_handler import VintedJobHandler


class PublishJobHandler(VintedJobHandler):
    """
    Handler pour la publication de produits sur Vinted.

    Délègue la logique métier à VintedPublicationService.
    """

    ACTION_CODE = "publish"

    def get_service(self) -> VintedPublicationService:
        """Return VintedPublicationService instance."""
        return VintedPublicationService(self.db)

    def get_service_method_name(self) -> str:
        """Return service method name to call."""
        return "publish_product"

    def create_tasks(self, job: MarketplaceJob) -> list[str]:
        """Create task list for publication workflow."""
        return [
            "Validate product",
            "Map attributes",
            "Calculate price",
            "Upload images",
            "Create listing"
        ]
