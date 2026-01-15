"""
Delete Job Handler - Suppression de produits sur Vinted

Delegates business logic to VintedDeletionService.
Handler is responsible for orchestration and logging only.

Author: Claude
Date: 2025-12-19
Updated: 2026-01-15 - Migrated to service delegation pattern
"""

from typing import Any

from sqlalchemy.orm import Session

from models.user.marketplace_job import MarketplaceJob
from services.vinted.vinted_deletion_service import VintedDeletionService
from .base_job_handler import BaseJobHandler


class DeleteJobHandler(BaseJobHandler):
    """
    Handler pour la suppression de produits sur Vinted.

    Délègue la logique métier à VintedDeletionService.
    """

    ACTION_CODE = "delete"

    async def execute(self, job: MarketplaceJob) -> dict[str, Any]:
        """
        Supprime un produit sur Vinted.

        Args:
            job: MarketplaceJob contenant product_id

        Returns:
            dict: {"success": bool, "product_id": int, "error": str | None}
        """
        product_id = job.product_id
        if not product_id:
            return {"success": False, "error": "product_id required for delete"}

        # Extract check_conditions from job if present
        check_conditions = True
        if job.result_data and isinstance(job.result_data, dict):
            check_conditions = job.result_data.get('check_conditions', True)

        try:
            self.log_start(f"Suppression produit #{product_id}")

            # Delegate to service
            service = VintedDeletionService(self.db)
            result = await service.delete_product(
                product_id=product_id,
                user_id=self.user_id,
                shop_id=self.shop_id,
                job_id=self.job_id,
                check_conditions=check_conditions
            )

            if result.get("success"):
                vinted_id = result.get("vinted_id")
                self.log_success(f"Produit #{product_id} supprimé (vinted_id={vinted_id})")
            else:
                error = result.get("error")
                self.log_error(f"Produit #{product_id}: {error}")

            return result

        except Exception as e:
            self.log_error(f"Produit #{product_id}: {e}", exc_info=True)
            return {"success": False, "product_id": product_id, "error": str(e)}
