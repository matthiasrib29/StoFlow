"""
Vinted Link Product Service - Service wrapper for product linking

Wraps VintedLinkService and VintedImageDownloader to follow standard pattern.

Author: Claude
Date: 2026-01-15
"""

from typing import Any
from sqlalchemy.orm import Session

from services.vinted.vinted_link_service import VintedLinkService
from services.vinted.vinted_image_downloader import VintedImageDownloader
from shared.database import get_tenant_schema


class VintedLinkProductService:
    """
    Service for linking VintedProduct to Product with image download.

    Wraps VintedLinkService + VintedImageDownloader to provide
    consistent interface with other Vinted services.
    """

    def __init__(self, db: Session):
        """
        Initialize link product service.

        Args:
            db: Database session
        """
        self.db = db

    async def link_product(
        self,
        vinted_product_id: int,
        product_id: int | None,
        user_id: int
    ) -> dict[str, Any]:
        """
        Link VintedProduct to Product and download images.

        Note: product_id parameter is unused, kept for signature compatibility.
        The new Product is always created from VintedProduct.

        Args:
            vinted_product_id: Vinted product ID
            product_id: Unused (Product is created, not linked to existing)
            user_id: User ID

        Returns:
            dict: {
                "success": bool,
                "product_id": int | None,
                "vinted_id": int,
                "images_copied": int,
                "images_failed": int,
                "total_images": int,
                "linked": bool,
                "error": str | None
            }
        """
        try:
            # Verify user schema
            schema = get_tenant_schema(self.db)
            if not schema or not schema.startswith("user_"):
                return {
                    "success": False,
                    "linked": False,
                    "error": "Invalid user schema"
                }

            # Create Product from VintedProduct
            link_service = VintedLinkService(self.db)
            product, vinted_product = link_service.create_product_from_vinted(
                vinted_id=vinted_product_id,
                override_data=None
            )
            self.db.flush()  # Get product.id

            # Download images in background
            download_result = await VintedImageDownloader.download_and_attach_images(
                db=self.db,
                user_id=user_id,
                product_id=product.id,
                photos_data=vinted_product.photos_data
            )

            self.db.commit()

            return {
                "success": True,
                "linked": True,
                "product_id": product.id,
                "vinted_id": vinted_product_id,
                "images_copied": download_result["images_copied"],
                "images_failed": download_result["images_failed"],
                "total_images": download_result["total_images"],
            }

        except Exception as e:
            self.db.rollback()
            return {
                "success": False,
                "linked": False,
                "vinted_id": vinted_product_id,
                "error": str(e)
            }
