"""
Product Image Service

Service for managing product images using product_images table.

Business Rules:
- Maximum 20 images per product (Vinted limit)
- Images stored in product_images table
- Auto-reorder when adding/deleting images
- Only one label per product allowed

Refactored: 2026-01-15 (Phase 3.2)
Author: Claude
"""

from sqlalchemy.orm import Session
from typing import Optional

from models.user.product import Product, ProductStatus
from models.user.product_image import ProductImage
from repositories.product_repository import ProductRepository
from repositories.product_image_repository import ProductImageRepository
from shared.logging_setup import get_logger

logger = get_logger(__name__)

# Maximum images per product (Vinted limit)
MAX_IMAGES_PER_PRODUCT = 20


class ProductImageService:
    """Service for product image operations."""

    @staticmethod
    def add_image(
        db: Session,
        product_id: int,
        image_url: str,
        display_order: int | None = None,
        **kwargs  # NEW: mime_type, file_size, width, height, alt_text, tags, is_label
    ) -> dict:
        """
        Add an image to a product.

        Business Rules:
        - Maximum 20 images per product (Vinted limit)
        - Verify product exists and is not SOLD
        - display_order auto-calculated if not provided (append at end)
        - Images stored in product_images table

        Args:
            db: SQLAlchemy Session
            product_id: Product ID
            image_url: Image URL (CDN)
            display_order: Display order (auto if None)
            **kwargs: Optional metadata (mime_type, file_size, width, height, alt_text, tags, is_label)

        Returns:
            dict: Created image (compatible with old JSONB format for API)

        Raises:
            ValueError: If product not found, SOLD status, or limit reached
        """
        product = ProductRepository.get_by_id(db, product_id)
        if not product:
            raise ValueError(f"Product with id {product_id} not found")

        if product.status == ProductStatus.SOLD:
            raise ValueError("Cannot add images to SOLD product.")

        # Get current image count from table
        current_images = ProductImageRepository.get_by_product(db, product_id)

        if len(current_images) >= MAX_IMAGES_PER_PRODUCT:
            raise ValueError(
                f"Product already has {len(current_images)} images (max {MAX_IMAGES_PER_PRODUCT})"
            )

        # Auto-calculate display_order if not provided
        if display_order is None:
            display_order = len(current_images)

        # Create image in table
        image = ProductImageRepository.create(
            db,
            product_id=product_id,
            url=image_url,
            order=display_order,
            **kwargs  # Pass through metadata
        )

        db.flush()  # Get ID without committing

        logger.debug(
            f"[ProductImageService] Image added: product_id={product_id}, "
            f"id={image.id}, url={image_url[:50]}..., order={display_order}"
        )

        # Return dict for API backward compatibility
        return _image_to_dict(image)

    @staticmethod
    def delete_image(db: Session, product_id: int, image_url: str) -> bool:
        """
        Delete an image by URL.

        Business Rules:
        - Remove from product_images table
        - Auto-reorder remaining images (gap filling)
        - CDN file must be deleted by FileService (R2)

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

        # Find image by URL
        images = ProductImageRepository.get_by_product(db, product_id)
        image_to_delete = next((img for img in images if img.url == image_url), None)

        if not image_to_delete:
            return False

        # Delete image
        ProductImageRepository.delete(db, image_to_delete.id)

        # Reorder remaining images (fill gap)
        remaining = [img for img in images if img.id != image_to_delete.id]
        for new_order, img in enumerate(remaining):
            ProductImageRepository.update_order(db, img.id, new_order)

        db.commit()

        logger.debug(
            f"[ProductImageService] Image deleted: product_id={product_id}, "
            f"id={image_to_delete.id}, url={image_url[:50]}..."
        )

        return True

    @staticmethod
    def reorder_images(
        db: Session, product_id: int, ordered_urls: list[str]
    ) -> list[dict]:
        """
        Reorder product images.

        Business Rules:
        - ordered_urls: list of URLs in new order
        - Order in list determines display_order (0, 1, 2, ...)
        - Verify all URLs belong to the product

        Args:
            db: SQLAlchemy Session
            product_id: Product ID
            ordered_urls: List of URLs in desired order

        Returns:
            list[dict]: Reordered images (API format)

        Raises:
            ValueError: If a URL doesn't belong to the product
        """
        product = ProductRepository.get_by_id(db, product_id)
        if not product:
            raise ValueError(f"Product with id {product_id} not found")

        images = ProductImageRepository.get_by_product(db, product_id)
        url_to_image = {img.url: img for img in images}

        # Verify all URLs exist
        for url in ordered_urls:
            if url not in url_to_image:
                raise ValueError(f"Image URL not found in product {product_id}: {url}")

        # Update orders
        for new_order, url in enumerate(ordered_urls):
            image = url_to_image[url]
            ProductImageRepository.update_order(db, image.id, new_order)

        db.commit()
        db.flush()

        # Fetch updated images
        updated_images = ProductImageRepository.get_by_product(db, product_id)

        logger.debug(
            f"[ProductImageService] Images reordered: product_id={product_id}, "
            f"count={len(updated_images)}"
        )

        # Return as dicts for API
        return [_image_to_dict(img) for img in updated_images]

    @staticmethod
    def get_images(db: Session, product_id: int) -> list[dict]:
        """
        Get all images for a product (photos + label).

        Args:
            db: SQLAlchemy Session
            product_id: Product ID

        Returns:
            list[dict]: List of images or empty list if product not found
        """
        product = ProductRepository.get_by_id(db, product_id)
        if not product:
            return []

        images = ProductImageRepository.get_by_product(db, product_id)
        return [_image_to_dict(img) for img in images]

    @staticmethod
    def get_image_count(db: Session, product_id: int) -> int:
        """
        Get image count for a product (photos + label).

        Args:
            db: SQLAlchemy Session
            product_id: Product ID

        Returns:
            int: Number of images (0 if product not found)
        """
        product = ProductRepository.get_by_id(db, product_id)
        if not product:
            return 0

        return len(ProductImageRepository.get_by_product(db, product_id))

    @staticmethod
    def get_product_photos(db: Session, product_id: int) -> list[dict]:
        """
        Get product photos only (excludes labels).

        Used for marketplace publishing (Vinted, eBay, Etsy).

        Args:
            db: SQLAlchemy Session
            product_id: Product ID

        Returns:
            list[dict]: Product photos (is_label=False) ordered by display order
        """
        product = ProductRepository.get_by_id(db, product_id)
        if not product:
            return []

        photos = ProductImageRepository.get_photos_only(db, product_id)
        return [_image_to_dict(img) for img in photos]

    @staticmethod
    def get_label_image(db: Session, product_id: int) -> dict | None:
        """
        Get label image (internal price tag).

        Args:
            db: SQLAlchemy Session
            product_id: Product ID

        Returns:
            dict | None: Label image if exists, else None
        """
        product = ProductRepository.get_by_id(db, product_id)
        if not product:
            return None

        label = ProductImageRepository.get_label(db, product_id)
        return _image_to_dict(label) if label else None

    @staticmethod
    def set_label_flag(
        db: Session, product_id: int, image_id: int, is_label: bool
    ) -> dict:
        """
        Set or unset label flag on an image.

        Business Rules:
        - Only one label allowed per product
        - If setting is_label=True on another image, unset previous label
        - Verify image belongs to product

        Args:
            db: SQLAlchemy Session
            product_id: Product ID
            image_id: Image ID
            is_label: Whether this is a label

        Returns:
            dict: Updated image

        Raises:
            ValueError: If image not found or doesn't belong to product
        """
        # Verify image belongs to product
        image = ProductImageRepository.get_by_id(db, image_id)
        if not image or image.product_id != product_id:
            raise ValueError(f"Image {image_id} not found in product {product_id}")

        # If setting as label, unset any existing label
        if is_label:
            existing_label = ProductImageRepository.get_label(db, product_id)
            if existing_label and existing_label.id != image_id:
                ProductImageRepository.set_label_flag(db, existing_label.id, False)

        # Set flag on target image
        updated_image = ProductImageRepository.set_label_flag(db, image_id, is_label)
        db.commit()

        logger.debug(
            f"[ProductImageService] Label flag updated: product_id={product_id}, "
            f"image_id={image_id}, is_label={is_label}"
        )

        return _image_to_dict(updated_image)


def _image_to_dict(image: ProductImage) -> dict:
    """Convert ProductImage model to dict (API format)."""
    return {
        "id": image.id,
        "url": image.url,
        "order": image.order,
        "is_label": image.is_label,
        "alt_text": image.alt_text,
        "tags": image.tags,
        "mime_type": image.mime_type,
        "file_size": image.file_size,
        "width": image.width,
        "height": image.height,
        "created_at": image.created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "updated_at": image.updated_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


__all__ = ["ProductImageService", "MAX_IMAGES_PER_PRODUCT"]
