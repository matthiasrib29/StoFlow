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

from sqlalchemy import update
from sqlalchemy.orm import Session

from models.user.product import Product, ProductStatus
from models.user.product_attributes_m2m import (
    ProductColor,
    ProductMaterial,
    ProductConditionSup,
)
from repositories.product_attribute_repository import ProductAttributeRepository
from repositories.product_repository import ProductRepository
from schemas.product_schemas import ProductCreate, ProductUpdate
from services.pricing_service import PricingService
from services.product_image_service import ProductImageService
from services.product_status_manager import ProductStatusManager
from services.product_utils import ProductUtils
from services.validators import AttributeValidator
from shared.datetime_utils import utc_now
from shared.exceptions import ConcurrentModificationError
from shared.logging_setup import get_logger
from shared.timing import timed_operation

logger = get_logger(__name__)


class ProductService:
    """Service for product management."""

    @staticmethod
    # ===== HELPER METHODS FOR update_product() (Refactored 2026-01-12 Phase 3.2) =====

    @staticmethod
    def _extract_m2m_fields_from_update(update_dict: dict) -> tuple:
        """Extract M2M fields from update dict (modifies dict in-place)."""
        colors_to_update = None
        if 'colors' in update_dict:
            colors_to_update = update_dict.pop('colors') or []
        elif 'color' in update_dict:
            color_value = update_dict.pop('color')
            colors_to_update = [color_value] if color_value else []

        materials_to_update = None
        material_details_to_update = None
        if 'materials' in update_dict:
            materials_to_update = update_dict.pop('materials') or []
        if 'material_details' in update_dict:
            material_details_to_update = update_dict.pop('material_details')
        if materials_to_update is None and 'material' in update_dict:
            material_value = update_dict.pop('material')
            materials_to_update = [material_value] if material_value else []

        condition_sups_to_update = None
        if 'condition_sups' in update_dict:
            condition_sups_to_update = update_dict.pop('condition_sups') or []
        elif 'condition_sup' in update_dict:
            condition_sups_to_update = update_dict.pop('condition_sup') or []

        return colors_to_update, materials_to_update, material_details_to_update, condition_sups_to_update

    @staticmethod
    def _process_size_original_update(db: Session, update_dict: dict, product: Product) -> None:
        """Auto-create size_original if modified (modifies dict in-place)."""
        if 'size_original' not in update_dict:
            return

        size_original_value = ProductUtils.adjust_size(
            update_dict.get('size_original'),
            update_dict.get('dim1', product.dim1),
            update_dict.get('dim6', product.dim6)
        )

        if size_original_value:
            from repositories.size_original_repository import SizeOriginalRepository
            SizeOriginalRepository.get_or_create(db, size_original_value)
            update_dict['size_original'] = size_original_value

    @staticmethod
    def _validate_m2m_update_fields(
        db: Session,
        colors: list | None,
        materials: list | None,
        material_details: list | None,
        condition_sups: list | None
    ) -> tuple:
        """Validate M2M fields and return validated data."""
        validated_colors = None
        validated_materials = None
        material_percentages = {}
        validated_condition_sups = None

        if colors is not None:
            validated_colors = AttributeValidator.validate_colors(db, colors)

        if materials is not None:
            validated_materials, material_percentages = AttributeValidator.validate_materials(
                db, materials,
                [md.model_dump() for md in material_details] if material_details else None
            )

        if condition_sups is not None:
            validated_condition_sups = AttributeValidator.validate_condition_sups(db, condition_sups)

        return validated_colors, validated_materials, material_percentages, validated_condition_sups

    @staticmethod
    def _execute_optimistic_update(db: Session, product: Product, update_dict: dict) -> None:
        """Apply update with optimistic locking (version + SOLD check)."""
        if not update_dict:
            return

        set_values = {**update_dict, "version_number": Product.version_number + 1}

        result = db.execute(
            update(Product)
            .where(
                Product.id == product.id,
                Product.version_number == product.version_number,
                Product.status != ProductStatus.SOLD
            )
            .values(**set_values)
            .execution_options(synchronize_session="fetch")
        )

        if result.rowcount == 0:
            db.refresh(product)
            if product.status == ProductStatus.SOLD:
                raise ValueError(
                    "Cannot modify SOLD product. Product was sold while you were editing. "
                    "Please refresh the page."
                )
            raise ConcurrentModificationError(
                f"Product {product.id} was modified by another user. Please refresh and try again.",
                details={"product_id": product.id, "expected_version": product.version_number}
            )

        db.refresh(product)

    @staticmethod
    def _sync_m2m_relationships(
        db: Session, product_id: int,
        validated_colors: list | None,
        validated_materials: list | None,
        material_percentages: dict,
        validated_condition_sups: list | None
    ) -> bool:
        """Update M2M relationships (REPLACE strategy). Returns True if any updated."""
        updated = False

        if validated_colors is not None:
            ProductService._replace_product_colors(db, product_id, validated_colors)
            updated = True

        if validated_materials is not None:
            ProductService._replace_product_materials(db, product_id, validated_materials, material_percentages)
            updated = True

        if validated_condition_sups is not None:
            ProductService._replace_product_condition_sups(db, product_id, validated_condition_sups)
            updated = True

        return updated


    @staticmethod
    @timed_operation('product_update', threshold_ms=1000)
    def update_product(db: Session, product_id: int, product_data: ProductUpdate) -> Optional[Product]:
        """
        Update a product (refactored 2026-01-12 Phase 3.2).

        Business Rules:
        - FK validation if modified
        - SOLD products are immutable
        - Optimistic locking (version check)

        Returns:
            Updated Product or None if not found

        Raises:
            ValueError: If product is SOLD or FK invalid
            ConcurrentModificationError: If version mismatch
        """
        logger.info(f"Updating product: product_id={product_id}")

        # 1. Load and validate immutability
        product = ProductRepository.get_by_id(db, product_id)
        if not product:
            logger.warning(f"[ProductService] update_product: product_id={product_id} not found")
            return None

        if ProductStatusManager.is_immutable(product):
            raise ValueError(
                "Cannot modify SOLD product. Product is locked after sale. "
                "Contact support if price/data correction needed."
            )

        # 2. Extract and process update data
        update_dict = product_data.model_dump(exclude_unset=True)
        colors, materials, material_details, condition_sups = (
            ProductService._extract_m2m_fields_from_update(update_dict)
        )

        # 3. Handle special fields
        ProductService._process_size_original_update(db, update_dict, product)

        # 4. Validate all fields
        validated_colors, validated_materials, material_percentages, validated_condition_sups = (
            ProductService._validate_m2m_update_fields(db, colors, materials, material_details, condition_sups)
        )
        AttributeValidator.validate_product_attributes(db, update_dict, partial=True)

        # 5. Apply scalar field updates with locking
        ProductService._execute_optimistic_update(db, product, update_dict)

        # 6. Update M2M relationships
        if ProductService._sync_m2m_relationships(
            db, product.id, validated_colors, validated_materials,
            material_percentages, validated_condition_sups
        ):
            db.refresh(product)

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

    # ===== M2M HELPER METHODS (Added 2026-01-07) =====

    @staticmethod
    def _create_product_colors(
        db: Session,
        product_id: int,
        colors: list[str]
    ) -> None:
        """
        Create ProductColor M2M entries for a product.

        Args:
            db: SQLAlchemy Session
            product_id: Product ID
            colors: List of color names (validated)

        Business Rules:
            - First color is automatically marked as primary (is_primary=TRUE)
            - Only one color can be primary per product
        """
        if not colors:
            return

        for idx, color_name in enumerate(colors):
            product_color = ProductColor(
                product_id=product_id,
                color=color_name,
                is_primary=(idx == 0)  # First color = primary
            )
            db.add(product_color)

        logger.debug(f"[ProductService] Created {len(colors)} color entries for product_id={product_id}")

    @staticmethod
    def _create_product_materials(
        db: Session,
        product_id: int,
        materials: list[str],
        percentages: dict[str, int | None]
    ) -> None:
        """
        Create ProductMaterial M2M entries for a product.

        Args:
            db: SQLAlchemy Session
            product_id: Product ID
            materials: List of material names (validated)
            percentages: Dict mapping material_name -> percentage (or None)
        """
        if not materials:
            return

        for material_name in materials:
            percentage = percentages.get(material_name)
            product_material = ProductMaterial(
                product_id=product_id,
                material=material_name,
                percentage=percentage
            )
            db.add(product_material)

        logger.debug(f"[ProductService] Created {len(materials)} material entries for product_id={product_id}")

    @staticmethod
    def _create_product_condition_sups(
        db: Session,
        product_id: int,
        condition_sups: list[str]
    ) -> None:
        """
        Create ProductConditionSup M2M entries for a product.

        Args:
            db: SQLAlchemy Session
            product_id: Product ID
            condition_sups: List of condition_sup names (validated)
        """
        if not condition_sups:
            return

        for condition_sup_name in condition_sups:
            product_condition_sup = ProductConditionSup(
                product_id=product_id,
                condition_sup=condition_sup_name
            )
            db.add(product_condition_sup)

        logger.debug(f"[ProductService] Created {len(condition_sups)} condition_sup entries for product_id={product_id}")

    @staticmethod
    def _replace_product_colors(
        db: Session,
        product_id: int,
        new_colors: list[str]
    ) -> None:
        """
        Replace all ProductColor entries for a product (REPLACE strategy).

        Args:
            db: SQLAlchemy Session
            product_id: Product ID
            new_colors: New list of color names (validated)

        Strategy:
            - Delete all existing color entries
            - Create new entries (first = primary)
        """
        # Delete existing entries
        db.query(ProductColor).filter(ProductColor.product_id == product_id).delete()

        # Create new entries
        ProductService._create_product_colors(db, product_id, new_colors)

        logger.debug(f"[ProductService] Replaced colors for product_id={product_id}: {new_colors}")

    @staticmethod
    def _replace_product_materials(
        db: Session,
        product_id: int,
        new_materials: list[str],
        percentages: dict[str, int | None]
    ) -> None:
        """
        Replace all ProductMaterial entries for a product (REPLACE strategy).

        Args:
            db: SQLAlchemy Session
            product_id: Product ID
            new_materials: New list of material names (validated)
            percentages: Dict mapping material_name -> percentage
        """
        # Delete existing entries
        db.query(ProductMaterial).filter(ProductMaterial.product_id == product_id).delete()

        # Create new entries
        ProductService._create_product_materials(db, product_id, new_materials, percentages)

        logger.debug(f"[ProductService] Replaced materials for product_id={product_id}: {new_materials}")

    @staticmethod
    def _replace_product_condition_sups(
        db: Session,
        product_id: int,
        new_condition_sups: list[str]
    ) -> None:
        """
        Replace all ProductConditionSup entries for a product (REPLACE strategy).

        Args:
            db: SQLAlchemy Session
            product_id: Product ID
            new_condition_sups: New list of condition_sup names (validated)
        """
        # Delete existing entries
        db.query(ProductConditionSup).filter(ProductConditionSup.product_id == product_id).delete()

        # Create new entries
        ProductService._create_product_condition_sups(db, product_id, new_condition_sups)

        logger.debug(f"[ProductService] Replaced condition_sups for product_id={product_id}: {new_condition_sups}")


__all__ = ["ProductService"]
