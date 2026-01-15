"""
Etsy Orders Sync Job Handler

Syncs orders for a product from Etsy to local database.

Author: Claude
Date: 2026-01-09
"""

from models.user.marketplace_job import MarketplaceJob
from services.marketplace.direct_api_job_handler import DirectAPIJobHandler
from services.etsy.etsy_order_sync_service import EtsyOrderSyncService


class EtsyOrdersSyncJobHandler(DirectAPIJobHandler):
    """
    Handler for syncing orders from Etsy.

    NOTE: Currently uses stub EtsyOrderSyncService. Real implementation pending.

    Action code: sync_orders_etsy
    """

    ACTION_CODE = "sync_orders_etsy"

    def get_service(self) -> EtsyOrderSyncService:
        """Return Etsy order sync service instance."""
        return EtsyOrderSyncService(self.db)

    def get_service_method_name(self) -> str:
        """Return method name to call on service."""
        return "sync_orders"

    def create_tasks(self, job: MarketplaceJob) -> list[str]:
        """Return empty task list (DirectAPI handlers don't use tasks yet)."""
        return []
