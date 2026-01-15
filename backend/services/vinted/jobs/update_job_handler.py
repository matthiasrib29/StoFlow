"""
Update Job Handler - Mise à jour de produits sur Vinted

Delegates business logic to VintedUpdateService.
Handler is responsible for orchestration and logging only.

Author: Claude
Date: 2025-12-19
Updated: 2026-01-15 - Migrated to service delegation pattern
"""

from models.user.marketplace_job import MarketplaceJob
from services.vinted.vinted_update_service import VintedUpdateService
from services.vinted.vinted_job_handler import VintedJobHandler


class UpdateJobHandler(VintedJobHandler):
    """
    Handler pour la mise à jour de produits sur Vinted.

    Délègue la logique métier à VintedUpdateService.
    """

    ACTION_CODE = "update"

    def get_service(self) -> VintedUpdateService:
        """Return VintedUpdateService instance."""
        return VintedUpdateService(self.db)

    def get_service_method_name(self) -> str:
        """Return service method name to call."""
        return "update_product"

    def create_tasks(self, job: MarketplaceJob) -> list[str]:
        """Create task list for update workflow."""
        return [
            "Validate product",
            "Recalculate attributes",
            "Update listing"
        ]
