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
from shared.logging_setup import get_logger
from shared.timing import timed_operation

logger = get_logger(__name__)


class ProductService:
    """Service for product management."""

    @staticmethod
    @timed_operation('product_creation', threshold_ms=1000)
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
        logger.info(
            f"Creating product: user_id={user_id}, "
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

        # ===== 4. VALIDATE M2M ATTRIBUTES (Added 2026-01-07) =====
        # Prefer new M2M fields (colors, materials, condition_sups) over deprecated fields
        # Standardize: None and [] are equivalent for M2M fields
        colors_to_use = product_data.colors if product_data.colors is not None else (
            [product_data.color] if product_data.color else []
        )
        colors_to_use = colors_to_use or []  # Normalize: None → []

        materials_to_use = product_data.materials if product_data.materials is not None else (
            [product_data.material] if product_data.material else []
        )
        materials_to_use = materials_to_use or []  # Normalize: None → []

        condition_sups_to_use = product_data.condition_sups if product_data.condition_sups is not None else (
            product_data.condition_sup if product_data.condition_sup else []
        )
        condition_sups_to_use = condition_sups_to_use or []  # Normalize: None → []

        # Validate M2M attributes
        validated_colors = AttributeValidator.validate_colors(db, colors_to_use)
        validated_materials, material_percentages = AttributeValidator.validate_materials(
            db,
            materials_to_use,
            [md.model_dump() for md in product_data.material_details] if product_data.material_details else None
        )
        validated_condition_sups = AttributeValidator.validate_condition_sups(db, condition_sups_to_use)

        # ===== 5. VALIDATE OTHER ATTRIBUTES (Refactored 2025-12-09) =====
        validation_data = product_data.model_dump()
        validation_data['size_original'] = size_original  # Use adjusted size
        AttributeValidator.validate_product_attributes(db, validation_data)

        # ===== 6. CREATE PRODUCT (Phase 1: NO MORE DUAL-WRITE) =====
        # 2026-01-07: STOPPED writing to deprecated color/material columns
        # All data now goes to M2M tables only (product_colors, product_materials)
        # Old columns will be dropped in next migration
        product = Product(
            title=product_data.title,
            description=product_data.description,
            price=price,
            category=product_data.category,
            brand=product_data.brand,
            condition=product_data.condition,
            size_original=size_original,
            # ✂️ REMOVED: color=..., material=... (use M2M only)
            # condition_sup can remain for now (used by API)
            condition_sup=validated_condition_sups if validated_condition_sups else None,
            fit=product_data.fit,
            gender=product_data.gender,
            season=product_data.season,
            rise=product_data.rise,
            closure=product_data.closure,
            sleeve_length=product_data.sleeve_length,
            origin=product_data.origin,
            decade=product_data.decade,
            trend=product_data.trend,
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

        # ===== 7. CREATE M2M ENTRIES (Added 2026-01-07) =====
        ProductService._create_product_colors(db, product.id, validated_colors)
        ProductService._create_product_materials(db, product.id, validated_materials, material_percentages)
        ProductService._create_product_condition_sups(db, product.id, validated_condition_sups)

        # Commit M2M entries
        db.commit()
        db.refresh(product)

        return product

    @staticmethod
    def create_draft_for_upload(db: Session, user_id: int) -> Product:
        """
        Create a minimal DRAFT product to allow instant image upload.

        This method is called when a user drops images BEFORE filling the form.
        The product is created with minimal values and will be completed later.

        Business Rules:
        - Status: DRAFT
        - Title: "" (empty to identify auto-created drafts for cleanup)
        - Stock: 1
        - All other fields: NULL/default
        - No validation (since fields are empty)
        - No price calculation

        Args:
            db: SQLAlchemy Session
            user_id: User ID (for user_X schema)

        Returns:
            Product: Created minimal draft product
        """
        logger.info(
            f"[ProductService] Creating draft for upload: user_id={user_id}"
        )

        # Create minimal product in DRAFT status
        product = Product(
            title="",  # Empty to identify auto-created drafts
            description=None,
            price=None,
            category=None,
            brand=None,
            condition=None,
            size_original=None,
            color=None,
            material=None,
            gender=None,
            stock_quantity=1,  # Default stock
            status=ProductStatus.DRAFT,
        )

        ProductRepository.create(db, product)
        db.commit()
        db.refresh(product)

        logger.info(
            f"[ProductService] Draft product created: product_id={product.id}"
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
    @timed_operation('product_update', threshold_ms=1000)
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
        logger.info(f"Updating product: product_id={product_id}")

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

        # ===== EXTRACT M2M FIELDS (Added 2026-01-07) =====
        # Extract M2M fields from update_dict (they need special handling)
        # Standardize: None and [] are equivalent for M2M fields (both mean "clear all")
        colors_provided = 'colors' in update_dict or 'color' in update_dict
        materials_provided = 'materials' in update_dict or 'material' in update_dict
        condition_sups_provided = 'condition_sups' in update_dict or 'condition_sup' in update_dict

        # Prefer new M2M fields over deprecated fields
        colors_to_update = None
        if 'colors' in update_dict:
            colors_to_update = update_dict.pop('colors') or []  # Normalize: None → []
        elif 'color' in update_dict:
            color_value = update_dict.pop('color')
            colors_to_update = [color_value] if color_value else []

        materials_to_update = None
        material_details_to_update = None
        if 'materials' in update_dict:
            materials_to_update = update_dict.pop('materials') or []  # Normalize: None → []
        if 'material_details' in update_dict:
            material_details_to_update = update_dict.pop('material_details')
        if materials_to_update is None and 'material' in update_dict:
            material_value = update_dict.pop('material')
            materials_to_update = [material_value] if material_value else []

        condition_sups_to_update = None
        if 'condition_sups' in update_dict:
            condition_sups_to_update = update_dict.pop('condition_sups') or []  # Normalize: None → []
        elif 'condition_sup' in update_dict:
            condition_sups_to_update = update_dict.pop('condition_sup') or []  # Normalize: None → []

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

        # ===== VALIDATE M2M ATTRIBUTES IF PROVIDED (Added 2026-01-07) =====
        validated_colors = None
        validated_materials = None
        material_percentages = {}

        if colors_to_update is not None:
            validated_colors = AttributeValidator.validate_colors(db, colors_to_update)

        if materials_to_update is not None:
            validated_materials, material_percentages = AttributeValidator.validate_materials(
                db,
                materials_to_update,
                [md.model_dump() for md in material_details_to_update] if material_details_to_update else None
            )

        validated_condition_sups = None
        if condition_sups_to_update is not None:
            validated_condition_sups = AttributeValidator.validate_condition_sups(db, condition_sups_to_update)
            # Update the old column for backward compat (will be removed in Phase 4)
            update_dict['condition_sup'] = validated_condition_sups if validated_condition_sups else None

        # ✂️ 2026-01-07: STOPPED updating deprecated color/material columns (Phase 1)
        # Previously: if validated_colors is not None: update_dict['color'] = ...
        # Previously: if validated_materials is not None: update_dict['material'] = ...
        # Now: M2M tables only

        AttributeValidator.validate_product_attributes(db, update_dict, partial=True)

        # Apply modifications to simple columns
        for key, value in update_dict.items():
            setattr(product, key, value)

        ProductRepository.update(db, product)
        db.commit()
        db.refresh(product)

        # ===== UPDATE M2M ENTRIES (Added 2026-01-07) =====
        # REPLACE strategy: if M2M field provided, replace all entries
        if validated_colors is not None:
            ProductService._replace_product_colors(db, product.id, validated_colors)

        if validated_materials is not None:
            ProductService._replace_product_materials(db, product.id, validated_materials, material_percentages)

        if validated_condition_sups is not None:
            ProductService._replace_product_condition_sups(db, product.id, validated_condition_sups)

        # Commit M2M updates
        if any([validated_colors is not None, validated_materials is not None, validated_condition_sups is not None]):
            db.commit()
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
