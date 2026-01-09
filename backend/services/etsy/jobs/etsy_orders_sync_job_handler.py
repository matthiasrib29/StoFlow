"""
Etsy Orders Sync Job Handler

Syncs orders from Etsy to local database.
This is a batch operation that retrieves recent shop receipts.

Author: Claude
Date: 2026-01-09
"""

from typing import Any

from sqlalchemy.orm import Session

from models.user.marketplace_job import MarketplaceJob
from services.vinted.jobs.base_job_handler import BaseJobHandler
from services.etsy.etsy_polling_service import EtsyPollingService
from shared.logging_setup import get_logger

logger = get_logger(__name__)


class EtsyOrdersSyncJobHandler(BaseJobHandler):
    """
    Handler for syncing orders from Etsy.

    This is a batch operation that retrieves shop receipts (orders) from Etsy
    and syncs them with the local database.

    Action code: sync_orders_etsy
    """

    ACTION_CODE = "sync_orders_etsy"

    async def execute(self, job: MarketplaceJob) -> dict[str, Any]:
        """
        Sync orders from Etsy shop.

        Args:
            job: MarketplaceJob (product_id not required for batch sync)

        Returns:
            dict: {
                "success": bool,
                "synced_count": int (if success),
                "new_orders_count": int (if success),
                "error": str (if failure)
            }
        """
        self.log_start("Syncing orders from Etsy shop")

        try:
            # Use existing polling service
            service = EtsyPollingService(self.db)
            result = await service.sync_orders()

            if result.get("success", False):
                synced_count = result.get("synced_count", 0)
                new_orders_count = result.get("new_orders_count", 0)

                self.log_success(
                    f"Synced {synced_count} orders from Etsy "
                    f"(new: {new_orders_count})"
                )
            else:
                error_msg = result.get("error", "Unknown error")
                self.log_error(f"Failed to sync Etsy orders: {error_msg}")

            return result

        except Exception as e:
            error_msg = f"Exception syncing Etsy orders: {e}"
            self.log_error(error_msg, exc_info=True)
            return {"success": False, "error": str(e)}
