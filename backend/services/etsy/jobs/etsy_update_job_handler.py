"""
Etsy Update Job Handler

Updates an existing Etsy listing.

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


class EtsyUpdateJobHandler(BaseJobHandler):
    """
    Handler for updating existing Etsy listings.

    Updates listing data for an existing product on Etsy.

    Action code: update_etsy
    """

    ACTION_CODE = "update_etsy"

    async def execute(self, job: MarketplaceJob) -> dict[str, Any]:
        """
        Update existing Etsy listing.

        Args:
            job: MarketplaceJob with product_id

        Returns:
            dict: {
                "success": bool,
                "etsy_listing_id": str (if success),
                "updated_fields": list (if success),
                "error": str (if failure)
            }
        """
        product_id = job.product_id

        if not product_id:
            self.log_error("product_id is required")
            return {"success": False, "error": "product_id required"}

        self.log_start(f"Updating Etsy listing for product {product_id}")

        try:
            # Use existing publication service (update method)
            service = EtsyPublicationService(self.db)
            result = await service.update_product(product_id)

            if result.get("success", False):
                etsy_listing_id = result.get("etsy_listing_id", "unknown")
                updated_fields = result.get("updated_fields", [])

                self.log_success(
                    f"Updated product {product_id} → "
                    f"Etsy listing {etsy_listing_id} (fields: {', '.join(updated_fields)})"
                )
            else:
                error_msg = result.get("error", "Unknown error")
                self.log_error(f"Failed to update product {product_id}: {error_msg}")

            return result

        except Exception as e:
            error_msg = f"Exception updating product {product_id}: {e}"
            self.log_error(error_msg, exc_info=True)
            return {"success": False, "error": str(e)}
