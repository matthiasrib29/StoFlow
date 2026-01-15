"""
Publish Job Handler - Publication de produits sur Vinted

Delegates business logic to VintedPublicationService.
Handler is responsible for orchestration and logging only.

Author: Claude
Date: 2025-12-19
Updated: 2026-01-15 - Migrated to service delegation pattern
"""

from typing import Any

from sqlalchemy.orm import Session

from models.user.marketplace_job import MarketplaceJob
from services.vinted.vinted_publication_service import VintedPublicationService
from .base_job_handler import BaseJobHandler


class PublishJobHandler(BaseJobHandler):
    """
    Handler pour la publication de produits sur Vinted.

    Délègue la logique métier à VintedPublicationService.
    """

    ACTION_CODE = "publish"

    async def execute(self, job: MarketplaceJob) -> dict[str, Any]:
        """
        Publie un produit sur Vinted.

        Args:
            job: MarketplaceJob contenant product_id

        Returns:
            dict: {
                "success": bool,
                "vinted_id": int | None,
                "url": str | None,
                "product_id": int,
                "error": str | None
            }
        """
        product_id = job.product_id
        if not product_id:
            return {"success": False, "error": "product_id required for publish"}

        try:
            self.log_start(f"Publication produit #{product_id}")

            # Delegate to service
            service = VintedPublicationService(self.db)
            result = await service.publish_product(
                product_id=product_id,
                user_id=self.user_id,
                shop_id=self.shop_id,
                job_id=self.job_id
            )

            if result.get("success"):
                vinted_id = result.get("vinted_id")
                self.log_success(f"Produit #{product_id} -> vinted_id={vinted_id}")
            else:
                error = result.get("error")
                self.log_error(f"Produit #{product_id}: {error}")

            return result

        except Exception as e:
            self.log_error(f"Produit #{product_id}: {e}", exc_info=True)
            return {
                "success": False,
                "vinted_id": None,
                "url": None,
                "product_id": product_id,
                "error": str(e)
            }
