"""
Vinted Publish Handler

Publication handler for Vinted marketplace.
Uses BasePublishHandler for common publication logic.

Author: Claude
Date: 2026-01-08 (Security Audit 2)
"""

from typing import Any

from sqlalchemy.orm import Session

from models.user.product import Product, ProductStatus
from models.user.vinted_product import VintedProduct
from services.marketplace.handlers.base_publish_handler import BasePublishHandler
from services.vinted.vinted_mapping_service import VintedMappingService
from services.vinted.vinted_pricing_service import VintedPricingService
from services.vinted.vinted_title_service import VintedTitleService
from services.vinted.vinted_description_service import VintedDescriptionService
from services.vinted.vinted_product_converter import VintedProductConverter
from shared.vinted_constants import VintedProductAPI
from shared.logging_setup import get_logger

logger = get_logger(__name__)


class VintedPublishHandler(BasePublishHandler):
    """
    Vinted publication handler.

    Implements Vinted-specific logic:
    - Photo upload via plugin
    - Attribute mapping
    - Price calculation
    - Title/description generation
    """

    def __init__(self, db: Session, job_id: int, user_id: int):
        """
        Initialize Vinted publish handler.

        Args:
            db: SQLAlchemy session (user schema)
            job_id: MarketplaceJob ID
            user_id: User ID
        """
        super().__init__(db, job_id, user_id)

        # Initialize Vinted services
        self.mapping_service = VintedMappingService()
        self.pricing_service = VintedPricingService()
        self.title_service = VintedTitleService()
        self.description_service = VintedDescriptionService()

    def marketplace_name(self) -> str:
        """Return 'vinted'."""
        return "vinted"

    async def _upload_photos(self, product: Product) -> list[int]:
        """
        Upload photos to Vinted via plugin.

        Args:
            product: Product with images

        Returns:
            list[int]: Photo IDs uploaded to Vinted

        Raises:
            Exception: If upload fails
        """
        images = self._get_product_images(product, max_images=10)

        if not images:
            self.log_warning(f"Product #{product.id} has no images, skipping upload")
            return []

        photo_ids = []

        for idx, image in enumerate(images, 1):
            try:
                self.log_debug(f"Uploading photo {idx}/{len(images)}")

                # Call plugin to upload photo
                result = await self.call_plugin(
                    http_method="POST",
                    path=VintedProductAPI.UPLOAD_PHOTO,
                    payload={"body": {"url": image.get("url")}},
                    product_id=product.id,
                    timeout=30,
                    description=f"Upload photo {idx}/{len(images)}"
                )

                photo_id = result.get("id")
                if photo_id:
                    photo_ids.append(photo_id)
                    self.log_debug(f"✅ Photo {idx} uploaded (id: {photo_id})")
                else:
                    self.log_warning(f"⚠️ Photo {idx}: no ID returned")

            except Exception as e:
                self.log_warning(f"⚠️ Photo {idx} upload failed: {e}")
                # Continue with remaining photos

        if not photo_ids:
            raise ValueError("No photos were successfully uploaded")

        return photo_ids

    async def _create_listing(
        self, product: Product, photo_ids: list[int]
    ) -> dict[str, Any]:
        """
        Create Vinted listing.

        Args:
            product: Product to publish
            photo_ids: Photo IDs uploaded

        Returns:
            dict: {
                "listing_id": str (vinted_id),
                "url": str,
                "price": float,
                "title": str
            }

        Raises:
            Exception: If creation fails
        """
        # 1. Map attributes
        mapped_attrs = self.mapping_service.map_product_to_vinted(product)
        self.log_debug(f"Attributes mapped: {list(mapped_attrs.keys())}")

        # 2. Calculate price
        vinted_price = self.pricing_service.calculate_vinted_price(product.price)
        self.log_debug(f"Price calculated: {product.price} → {vinted_price}")

        # 3. Generate title
        title = self.title_service.generate_title(product)
        self.log_debug(f"Title generated: {title[:50]}...")

        # 4. Generate description
        description = self.description_service.generate_description(product)
        self.log_debug(f"Description generated: {len(description)} chars")

        # 5. Build payload
        payload = VintedProductConverter.build_create_payload(
            product=product,
            title=title,
            description=description,
            price=vinted_price,
            photo_ids=photo_ids,
            **mapped_attrs
        )

        # 6. Create listing via plugin
        self.log_debug("Creating Vinted listing")
        result = await self.call_plugin(
            http_method="POST",
            path=VintedProductAPI.CREATE,
            payload={"body": payload},
            product_id=product.id,
            timeout=60,
            description="Create Vinted listing"
        )

        # 7. Extract listing data
        item = result.get("item", result)
        vinted_id = item.get("id")
        vinted_url = item.get("url")

        if not vinted_id:
            raise ValueError("No vinted_id in response")

        # 8. Save VintedProduct
        self._save_vinted_product(
            product_id=product.id,
            vinted_id=vinted_id,
            title=title,
            price=vinted_price,
            photo_ids=photo_ids,
            vinted_url=vinted_url,
            mapped_attrs=mapped_attrs
        )

        # 9. Update product status
        product.status = ProductStatus.PUBLISHED
        self.db.commit()

        self.log_success(f"Vinted listing created: {vinted_id} ({vinted_url})")

        return {
            "listing_id": str(vinted_id),
            "url": vinted_url,
            "price": float(vinted_price),
            "title": title,
        }

    def _save_vinted_product(
        self,
        product_id: int,
        vinted_id: int,
        title: str,
        price: float,
        photo_ids: list[int],
        vinted_url: str,
        mapped_attrs: dict
    ) -> VintedProduct:
        """
        Save VintedProduct record.

        Args:
            product_id: Product ID
            vinted_id: Vinted listing ID
            title: Title used
            price: Price used
            photo_ids: Photo IDs
            vinted_url: Listing URL
            mapped_attrs: Mapped attributes

        Returns:
            VintedProduct instance
        """
        vinted_product = VintedProduct(
            vinted_id=vinted_id,
            product_id=product_id,
            title=title,
            price=price,
            currency="EUR",
            url=vinted_url,
            status="published",
            # Attributes
            brand=mapped_attrs.get("brand_title"),
            brand_id=mapped_attrs.get("brand_id"),
            size=mapped_attrs.get("size_title"),
            size_id=mapped_attrs.get("size_id"),
            color1=mapped_attrs.get("color1_title"),
            color1_id=mapped_attrs.get("color1_id"),
            color2=mapped_attrs.get("color2_title"),
            color2_id=mapped_attrs.get("color2_id"),
            catalog_id=mapped_attrs.get("catalog_id"),
            status_id=mapped_attrs.get("status_id"),
        )

        # Store photo IDs as JSON
        vinted_product.set_image_ids(photo_ids)

        self.db.add(vinted_product)
        self.db.flush()

        self.log_debug(f"VintedProduct saved: {vinted_id}")

        return vinted_product
