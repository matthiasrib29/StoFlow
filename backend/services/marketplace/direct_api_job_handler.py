"""
DirectAPI Job Handler - Abstract base class for eBay/Etsy job handlers.

This class factorizes 80%+ code duplication between eBay and Etsy handlers
by providing a common execution pattern for direct marketplace API calls.

Common pattern:
1. Validate product_id
2. Log start
3. Get marketplace service (abstract)
4. Call service method (abstract)
5. Handle result
6. Handle exceptions

Author: Claude
Date: 2026-01-15
Phase: 03-01 DirectAPI Handler Base
"""

from abc import abstractmethod
from typing import Any

from models.user.marketplace_job import MarketplaceJob
from services.vinted.jobs.base_job_handler import BaseJobHandler
from shared.logging import get_logger

logger = get_logger(__name__)


class DirectAPIJobHandler(BaseJobHandler):
    """
    Abstract base class for handlers that call marketplace APIs directly.

    Used by eBay and Etsy handlers (not Vinted, which uses WebSocket plugin).

    Subclasses must implement:
    - get_service(): Return marketplace-specific service instance
    - get_service_method_name(): Return method name to call on service

    Example Usage:
        class EbayPublishJobHandler(DirectAPIJobHandler):
            ACTION_CODE = "ebay_publish"

            def get_service(self) -> EbayPublicationService:
                return EbayPublicationService(self.db)

            def get_service_method_name(self) -> str:
                return "publish_product"

    Benefits:
    - 81% code reduction (81 lines → 15 lines per handler)
    - Uniform error handling across all direct API handlers
    - Single point of maintenance for common workflow
    """

    @abstractmethod
    def get_service(self) -> Any:
        """
        Return marketplace-specific service instance.

        Returns:
            Service instance (e.g., EbayPublicationService, EtsyUpdateService)

        Example:
            def get_service(self) -> EbayPublicationService:
                return EbayPublicationService(self.db)
        """
        pass

    @abstractmethod
    def get_service_method_name(self) -> str:
        """
        Return name of the method to call on the service.

        Returns:
            Method name as string (e.g., "publish_product", "update_product")

        Example:
            def get_service_method_name(self) -> str:
                return "publish_product"
        """
        pass

    async def execute(self, job: MarketplaceJob) -> dict[str, Any]:
        """
        Execute marketplace API operation using service delegation pattern.

        Workflow:
        1. Validate product_id exists
        2. Get marketplace service via get_service()
        3. Call service method via get_service_method_name()
        4. Log success/error based on result
        5. Handle exceptions uniformly

        Args:
            job: MarketplaceJob with product_id

        Returns:
            dict: {
                "success": bool,
                "error": str | None,
                "ebay_listing_id" or "etsy_listing_id": str | None
            }
        """
        product_id = job.product_id

        # Pre-execution cancellation check
        if self.is_cancelled(job):
            self.log_start(f"Job #{job.id} cancelled before execution")
            return {"success": False, "error": "cancelled"}

        # 1. Validate product_id
        if not product_id:
            self.log_error("product_id is required")
            return {"success": False, "error": "product_id required"}

        method_name = self.get_service_method_name()
        self.log_start(f"Executing {method_name} for product {product_id}")

        try:
            # 2. Get service instance
            service = self.get_service()

            # 3. Call service method
            method = getattr(service, method_name)
            result = await method(product_id)

            # 4. Log result
            if result.get("success", False):
                # Extract listing ID from either eBay or Etsy field
                listing_id = (
                    result.get("ebay_listing_id")
                    or result.get("etsy_listing_id")
                    or "unknown"
                )
                self.log_success(
                    f"Executed {method_name} for product {product_id} → listing {listing_id}"
                )
            else:
                error_msg = result.get("error", "Unknown error")
                self.log_error(
                    f"Failed {method_name} for product {product_id}: {error_msg}"
                )

            return result

        except Exception as e:
            # 5. Handle exceptions uniformly
            error_msg = f"Exception in {method_name} for product {product_id}: {e}"
            self.log_error(error_msg, exc_info=True)
            return {"success": False, "error": str(e)}
