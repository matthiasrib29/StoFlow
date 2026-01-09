"""
eBay Sync Job Handler

Syncs all products from eBay inventory to local database.
This is a batch operation that retrieves all inventory items.

Author: Claude
Date: 2026-01-09
"""

from typing import Any

from sqlalchemy.orm import Session

from models.user.marketplace_job import MarketplaceJob
from services.vinted.jobs.base_job_handler import BaseJobHandler
from services.ebay.ebay_importer import EbayImporter
from shared.logging_setup import get_logger

logger = get_logger(__name__)


class EbaySyncJobHandler(BaseJobHandler):
    """
    Handler for syncing all products from eBay inventory.

    This is a batch operation that retrieves inventory items from eBay
    and syncs them with the local database.

    Action code: sync_ebay
    """

    ACTION_CODE = "sync_ebay"

    async def execute(self, job: MarketplaceJob) -> dict[str, Any]:
        """
        Sync all products from eBay inventory.

        Args:
            job: MarketplaceJob (product_id not required for batch sync)

        Returns:
            dict: {
                "success": bool,
                "synced_count": int (if success),
                "created_count": int (if success),
                "updated_count": int (if success),
                "error": str (if failure)
            }
        """
        self.log_start("Syncing products from eBay inventory")

        try:
            # Use existing importer service
            importer = EbayImporter(self.db)
            result = await importer.sync_all_products()

            if result.get("success", False):
                synced_count = result.get("synced_count", 0)
                created_count = result.get("created_count", 0)
                updated_count = result.get("updated_count", 0)

                self.log_success(
                    f"Synced {synced_count} products from eBay "
                    f"(created: {created_count}, updated: {updated_count})"
                )
            else:
                error_msg = result.get("error", "Unknown error")
                self.log_error(f"Failed to sync eBay products: {error_msg}")

            return result

        except Exception as e:
            error_msg = f"Exception syncing eBay products: {e}"
            self.log_error(error_msg, exc_info=True)
            return {"success": False, "error": str(e)}
