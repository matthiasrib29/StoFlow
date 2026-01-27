"""
Pending Action Service

Service for managing pending actions (confirmation queue).
When sync detects a product sold/deleted on marketplace, it creates
a pending action instead of immediately changing the product status.

Business Rules (2026-01-22):
- create_pending_action: Sets product to PENDING_DELETION, creates PendingAction record
- confirm_action: Applies the action (SOLD/ARCHIVED), sets confirmed_at
- reject_action: Restores product to previous status (PUBLISHED)
- Bulk operations supported for mass confirm/reject
"""

from sqlalchemy import select, func
from sqlalchemy.orm import Session, joinedload, subqueryload

from models.user.pending_action import PendingAction, PendingActionType
from models.user.product import Product, ProductStatus
from shared.datetime_utils import utc_now
from shared.logging import get_logger

logger = get_logger(__name__)


# Map action types to their target product status
ACTION_TYPE_TO_STATUS = {
    PendingActionType.MARK_SOLD: ProductStatus.SOLD,
    PendingActionType.DELETE: ProductStatus.ARCHIVED,
    PendingActionType.ARCHIVE: ProductStatus.ARCHIVED,
    PendingActionType.DELETE_VINTED_LISTING: ProductStatus.SOLD,  # Keep SOLD
    PendingActionType.DELETE_EBAY_LISTING: ProductStatus.SOLD,    # Keep SOLD
}

# Action types that don't change product status to PENDING_DELETION on create
_NO_STATUS_CHANGE_TYPES = {
    PendingActionType.DELETE_VINTED_LISTING,
    PendingActionType.DELETE_EBAY_LISTING,
}


