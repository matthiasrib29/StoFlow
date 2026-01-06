"""
Product Image Service

Service for managing product images (JSONB operations).

Business Rules:
- Maximum 20 images per product (Vinted limit)
- Images stored in JSONB: [{url, order, created_at}, ...]
- Auto-reorder when adding/deleting images

Created: 2026-01-06
Author: Claude
"""

from sqlalchemy.orm import Session

from models.user.product import Product, ProductStatus
from repositories.product_repository import ProductRepository
from shared.datetime_utils import utc_now
from shared.logging_setup import get_logger

logger = get_logger(__name__)

# Maximum images per product (Vinted limit)
MAX_IMAGES_PER_PRODUCT = 20


class ProductImageService:
    """Service for product image operations."""

    @staticmethod
    def add_image(
        db: Session, product_id: int, image_url: str, display_order: int | None = None
    ) -> dict:
        """
        Add an image to a product (JSONB).

        Business Rules (Updated 2026-01-06):
        - Maximum 20 images per product (Vinted limit)
        - Verify product exists and is not deleted
        - display_order auto-calculated if not provided (append at end)
        - Images stored in JSONB: [{url, order, created_at}, ...]

        ⚠️ IMPORTANT: This method does NOT commit the transaction.
        The caller is responsible for calling db.commit() or relying on
        FastAPI's auto-commit from get_db() dependency.

        Args:
            db: SQLAlchemy Session
            product_id: Product ID
            image_url: Image URL (CDN)
            display_order: Display order (auto if None)

        Returns:
            dict: Created image {url, order, created_at}

        Raises:
            ValueError: If product not found or limit reached
        """
        product = ProductRepository.get_by_id(db, product_id)
        if not product:
            raise ValueError(f"Product with id {product_id} not found")

        # BUSINESS RULE: Cannot add images to SOLD products
        if product.status == ProductStatus.SOLD:
            raise ValueError(
                "Cannot add images to SOLD product. Product is locked after sale."
            )

        # Get current images (ensure list)
        images = product.images or []

        # Check 20 images limit
        if len(images) >= MAX_IMAGES_PER_PRODUCT:
            raise ValueError(
                f"Product already has {len(images)} images (max {MAX_IMAGES_PER_PRODUCT})"
            )

        # Auto-calculate display_order if not provided
        if display_order is None:
            display_order = len(images)

        # Create new image entry
        new_image = {
            "url": image_url,
            "order": display_order,
            "created_at": utc_now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        }

        # Append to images list
        images.append(new_image)
        product.images = images
        # NOTE: Transaction is NOT committed here
        # Caller is responsible for calling db.commit() or db.flush()

        logger.debug(
            f"[ProductImageService] Image added: product_id={product_id}, "
            f"url={image_url[:50]}..., order={display_order}"
        )

        return new_image

    @staticmethod
    def delete_image(db: Session, product_id: int, image_url: str) -> bool:
        """
        Delete an image by URL.

        Business Rules (Updated 2026-01-03):
        - Remove JSONB entry
        - CDN file must be deleted by FileService (R2)
        - Auto-reorder remaining images

        Args:
            db: SQLAlchemy Session
            product_id: Product ID
            image_url: Image URL to delete

        Returns:
            bool: True if deleted, False if not found
        """
        product = ProductRepository.get_by_id(db, product_id)
        if not product:
            return False

        images = product.images or []

        # Filter out the image to delete
        new_images = [img for img in images if img.get("url") != image_url]

        if len(new_images) == len(images):
            return False  # Image not found

        # Reorder remaining images (0, 1, 2, ...)
        for i, img in enumerate(new_images):
            img["order"] = i

        product.images = new_images
        db.commit()

        logger.debug(
            f"[ProductImageService] Image deleted: product_id={product_id}, "
            f"url={image_url[:50]}..."
        )

        return True

    @staticmethod
    def reorder_images(
        db: Session, product_id: int, ordered_urls: list[str]
    ) -> list[dict]:
        """
        Reorder product images.

        Business Rules (Updated 2026-01-03):
        - ordered_urls: list of URLs in new order
        - Order in list determines display_order (0, 1, 2, ...)
        - Verify all URLs belong to the product

        Args:
            db: SQLAlchemy Session
            product_id: Product ID
            ordered_urls: List of URLs in desired order

        Returns:
            list[dict]: Reordered images

        Raises:
            ValueError: If a URL doesn't belong to the product
        """
        product = ProductRepository.get_by_id(db, product_id)
        if not product:
            raise ValueError(f"Product with id {product_id} not found")

        images = product.images or []
        current_urls = {img.get("url") for img in images}

        # Verify all URLs exist
        for url in ordered_urls:
            if url not in current_urls:
                raise ValueError(
                    f"Image URL not found in product {product_id}: {url}"
                )

        # Build URL -> image mapping
        url_to_image = {img.get("url"): img for img in images}

        # Reorder based on ordered_urls
        reordered = []
        for i, url in enumerate(ordered_urls):
            img = url_to_image[url].copy()
            img["order"] = i
            reordered.append(img)

        product.images = reordered
        db.commit()
        db.refresh(product)

        logger.debug(
            f"[ProductImageService] Images reordered: product_id={product_id}, "
            f"count={len(reordered)}"
        )

        return product.images

    @staticmethod
    def get_images(db: Session, product_id: int) -> list[dict]:
        """
        Get all images for a product.

        Args:
            db: SQLAlchemy Session
            product_id: Product ID

        Returns:
            list[dict]: List of images or empty list if product not found
        """
        product = ProductRepository.get_by_id(db, product_id)
        if not product:
            return []

        return product.images or []

    @staticmethod
    def get_image_count(db: Session, product_id: int) -> int:
        """
        Get image count for a product.

        Args:
            db: SQLAlchemy Session
            product_id: Product ID

        Returns:
            int: Number of images (0 if product not found)
        """
        product = ProductRepository.get_by_id(db, product_id)
        if not product:
            return 0

        return len(product.images or [])


__all__ = ["ProductImageService", "MAX_IMAGES_PER_PRODUCT"]
