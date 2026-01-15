"""
Sync Job Handler - Synchronisation des produits depuis l'API Vinted

Thin handler that delegates to VintedSyncService.

Author: Claude
Date: 2025-12-19
Updated: 2026-01-15 - Refactored to follow standard pattern
"""

from typing import Any

from sqlalchemy.orm import Session

from models.user.marketplace_job import MarketplaceJob
from services.vinted.vinted_sync_service import VintedSyncService
from .base_job_handler import BaseJobHandler


class SyncJobHandler(BaseJobHandler):
    """
    Handler for synchronizing products from Vinted API.

    Delegates all business logic to VintedSyncService.
    """

    ACTION_CODE = "sync"

    def create_tasks(self, job: MarketplaceJob) -> list[str]:
        """
        Define task steps for product synchronization.

        Args:
            job: MarketplaceJob

        Returns:
            List of task step descriptions
        """
        return [
            "Fetch products from Vinted API",
            "Import new products to database",
            "Update existing products",
            "Enrich descriptions"
        ]

    def get_service(self) -> VintedSyncService:
        """
        Get service instance for sync operations.

        Returns:
            VintedSyncService instance
        """
        return VintedSyncService(self.db)

    async def execute(self, job: MarketplaceJob) -> dict[str, Any]:
        """
        Execute product synchronization by delegating to service.

        Args:
            job: MarketplaceJob (product_id not used)

        Returns:
            dict: {
                "success": bool,
                "products_synced": int,
                "imported": int,
                "updated": int,
                "errors": int,
                "error": str | None
            }
        """
        try:
            if not self.shop_id:
                return {"success": False, "error": "shop_id required for sync"}

            self.log_start(f"Sync products (shop_id={self.shop_id})")

            # Delegate to service
            service = self.get_service()
            result = await service.sync_products(
                shop_id=self.shop_id,
                user_id=self.user_id,
                job=job
            )

            if result.get("success"):
                imported = result.get("imported", 0)
                updated = result.get("updated", 0)
                self.log_success(f"{imported} imported, {updated} updated")
            else:
                self.log_error(f"Sync failed: {result.get('error')}")

            return result

        except Exception as e:
            self.log_error(f"Sync error: {e}", exc_info=True)
            return {"success": False, "error": str(e)}


