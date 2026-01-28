"""
Vinted Update Service - Service for updating products on Vinted.

Handles:
- Product and VintedProduct retrieval
- Validation for updates
- Attribute remapping
- Price recalculation
- Title/description regeneration
- Payload construction
- Update via plugin
- Local VintedProduct update

This service extracts business logic from UpdateJobHandler to improve
separation of concerns and testability.

Author: Claude
Date: 2026-01-15
"""

import time
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from models.user.product import Product
from models.user.vinted_product import VintedProduct
from services.vinted.vinted_mapping_service import VintedMappingService
from services.vinted.vinted_pricing_service import VintedPricingService
from services.vinted.vinted_product_validator import VintedProductValidator
from services.vinted.vinted_title_service import VintedTitleService
from services.vinted.vinted_description_service import VintedDescriptionService
from services.vinted.vinted_product_converter import VintedProductConverter
from services.plugin_websocket_helper import PluginWebSocketHelper
from shared.vinted import VintedProductAPI
from shared.logging import get_logger

logger = get_logger(__name__)


class VintedUpdateService:
    """
    Service for updating products on Vinted.

    Handles:
    - Product and VintedProduct retrieval
    - Validation for updates
    - Attribute remapping
    - Price recalculation
    - Title/description regeneration
    - Payload construction
    - Update via plugin
    - Local VintedProduct update
    """

    def __init__(self, db: Session):
        """
        Initialize the update service.

        Args:
            db: SQLAlchemy session
        """
        self.db = db
        self.mapping_service = VintedMappingService()
        self.pricing_service = VintedPricingService()
        self.validator = VintedProductValidator()
        self.title_service = VintedTitleService()
        self.description_service = VintedDescriptionService()

    async def update_product(
        self,
        product_id: int,
        user_id: int,
        shop_id: int | None = None,
        job_id: int | None = None
    ) -> dict[str, Any]:
        """
        Updates a product on Vinted.

        Args:
            product_id: Product ID to update
            user_id: User ID for plugin communication
            shop_id: Optional shop ID
            job_id: Optional job ID for tracking

        Returns:
            dict: {
                "success": bool,
                "product_id": int,
                "old_price": float,
                "new_price": float,
                "error": str | None
            }
        """
        start_time = time.time()

        try:
            logger.info(f"Starting update for product #{product_id}")

            # 1. Retrieve local product
            product = self._get_product(product_id)

            # 2. Retrieve VintedProduct
            vinted_product = self._get_vinted_product(product_id)

            # 3. Validate for update
            self._validate_product(product)

            # 4. Map attributes
            mapped_attrs = self._map_attributes(product)

            # 5. Calculate price
            prix_vinted = self.pricing_service.calculate_vinted_price(product)

            # 6. Check if price is identical -> skip optional
            prix_actuel = float(vinted_product.price) if vinted_product.price else 0.0
            if abs(prix_vinted - prix_actuel) < 0.01:
                logger.debug(f"Price unchanged ({prix_vinted}EUR)")
                # Continue anyway to update other fields

            # 7. Generate title and description
            title = self.title_service.generate_title(product)
            description = self.description_service.generate_description(product)

            # 8. Build payload
            payload = VintedProductConverter.build_update_payload(
                product=product,
                vinted_product=vinted_product,
                mapped_attrs=mapped_attrs,
                prix_vinted=prix_vinted,
                title=title,
                description=description
            )

            # 9. Update via plugin
            logger.debug(
                f"Updating listing (price: {prix_actuel}EUR -> {prix_vinted}EUR)..."
            )
            await self._call_plugin(
                user_id=user_id,
                job_id=job_id,
                http_method="PUT",
                path=VintedProductAPI.update(vinted_product.vinted_id),
                payload={"body": payload},
                product_id=product_id,
                timeout=60,
                description="Update Vinted product"
            )

            # 10. Update local VintedProduct
            self._update_vinted_product(vinted_product, prix_vinted, title)

            elapsed = time.time() - start_time
            logger.info(f"Product #{product_id} updated successfully ({elapsed:.1f}s)")

            return {
                "success": True,
                "product_id": product_id,
                "old_price": prix_actuel,
                "new_price": prix_vinted
            }

        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(
                f"Update failed for product #{product_id}: {e} ({elapsed:.1f}s)",
                exc_info=True
            )
            self.db.rollback()
            return {"success": False, "product_id": product_id, "error": str(e)}

    # =========================================================================
    # PRIVATE METHODS
    # =========================================================================

    def _get_product(self, product_id: int) -> Product:
        """Retrieve local product."""
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise ValueError(f"Product #{product_id} not found")
        return product

    def _get_vinted_product(self, product_id: int) -> VintedProduct:
        """Retrieve existing VintedProduct."""
        vinted_product = self.db.query(VintedProduct).filter(
            VintedProduct.product_id == product_id
        ).first()

        if not vinted_product:
            raise ValueError(f"Product #{product_id} not published on Vinted")

        if vinted_product.status != 'published':
            raise ValueError(
                f"Incorrect status: {vinted_product.status} (expected: published)"
            )

        return vinted_product

    def _validate_product(self, product: Product):
        """Validate product for update."""
        is_valid, error = self.validator.validate_for_update(product)
        if not is_valid:
            raise ValueError(f"Validation failed: {error}")

    def _map_attributes(self, product: Product) -> dict:
        """Map attributes."""
        mapped_attrs = self.mapping_service.map_all_attributes(self.db, product)

        is_valid, error = self.validator.validate_mapped_attributes(
            mapped_attrs, product.id
        )
        if not is_valid:
            raise ValueError(f"Invalid attributes: {error}")

        return mapped_attrs

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
        result = await PluginWebSocketHelper.call_plugin(
            db=self.db,
            user_id=user_id,
            http_method=http_method,
            path=path,
            payload=payload,
            timeout=timeout,
            description=description,
        )
        return result

    def _update_vinted_product(
        self,
        vinted_product: VintedProduct,
        prix_vinted: float,
        title: str
    ):
        """Update local VintedProduct."""
        vinted_product.price = Decimal(str(prix_vinted))
        vinted_product.title = title
        self.db.commit()
