"""
eBay Delete Job Handler

Deletes/ends an eBay listing (withdraws offer and optionally deletes inventory item).

Author: Claude
Date: 2026-01-09
Refactored: 2026-01-15 (Phase 4 - DirectAPI Handler Pattern)
"""

from models.user.marketplace_job import MarketplaceJob
from services.marketplace.direct_api_job_handler import DirectAPIJobHandler
from services.ebay.ebay_publication_service import EbayPublicationService


class EbayDeleteJobHandler(DirectAPIJobHandler):
    """
    Handler for deleting eBay listings.

    Uses EbayPublicationService to withdraw offer (end listing)
    and optionally delete inventory item.

    Action code: delete_ebay
    """

    ACTION_CODE = "delete_ebay"

    def get_service(self) -> EbayPublicationService:
        """Return eBay publication service instance."""
        return EbayPublicationService(self.db)

    def get_service_method_name(self) -> str:
        """Return method name to call on service."""
        return "delete_product"

    def create_tasks(self, job: MarketplaceJob) -> list[str]:
        """Return empty task list (DirectAPI handlers don't use tasks yet)."""
        return []
