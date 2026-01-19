"""
Orders Job Handler - Synchronisation des commandes Vinted

Thin handler that delegates to VintedOrdersService.

Modes:
- Default: sync all orders via /my_orders
- Optional: sync by month via /wallet/invoices

Note: /my_orders is default because /wallet/invoices doesn't capture direct card payments.

Author: Claude
Date: 2025-12-19
Updated: 2026-01-15 - Refactored to follow standard pattern
"""

from typing import Any

from sqlalchemy.orm import Session

from models.user.marketplace_job import MarketplaceJob
from services.vinted.vinted_orders_service import VintedOrdersService
from .base_job_handler import BaseJobHandler


class OrdersJobHandler(BaseJobHandler):
    """
    Handler for synchronizing Vinted orders.

    Delegates all business logic to VintedOrdersService.
    """

    ACTION_CODE = "orders"

    def create_tasks(self, job: MarketplaceJob) -> list[str]:
        """
        Define task steps for order synchronization.

        Args:
            job: MarketplaceJob

        Returns:
            List of task step descriptions
        """
        params = job.result_data if isinstance(job.result_data, dict) else {}
        year = params.get('year')
        month = params.get('month')

        if year and month:
            return [
                f"Fetch orders from {year}-{month:02d}",
                "Parse order transactions",
                "Save to database"
            ]
        else:
            return [
                "Fetch all orders from Vinted",
                "Parse order transactions",
                "Save to database"
            ]

    def get_service(self) -> VintedOrdersService:
        """
        Get service instance for order operations.

        Returns:
            VintedOrdersService instance
        """
        return VintedOrdersService(self.db)

    async def execute(self, job: MarketplaceJob) -> dict[str, Any]:
        """
        Execute order synchronization by delegating to service.

        Args:
            job: MarketplaceJob with optional result_data:
                - {} or None: sync all orders via /my_orders (default)
                - {"year": int, "month": int}: sync by month via /wallet/invoices

        Returns:
            dict: {
                "success": bool,
                "orders_synced": int,
                "mode": "classic" | "month",
                "error": str | None
            }
        """
        # Extract parameters from job
        params = job.result_data if isinstance(job.result_data, dict) else {}
        year = params.get('year')
        month = params.get('month')

        try:
            mode = f"month {year}-{month:02d}" if year and month else "all orders"
            self.log_start(f"Sync orders ({mode})")

            # Delegate to service
            service = self.get_service()
            result = await service.sync_orders(
                shop_id=self.shop_id or 0,
                user_id=self.user_id,
                params=params
            )

            if result.get("success"):
                synced = result.get("orders_synced", 0)
                self.log_success(f"{synced} orders synced")
            else:
                self.log_error(f"Sync failed: {result.get('error')}")

            return result

        except Exception as e:
            self.log_error(f"Orders sync error: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
