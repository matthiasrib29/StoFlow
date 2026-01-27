"""
Vinted Sync Reconciliation Activities for Temporal.

Activities for reconciling product sold status between Vinted and StoFlow:
- sync_sold_status: Mark Vinted-sold products as PENDING_DELETION in StoFlow
- detect_sold_with_active_listing: Find StoFlow-SOLD products still active on Vinted
- delete_vinted_listing: Delete a Vinted listing for a SOLD product

Author: Claude
Date: 2026-01-27 - Extracted from vinted_activities.py
"""

from sqlalchemy import text
from temporalio import activity

from shared.database import SessionLocal
from shared.logging import get_logger
from temporal.activities.job_state_activities import configure_activity_session

logger = get_logger(__name__)


@activity.defn(name="vinted_sync_sold_status")
async def sync_sold_status(user_id: int) -> dict:
    """
    Sync sold status from Vinted to StoFlow products.

    Creates pending actions for products detected as sold/closed on Vinted.
    Products are set to PENDING_DELETION status and require user confirmation.

    Args:
        user_id: User ID for schema isolation

    Returns:
        Dict with 'pending_count' and 'product_ids' affected
    """
    db = SessionLocal()
    try:
        configure_activity_session(db, user_id)

        from services.pending_action_service import PendingActionService
        from models.user.pending_action import PendingActionType

        result = db.execute(
            text("""
                SELECT vp.vinted_id, vp.product_id, vp.title, vp.price,
                       p.status as stoflow_status
                FROM vinted_products vp
                JOIN products p ON p.id = vp.product_id
                WHERE (vp.is_closed = true OR vp.status = 'sold')
                  AND vp.product_id IS NOT NULL
                  AND p.status NOT IN ('SOLD', 'PENDING_DELETION')
            """)
        ).fetchall()

        if not result:
            activity.logger.info("No products to update - all sold statuses are in sync")
            return {"pending_count": 0, "product_ids": []}

        service = PendingActionService(db)
        product_ids = []

        for vinted_id, product_id, title, price, stoflow_status in result:
            action = service.create_pending_action(
                product_id=product_id,
                action_type=PendingActionType.MARK_SOLD,
                marketplace="vinted",
                reason=f"Produit vendu/fermé sur Vinted (#{vinted_id})",
                context_data={
                    "vinted_id": vinted_id,
                    "title": title,
                    "price": float(price) if price else None,
                    "previous_status": stoflow_status,
                },
            )
            if action:
                product_ids.append(product_id)
                activity.logger.info(
                    f"Created pending action for StoFlow #{product_id} "
                    f"(Vinted #{vinted_id} is closed, was {stoflow_status})"
                )

        db.commit()

        activity.logger.info(
            f"Created {len(product_ids)} pending actions for sold Vinted products"
        )

        return {
            "pending_count": len(product_ids),
            "product_ids": product_ids,
        }

    finally:
        db.close()


@activity.defn(name="vinted_detect_sold_with_active_listing")
async def detect_sold_with_active_listing(user_id: int) -> dict:
    """
    Detect products SOLD on StoFlow but still active on Vinted.

    Creates PendingAction (DELETE_VINTED_LISTING) for each product found.

    Args:
        user_id: User ID for schema isolation

    Returns:
        Dict with 'pending_count' and 'product_ids'
    """
    db = SessionLocal()
    try:
        configure_activity_session(db, user_id)

        from services.pending_action_service import PendingActionService
        from models.user.pending_action import PendingActionType

        result = db.execute(
            text("""
                SELECT vp.vinted_id, vp.product_id, vp.title, vp.price,
                       p.status as stoflow_status
                FROM vinted_products vp
                JOIN products p ON p.id = vp.product_id
                WHERE p.status::text = 'SOLD'
                  AND vp.is_closed = false
                  AND vp.status != 'sold'
                  AND vp.product_id IS NOT NULL
            """)
        ).fetchall()

        if not result:
            activity.logger.info(
                "No products to clean up - all SOLD products have inactive Vinted listings"
            )
            return {"pending_count": 0, "product_ids": []}

        service = PendingActionService(db)
        product_ids = []

        for vinted_id, product_id, title, price, stoflow_status in result:
            action = service.create_pending_action(
                product_id=product_id,
                action_type=PendingActionType.DELETE_VINTED_LISTING,
                marketplace="vinted",
                reason=f"Produit vendu sur StoFlow mais annonce Vinted #{vinted_id} encore active",
                context_data={
                    "vinted_id": vinted_id,
                    "title": title,
                    "price": float(price) if price else None,
                },
            )
            if action:
                product_ids.append(product_id)
                activity.logger.info(
                    f"Created DELETE_VINTED_LISTING pending action for product #{product_id} "
                    f"(Vinted #{vinted_id} still active)"
                )

        db.commit()

        activity.logger.info(
            f"Created {len(product_ids)} pending actions for SOLD products "
            f"with active Vinted listings"
        )

        return {
            "pending_count": len(product_ids),
            "product_ids": product_ids,
        }

    finally:
        db.close()


@activity.defn(name="delete_vinted_listing")
async def delete_vinted_listing(user_id: int, product_id: int) -> dict:
    """
    Delete a Vinted listing for a product marked as SOLD.

    Args:
        user_id: User ID for schema isolation and plugin communication
        product_id: StoFlow product ID

    Returns:
        Dict with 'success', 'product_id', and optionally 'vinted_id' or 'error'
    """
    db = SessionLocal()
    try:
        configure_activity_session(db, user_id)

        from services.vinted.vinted_deletion_service import VintedDeletionService

        service = VintedDeletionService(db)
        result = await service.delete_product(
            product_id=product_id,
            user_id=user_id,
            check_conditions=False,
        )
        return result

    except Exception as e:
        activity.logger.error(f"Vinted deletion failed for product #{product_id}: {e}")
        return {"success": False, "product_id": product_id, "error": str(e)}

    finally:
        db.close()


# All reconciliation activities
VINTED_RECONCILIATION_ACTIVITIES = [
    sync_sold_status,
    detect_sold_with_active_listing,
    delete_vinted_listing,
]
