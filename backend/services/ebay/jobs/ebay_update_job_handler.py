"""
eBay Update Job Handler

Updates an existing eBay listing (inventory item and/or offer).

Author: Claude
Date: 2026-01-09
Refactored: 2026-01-15 (Phase 4 - DirectAPI Handler Pattern)
"""

from models.user.marketplace_job import MarketplaceJob
from services.marketplace.direct_api_job_handler import DirectAPIJobHandler
from services.ebay.ebay_publication_service import EbayPublicationService


class EbayUpdateJobHandler(DirectAPIJobHandler):
    """
    Handler for updating existing eBay listings.

    Uses EbayPublicationService to update inventory item and/or offer
    for an existing product on eBay.

    Action code: update_ebay
    """

    ACTION_CODE = "update_ebay"

    def get_service(self) -> EbayPublicationService:
        """Return eBay publication service instance."""
        return EbayPublicationService(self.db)

    def get_service_method_name(self) -> str:
        """Return method name to call on service."""
        return "update_product"

    def create_tasks(self, job: MarketplaceJob) -> list[str]:
        """Return empty task list (DirectAPI handlers don't use tasks yet)."""
        return []
