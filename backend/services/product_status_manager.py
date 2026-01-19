"""
Product Status Manager

Service for managing product status transitions.

Business Rules (MVP - 2025-12-04, updated 2026-01-19):
- Allowed statuses: DRAFT, PUBLISHED, SOLD, ARCHIVED
- Valid transitions:
  - DRAFT -> PUBLISHED, ARCHIVED
  - PUBLISHED -> SOLD, ARCHIVED
  - SOLD -> ARCHIVED
  - ARCHIVED -> DRAFT, PUBLISHED (unarchiving)
- Publication requires: stock > 0, images >= 1

Created: 2026-01-06
Author: Claude
"""

from typing import Optional

from sqlalchemy import update, func
from sqlalchemy.orm import Session

from models.user.product import Product, ProductStatus
from repositories.product_repository import ProductRepository
from shared.datetime_utils import utc_now
from shared.exceptions import ConcurrentModificationError, OutOfStockError
from shared.logging_setup import get_logger

logger = get_logger(__name__)

# MVP allowed statuses
MVP_STATUSES = [
    ProductStatus.DRAFT,
    ProductStatus.PUBLISHED,
    ProductStatus.SOLD,
    ProductStatus.ARCHIVED,
]

# Valid status transitions
VALID_TRANSITIONS = {
    ProductStatus.DRAFT: [ProductStatus.PUBLISHED, ProductStatus.ARCHIVED],
    ProductStatus.PUBLISHED: [ProductStatus.SOLD, ProductStatus.ARCHIVED],
    ProductStatus.SOLD: [ProductStatus.ARCHIVED],
    ProductStatus.ARCHIVED: [ProductStatus.DRAFT, ProductStatus.PUBLISHED],  # Allow unarchiving
}


class ProductStatusManager:
    """Service for product status management."""

    @staticmethod
    def update_status(
        db: Session, product_id: int, new_status: ProductStatus
    ) -> Optional[Product]:
        """
        Update product status.

        Business Rules (MVP - 2025-12-04, updated 2026-01-19):
        - MVP allowed transitions:
          - DRAFT -> PUBLISHED, ARCHIVED
          - PUBLISHED -> SOLD, ARCHIVED
          - SOLD -> ARCHIVED
          - ARCHIVED -> DRAFT, PUBLISHED (unarchiving)

        Args:
            db: SQLAlchemy Session
            product_id: Product ID
            new_status: New status

        Returns:
            Updated Product or None if not found

        Raises:
            ValueError: If status not allowed for MVP or invalid transition
        """
        if new_status not in MVP_STATUSES:
            raise ValueError(
                f"Status {new_status} not allowed in MVP. "
                f"Allowed: {', '.join([s.value for s in MVP_STATUSES])}"
            )

        product = ProductRepository.get_by_id(db, product_id)
        if not product:
            return None

        current_status = product.status
        valid_next = VALID_TRANSITIONS.get(current_status, [])

        if new_status not in valid_next:
            raise ValueError(
                f"Invalid transition: {current_status.value} -> {new_status.value}"
            )

        # Publication validation
        if new_status == ProductStatus.PUBLISHED:
            ProductStatusManager._validate_for_publication(product)

        # Handle SOLD status atomically (Business Rule 2025-12-05)
        if new_status == ProductStatus.SOLD:
            # Atomic decrement with stock check
            result = db.execute(
                update(Product)
                .where(
                    Product.id == product_id,
                    Product.stock_quantity > 0  # Atomic condition
                )
                .values(
                    status=ProductStatus.SOLD,
                    stock_quantity=0,
                    sold_at=func.now(),  # Timestamp on DB side
                    version_number=Product.version_number + 1  # Increment version
                )
                .execution_options(synchronize_session="fetch")
            )

            if result.rowcount == 0:
                # Either product not found OR stock already 0
                db.refresh(product)

                if product.stock_quantity == 0:
                    raise OutOfStockError(
                        f"Cannot mark product as SOLD: already out of stock.",
                        details={
                            "product_id": product_id,
                            "current_stock": product.stock_quantity
                        }
                    )
                else:
                    raise ConcurrentModificationError(
                        f"Product {product_id} was modified by another transaction.",
                        details={"product_id": product_id}
                    )

            db.refresh(product)

            logger.info(
                f"[ProductStatusManager] Product marked as SOLD atomically: "
                f"product_id={product_id}, stock decremented to 0"
            )
        else:
            # CRITICAL: Make ALL status changes atomic (not just SOLD) (Security 2026-01-12)
            result = db.execute(
                update(Product)
                .where(
                    Product.id == product_id,
                    Product.version_number == product.version_number  # Optimistic lock
                )
                .values(
                    status=new_status,
                    version_number=Product.version_number + 1
                )
                .execution_options(synchronize_session="fetch")
            )

            if result.rowcount == 0:
                # Version mismatch (concurrent modification)
                db.refresh(product)
                raise ConcurrentModificationError(
                    f"Product {product_id} was modified by another transaction. "
                    f"Please refresh and try again.",
                    details={"product_id": product_id}
                )

            db.refresh(product)
            logger.info(
                f"[ProductStatusManager] Status updated atomically: "
                f"product_id={product_id}, {current_status.value} -> {new_status.value}"
            )

        return product

    @staticmethod
    def _validate_for_publication(product: Product) -> None:
        """
        Validate product can be published.

        Business Rules (2025-12-05, updated 2026-01-19):
        - title: required, non-empty
        - description: required, non-empty
        - price: required, > 0
        - category: required, non-empty
        - condition: required (0-10)
        - stock_quantity: > 0
        - images: at least 1 required

        Args:
            product: Product to validate

        Raises:
            ValueError: If validation fails
        """
        errors = []

        # Title validation
        if not product.title or not product.title.strip():
            errors.append("Title is required")

        # Description validation
        if not product.description or not product.description.strip():
            errors.append("Description is required")

        # Price validation
        if product.price is None or product.price <= 0:
            errors.append("Price must be greater than 0")

        # Category validation
        if not product.category or not product.category.strip():
            errors.append("Category is required")

        # Condition validation
        if product.condition is None:
            errors.append("Condition is required (0-10)")

        # Stock validation
        if product.stock_quantity is None or product.stock_quantity <= 0:
            errors.append(f"Stock must be greater than 0 (current: {product.stock_quantity})")

        # Images validation
        image_count = len(product.images or [])
        if image_count == 0:
            errors.append("At least 1 image is required")

        if errors:
            raise ValueError(
                f"Cannot publish product. Missing required fields: {'; '.join(errors)}"
            )

    @staticmethod
    def can_transition(
        current_status: ProductStatus, new_status: ProductStatus
    ) -> bool:
        """
        Check if a status transition is valid.

        Args:
            current_status: Current product status
            new_status: Desired new status

        Returns:
            bool: True if transition is valid
        """
        valid_next = VALID_TRANSITIONS.get(current_status, [])
        return new_status in valid_next

    @staticmethod
    def get_valid_transitions(status: ProductStatus) -> list[ProductStatus]:
        """
        Get valid next statuses for a given status.

        Args:
            status: Current status

        Returns:
            list[ProductStatus]: Valid next statuses
        """
        return VALID_TRANSITIONS.get(status, [])

    @staticmethod
    def is_immutable(product: Product) -> bool:
        """
        Check if product is immutable (cannot be modified).

        Business Rule: SOLD products are immutable.

        Args:
            product: Product to check

        Returns:
            bool: True if product is immutable
        """
        return product.status == ProductStatus.SOLD


__all__ = [
    "ProductStatusManager",
    "MVP_STATUSES",
    "VALID_TRANSITIONS",
]
