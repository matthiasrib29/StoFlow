"""
eBay Publish Job Handler

Publishes a product to eBay using eBay Inventory API.
Creates inventory item and offer for the product.

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


class EbayPublishJobHandler(BaseJobHandler):
    """
    Handler for publishing products to eBay.

    Uses EbayPublicationService to create inventory item and offer.
    This creates a new listing on eBay marketplace.

    Action code: publish_ebay
    """

    ACTION_CODE = "publish_ebay"

    async def execute(self, job: MarketplaceJob) -> dict[str, Any]:
        """
        Publish product to eBay.

        Args:
            job: MarketplaceJob with product_id

        Returns:
            dict: {
                "success": bool,
                "ebay_listing_id": str (if success),
                "ebay_sku": str (if success),
                "error": str (if failure)
            }
        """
        product_id = job.product_id

        if not product_id:
            self.log_error("product_id is required")
            return {"success": False, "error": "product_id required"}

        self.log_start(f"Publishing product {product_id} to eBay")

        try:
            # Use existing publication service
            service = EbayPublicationService(self.db)
            result = await service.publish_product(product_id)

            if result.get("success", False):
                ebay_listing_id = result.get("ebay_listing_id", "unknown")
                ebay_sku = result.get("ebay_sku", "unknown")

                self.log_success(
                    f"Published product {product_id} → "
                    f"eBay listing {ebay_listing_id} (SKU: {ebay_sku})"
                )
            else:
                error_msg = result.get("error", "Unknown error")
                self.log_error(f"Failed to publish product {product_id}: {error_msg}")

            return result

        except Exception as e:
            error_msg = f"Exception publishing product {product_id}: {e}"
            self.log_error(error_msg, exc_info=True)
            return {"success": False, "error": str(e)}
