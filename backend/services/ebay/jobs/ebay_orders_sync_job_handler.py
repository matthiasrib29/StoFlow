"""
eBay Orders Sync Job Handler

Synchronizes orders from eBay Fulfillment API to local database.

Author: Claude
Date: 2026-01-07
Refactored: 2026-01-15 (Phase 4 - DirectAPI Handler Pattern)
"""

from models.user.marketplace_job import MarketplaceJob
from services.marketplace.direct_api_job_handler import DirectAPIJobHandler
from services.ebay.ebay_order_sync_service import EbayOrderSyncService


class EbayOrdersSyncJobHandler(DirectAPIJobHandler):
    """
    Handler for syncing orders from eBay.

    Uses EbayOrderSyncService to retrieve and sync order data
    from eBay Fulfillment API to the local database.

    Action code: sync_orders_ebay
    """

    ACTION_CODE = "sync_orders_ebay"

    def get_service(self) -> EbayOrderSyncService:
        """Return eBay order sync service instance."""
        return EbayOrderSyncService(self.db, self.shop_id)

    def get_service_method_name(self) -> str:
        """Return method name to call on service."""
        return "sync_orders"

    def create_tasks(self, job: MarketplaceJob) -> list[str]:
        """Return empty task list (DirectAPI handlers don't use tasks yet)."""
        return []
