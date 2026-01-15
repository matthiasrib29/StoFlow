"""
eBay Publish Job Handler

Publishes a product to eBay using eBay Inventory API.
Creates inventory item and offer for the product.

Author: Claude
Date: 2026-01-09
Refactored: 2026-01-15 (Phase 4 - DirectAPI Handler Pattern)
"""

from models.user.marketplace_job import MarketplaceJob
from services.marketplace.direct_api_job_handler import DirectAPIJobHandler
from services.ebay.ebay_publication_service import EbayPublicationService


class EbayPublishJobHandler(DirectAPIJobHandler):
    """
    Handler for publishing products to eBay.

    Uses EbayPublicationService to create inventory item and offer.
    This creates a new listing on eBay marketplace.

    Action code: publish_ebay
    """

    ACTION_CODE = "publish_ebay"

    def get_service(self) -> EbayPublicationService:
        """Return eBay publication service instance."""
        return EbayPublicationService(self.db)

    def get_service_method_name(self) -> str:
        """Return method name to call on service."""
        return "publish_product"

    def create_tasks(self, job: MarketplaceJob) -> list[str]:
        """Return empty task list (DirectAPI handlers don't use tasks yet)."""
        return []
