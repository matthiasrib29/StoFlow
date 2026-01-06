"""
Product Service

Service for product business logic.

Business Rules (Updated 2025-12-09):
- Auto-incremented ID as unique identifier (PostgreSQL SERIAL)
- Price calculated automatically if absent
- Size adjusted automatically based on dimensions
- Auto-create size if missing
- Strict FK validation (brand, category, condition must exist)
- Status MVP: DRAFT, PUBLISHED, SOLD, ARCHIVED only
- Soft delete (deleted_at instead of physical deletion)

Refactored: 2026-01-06
- Extracted image operations to ProductImageService
- Extracted status management to ProductStatusManager
- Migrated DB operations to ProductRepository
"""

from typing import Optional

from sqlalchemy.orm import Session

from models.user.product import Product, ProductStatus
from repositories.product_attribute_repository import ProductAttributeRepository
from repositories.product_repository import ProductRepository
from schemas.product_schemas import ProductCreate, ProductUpdate
from services.pricing_service import PricingService
from services.product_image_service import ProductImageService
from services.product_status_manager import ProductStatusManager
from services.product_utils import ProductUtils
from services.validators import AttributeValidator
from shared.datetime_utils import utc_now
from shared.logging_setup import get_logger

logger = get_logger(__name__)


class ProductService:
    """Service for product management."""

    @staticmethod
    def create_product(db: Session, product_data: ProductCreate, user_id: int) -> Product:
        """
        Create a new product with all PostEditFlet features.

        Business Rules (Updated 2025-12-09):
        - Auto-incremented ID as unique identifier (PostgreSQL SERIAL)
        - Price calculated automatically if absent (PricingService)
        - Size adjusted automatically if dim1/dim6 provided (W{dim1}/L{dim6})
        - Auto-create size if missing (vintage unique piece)
        - Strict brand validation (no auto-creation)
        - Default status: DRAFT
        - Default stock_quantity: 1 (unique piece)

        Args:
            db: SQLAlchemy Session
            product_data: Product data to create
            user_id: User ID (for user_X schema)

        Returns:
            Product: Created product

        Raises:
            ValueError: If a FK attribute is invalid (brand, category, condition, etc.)
        """
        import time
        start_time = time.time()

        logger.info(
            f"[ProductService] Starting create_product: user_id={user_id}, "
            f"title={product_data.title[:50] if product_data.title else 'N/A'}, "
            f"category={product_data.category}, brand={product_data.brand}"
        )

        # ===== 1. ADJUST SIZE IF DIMENSIONS PROVIDED (Business Rule 2025-12-09) =====
        size_original = ProductUtils.adjust_size(
            product_data.size_original,
            product_data.dim1,
            product_data.dim6
        )

        # ===== 2. AUTO-CREATE SIZE ORIGINAL IF PROVIDED (Business Rule 2026-01-06) =====
        if size_original:
            from repositories.size_original_repository import SizeOriginalRepository
            SizeOriginalRepository.get_or_create(db, size_original)

        # ===== 3. CALCULATE PRICE IF ABSENT (Business Rule 2025-12-09) =====
        price = product_data.price
        if not price:
            price = PricingService.calculate_price(
                db=db,
                brand=product_data.brand,
                category=product_data.category,
                condition=product_data.condition,
                rarity=None,
                quality=None,
            )

        # ===== 4. VALIDATE ATTRIBUTES (Refactored 2025-12-09) =====
        validation_data = product_data.model_dump()
        validation_data['size_original'] = size_original  # Use adjusted size
        AttributeValidator.validate_product_attributes(db, validation_data)

        # ===== 5. CREATE PRODUCT =====
        product = Product(
            title=product_data.title,
            description=product_data.description,
            price=price,
            category=product_data.category,
            brand=product_data.brand,
            condition=product_data.condition,
            size_original=size_original,
            color=product_data.color,
            material=product_data.material,
            fit=product_data.fit,
            gender=product_data.gender,
            season=product_data.season,
            condition_sup=product_data.condition_sup,
            rise=product_data.rise,
            closure=product_data.closure,
            sleeve_length=product_data.sleeve_length,
            origin=product_data.origin,
            decade=product_data.decade,
            trend=product_data.trend,
            name_sup=product_data.name_sup,
            location=product_data.location,
            model=product_data.model,
            dim1=product_data.dim1,
            dim2=product_data.dim2,
            dim3=product_data.dim3,
            dim4=product_data.dim4,
            dim5=product_data.dim5,
            dim6=product_data.dim6,
            stock_quantity=product_data.stock_quantity,
            status=ProductStatus.DRAFT,
        )

        ProductRepository.create(db, product)
        db.commit()
        db.refresh(product)

        elapsed = time.time() - start_time
        logger.info(
            f"[ProductService] create_product completed: product_id={product.id}, "
            f"title={product.title[:50] if product.title else 'N/A'}, "
            f"price={product.price}, duration={elapsed:.2f}s"
        )

        return product

    @staticmethod
    def get_product_by_id(db: Session, product_id: int) -> Optional[Product]:
        """
        Get a product by ID.

        Business Rules:
        - Ignores soft-deleted products (deleted_at NOT NULL)

        Args:
            db: SQLAlchemy Session
            product_id: Product ID

        Returns:
            Product or None if not found/deleted
        """
        return ProductRepository.get_by_id(db, product_id)

    @staticmethod
    def list_products(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        status: Optional[ProductStatus] = None,
        category: Optional[str] = None,
        brand: Optional[str] = None,
    ) -> tuple[list[Product], int]:
        """
        List products with filters and pagination.

        Business Rules:
        - Ignores soft-deleted products
        - Default sort: created_at DESC (newest first)
        - Max limit: 100 (defined by API)

        Args:
            db: SQLAlchemy Session
            skip: Number of results to skip (pagination)
            limit: Max number of results
            status: Filter by status (optional)
            category: Filter by category (optional)
            brand: Filter by brand (optional)

        Returns:
            Tuple (list of products, total count)
        """
        return ProductRepository.list(
            db,
            skip=skip,
            limit=limit,
            status=status,
            category=category,
            brand=brand,
        )

    @staticmethod
    def update_product(
        db: Session, product_id: int, product_data: ProductUpdate
    ) -> Optional[Product]:
        """
        Update a product.

        Business Rules:
        - FK validation if modified (brand, category, condition, etc.)
        - updated_at automatically updated by SQLAlchemy
        - Cannot modify a deleted product
        - SOLD products are immutable

        Args:
            db: SQLAlchemy Session
            product_id: Product ID to modify
            product_data: New data (optional fields)

        Returns:
            Updated Product or None if not found

        Raises:
            ValueError: If a FK attribute is invalid or product is SOLD
        """
        import time
        start_time = time.time()

        logger.info(f"[ProductService] Starting update_product: product_id={product_id}")

        product = ProductRepository.get_by_id(db, product_id)
        if not product:
            logger.warning(f"[ProductService] update_product: product_id={product_id} not found")
            return None

        # BUSINESS RULE (2025-12-05): SOLD products are immutable
        if ProductStatusManager.is_immutable(product):
            raise ValueError(
                "Cannot modify SOLD product. Product is locked after sale. "
                "Contact support if price/data correction needed."
            )

        # Partial validation: only modified attributes
        update_dict = product_data.model_dump(exclude_unset=True)

        # ===== AUTO-CREATE SIZE ORIGINAL IF MODIFIED (Business Rule 2026-01-06) =====
        if 'size_original' in update_dict:
            size_original_value = ProductUtils.adjust_size(
                update_dict.get('size_original'),
                update_dict.get('dim1', product.dim1),
                update_dict.get('dim6', product.dim6)
            )

            if size_original_value:
                from repositories.size_original_repository import SizeOriginalRepository
                SizeOriginalRepository.get_or_create(db, size_original_value)
                update_dict['size_original'] = size_original_value

        AttributeValidator.validate_product_attributes(db, update_dict, partial=True)

        # Apply modifications
        for key, value in update_dict.items():
            setattr(product, key, value)

        ProductRepository.update(db, product)
        db.commit()
        db.refresh(product)

        elapsed = time.time() - start_time
        logger.info(
            f"[ProductService] update_product completed: product_id={product_id}, "
            f"fields_updated={len(update_dict)}, duration={elapsed:.2f}s"
        )

        return product

    @staticmethod
    def delete_product(db: Session, product_id: int) -> bool:
        """
        Delete a product (soft delete).

        Business Rules (2025-12-04):
        - Soft delete: marks deleted_at instead of physical deletion
        - Images are NOT deleted (kept for history)
        - Product remains visible in reports but invisible in lists

        Args:
            db: SQLAlchemy Session
            product_id: Product ID to delete

        Returns:
            bool: True if deleted, False if not found
        """
        logger.info(f"[ProductService] Starting delete_product: product_id={product_id}")

        product = ProductRepository.get_by_id(db, product_id)
        if not product:
            logger.warning(f"[ProductService] delete_product: product_id={product_id} not found")
            return False

        ProductRepository.soft_delete(db, product)
        db.commit()

        logger.info(f"[ProductService] delete_product completed: product_id={product_id} (soft deleted)")

        return True

    # =========================================================================
    # DELEGATED METHODS (to specialized services)
    # =========================================================================

    @staticmethod
    def add_image(
        db: Session, product_id: int, image_url: str, display_order: int | None = None
    ) -> dict:
        """
        Add an image to a product. Delegates to ProductImageService.

        Args:
            db: SQLAlchemy Session
            product_id: Product ID
            image_url: Image URL (CDN)
            display_order: Display order (auto if None)

        Returns:
            dict: Created image {url, order, created_at}
        """
        return ProductImageService.add_image(db, product_id, image_url, display_order)

    @staticmethod
    def delete_image(db: Session, product_id: int, image_url: str) -> bool:
        """
        Delete an image by URL. Delegates to ProductImageService.

        Args:
            db: SQLAlchemy Session
            product_id: Product ID
            image_url: Image URL to delete

        Returns:
            bool: True if deleted, False if not found
        """
        return ProductImageService.delete_image(db, product_id, image_url)

    @staticmethod
    def reorder_images(
        db: Session, product_id: int, ordered_urls: list[str]
    ) -> list[dict]:
        """
        Reorder product images. Delegates to ProductImageService.

        Args:
            db: SQLAlchemy Session
            product_id: Product ID
            ordered_urls: List of URLs in desired order

        Returns:
            list[dict]: Reordered images
        """
        return ProductImageService.reorder_images(db, product_id, ordered_urls)

    @staticmethod
    def update_product_status(
        db: Session, product_id: int, new_status: ProductStatus
    ) -> Optional[Product]:
        """
        Update product status. Delegates to ProductStatusManager.

        Args:
            db: SQLAlchemy Session
            product_id: Product ID
            new_status: New status

        Returns:
            Updated Product or None if not found
        """
        return ProductStatusManager.update_status(db, product_id, new_status)


__all__ = ["ProductService"]
