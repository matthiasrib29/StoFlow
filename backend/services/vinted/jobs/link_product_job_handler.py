"""
Link Product Job Handler

Gère la liaison VintedProduct → Product avec téléchargement d'images en arrière-plan.

Workflow:
1. Créer Product depuis VintedProduct (via VintedLinkService)
2. Télécharger images de Vinted vers R2
3. Commit

Author: Claude
Date: 2026-01-06
"""

from typing import Any

from sqlalchemy.orm import Session

from models.user.product import Product
from models.user.vinted_product import VintedProduct
from models.user.vinted_job import VintedJob
from services.vinted.vinted_link_service import VintedLinkService
from services.vinted.vinted_image_downloader import VintedImageDownloader
from shared.schema_utils import get_current_schema
from .base_job_handler import BaseJobHandler


class LinkProductJobHandler(BaseJobHandler):
    """
    Handler pour la liaison de produits Vinted.

    Workflow:
    1. Créer Product depuis VintedProduct (via VintedLinkService)
    2. Télécharger images en arrière-plan (async)
    3. Commit en BDD
    """

    ACTION_CODE = "link_product"

    async def execute(self, job: VintedJob) -> dict[str, Any]:
        """
        Lie un VintedProduct à un nouveau Product et télécharge les images.

        Args:
            job: VintedJob avec product_id = vinted_id dans ce cas

        Returns:
            {
                "success": bool,
                "product_id": int | None,
                "vinted_id": int,
                "images_copied": int,
                "images_failed": int,
                "total_images": int,
                "error": str | None
            }
        """
        # Note: job.product_id contient le vinted_id pour cette action
        vinted_id = job.product_id

        if not vinted_id:
            return {"success": False, "error": "vinted_id required"}

        try:
            self.log_start(f"Linking VintedProduct #{vinted_id}")

            # Get user_id from schema (user_123 -> 123)
            schema = get_current_schema(self.db)
            if not schema or not schema.startswith("user_"):
                self.log_error(f"Invalid schema: {schema}")
                return {"success": False, "error": "Invalid user schema"}

            user_id = int(schema.replace("user_", ""))

            # 1. Create Product from VintedProduct
            link_service = VintedLinkService(self.db)
            product, vinted_product = link_service.create_product_from_vinted(
                vinted_id=vinted_id,
                override_data=None
            )
            self.db.flush()  # Get product.id

            self.log_success(f"Product #{product.id} created from Vinted #{vinted_id}")

            # 2. Download images in background
            download_result = await VintedImageDownloader.download_and_attach_images(
                db=self.db,
                user_id=user_id,
                product_id=product.id,
                photos_data=vinted_product.photos_data
            )

            self.db.commit()

            self.log_success(
                f"Linked successfully: {download_result['images_copied']} images copied, "
                f"{download_result['images_failed']} failed"
            )

            return {
                "success": True,
                "product_id": product.id,
                "vinted_id": vinted_id,
                "images_copied": download_result["images_copied"],
                "images_failed": download_result["images_failed"],
                "total_images": download_result["total_images"],
            }

        except Exception as e:
            self.db.rollback()
            self.log_error(f"Failed to link Vinted #{vinted_id}: {e}", exc_info=True)
            return {
                "success": False,
                "vinted_id": vinted_id,
                "error": str(e)
            }