class PendingActionService:
    """Service for pending action management (confirmation queue)."""

    def __init__(self, db: Session):
        self.db = db

    def create_pending_action(
        self,
        product_id: int,
        action_type: PendingActionType,
        marketplace: str,
        reason: str = None,
        context_data: dict = None,
    ) -> PendingAction:
        """
        Create a pending action and set product to PENDING_DELETION.

        Args:
            product_id: The product ID.
            action_type: Type of action detected (MARK_SOLD, DELETE, ARCHIVE).
            marketplace: Source marketplace (vinted, ebay, etsy).
            reason: Human-readable reason.
            context_data: Additional context (sale price, etc.).

        Returns:
            The created PendingAction.
        """
        product = self.db.get(Product, product_id)
        if not product:
            logger.warning(f"Product {product_id} not found, skipping pending action")
            return None

        # Don't create duplicate pending actions for same product
        existing = self.db.execute(
            select(PendingAction).where(
                PendingAction.product_id == product_id,
                PendingAction.confirmed_at.is_(None),
            )
        ).scalar_one_or_none()

        if existing:
            logger.info(
                f"Pending action already exists for product {product_id}, skipping",
                extra={"product_id": product_id, "existing_action_id": existing.id}
            )
            return existing

        # Save previous status before changing to PENDING_DELETION
        previous_status = product.status.value if product.status else "published"

        pending_action = PendingAction(
            product_id=product_id,
            action_type=action_type,
            marketplace=marketplace,
            reason=reason,
            context_data=context_data,
            previous_status=previous_status,
        )
        self.db.add(pending_action)

        # Set product to PENDING_DELETION (unless action type preserves current status)
        if action_type not in _NO_STATUS_CHANGE_TYPES:
            product.status = ProductStatus.PENDING_DELETION
        self.db.flush()

        logger.info(
            f"Created pending action for product {product_id}: "
            f"{action_type.value} from {marketplace}",
            extra={
                "product_id": product_id,
                "action_type": action_type.value,
                "marketplace": marketplace,
                "pending_action_id": pending_action.id,
            }
        )

        return pending_action

    def get_pending_actions(self, limit: int = 50, offset: int = 0) -> list[PendingAction]:
        """
        List pending actions (not yet confirmed/rejected).

        Args:
            limit: Max number of results.
            offset: Pagination offset.

        Returns:
            List of pending actions with product info loaded.
        """
        stmt = (
            select(PendingAction)
            .where(PendingAction.confirmed_at.is_(None))
            .options(
                joinedload(PendingAction.product)
                .subqueryload(Product.product_images)
            )
            .order_by(PendingAction.detected_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = self.db.execute(stmt)
        return list(result.scalars().unique().all())

    def get_pending_count(self) -> int:
        """Get the number of pending actions awaiting confirmation."""
        stmt = (
            select(func.count(PendingAction.id))
            .where(PendingAction.confirmed_at.is_(None))
        )
        return self.db.execute(stmt).scalar() or 0

    def confirm_action(self, action_id: int, confirmed_by: str = "user") -> Product | None:
        """
        Confirm a pending action (apply the status change).

        Args:
            action_id: The pending action ID.
            confirmed_by: Who confirmed (user_id or 'auto').

        Returns:
            The updated Product, or None if action not found.
        """
        action = self.db.get(PendingAction, action_id)
        if not action or action.confirmed_at is not None:
            return None

        product = self.db.get(Product, action.product_id)
        if not product:
            return None

        # Apply the target status
        target_status = ACTION_TYPE_TO_STATUS.get(action.action_type, ProductStatus.ARCHIVED)
        product.status = target_status

        # If marking as sold, set sold_at
        if action.action_type == PendingActionType.MARK_SOLD:
            product.sold_at = utc_now()

        # Mark action as confirmed
        action.confirmed_at = utc_now()
        action.confirmed_by = confirmed_by
        action.is_confirmed = True

        self.db.flush()

        logger.info(
            f"Confirmed pending action {action_id}: product {product.id} -> {target_status.value}",
            extra={"action_id": action_id, "product_id": product.id, "new_status": target_status.value}
        )

        return product

    def reject_action(self, action_id: int, restored_by: str = "user") -> Product | None:
        """
        Reject a pending action (restore product to previous status).

        Args:
            action_id: The pending action ID.
            restored_by: Who rejected (user_id or 'user').

        Returns:
            The restored Product, or None if action not found.
        """
        action = self.db.get(PendingAction, action_id)
        if not action or action.confirmed_at is not None:
            return None

        product = self.db.get(Product, action.product_id)
        if not product:
            return None

        # Restore to previous status (default: PUBLISHED)
        restore_status = ProductStatus.PUBLISHED
        if action.previous_status:
            try:
                restore_status = ProductStatus(action.previous_status)
            except ValueError:
                restore_status = ProductStatus.PUBLISHED

        product.status = restore_status

        # Mark action as rejected
        action.confirmed_at = utc_now()
        action.confirmed_by = restored_by
        action.is_confirmed = False

        self.db.flush()

        logger.info(
            f"Rejected pending action {action_id}: product {product.id} restored to {restore_status.value}",
            extra={"action_id": action_id, "product_id": product.id, "restored_status": restore_status.value}
        )

        return product

    def bulk_confirm(self, action_ids: list[int], confirmed_by: str = "user") -> int:
        """
        Confirm multiple pending actions at once.

        Args:
            action_ids: List of pending action IDs to confirm.
            confirmed_by: Who confirmed.

        Returns:
            Number of actions confirmed.
        """
        count = 0
        for action_id in action_ids:
            result = self.confirm_action(action_id, confirmed_by)
            if result:
                count += 1
        return count

    def bulk_reject(self, action_ids: list[int], restored_by: str = "user") -> int:
        """
        Reject multiple pending actions at once.

        Args:
            action_ids: List of pending action IDs to reject.
            restored_by: Who rejected.

        Returns:
            Number of actions rejected.
        """
        count = 0
        for action_id in action_ids:
            result = self.reject_action(action_id, restored_by)
            if result:
                count += 1
        return count
