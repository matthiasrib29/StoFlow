"""
Link Product Job Handler

Thin handler that delegates to VintedLinkProductService.

Workflow:
1. Create Product from VintedProduct
2. Download images from Vinted to R2
3. Commit

Author: Claude
Date: 2026-01-06
Updated: 2026-01-15 - Refactored to follow standard pattern
"""

from typing import Any

from sqlalchemy.orm import Session

from models.user.marketplace_job import MarketplaceJob
from services.vinted.vinted_link_product_service import VintedLinkProductService
from shared.database import get_tenant_schema
from .base_job_handler import BaseJobHandler


class LinkProductJobHandler(BaseJobHandler):
    """
    Handler for linking Vinted products.

    Delegates all business logic to VintedLinkProductService.
    """

    ACTION_CODE = "link_product"

    def create_tasks(self, job: MarketplaceJob) -> list[str]:
        """
        Define task steps for product linking.

        Args:
            job: MarketplaceJob

        Returns:
            List of task step descriptions
        """
        return [
            "Fetch VintedProduct data",
            "Create Product from VintedProduct",
            "Download images to R2",
            "Save and commit"
        ]

    def get_service(self) -> VintedLinkProductService:
        """
        Get service instance for link operations.

        Returns:
            VintedLinkProductService instance
        """
        return VintedLinkProductService(self.db)

    async def execute(self, job: MarketplaceJob) -> dict[str, Any]:
        """
        Execute product linking by delegating to service.

        Args:
            job: MarketplaceJob (product_id contains vinted_id)

        Returns:
            dict: {
                "success": bool,
                "linked": bool,
                "product_id": int | None,
                "vinted_id": int,
                "images_copied": int,
                "images_failed": int,
                "total_images": int,
                "error": str | None
            }
        """
        # Note: job.product_id contains vinted_id for this action
        vinted_id = job.product_id

        if not vinted_id:
            return {"success": False, "error": "vinted_id required"}

        try:
            self.log_start(f"Link VintedProduct #{vinted_id}")

            # Get user_id from schema
            schema = get_tenant_schema(self.db)
            if not schema or not schema.startswith("user_"):
                return {"success": False, "error": "Invalid user schema"}

            user_id = int(schema.replace("user_", ""))

            # Delegate to service
            service = self.get_service()
            result = await service.link_product(
                vinted_product_id=vinted_id,
                product_id=None,  # Unused parameter
                user_id=user_id
            )

            if result.get("success"):
                product_id = result.get("product_id")
                images_copied = result.get("images_copied", 0)
                self.log_success(f"Linked Product #{product_id}, {images_copied} images")
            else:
                self.log_error(f"Link failed: {result.get('error')}")

            return result

        except Exception as e:
            self.log_error(f"Link error: {e}", exc_info=True)
            return {"success": False, "vinted_id": vinted_id, "error": str(e)}
