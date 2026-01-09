"""
Etsy Publish Job Handler

Publishes a product to Etsy using Etsy API v3.
Creates a listing for the product.

Author: Claude
Date: 2026-01-09
"""

from typing import Any

from sqlalchemy.orm import Session

from models.user.marketplace_job import MarketplaceJob
from services.vinted.jobs.base_job_handler import BaseJobHandler
from services.etsy.etsy_publication_service import EtsyPublicationService
from shared.logging_setup import get_logger

logger = get_logger(__name__)


class EtsyPublishJobHandler(BaseJobHandler):
    """
    Handler for publishing products to Etsy.

    Uses EtsyPublicationService to create listing on Etsy marketplace.

    Action code: publish_etsy
    """

    ACTION_CODE = "publish_etsy"

    async def execute(self, job: MarketplaceJob) -> dict[str, Any]:
        """
        Publish product to Etsy.

        Args:
            job: MarketplaceJob with product_id

        Returns:
            dict: {
                "success": bool,
                "etsy_listing_id": str (if success),
                "error": str (if failure)
            }
        """
        product_id = job.product_id

        if not product_id:
            self.log_error("product_id is required")
            return {"success": False, "error": "product_id required"}

        self.log_start(f"Publishing product {product_id} to Etsy")

        try:
            # Use existing publication service
            service = EtsyPublicationService(self.db)
            result = await service.publish_product(product_id)

            if result.get("success", False):
                etsy_listing_id = result.get("etsy_listing_id", "unknown")

                self.log_success(
                    f"Published product {product_id} → "
                    f"Etsy listing {etsy_listing_id}"
                )
            else:
                error_msg = result.get("error", "Unknown error")
                self.log_error(f"Failed to publish product {product_id}: {error_msg}")

            return result

        except Exception as e:
            error_msg = f"Exception publishing product {product_id}: {e}"
            self.log_error(error_msg, exc_info=True)
            return {"success": False, "error": str(e)}
