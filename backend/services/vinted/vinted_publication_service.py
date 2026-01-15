"""
Vinted Publication Service - Service for publishing products to Vinted.

Encapsulates the complete publication workflow:
- Product validation
- Attribute mapping
- Price calculation
- Title/description generation
- Image upload
- Listing creation
- Post-processing

This service extracts business logic from PublishJobHandler to improve
separation of concerns and testability.

Author: Claude
Date: 2026-01-15
"""

import time
from typing import Any

from sqlalchemy.orm import Session

from models.user.product import Product, ProductStatus
from models.user.vinted_product import VintedProduct
from services.vinted.vinted_mapping_service import VintedMappingService
from services.vinted.vinted_pricing_service import VintedPricingService
from services.vinted.vinted_product_validator import VintedProductValidator
from services.vinted.vinted_title_service import VintedTitleService
from services.vinted.vinted_description_service import VintedDescriptionService
from services.vinted.vinted_product_converter import VintedProductConverter
from services.vinted.vinted_product_helpers import (
    upload_product_images,
    save_new_vinted_product,
)
from services.plugin_websocket_helper import PluginWebSocketHelper
from shared.vinted_constants import VintedProductAPI
from shared.logging_setup import get_logger

logger = get_logger(__name__)


class VintedPublicationService:
    """
    Service for publishing products to Vinted.

    Encapsulates the complete publication workflow:
    - Product validation
    - Attribute mapping
    - Price calculation
    - Title/description generation
    - Image upload
    - Listing creation
    - Post-processing
    """

    def __init__(self, db: Session):
        """
        Initialize the publication service.

        Args:
            db: SQLAlchemy session
        """
        self.db = db
        self.mapping_service = VintedMappingService()
        self.pricing_service = VintedPricingService()
        self.validator = VintedProductValidator()
        self.title_service = VintedTitleService()
        self.description_service = VintedDescriptionService()

    async def publish_product(
        self,
        product_id: int,
        user_id: int,
        shop_id: int | None = None,
        job_id: int | None = None
    ) -> dict[str, Any]:
        """
        Publishes a product to Vinted.

        Args:
            product_id: Product ID to publish
            user_id: User ID for plugin communication
            shop_id: Optional shop ID
            job_id: Optional job ID for tracking

        Returns:
            dict: {
                "success": bool,
                "vinted_id": int | None,
                "url": str | None,
                "product_id": int,
                "price": float | None,
                "error": str | None
            }
        """
        start_time = time.time()

        try:
            logger.info(f"Starting publication for product #{product_id}")

            # 1. Retrieve product
            product = self._get_product(product_id)

            # 2. Check if already published
            self._check_not_already_published(product_id)

            # 3. Validate product
            self._validate_product(product)

            # 4. Map attributes
            mapped_attrs = self._map_attributes(product)

            # 5. Calculate price
            prix_vinted = self._calculate_price(product)

            # 6. Generate title and description
            title = self.title_service.generate_title(product)
            description = self.description_service.generate_description(product)

            # 7. Upload images
            photo_ids = await self._upload_images(product, user_id, job_id)

            # 8. Build payload
            payload = VintedProductConverter.build_create_payload(
                product=product,
                photo_ids=photo_ids,
                mapped_attrs=mapped_attrs,
                prix_vinted=prix_vinted,
                title=title,
                description=description
            )

            # 9. Create product via plugin
            logger.debug(f"Creating Vinted listing for product #{product_id}...")
            result = await self._call_plugin(
                user_id=user_id,
                job_id=job_id,
                http_method="POST",
                path=VintedProductAPI.CREATE,
                payload={"body": payload},
                product_id=product_id,
                timeout=60,
                description="Create Vinted product"
            )

            # 10. Extract result
            item_data = result.get('item', result)
            vinted_id = item_data.get('id')
            vinted_url = item_data.get('url')

            if not vinted_id:
                raise ValueError("vinted_id missing from response")

            # 11. Post-processing
            self._save_vinted_product(
                product_id, result, prix_vinted, photo_ids, title
            )
            self._update_product_status(product)

            elapsed = time.time() - start_time
            logger.info(
                f"Product #{product_id} published successfully -> "
                f"vinted_id={vinted_id} ({elapsed:.1f}s)"
            )

            return {
                "success": True,
                "vinted_id": vinted_id,
                "url": vinted_url,
                "product_id": product_id,
                "price": prix_vinted
            }

        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(
                f"Publication failed for product #{product_id}: {e} ({elapsed:.1f}s)",
                exc_info=True
            )
            self.db.rollback()
            return {
                "success": False,
                "vinted_id": None,
                "url": None,
                "product_id": product_id,
                "error": str(e)
            }

    # =========================================================================
    # PRIVATE METHODS
    # =========================================================================

    def _get_product(self, product_id: int) -> Product:
        """Retrieve product or raise exception."""
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise ValueError(f"Product #{product_id} not found")

        logger.debug(
            f"Product: {product.title[:50] if product.title else 'Untitled'}..."
        )
        return product

    def _check_not_already_published(self, product_id: int):
        """Check that product is not already published."""
        existing = self.db.query(VintedProduct).filter(
            VintedProduct.product_id == product_id
        ).first()

        if existing:
            raise ValueError(
                f"Product #{product_id} already published on Vinted "
                f"(vinted_id: {existing.vinted_id})"
            )

    def _validate_product(self, product: Product):
        """Validate product for publication."""
        logger.debug("Validating product...")
        is_valid, error = self.validator.validate_for_creation(product)
        if not is_valid:
            raise ValueError(f"Validation failed: {error}")

    def _map_attributes(self, product: Product) -> dict:
        """Map product attributes to Vinted."""
        logger.debug("Mapping attributes...")
        mapped_attrs = self.mapping_service.map_all_attributes(self.db, product)

        is_valid, error = self.validator.validate_mapped_attributes(
            mapped_attrs, product.id
        )
        if not is_valid:
            raise ValueError(f"Invalid attributes: {error}")

        return mapped_attrs

    def _calculate_price(self, product: Product) -> float:
        """Calculate Vinted price."""
        logger.debug("Calculating price...")
        prix_vinted = self.pricing_service.calculate_vinted_price(product)
        logger.debug(f"Price: {prix_vinted}EUR")
        return prix_vinted

    async def _upload_images(
        self,
        product: Product,
        user_id: int,
        job_id: int | None
    ) -> list[int]:
        """Upload images to Vinted."""
        logger.debug("Uploading images...")
        photo_ids = await upload_product_images(
            self.db, product, user_id=user_id, job_id=job_id
        )

        is_valid, error = self.validator.validate_images(photo_ids)
        if not is_valid:
            raise ValueError(f"Invalid images: {error}")

        logger.debug(f"{len(photo_ids)} images uploaded")
        return photo_ids

    async def _call_plugin(
        self,
        user_id: int,
        job_id: int | None,
        http_method: str,
        path: str,
        payload: dict,
        product_id: int,
        timeout: int,
        description: str
    ) -> dict:
        """Call plugin via WebSocket helper."""
        result = await PluginWebSocketHelper.call_plugin_action(
            user_id=user_id,
            job_id=job_id,
            http_method=http_method,
            path=path,
            payload=payload,
            product_id=product_id,
            timeout=timeout,
            description=description
        )
        return result

    def _save_vinted_product(
        self,
        product_id: int,
        response_data: dict,
        prix_vinted: float,
        photo_ids: list[int],
        title: str
    ):
        """Save VintedProduct after creation."""
        logger.debug("Post-processing...")
        save_new_vinted_product(
            db=self.db,
            product_id=product_id,
            response_data=response_data,
            prix_vinted=prix_vinted,
            image_ids=photo_ids,
            title=title
        )

    def _update_product_status(self, product: Product):
        """Update local product status."""
        product.status = ProductStatus.PUBLISHED
        self.db.commit()
