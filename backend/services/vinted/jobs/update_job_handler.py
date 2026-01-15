"""
Update Job Handler - Mise à jour de produits sur Vinted

Delegates business logic to VintedUpdateService.
Handler is responsible for orchestration and logging only.

Author: Claude
Date: 2025-12-19
Updated: 2026-01-15 - Migrated to service delegation pattern
"""

from typing import Any

from sqlalchemy.orm import Session

from models.user.marketplace_job import MarketplaceJob
from services.vinted.vinted_update_service import VintedUpdateService
from .base_job_handler import BaseJobHandler


class UpdateJobHandler(BaseJobHandler):
    """
    Handler pour la mise à jour de produits sur Vinted.

    Délègue la logique métier à VintedUpdateService.
    """

    ACTION_CODE = "update"

    async def execute(self, job: MarketplaceJob) -> dict[str, Any]:
        """
        Met à jour un produit sur Vinted.

        Args:
            job: MarketplaceJob contenant product_id

        Returns:
            dict: {"success": bool, "product_id": int, "error": str | None}
        """
        product_id = job.product_id
        if not product_id:
            return {"success": False, "error": "product_id required for update"}

        try:
            self.log_start(f"Mise à jour produit #{product_id}")

            # Delegate to service
            service = VintedUpdateService(self.db)
            result = await service.update_product(
                product_id=product_id,
                user_id=self.user_id,
                shop_id=self.shop_id,
                job_id=self.job_id
            )

            if result.get("success"):
                old_price = result.get("old_price", 0)
                new_price = result.get("new_price", 0)
                self.log_success(
                    f"Produit #{product_id} mis à jour "
                    f"(prix: {old_price}EUR -> {new_price}EUR)"
                )
            else:
                error = result.get("error")
                self.log_error(f"Produit #{product_id}: {error}")

            return result

        except Exception as e:
            self.log_error(f"Produit #{product_id}: {e}", exc_info=True)
            return {"success": False, "product_id": product_id, "error": str(e)}
