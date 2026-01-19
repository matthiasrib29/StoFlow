"""
Etsy Delete Job Handler

Deletes/deactivates an Etsy listing.

Author: Claude
Date: 2026-01-09
"""

from models.user.marketplace_job import MarketplaceJob
from services.marketplace.direct_api_job_handler import DirectAPIJobHandler
from services.etsy.etsy_publication_service import EtsyPublicationService


class EtsyDeleteJobHandler(DirectAPIJobHandler):
    """
    Handler for deleting Etsy listings.

    Deactivates or deletes listing on Etsy marketplace.

    Action code: delete_etsy
    """

    ACTION_CODE = "delete_etsy"

    def get_service(self) -> EtsyPublicationService:
        """Return Etsy publication service instance."""
        return EtsyPublicationService(self.db)

    def get_service_method_name(self) -> str:
        """Return method name to call on service."""
        return "delete_product"

    def create_tasks(self, job: MarketplaceJob) -> list[str]:
        """Return empty task list (DirectAPI handlers don't use tasks yet)."""
        return []
