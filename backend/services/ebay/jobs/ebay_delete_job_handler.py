"""
eBay Delete Job Handler

Deletes/ends an eBay listing (withdraws offer and optionally deletes inventory item).

Author: Claude
Date: 2026-01-09
"""

from typing import Any

from sqlalchemy.orm import Session

from models.user.marketplace_job import MarketplaceJob
from services.vinted.jobs.base_job_handler import BaseJobHandler
from services.ebay.ebay_publication_service import EbayPublicationService
from shared.logging_setup import get_logger

logger = get_logger(__name__)


class EbayDeleteJobHandler(BaseJobHandler):
    """
    Handler for deleting eBay listings.

    Withdraws offer (ends listing) and optionally deletes inventory item.

    Action code: delete_ebay
    """

    ACTION_CODE = "delete_ebay"

    async def execute(self, job: MarketplaceJob) -> dict[str, Any]:
        """
        Delete eBay listing (end offer).

        Args:
            job: MarketplaceJob with product_id

        Returns:
            dict: {
                "success": bool,
                "ebay_listing_id": str (if success),
                "deleted": bool (if success),
                "error": str (if failure)
            }
        """
        product_id = job.product_id

        if not product_id:
            self.log_error("product_id is required")
            return {"success": False, "error": "product_id required"}

        self.log_start(f"Deleting eBay listing for product {product_id}")

        try:
            # Use existing publication service (delete method)
            service = EbayPublicationService(self.db)
            result = await service.delete_product(product_id)

            if result.get("success", False):
                ebay_listing_id = result.get("ebay_listing_id", "unknown")

                self.log_success(
                    f"Deleted product {product_id} → "
                    f"eBay listing {ebay_listing_id} ended"
                )
            else:
                error_msg = result.get("error", "Unknown error")
                self.log_error(f"Failed to delete product {product_id}: {error_msg}")

            return result

        except Exception as e:
            error_msg = f"Exception deleting product {product_id}: {e}"
            self.log_error(error_msg, exc_info=True)
            return {"success": False, "error": str(e)}
