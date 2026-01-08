"""
Base Publish Handler

Abstract base class for product publication across all marketplaces.
Extends BaseMarketplaceHandler with publication-specific logic:
- Idempotency checking
- Photo upload with tracking
- Cleanup on partial failures (logging)

Author: Claude
Date: 2026-01-08 (Security Audit 2)
"""

from abc import abstractmethod
from typing import Any

from sqlalchemy.orm import Session

from models.user.marketplace_job import MarketplaceJob, JobStatus
from models.user.product import Product
from services.marketplace.handlers.base_handler import BaseMarketplaceHandler
from shared.exceptions import ConflictError, ValidationError
from shared.logging_setup import get_logger

logger = get_logger(__name__)


class BasePublishHandler(BaseMarketplaceHandler):
    """
    Abstract base class for publication handlers.

    Provides common publication flow:
    1. Check idempotency
    2. Validate product
    3. Upload photos
    4. Create listing
    5. Save result
    6. Handle partial failures

    Subclasses must implement:
    - marketplace_name()
    - _upload_photos()
    - _create_listing()
    """

    ACTION_CODE = "publish"

    def __init__(self, db: Session, job_id: int, user_id: int):
        """
        Initialize publish handler.

        Args:
            db: SQLAlchemy session (user schema)
            job_id: MarketplaceJob ID to execute
            user_id: User ID (for permissions checks)
        """
        super().__init__(db, job_id)
        self.user_id = user_id

    async def execute(self) -> dict[str, Any]:
        """
        Execute publication job.

        Returns:
            dict: {
                "success": bool,
                "listing_id": str,
                "url": str,
                "photo_ids": list[int],
                "error": str | None
            }
        """
        self.log_start(
            f"Publishing product #{self.product_id} to {self.marketplace} "
            f"(job #{self.job_id})"
        )

        # 1. Check idempotency
        if self.job.idempotency_key:
            cached_result = self._check_idempotency()
            if cached_result:
                return cached_result

        # 2. Load and validate product
        product = self._load_product()
        self._validate_product(product)

        # 3. Upload photos with tracking
        uploaded_photo_ids = []
        try:
            uploaded_photo_ids = await self._upload_photos(product)
            self.log_success(f"{len(uploaded_photo_ids)} photos uploaded")

            # 4. Create listing
            result = await self._create_listing(product, uploaded_photo_ids)
            self.log_success(
                f"Listing created: {result.get('listing_id')} ({result.get('url')})"
            )

            # 5. Mark job as completed
            self.job.status = JobStatus.COMPLETED
            self.job.result_data = result
            self.db.commit()

            return {
                "success": True,
                "photo_ids": uploaded_photo_ids,
                **result,
            }

        except Exception as e:
            # Cleanup: log orphaned photos
            if uploaded_photo_ids:
                self.log_error(
                    f"🚨 PARTIAL FAILURE: {len(uploaded_photo_ids)} orphaned photos "
                    f"(product_id={self.product_id}, photo_ids={uploaded_photo_ids})"
                )

            # Mark job as failed
            self.job.status = JobStatus.FAILED
            self.job.error_message = str(e)
            self.db.commit()

            self.log_error(f"Publication failed: {e}", exc_info=True)

            return {
                "success": False,
                "error": str(e),
                "photo_ids": uploaded_photo_ids,
            }

    # =========================================================================
    # IDEMPOTENCY
    # =========================================================================

    def _check_idempotency(self) -> dict[str, Any] | None:
        """
        Check if publication already processed.

        Returns:
            dict: Cached result if exists and completed, None otherwise

        Raises:
            ConflictError: If publication already in progress
        """
        idempotency_key = self.job.idempotency_key

        # Find existing job with same key
        existing = (
            self.db.query(MarketplaceJob)
            .filter(
                MarketplaceJob.idempotency_key == idempotency_key,
                MarketplaceJob.id != self.job_id,  # Exclude current job
            )
            .first()
        )

        if not existing:
            return None

        # Job already completed: return cached result
        if existing.status == JobStatus.COMPLETED:
            self.log_success(
                f"✅ Idempotency hit: returning cached result (key={idempotency_key})"
            )
            return {
                "success": True,
                "cached": True,
                **(existing.result_data or {}),
            }

        # Job in progress: conflict
        if existing.status in (JobStatus.RUNNING, JobStatus.PENDING):
            raise ConflictError(
                f"Publication already in progress (job #{existing.id}, "
                f"key={idempotency_key})"
            )

        # Job failed: allow retry
        self.log_warning(
            f"Previous job #{existing.id} failed, retrying (key={idempotency_key})"
        )
        return None

    # =========================================================================
    # PRODUCT VALIDATION
    # =========================================================================

    def _load_product(self) -> Product:
        """
        Load product from database.

        Returns:
            Product instance

        Raises:
            ValueError: If product not found
        """
        product = (
            self.db.query(Product).filter(Product.id == self.product_id).first()
        )

        if not product:
            raise ValueError(f"Product #{self.product_id} not found")

        if product.deleted_at is not None:
            raise ValueError(f"Product #{self.product_id} is deleted")

        return product

    def _validate_product(self, product: Product) -> None:
        """
        Validate product for publication.

        Args:
            product: Product to validate

        Raises:
            ValidationError: If product invalid
        """
        errors = []

        if not product.title or len(product.title.strip()) == 0:
            errors.append("Title is required")

        if not product.price or product.price <= 0:
            errors.append("Price must be greater than 0")

        if product.stock_quantity is not None and product.stock_quantity <= 0:
            errors.append("Cannot publish product with zero stock")

        if errors:
            raise ValidationError("; ".join(errors))

        self.log_debug(f"Product #{self.product_id} validation passed")

    # =========================================================================
    # ABSTRACT METHODS (to be implemented by subclasses)
    # =========================================================================

    @abstractmethod
    def marketplace_name(self) -> str:
        """
        Return marketplace name.

        Returns:
            str: "vinted", "ebay", or "etsy"
        """
        pass

    @abstractmethod
    async def _upload_photos(self, product: Product) -> list[int]:
        """
        Upload product photos to marketplace.

        Args:
            product: Product with images

        Returns:
            list[int]: List of photo IDs uploaded

        Raises:
            Exception: If upload fails
        """
        pass

    @abstractmethod
    async def _create_listing(
        self, product: Product, photo_ids: list[int]
    ) -> dict[str, Any]:
        """
        Create listing on marketplace.

        Args:
            product: Product to list
            photo_ids: Photo IDs uploaded

        Returns:
            dict: {
                "listing_id": str,
                "url": str,
                ...marketplace-specific fields
            }

        Raises:
            Exception: If creation fails
        """
        pass

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def _get_product_images(self, product: Product, max_images: int = 10) -> list[dict]:
        """
        Get product images from JSONB field.

        Args:
            product: Product with images
            max_images: Maximum number of images to return

        Returns:
            list[dict]: List of images [{url, order}, ...]
        """
        images = product.images or []

        if not isinstance(images, list):
            self.log_warning(
                f"Product #{product.id} images field is not a list: {type(images)}"
            )
            return []

        # Sort by order (if present)
        images = sorted(images, key=lambda img: img.get("order", 999))

        # Limit to max_images
        return images[:max_images]
