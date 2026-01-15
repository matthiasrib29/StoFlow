"""
Delete Job Handler - Suppression de produits sur Vinted

Delegates business logic to VintedDeletionService.
Handler is responsible for orchestration and logging only.

Author: Claude
Date: 2025-12-19
Updated: 2026-01-15 - Migrated to service delegation pattern
"""

from typing import Any

from models.user.marketplace_job import MarketplaceJob
from services.vinted.vinted_deletion_service import VintedDeletionService
from services.vinted.vinted_job_handler import VintedJobHandler


class DeleteJobHandler(VintedJobHandler):
    """
    Handler pour la suppression de produits sur Vinted.

    Délègue la logique métier à VintedDeletionService.
    """

    ACTION_CODE = "delete"

    def get_service(self) -> VintedDeletionService:
        """Return VintedDeletionService instance."""
        return VintedDeletionService(self.db)

    def get_service_method_name(self) -> str:
        """Return service method name to call."""
        return "delete_product"

    def create_tasks(self, job: MarketplaceJob) -> list[str]:
        """Create task list for deletion workflow."""
        return [
            "Check conditions",
            "Archive stats",
            "Delete listing"
        ]

    async def execute(self, job: MarketplaceJob) -> dict[str, Any]:
        """Override to handle check_conditions parameter."""
        product_id = job.product_id
        if not product_id:
            return {"success": False, "error": "product_id required"}

        # Extract check_conditions from job data
        check_conditions = job.result_data.get("check_conditions", True) if job.result_data else True

        try:
            self.log_start(f"Delete product #{product_id}")

            service = self.get_service()
            result = await service.delete_product(
                product_id=product_id,
                user_id=self.user_id,
                shop_id=self.shop_id,
                job_id=self.job_id,
                check_conditions=check_conditions
            )

            if result.get("success"):
                self.log_success(f"Product #{product_id} deleted")
            else:
                self.log_error(f"Product #{product_id}: {result.get('error')}")

            return result
        except Exception as e:
            self.log_error(f"Product #{product_id}: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
