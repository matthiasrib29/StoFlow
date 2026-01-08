"""
Etsy Publish Handler

Publication handler for Etsy marketplace.
Uses BasePublishHandler for common publication logic.

Etsy uses direct API calls (no browser plugin).

Author: Claude
Date: 2026-01-08 (Security Audit 2)
"""

from typing import Any

from sqlalchemy.orm import Session

from models.user.product import Product, ProductStatus
from services.marketplace.handlers.base_publish_handler import BasePublishHandler
from services.etsy.etsy_publication_service import EtsyPublicationService
from shared.logging_setup import get_logger

logger = get_logger(__name__)


class EtsyPublishHandler(BasePublishHandler):
    """
    Etsy publication handler.

    Etsy specifics:
    - Photos uploaded during listing creation
    - Direct API calls (no plugin)
    - Requires taxonomy_id, shipping_profile_id
    """

    def __init__(self, db: Session, job_id: int, user_id: int):
        """
        Initialize Etsy publish handler.

        Args:
            db: SQLAlchemy session (user schema)
            job_id: MarketplaceJob ID
            user_id: User ID
        """
        super().__init__(db, job_id, user_id)

        # Initialize Etsy publication service
        self.etsy_service = EtsyPublicationService(db, user_id)

    def marketplace_name(self) -> str:
        """Return 'etsy'."""
        return "etsy"

    async def _upload_photos(self, product: Product) -> list[int]:
        """
        Etsy handles photos during listing creation.

        This method returns empty list as photos are not uploaded separately.

        Args:
            product: Product with images

        Returns:
            list[int]: Empty list (photos handled in _create_listing)
        """
        images = self._get_product_images(product, max_images=10)

        if not images:
            self.log_warning(f"Product #{product.id} has no images")

        # Etsy photos are uploaded as part of listing creation
        # No separate upload step needed
        self.log_debug(f"Found {len(images)} images (will be included in listing)")

        return []  # No separate photo IDs

    async def _create_listing(
        self, product: Product, photo_ids: list[int]
    ) -> dict[str, Any]:
        """
        Create Etsy listing.

        Args:
            product: Product to publish
            photo_ids: Not used for Etsy (empty list)

        Returns:
            dict: {
                "listing_id": str,
                "url": str,
                "state": str
            }

        Raises:
            Exception: If creation fails
        """
        # Get required parameters from job input_data
        input_data = self.job.input_data or {}
        taxonomy_id = input_data.get("taxonomy_id")
        shipping_profile_id = input_data.get("shipping_profile_id")
        return_policy_id = input_data.get("return_policy_id")
        shop_section_id = input_data.get("shop_section_id")
        state = input_data.get("state", "active")  # "draft" or "active"

        if not taxonomy_id:
            raise ValueError("taxonomy_id required in job.input_data")

        self.log_debug(
            f"Creating Etsy listing (taxonomy={taxonomy_id}, state={state})"
        )

        # Call existing Etsy publication service
        result = self.etsy_service.publish_product(
            product=product,
            taxonomy_id=taxonomy_id,
            shipping_profile_id=shipping_profile_id,
            return_policy_id=return_policy_id,
            shop_section_id=shop_section_id,
            state=state
        )

        if not result.get("success"):
            error = result.get("error", "Unknown error")
            raise Exception(f"Etsy publication failed: {error}")

        listing_id = result.get("listing_id")
        listing_url = result.get("listing_url")
        listing_state = result.get("state", state)

        if not listing_id:
            raise ValueError("No listing_id in Etsy response")

        # Update product status
        product.status = ProductStatus.PUBLISHED
        self.db.commit()

        self.log_success(
            f"Etsy listing created: {listing_id} (state={listing_state})"
        )

        return {
            "listing_id": str(listing_id),
            "url": listing_url,
            "state": listing_state,
        }
