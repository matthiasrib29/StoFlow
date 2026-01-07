"""
Vinted Image Downloader

Service pour télécharger les images depuis Vinted et les uploader vers R2.
Utilisé par LinkProductJobHandler pour le téléchargement en arrière-plan.

Author: Claude
Date: 2026-01-06
"""

import asyncio
import json
from typing import Dict, Any

from sqlalchemy.orm import Session

from services.file_service import FileService
from services.product_service import ProductService
from shared.logging_setup import get_logger

logger = get_logger(__name__)


class VintedImageDownloader:
    """Downloads images from Vinted and uploads to R2."""

    @staticmethod
    async def download_and_attach_images(
        db: Session,
        user_id: int,
        product_id: int,
        photos_data: str | None
    ) -> Dict[str, Any]:
        """
        Download images from Vinted and attach to Product.

        Args:
            db: SQLAlchemy session
            user_id: User ID for R2 path
            product_id: Product ID to attach images to
            photos_data: JSON string with Vinted photos

        Returns:
            {
                "images_copied": int,
                "images_failed": int,
                "total_images": int
            }
        """
        images_copied = 0
        images_failed = 0

        if not photos_data:
            logger.info(f"[ImageDownloader] No photos_data for product {product_id}")
            return {"images_copied": 0, "images_failed": 0, "total_images": 0}

        try:
            photos = json.loads(photos_data)
        except json.JSONDecodeError as e:
            logger.error(f"[ImageDownloader] Failed to parse photos_data: {e}")
            return {"images_copied": 0, "images_failed": 0, "total_images": 0}

        total_images = len(photos)
        logger.info(
            f"[ImageDownloader] Starting download of {total_images} images "
            f"for product {product_id}"
        )

        for i, photo in enumerate(photos):
            # Delay between downloads (except first)
            if i > 0:
                await asyncio.sleep(0.5)

            photo_url = photo.get("full_size_url") or photo.get("url")
            if not photo_url:
                logger.warning(
                    f"[ImageDownloader] Photo {i} has no URL, "
                    f"keys: {list(photo.keys()) if isinstance(photo, dict) else 'N/A'}"
                )
                images_failed += 1
                continue

            logger.info(
                f"[ImageDownloader] Downloading image {i+1}/{total_images}: "
                f"{photo_url[:100]}..."
            )

            # Retry logic with exponential backoff
            max_retries = 3
            r2_url = None

            for attempt in range(max_retries):
                try:
                    r2_url = await FileService.download_and_upload_from_url(
                        user_id=user_id,
                        product_id=product_id,
                        image_url=photo_url,
                        timeout=45.0
                    )
                    break  # Success
                except Exception as retry_error:
                    if attempt < max_retries - 1:
                        delay = 1.0 * (2 ** attempt)  # 1s, 2s, 4s
                        logger.warning(
                            f"[ImageDownloader] Image {i+1} attempt {attempt+1} failed: "
                            f"{type(retry_error).__name__}: {retry_error}. "
                            f"Retrying in {delay}s..."
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            f"[ImageDownloader] Image {i+1} FAILED after {max_retries} attempts: "
                            f"{type(retry_error).__name__}: {retry_error}"
                        )
                        images_failed += 1

            if r2_url:
                # Add image to product
                ProductService.add_image(
                    db=db,
                    product_id=product_id,
                    image_url=r2_url,
                    display_order=images_copied
                )
                images_copied += 1
                logger.info(
                    f"[ImageDownloader] Image {i+1}/{total_images} uploaded successfully: "
                    f"{r2_url[:80]}..."
                )

        logger.info(
            f"[ImageDownloader] Completed: {images_copied} copied, "
            f"{images_failed} failed for product {product_id}"
        )

        return {
            "images_copied": images_copied,
            "images_failed": images_failed,
            "total_images": total_images
        }
