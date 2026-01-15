"""
VintedJobHandler - Base class for Vinted-specific job handlers.

Provides common patterns for handlers that delegate to Vinted services:
- Product validation
- Service instantiation and method calling
- Logging patterns
- Exception handling

Unlike DirectAPIJobHandler (for eBay/Etsy), this supports Vinted's
WebSocket-based plugin communication.
"""

from typing import Any

from sqlalchemy.orm import Session

from models.user.marketplace_job import MarketplaceJob
from services.vinted.jobs.base_job_handler import BaseJobHandler


class VintedJobHandler(BaseJobHandler):
    """
    Abstract base class for Vinted job handlers that delegate to services.

    Pattern:
    - Subclass defines get_service() and get_service_method_name()
    - Base class handles execution orchestration
    - Services contain all business logic
    """

    def get_service(self):
        """
        Return the service instance for this handler.

        Returns:
            Service instance (e.g., VintedPublicationService)
        """
        raise NotImplementedError("Subclass must implement get_service()")

    def get_service_method_name(self) -> str:
        """
        Return the method name to call on the service.

        Returns:
            Method name as string (e.g., "publish_product")
        """
        raise NotImplementedError("Subclass must implement get_service_method_name()")

    async def execute(self, job: MarketplaceJob) -> dict[str, Any]:
        """
        Execute job by delegating to service.

        Args:
            job: MarketplaceJob to execute

        Returns:
            dict: {
                "success": bool,
                "error": str | None,
                ... service-specific fields
            }
        """
        product_id = job.product_id
        if not product_id:
            return {"success": False, "error": "product_id required"}

        try:
            self.log_start(f"{self.ACTION_CODE} product #{product_id}")

            # Get service and method
            service = self.get_service()
            method_name = self.get_service_method_name()
            method = getattr(service, method_name)

            # Call service method
            result = await method(
                product_id=product_id,
                user_id=self.user_id,
                shop_id=self.shop_id,
                job_id=self.job_id
            )

            # Log result
            if result.get("success"):
                self.log_success(f"Product #{product_id} {self.ACTION_CODE}ed successfully")
            else:
                error = result.get("error", "Unknown error")
                self.log_error(f"Product #{product_id}: {error}")

            return result

        except Exception as e:
            self.log_error(f"Product #{product_id}: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
