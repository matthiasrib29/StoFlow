"""
Vinted Image Synchronization Service

Service for downloading and syncing images from Vinted to R2 storage.
Extracted from api/vinted/products.py link_product() for better maintainability.

Created: 2026-01-08
Author: Claude
"""

import asyncio
import json
from typing import Optional

from sqlalchemy.orm import Session

from models.user.vinted_product import VintedProduct
from models.user.product import Product
from services.file_service import FileService
from services.product_service import ProductService
from shared.logging import get_logger

logger = get_logger(__name__)


class VintedImageSyncService:
    """Service for syncing Vinted images to Product storage (R2)."""

    @staticmethod
    def parse_photos_data(photos_data: str) -> list[dict]:
        """
        Parse photos_data JSON string from VintedProduct.

        Args:
            photos_data: JSON string containing photo URLs

        Returns:
            List of photo dictionaries, empty list if parsing fails
        """
        if not photos_data:
            return []

        try:
            photos = json.loads(photos_data)
            logger.debug(f"[VintedImageSync] Parsed {len(photos)} photos from photos_data")
            return photos if isinstance(photos, list) else []
        except json.JSONDecodeError as e:
            logger.error(f"[VintedImageSync] Failed to parse photos_data: {e}", exc_info=True)
            return []

    @staticmethod
    async def download_with_retry(
        user_id: int,
        product_id: int,
        photo_url: str,
        max_retries: int = 3,
        timeout: float = 45.0
    ) -> Optional[str]:
        """
        Download image with exponential backoff retry logic.

        Args:
            user_id: User ID for R2 path
            product_id: Product ID for R2 path
            photo_url: URL of image to download
            max_retries: Maximum retry attempts (default 3)
            timeout: Timeout per attempt in seconds (default 45)

        Returns:
            R2 URL of uploaded image, or None if all retries failed
        """
        for attempt in range(max_retries):
            try:
                r2_url = await FileService.download_and_upload_from_url(
                    user_id=user_id,
                    product_id=product_id,
                    image_url=photo_url,
                    timeout=timeout
                )
                return r2_url

            except Exception as retry_error:
                if attempt < max_retries - 1:
                    delay = 1.0 * (2 ** attempt)  # 1s, 2s, 4s
                    logger.warning(
                        f"[VintedImageSync] Attempt {attempt+1}/{max_retries} failed: "
                        f"{type(retry_error).__name__}: {retry_error}. "
                        f"Retrying in {delay}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"[VintedImageSync] FAILED after {max_retries} attempts: "
                        f"{type(retry_error).__name__}: {retry_error}"
                    )

        return None

    @staticmethod
    async def sync_images_to_product(
        db: Session,
        vinted_product: VintedProduct,
        product: Product,
        user_id: int,
        delay_between_downloads: float = 0.5
    ) -> tuple[int, int]:
        """
        Sync all images from VintedProduct to Product (R2 storage).

        This method:
        1. Parses photos_data JSON
        2. Downloads each image with retry logic
        3. Uploads to R2 storage
        4. Adds image URLs to Product.images JSONB

        Args:
            db: SQLAlchemy session
            vinted_product: Source VintedProduct with photos_data
            product: Target Product to add images to
            user_id: User ID for R2 path
            delay_between_downloads: Delay between downloads to avoid rate limiting (default 0.5s)

        Returns:
            Tuple (images_copied, images_failed)

        Raises:
            Exception: On critical errors (database, etc.)
        """
        images_copied = 0
        images_failed = 0

        photos = VintedImageSyncService.parse_photos_data(vinted_product.photos_data)

        if not photos:
            logger.info(f"[VintedImageSync] No photos to sync for product {product.id}")
            return (0, 0)

        logger.info(
            f"[VintedImageSync] Starting sync of {len(photos)} images "
            f"from Vinted to R2 for product {product.id}"
        )

        # Log all photos for debugging
        for idx, photo in enumerate(photos):
            if isinstance(photo, dict):
                photo_url = photo.get("full_size_url") or photo.get("url")
                logger.debug(
                    f"[VintedImageSync] Photo {idx}: "
                    f"url={photo_url[:80] if photo_url else 'None'}..."
                )
            else:
                logger.warning(f"[VintedImageSync] Photo {idx} is not a dict: {type(photo)}")

        for i, photo in enumerate(photos):
            # Add delay between downloads (except first)
            if i > 0:
                await asyncio.sleep(delay_between_downloads)

            # Extract URL (prefer full_size_url for original quality)
            if not isinstance(photo, dict):
                logger.warning(f"[VintedImageSync] Photo {i} is not a dict, skipping")
                images_failed += 1
                continue

            photo_url = photo.get("full_size_url") or photo.get("url")
            if not photo_url:
                logger.warning(
                    f"[VintedImageSync] Photo {i} has no URL, "
                    f"keys present: {list(photo.keys())}"
                )
                images_failed += 1
                continue

            logger.info(
                f"[VintedImageSync] Downloading image {i+1}/{len(photos)}: "
                f"{photo_url[:100]}..."
            )

            # Download with retry logic
            r2_url = await VintedImageSyncService.download_with_retry(
                user_id=user_id,
                product_id=product.id,
                photo_url=photo_url
            )

            if r2_url:
                # Add image to product (JSONB array)
                ProductService.add_image(
                    db=db,
                    product_id=product.id,
                    image_url=r2_url,
                    display_order=images_copied
                )
                images_copied += 1
                logger.info(f"[VintedImageSync] Image {i+1} uploaded successfully: {r2_url}")
            else:
                images_failed += 1

        # Log summary
        if images_failed > 0:
            logger.warning(
                f"[VintedImageSync] {images_failed}/{len(photos)} images "
                f"failed to copy for product {product.id}"
            )

        logger.info(
            f"[VintedImageSync] Completed: {images_copied} images copied, "
            f"{images_failed} failed for product {product.id}"
        )

        return (images_copied, images_failed)
