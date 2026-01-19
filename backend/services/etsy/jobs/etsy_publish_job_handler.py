"""
Etsy Publish Job Handler

Publishes a product to Etsy using Etsy API v3.
Creates a listing for the product.

Author: Claude
Date: 2026-01-09
"""

from models.user.marketplace_job import MarketplaceJob
from services.marketplace.direct_api_job_handler import DirectAPIJobHandler
from services.etsy.etsy_publication_service import EtsyPublicationService


class EtsyPublishJobHandler(DirectAPIJobHandler):
    """
    Handler for publishing products to Etsy.

    Uses EtsyPublicationService to create listing on Etsy marketplace.

    Action code: publish_etsy
    """

    ACTION_CODE = "publish_etsy"

    def get_service(self) -> EtsyPublicationService:
        """Return Etsy publication service instance."""
        return EtsyPublicationService(self.db)

    def get_service_method_name(self) -> str:
        """Return method name to call on service."""
        return "publish_product"

    def create_tasks(self, job: MarketplaceJob) -> list[str]:
        """Return empty task list (DirectAPI handlers don't use tasks yet)."""
        return []
