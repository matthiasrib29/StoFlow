"""
Link Product Handler (Vinted)

Links VintedProduct → Product with granular image download tracking.

Workflow:
1. Create Product from VintedProduct (via VintedLinkService)
2. Create 1 MarketplaceTask per image (Option A - granular progress)
3. Download images from Vinted CDN to R2
4. Commit to database

Author: Claude
Date: 2026-01-07
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from models.user.marketplace_task import MarketplaceTaskType, TaskStatus
from services.vinted.vinted_link_service import VintedLinkService
from services.file_service import FileService
from services.product_service import ProductService
from shared.database import get_tenant_schema
from shared.logging_setup import get_logger
from ..base_handler import BaseMarketplaceHandler

logger = get_logger(__name__)


class LinkProductHandler(BaseMarketplaceHandler):
    """
    Handler for linking Vinted products to local products.

    Implements Option A: Creates 1 MarketplaceTask per image for
    granular progress tracking (e.g., "3/5 images downloaded").

    Workflow:
    1. Create Product from VintedProduct
    2. Create task for each image
    3. Download images in parallel (with concurrency limit)
    4. Update Product.images with R2 URLs
    """

    ACTION_CODE = "link_product"

    async def execute(self) -> dict[str, Any]:
        """
        Link a VintedProduct to a new Product and download images.

        Returns:
            {
                "success": bool,
                "product_id": int | None,
                "vinted_id": int,
                "images_downloaded": int,
                "images_failed": int,
                "total_images": int,
                "error": str | None
            }
        """
        # Note: job.product_id contains vinted_id for this action
        vinted_id = self.job.product_id

        if not vinted_id:
            return {"success": False, "error": "vinted_id required"}

        try:
            self.log_start(f"Linking VintedProduct #{vinted_id}")

            # Get user_id from schema_translate_map (returns "user_123" -> extract 123)
            schema = get_tenant_schema(self.db)
            if not schema or not schema.startswith("user_"):
                self.log_error(f"Invalid schema: {schema}")
                return {"success": False, "error": "Invalid user schema"}

            user_id = int(schema.replace("user_", ""))

            # 1. Create Product from VintedProduct
            link_service = VintedLinkService(self.db)
            product, vinted_product = link_service.create_product_from_vinted(
                vinted_id=vinted_id, override_data=None
            )
            self.db.flush()  # Get product.id

            self.log_success(f"Product #{product.id} created from Vinted #{vinted_id}")

            # 2. Parse photos data
            photos = self._parse_photos_data(vinted_product.photos_data)
            total_images = len(photos)

            if total_images == 0:
                self.log_warning("No images to download")
                self.db.commit()
                return {
                    "success": True,
                    "product_id": product.id,
                    "vinted_id": vinted_id,
                    "images_downloaded": 0,
                    "images_failed": 0,
                    "total_images": 0,
                }

            self.log_debug(f"Found {total_images} images to download")

            # 3. Create tasks for each image (Option A - granular tracking)
            image_tasks = []
            for i, photo in enumerate(photos):
                photo_url = photo.get("full_size_url") or photo.get("url")
                if not photo_url:
                    self.log_warning(f"Photo {i+1} has no URL, skipping")
                    continue

                task = await self.create_task(
                    task_type=MarketplaceTaskType.FILE_OPERATION,
                    description=f"Download image {i+1}/{total_images}",
                    product_id=product.id,
                    http_method="GET",
                    path=photo_url,
                    payload={"user_id": user_id, "product_id": product.id},
                )
                image_tasks.append((task, photo_url))

            self.db.commit()  # Commit tasks creation

            # 4. Download images with concurrency limit
            self.log_debug(f"Starting download of {len(image_tasks)} images...")
            download_results = await self._download_images_concurrent(
                image_tasks, user_id, product.id, max_concurrent=3
            )

            # 5. Update Product.images with R2 URLs
            r2_urls = [r["r2_url"] for r in download_results if r["success"]]
            if r2_urls:
                product_service = ProductService(self.db)
                product_service.update_product_images(product.id, r2_urls)

            self.db.commit()

            images_downloaded = sum(1 for r in download_results if r["success"])
            images_failed = sum(1 for r in download_results if not r["success"])

            self.log_success(
                f"Linked successfully: {images_downloaded}/{total_images} images downloaded, "
                f"{images_failed} failed"
            )

            return {
                "success": True,
                "product_id": product.id,
                "vinted_id": vinted_id,
                "images_downloaded": images_downloaded,
                "images_failed": images_failed,
                "total_images": total_images,
            }

        except Exception as e:
            self.db.rollback()
            self.log_error(f"Failed to link Vinted #{vinted_id}: {e}", exc_info=True)
            return {"success": False, "vinted_id": vinted_id, "error": str(e)}

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def _parse_photos_data(self, photos_data: str | None) -> list[dict]:
        """
        Parse JSON photos data.

        Args:
            photos_data: JSON string with Vinted photos

        Returns:
            List of photo dicts
        """
        if not photos_data:
            return []

        try:
            photos = json.loads(photos_data)
            return photos if isinstance(photos, list) else []
        except json.JSONDecodeError as e:
            self.log_error(f"Failed to parse photos_data: {e}")
            return []

    async def _download_images_concurrent(
        self,
        image_tasks: list[tuple],
        user_id: int,
        product_id: int,
        max_concurrent: int = 3,
    ) -> list[dict]:
        """
        Download images concurrently with rate limiting.

        Args:
            image_tasks: List of (MarketplaceTask, photo_url) tuples
            user_id: User ID for R2 path
            product_id: Product ID for R2 path
            max_concurrent: Max concurrent downloads

        Returns:
            List of {"success": bool, "r2_url": str | None, "task_id": int}
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        results = []

        async def download_single(task, photo_url):
            async with semaphore:
                return await self._download_single_image(
                    task, photo_url, user_id, product_id
                )

        # Execute all downloads concurrently (with semaphore limit)
        tasks = [download_single(task, url) for task, url in image_tasks]
        results = await asyncio.gather(*tasks, return_exceptions=False)

        return results

    async def _download_single_image(
        self, task, photo_url: str, user_id: int, product_id: int
    ) -> dict:
        """
        Download a single image and update task status.

        Args:
            task: MarketplaceTask to track
            photo_url: Vinted CDN URL
            user_id: User ID
            product_id: Product ID

        Returns:
            {"success": bool, "r2_url": str | None, "task_id": int}
        """
        # Mark task as processing
        task.status = TaskStatus.PROCESSING
        task.started_at = datetime.now(timezone.utc)
        self.db.commit()

        # Retry logic with exponential backoff
        max_retries = 3
        r2_url = None

        for attempt in range(max_retries):
            try:
                r2_url = await FileService.download_and_upload_from_url(
                    user_id=user_id,
                    product_id=product_id,
                    image_url=photo_url,
                    timeout=45.0,
                )

                # Success
                task.status = TaskStatus.SUCCESS
                task.result = {"r2_url": r2_url}
                task.completed_at = datetime.now(timezone.utc)
                self.db.commit()

                self.log_debug(
                    f"Task #{task.id} completed: {task.description} -> {r2_url}"
                )

                return {"success": True, "r2_url": r2_url, "task_id": task.id}

            except Exception as e:
                if attempt < max_retries - 1:
                    # Retry with exponential backoff
                    wait_time = 2**attempt
                    self.log_warning(
                        f"Task #{task.id} attempt {attempt+1} failed, "
                        f"retrying in {wait_time}s: {e}"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    # Max retries reached
                    task.status = TaskStatus.FAILED
                    task.error_message = f"Max retries reached: {str(e)}"
                    task.completed_at = datetime.now(timezone.utc)
                    self.db.commit()

                    self.log_error(
                        f"Task #{task.id} failed after {max_retries} attempts: {e}"
                    )

                    return {"success": False, "r2_url": None, "task_id": task.id}

        # Should never reach here
        return {"success": False, "r2_url": None, "task_id": task.id}
