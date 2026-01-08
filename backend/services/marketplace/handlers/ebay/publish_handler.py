"""
eBay Publish Handler

Publication handler for eBay marketplace.
Uses BasePublishHandler for common publication logic.

eBay uses direct API calls (no browser plugin).

Author: Claude
Date: 2026-01-08 (Security Audit 2)
"""

from typing import Any

from sqlalchemy.orm import Session

from models.user.product import Product, ProductStatus
from models.user.ebay_product_marketplace import EbayProductMarketplace
from services.marketplace.handlers.base_publish_handler import BasePublishHandler
from services.ebay.ebay_publication_service import EbayPublicationService
from shared.logging_setup import get_logger

logger = get_logger(__name__)


class EbayPublishHandler(BasePublishHandler):
    """
    eBay publication handler.

    eBay specifics:
    - No photo upload step (handled within listing creation)
    - Direct API calls (no plugin)
    - Requires marketplace_id (EBAY_FR, EBAY_GB, etc.)
    """

    def __init__(self, db: Session, job_id: int, user_id: int):
        """
        Initialize eBay publish handler.

        Args:
            db: SQLAlchemy session (user schema)
            job_id: MarketplaceJob ID
            user_id: User ID
        """
        super().__init__(db, job_id, user_id)

        # Initialize eBay publication service
        self.ebay_service = EbayPublicationService(db, user_id)

    def marketplace_name(self) -> str:
        """Return 'ebay'."""
        return "ebay"

    async def _upload_photos(self, product: Product) -> list[int]:
        """
        eBay handles photos during listing creation.

        This method returns empty list as photos are not uploaded separately.

        Args:
            product: Product with images

        Returns:
            list[int]: Empty list (photos handled in _create_listing)
        """
        images = self._get_product_images(product, max_images=12)

        if not images:
            self.log_warning(f"Product #{product.id} has no images")

        # eBay photos are uploaded as part of inventory item creation
        # No separate upload step needed
        self.log_debug(f"Found {len(images)} images (will be included in listing)")

        return []  # No separate photo IDs

    async def _create_listing(
        self, product: Product, photo_ids: list[int]
    ) -> dict[str, Any]:
        """
        Create eBay listing.

        Args:
            product: Product to publish
            photo_ids: Not used for eBay (empty list)

        Returns:
            dict: {
                "listing_id": str,
                "url": str,
                "offer_id": str,
                "sku_derived": str
            }

        Raises:
            Exception: If creation fails
        """
        # Get marketplace_id from job input_data
        input_data = self.job.input_data or {}
        marketplace_id = input_data.get("marketplace_id")
        category_id = input_data.get("category_id")

        if not marketplace_id:
            raise ValueError("marketplace_id required in job.input_data (e.g., EBAY_FR)")

        self.log_debug(
            f"Creating eBay listing on {marketplace_id} "
            f"(category_id={category_id or 'auto'})"
        )

        # Call existing eBay publication service
        result = self.ebay_service.publish_product(
            product_id=product.id,
            marketplace_id=marketplace_id,
            category_id=category_id
        )

        listing_id = result.get("listing_id")
        offer_id = result.get("offer_id")
        sku_derived = result.get("sku_derived")

        if not listing_id:
            raise ValueError("No listing_id in eBay response")

        # Update product status
        product.status = ProductStatus.PUBLISHED
        self.db.commit()

        self.log_success(
            f"eBay listing created: {listing_id} "
            f"(offer={offer_id}, sku={sku_derived})"
        )

        # Build eBay listing URL
        # Format: https://www.ebay.fr/itm/{listing_id}
        marketplace_domain = self._get_marketplace_domain(marketplace_id)
        listing_url = f"https://www.ebay{marketplace_domain}/itm/{listing_id}"

        return {
            "listing_id": listing_id,
            "url": listing_url,
            "offer_id": offer_id,
            "sku_derived": sku_derived,
            "marketplace_id": marketplace_id,
        }

    def _get_marketplace_domain(self, marketplace_id: str) -> str:
        """
        Get eBay domain from marketplace_id.

        Args:
            marketplace_id: e.g., "EBAY_FR", "EBAY_GB", "EBAY_US"

        Returns:
            str: Domain like ".fr", ".co.uk", ".com"
        """
        domain_map = {
            "EBAY_FR": ".fr",
            "EBAY_GB": ".co.uk",
            "EBAY_US": ".com",
            "EBAY_DE": ".de",
            "EBAY_IT": ".it",
            "EBAY_ES": ".es",
        }

        return domain_map.get(marketplace_id, ".com")
