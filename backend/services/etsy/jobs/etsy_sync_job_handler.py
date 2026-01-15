"""
Etsy Sync Job Handler

Syncs individual product from Etsy to local database.

Author: Claude
Date: 2026-01-09
"""

from models.user.marketplace_job import MarketplaceJob
from services.marketplace.direct_api_job_handler import DirectAPIJobHandler
from services.etsy.etsy_sync_service import EtsySyncService


class EtsySyncJobHandler(DirectAPIJobHandler):
    """
    Handler for syncing individual product from Etsy.

    NOTE: Currently uses stub EtsySyncService. Real implementation pending.

    Action code: sync_etsy
    """

    ACTION_CODE = "sync_etsy"

    def get_service(self) -> EtsySyncService:
        """Return Etsy sync service instance."""
        return EtsySyncService(self.db)

    def get_service_method_name(self) -> str:
        """Return method name to call on service."""
        return "sync_product"

    def create_tasks(self, job: MarketplaceJob) -> list[str]:
        """Return empty task list (DirectAPI handlers don't use tasks yet)."""
        return []
