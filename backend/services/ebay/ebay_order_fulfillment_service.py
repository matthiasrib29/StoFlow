"""
eBay Order Fulfillment Service

Service pour gérer le fulfillment des commandes eBay (statut, tracking).
Responsabilité: Mettre à jour le statut et ajouter tracking (appels API eBay).

Architecture:
- Update fulfillment status (local DB only)
- Add tracking (eBay API + local DB)
- Business validation (order paid, valid status)

Created: 2026-01-07
Author: Claude
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from models.user.ebay_order import EbayOrder
from repositories.ebay_order_repository import EbayOrderRepository
from services.ebay.ebay_fulfillment_client import EbayFulfillmentClient
from shared.logging_setup import get_logger

logger = get_logger(__name__)

# Valid fulfillment statuses
VALID_STATUSES = {"NOT_STARTED", "IN_PROGRESS", "FULFILLED"}


class EbayOrderFulfillmentService:
    """
    Service pour gérer le fulfillment des commandes eBay.

    Fonctionnalités:
    - Mettre à jour le statut de fulfillment (local DB)
    - Ajouter tracking à une commande (eBay API + local DB)

    Usage:
        >>> service = EbayOrderFulfillmentService(db_session, user_id=1)
        >>> order = service.update_fulfillment_status(order_id=123, new_status="IN_PROGRESS")
        >>> result = service.add_tracking(order_id=123, tracking_number="1234567890", carrier_code="COLISSIMO")
    """

    def __init__(self, db: Session, user_id: int):
        """
        Initialize fulfillment service.

        Args:
            db: Session SQLAlchemy (avec search_path déjà défini)
            user_id: ID utilisateur pour authentification eBay
        """
        self.db = db
        self.user_id = user_id
        self.fulfillment_client = EbayFulfillmentClient(db, user_id)

        logger.info(f"[EbayOrderFulfillmentService] Initialized for user_id={user_id}")

    def update_fulfillment_status(self, order_id: int, new_status: str) -> EbayOrder:
        """
        Update order fulfillment status (local DB only).

        **Note:** This does NOT call eBay API. It only updates the local database.
        Use `add_tracking()` to update eBay's fulfillment status.

        Args:
            order_id: Internal order ID
            new_status: New fulfillment status (NOT_STARTED, IN_PROGRESS, FULFILLED)

        Returns:
            Updated EbayOrder instance

        Raises:
            ValueError: If order not found or invalid status

        Examples:
            >>> service = EbayOrderFulfillmentService(db, user_id=1)
            >>> order = service.update_fulfillment_status(123, "IN_PROGRESS")
            >>> print(order.order_fulfillment_status)
            IN_PROGRESS
        """
        logger.info(
            f"[EbayOrderFulfillmentService] update_fulfillment_status: "
            f"user_id={self.user_id}, order_id={order_id}, new_status={new_status}"
        )

        # Validate status
        if new_status not in VALID_STATUSES:
            raise ValueError(
                f"Invalid status '{new_status}'. Must be one of: {', '.join(VALID_STATUSES)}"
            )

        # Get order
        order = EbayOrderRepository.get_by_id(self.db, order_id)

        if not order:
            raise ValueError(f"Order {order_id} not found")

        # Update status
        old_status = order.order_fulfillment_status
        order.order_fulfillment_status = new_status
        order.updated_at = datetime.now(timezone.utc)

        # Save changes
        updated_order = EbayOrderRepository.update(self.db, order)
        self.db.commit()

        logger.info(
            f"[EbayOrderFulfillmentService] Order {order.order_id} status updated: "
            f"{old_status} → {new_status}"
        )

        return updated_order
    # ===== HELPER METHODS FOR add_tracking() (Refactored 2026-01-12 Phase 3.2c) =====

    @staticmethod
    def _validate_order_for_tracking(order: EbayOrder, tracking_number: str) -> None:
        """
        Validate order can receive tracking (PAID status, valid tracking format).

        Args:
            order: EbayOrder to validate
            tracking_number: Tracking number to validate

        Raises:
            ValueError: If order not paid or tracking format invalid
        """
        if order.order_payment_status != "PAID":
            raise ValueError(
                f"Order {order.order_id} is not paid (status: {order.order_payment_status}). "
                "Cannot add tracking to unpaid order."
            )

        if not tracking_number.isalnum():
            raise ValueError(
                f"Invalid tracking number '{tracking_number}'. "
                "Must be alphanumeric only (no spaces, dashes, or special characters)."
            )

    @staticmethod
    def _prepare_shipped_date(shipped_date: Optional[datetime]) -> str:
        """
        Prepare shipped date in eBay API format (ISO 8601).

        Args:
            shipped_date: Shipped date (default: now if None)

        Returns:
            ISO 8601 formatted date string
        """
        if shipped_date is None:
            shipped_date = datetime.now(timezone.utc)

        return shipped_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")

    @staticmethod
    def _build_line_items_payload(order: EbayOrder) -> list[dict]:
        """
        Build line items payload for eBay shipping fulfillment API.

        Args:
            order: EbayOrder with products

        Returns:
            List of line items with lineItemId and quantity

        Raises:
            ValueError: If no valid line items found
        """
        line_items_payload = []

        for product in order.products:
            if product.line_item_id:
                line_items_payload.append({
                    "lineItemId": product.line_item_id,
                    "quantity": product.quantity or 1,
                })

        if not line_items_payload:
            raise ValueError(
                f"Order {order.order_id} has no line items with lineItemId. "
                "Cannot create shipping fulfillment."
            )

        return line_items_payload

    def _update_order_tracking(
        self, order: EbayOrder, tracking_number: str, carrier_code: str
    ) -> None:
        """
        Update order tracking info in local DB.

        Args:
            order: EbayOrder to update
            tracking_number: Tracking number
            carrier_code: Carrier code
        """
        order.tracking_number = tracking_number
        order.shipping_carrier = carrier_code
        order.order_fulfillment_status = "IN_PROGRESS"
        order.updated_at = datetime.now(timezone.utc)

        EbayOrderRepository.update(self.db, order)
        self.db.commit()

        logger.info(
            f"[EbayOrderFulfillmentService] Order {order.order_id} tracking added: "
            f"{tracking_number} ({carrier_code})"
        )


    def add_tracking(
        self,
        order_id: int,
        tracking_number: str,
        carrier_code: str,
        shipped_date: Optional[datetime] = None,
    ) -> dict:
        """
        Add tracking information to order (calls eBay API + updates local DB).

        **Workflow (refactored 2026-01-12):**
        1. Validate order exists and is PAID
        2. Prepare payload for eBay API
        3. Call eBay API: POST /order/{orderId}/shipping_fulfillment
        4. Update local DB with tracking info
        5. Mark fulfillment status as IN_PROGRESS

        **Important:**
        - Order MUST have payment status "PAID"
        - Tracking number MUST be alphanumeric only (no spaces, dashes, special chars)
        - This will mark the order as shipped on eBay

        Args:
            order_id: Internal order ID
            tracking_number: Tracking number (alphanumeric only)
            carrier_code: Carrier code (e.g., "COLISSIMO", "CHRONOPOST", "UPS")
            shipped_date: Shipped date (default: now)

        Returns:
            Result dict:
            {
                "success": True,
                "fulfillment_id": str,  # eBay fulfillment ID
                "order_id": str,        # eBay order ID
                "tracking_number": str
            }

        Raises:
            ValueError: If order not found or not paid
            RuntimeError: If eBay API call fails

        Examples:
            >>> service = EbayOrderFulfillmentService(db, user_id=1)
            >>> result = service.add_tracking(
            ...     order_id=123,
            ...     tracking_number="1234567890",
            ...     carrier_code="COLISSIMO"
            ... )
            >>> print(result["fulfillment_id"])
            abc123xyz
        """
        logger.info(
            f"[EbayOrderFulfillmentService] add_tracking: user_id={self.user_id}, "
            f"order_id={order_id}, tracking={tracking_number}, carrier={carrier_code}"
        )

        # 1. Get and validate order
        order = EbayOrderRepository.get_by_id(self.db, order_id)

        if not order:
            raise ValueError(f"Order {order_id} not found")

        self._validate_order_for_tracking(order, tracking_number)

        # 2. Prepare payload
        shipped_date_iso = self._prepare_shipped_date(shipped_date)
        line_items_payload = self._build_line_items_payload(order)

        payload = {
            "lineItems": line_items_payload,
            "shippedDate": shipped_date_iso,
            "shippingCarrierCode": carrier_code,
            "trackingNumber": tracking_number,
        }

        logger.debug(
            f"[EbayOrderFulfillmentService] Calling eBay API for order {order.order_id}"
        )

        # 3. Call eBay API and update DB
        try:
            api_result = self.fulfillment_client.create_shipping_fulfillment(
                order_id=order.order_id,
                payload=payload,
            )

            fulfillment_id = api_result.get("fulfillmentId", "unknown")

            logger.info(
                f"[EbayOrderFulfillmentService] eBay API success: "
                f"fulfillment_id={fulfillment_id}"
            )

            self._update_order_tracking(order, tracking_number, carrier_code)

            return {
                "success": True,
                "fulfillment_id": fulfillment_id,
                "order_id": order.order_id,
                "tracking_number": tracking_number,
            }

        except Exception as e:
            self.db.rollback()
            logger.error(
                f"[EbayOrderFulfillmentService] Failed to add tracking for "
                f"order {order.order_id}: {e}",
                exc_info=True,
            )
            raise RuntimeError(
                f"Failed to add tracking to eBay: {str(e)}"
            ) from e

