"""
eBay Sync Job Handler

Syncs a single product from eBay inventory to local database.

Author: Claude
Date: 2026-01-09
Refactored: 2026-01-15 (Phase 4 - DirectAPI Handler Pattern)
"""

from models.user.marketplace_job import MarketplaceJob
from services.marketplace.direct_api_job_handler import DirectAPIJobHandler
from services.ebay.ebay_sync_service import EbaySyncService


class EbaySyncJobHandler(DirectAPIJobHandler):
    """
    Handler for syncing products from eBay inventory.

    Uses EbaySyncService to retrieve and sync product data
    from eBay to the local database.

    Action code: sync_ebay
    """

    ACTION_CODE = "sync_ebay"

    def get_service(self) -> EbaySyncService:
        """Return eBay sync service instance."""
        return EbaySyncService(self.db)

    def get_service_method_name(self) -> str:
        """Return method name to call on service."""
        return "sync_product"

    def create_tasks(self, job: MarketplaceJob) -> list[str]:
        """Return empty task list (DirectAPI handlers don't use tasks yet)."""
        return []
