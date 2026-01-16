"""
Product Image Repository.

Repository for ProductImage data access operations.
Follows the repository pattern with static methods.
"""

from sqlalchemy import select, update, delete
from sqlalchemy.orm import Session

from models.user.product_image import ProductImage


class ProductImageRepository:
    """Repository for ProductImage CRUD operations."""

    @staticmethod
    def get_by_id(db: Session, image_id: int) -> ProductImage | None:
        """
        Fetch a single product image by ID.

        Args:
            db: SQLAlchemy Session
            image_id: Image ID

        Returns:
            ProductImage if found, None otherwise
        """
        return db.scalar(select(ProductImage).where(ProductImage.id == image_id))

    @staticmethod
    def get_by_product(db: Session, product_id: int) -> list[ProductImage]:
        """
        Fetch all images for a product, ordered by display order.

        Args:
            db: SQLAlchemy Session
            product_id: Product ID

        Returns:
            List of ProductImage ordered by order ASC
        """
        return list(
            db.scalars(
                select(ProductImage)
                .where(ProductImage.product_id == product_id)
                .order_by(ProductImage.order)
            )
        )

    @staticmethod
    def get_photos_only(db: Session, product_id: int) -> list[ProductImage]:
        """
        Fetch product photos only (excludes labels).

        Used for marketplace publishing.

        Args:
            db: SQLAlchemy Session
            product_id: Product ID

        Returns:
            List of ProductImage where is_label=False, ordered by order ASC
        """
        return list(
            db.scalars(
                select(ProductImage)
                .where(
                    ProductImage.product_id == product_id,
                    ProductImage.is_label.is_(False),
                )
                .order_by(ProductImage.order)
            )
        )

    @staticmethod
    def get_label(db: Session, product_id: int) -> ProductImage | None:
        """
        Fetch label image (internal price tag).

        Should only be 0 or 1 label per product.

        Args:
            db: SQLAlchemy Session
            product_id: Product ID

        Returns:
            ProductImage if label exists, None otherwise
        """
        return db.scalar(
            select(ProductImage).where(
                ProductImage.product_id == product_id,
                ProductImage.is_label.is_(True),
            )
        )

    @staticmethod
    def create(
        db: Session,
        product_id: int,
        url: str,
        order: int,
        **kwargs,
    ) -> ProductImage:
        """
        Insert a new product image.

        Does NOT commit - caller controls transaction.

        Args:
            db: SQLAlchemy Session
            product_id: Product ID
            url: Image URL (CDN)
            order: Display order (0-indexed)
            **kwargs: Optional metadata (is_label, alt_text, tags, mime_type,
                      file_size, width, height)

        Returns:
            Created ProductImage instance (not yet committed)
        """
        image = ProductImage(
            product_id=product_id,
            url=url,
            order=order,
            **kwargs,
        )
        db.add(image)
        return image

    @staticmethod
    def delete(db: Session, image_id: int) -> bool:
        """
        Delete a product image by ID.

        Does NOT commit - caller controls transaction.

        Args:
            db: SQLAlchemy Session
            image_id: Image ID to delete

        Returns:
            True if deleted, False if not found
        """
        result = db.execute(
            delete(ProductImage).where(ProductImage.id == image_id)
        )
        return result.rowcount > 0

    @staticmethod
    def update_order(db: Session, image_id: int, new_order: int) -> ProductImage | None:
        """
        Update display order of an image.

        Does NOT commit - caller controls transaction.

        Args:
            db: SQLAlchemy Session
            image_id: Image ID
            new_order: New display order

        Returns:
            Updated ProductImage if found, None otherwise
        """
        db.execute(
            update(ProductImage)
            .where(ProductImage.id == image_id)
            .values(order=new_order)
        )
        return ProductImageRepository.get_by_id(db, image_id)

    @staticmethod
    def set_label_flag(
        db: Session, image_id: int, is_label: bool
    ) -> ProductImage | None:
        """
        Toggle is_label flag on an image.

        Does NOT commit - caller controls transaction.

        Args:
            db: SQLAlchemy Session
            image_id: Image ID
            is_label: Whether this is a label

        Returns:
            Updated ProductImage if found, None otherwise
        """
        db.execute(
            update(ProductImage)
            .where(ProductImage.id == image_id)
            .values(is_label=is_label)
        )
        return ProductImageRepository.get_by_id(db, image_id)
