"""
eBay Refund Service

Service for managing eBay refunds:
- Issue new refunds via Fulfillment API
- Sync refunds from order payment summaries
- Track refund statistics

Architecture:
- Uses EbayFulfillmentClient for API calls
- Uses EbayRefundRepository for database operations
- Extracts refunds from order data (no dedicated refund API)

Created: 2026-01-14
Author: Claude
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from models.user.ebay_refund import EbayRefund
from repositories.ebay_refund_repository import EbayRefundRepository
from services.ebay.ebay_fulfillment_client import EbayFulfillmentClient
from shared.exceptions import EbayError
from shared.logging import get_logger

logger = get_logger(__name__)


class EbayRefundService:
    """
    Service for managing eBay refunds.

    Provides:
    - issue_refund(): Issue a new refund for an order
    - sync_refunds_from_order(): Extract refunds from order data
    - get_statistics(): Get refund statistics
    """

    def __init__(self, db: Session, user_id: int):
        """
        Initialize the refund service.

        Args:
            db: SQLAlchemy session (already set to user schema)
            user_id: User ID for API client initialization
        """
        self.db = db
        self.user_id = user_id
        self._client: Optional[EbayFulfillmentClient] = None

    @property
    def client(self) -> EbayFulfillmentClient:
        """Lazy-load the fulfillment client."""
        if self._client is None:
            self._client = EbayFulfillmentClient(self.db, self.user_id)
        return self._client

    # =========================================================================
    # Issue Refund
    # =========================================================================

    def issue_refund(
        self,
        order_id: str,
        reason: str,
        amount: float,
        currency: str = "EUR",
        line_item_id: Optional[str] = None,
        comment: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Issue a refund for an order.

        Args:
            order_id: eBay order ID
            reason: Refund reason code:
                - BUYER_CANCEL: Buyer cancelled the order
                - BUYER_RETURN: Buyer returned the item
                - ITEM_NOT_RECEIVED: Item was not received
                - SELLER_WRONG_ITEM: Wrong item sent
                - SELLER_OUT_OF_STOCK: Item out of stock
                - SELLER_FOUND_ISSUE: Seller found issue with item
                - OTHER: Other reason
            amount: Refund amount
            currency: Currency code (default: EUR)
            line_item_id: Optional line item ID for item-specific refund
            comment: Optional comment

        Returns:
            Dict with:
            {
                "success": bool,
                "refund_id": str,
                "refund_status": str,
                "message": str | None
            }

        Raises:
            EbayError: If API call fails
        """
        logger.info(
            f"[EbayRefundService] Issuing refund for order {order_id}: "
            f"amount={amount} {currency}, reason={reason}"
        )

        try:
            # Call eBay API to issue refund
            result = self.client.issue_refund(
                order_id=order_id,
                reason_for_refund=reason,
                refund_amount=amount,
                currency=currency,
                line_item_id=line_item_id,
                comment=comment,
            )

            refund_id = result.get("refundId", "")
            refund_status = result.get("refundStatus", "PENDING")

            # Create local refund record
            refund = EbayRefund(
                refund_id=refund_id or f"MANUAL-{order_id}-{datetime.now().timestamp()}",
                order_id=order_id,
                refund_source="MANUAL",
                refund_status=refund_status,
                refund_amount=amount,
                refund_currency=currency,
                reason=reason,
                comment=comment,
                line_item_id=line_item_id,
                refund_date=datetime.now(timezone.utc),
                creation_date=datetime.now(timezone.utc),
                raw_data=result,
            )

            EbayRefundRepository.create(self.db, refund)
            self.db.flush()

            logger.info(
                f"[EbayRefundService] Refund issued successfully: "
                f"refund_id={refund_id}, status={refund_status}"
            )

            return {
                "success": True,
                "refund_id": refund_id,
                "refund_status": refund_status,
                "message": None,
            }

        except EbayError as e:
            logger.error(f"[EbayRefundService] Failed to issue refund: {e}", exc_info=True)
            return {
                "success": False,
                "refund_id": None,
                "refund_status": None,
                "message": str(e),
            }

    # =========================================================================
    # Sync from Order
    # =========================================================================

    def sync_refunds_from_order(self, order_id: str) -> Dict[str, int]:
        """
        Extract and sync refunds from an order's payment summary.

        eBay doesn't have a dedicated refund search endpoint.
        Refunds are embedded in the order's payment summary.

        Args:
            order_id: eBay order ID

        Returns:
            Dict with sync results:
            {
                "created": int,
                "updated": int,
                "skipped": int
            }
        """
        logger.info(f"[EbayRefundService] Syncing refunds from order {order_id}")

        created = 0
        updated = 0
        skipped = 0

        try:
            # Get order details
            order = self.client.get_order(order_id)
            payment_summary = order.get("paymentSummary", {})
            refunds = payment_summary.get("refunds", [])

            if not refunds:
                logger.debug(f"No refunds found in order {order_id}")
                return {"created": 0, "updated": 0, "skipped": 0}

            # Get buyer info from order
            buyer = order.get("buyer", {})
            buyer_username = buyer.get("username")

            for refund_data in refunds:
                result = self._process_refund_data(order_id, refund_data, buyer_username)

                if result == "created":
                    created += 1
                elif result == "updated":
                    updated += 1
                else:
                    skipped += 1

            self.db.flush()

            logger.info(
                f"[EbayRefundService] Sync complete for order {order_id}: "
                f"created={created}, updated={updated}, skipped={skipped}"
            )

        except EbayError as e:
            logger.error(f"[EbayRefundService] Failed to sync refunds: {e}", exc_info=True)

        return {"created": created, "updated": updated, "skipped": skipped}

    def _process_refund_data(
        self,
        order_id: str,
        refund_data: Dict[str, Any],
        buyer_username: Optional[str],
    ) -> str:
        """
        Process a single refund record from order data.

        Args:
            order_id: eBay order ID
            refund_data: Refund data from payment summary
            buyer_username: Buyer's username

        Returns:
            str: "created", "updated", or "skipped"
        """
        refund_id = refund_data.get("refundId", "")

        if not refund_id:
            return "skipped"

        # Check if refund already exists
        existing = EbayRefundRepository.get_by_ebay_refund_id(self.db, refund_id)

        # Extract amount
        amount_data = refund_data.get("refundAmount", {})
        amount = float(amount_data.get("value", 0))
        currency = amount_data.get("currency", "EUR")

        # Parse date
        refund_date_str = refund_data.get("refundDate")
        refund_date = None
        if refund_date_str:
            try:
                refund_date = datetime.fromisoformat(
                    refund_date_str.replace("Z", "+00:00")
                )
            except (ValueError, TypeError):
                pass

        if existing:
            # Update existing record
            existing.refund_status = refund_data.get("refundStatus", existing.refund_status)
            existing.refund_amount = amount or existing.refund_amount
            existing.refund_currency = currency or existing.refund_currency
            existing.refund_date = refund_date or existing.refund_date
            existing.refund_reference_id = refund_data.get(
                "refundReferenceId", existing.refund_reference_id
            )
            existing.raw_data = refund_data

            EbayRefundRepository.update(self.db, existing)
            return "updated"
        else:
            # Create new record
            # Determine source based on refund data
            source = self._determine_refund_source(refund_data)

            refund = EbayRefund(
                refund_id=refund_id,
                order_id=order_id,
                refund_source=source,
                refund_status=refund_data.get("refundStatus", "REFUNDED"),
                refund_amount=amount,
                refund_currency=currency,
                buyer_username=buyer_username,
                refund_reference_id=refund_data.get("refundReferenceId"),
                refund_date=refund_date,
                creation_date=refund_date,
                raw_data=refund_data,
            )

            EbayRefundRepository.create(self.db, refund)
            return "created"

    def _determine_refund_source(self, refund_data: Dict[str, Any]) -> str:
        """
        Determine the source of a refund based on available data.

        Args:
            refund_data: Refund data from payment summary

        Returns:
            str: Source type (RETURN, CANCELLATION, MANUAL, OTHER)
        """
        # Check for reference ID patterns or other indicators
        ref_id = refund_data.get("refundReferenceId", "")

        # eBay doesn't always clearly indicate the source
        # This is a best-effort determination
        if ref_id:
            if "RET" in ref_id.upper():
                return "RETURN"
            if "CAN" in ref_id.upper():
                return "CANCELLATION"

        # Default to OTHER if can't determine
        return "OTHER"

    # =========================================================================
    # Sync All Orders
    # =========================================================================

    def sync_refunds_from_recent_orders(self, days_back: int = 30) -> Dict[str, int]:
        """
        Sync refunds from all recent orders.

        Fetches orders modified in the last N days and extracts refunds.

        Args:
            days_back: Number of days to look back

        Returns:
            Dict with sync results
        """
        from datetime import timedelta

        logger.info(
            f"[EbayRefundService] Syncing refunds from orders in last {days_back} days"
        )

        total_created = 0
        total_updated = 0
        total_skipped = 0
        total_errors = 0

        try:
            # Get recent orders
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=days_back)

            orders = self.client.get_orders_by_date_range(start_date, end_date)

            logger.info(f"[EbayRefundService] Found {len(orders)} orders to process")

            for order in orders:
                order_id = order.get("orderId")
                if not order_id:
                    continue

                # Check if order has refunds
                payment_summary = order.get("paymentSummary", {})
                refunds = payment_summary.get("refunds", [])

                if not refunds:
                    continue

                try:
                    result = self.sync_refunds_from_order(order_id)
                    total_created += result.get("created", 0)
                    total_updated += result.get("updated", 0)
                    total_skipped += result.get("skipped", 0)
                except Exception as e:
                    logger.error(
                        f"[EbayRefundService] Error syncing order {order_id}: {e}"
                    )
                    total_errors += 1

        except EbayError as e:
            logger.error(f"[EbayRefundService] Failed to fetch orders: {e}", exc_info=True)

        logger.info(
            f"[EbayRefundService] Sync complete: created={total_created}, "
            f"updated={total_updated}, skipped={total_skipped}, errors={total_errors}"
        )

        return {
            "created": total_created,
            "updated": total_updated,
            "skipped": total_skipped,
            "errors": total_errors,
        }

    # =========================================================================
    # Statistics
    # =========================================================================

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get refund statistics.

        Returns:
            Dict with statistics:
            {
                "pending": int,
                "completed": int,
                "failed": int,
                "total_refunded": float,
                "by_source": {
                    "RETURN": int,
                    "CANCELLATION": int,
                    "MANUAL": int
                }
            }
        """
        return EbayRefundRepository.get_statistics(self.db)

    # =========================================================================
    # CRUD Operations (pass-through to repository)
    # =========================================================================

    def get_refund_by_id(self, refund_id: int) -> Optional[EbayRefund]:
        """Get refund by internal ID."""
        return EbayRefundRepository.get_by_id(self.db, refund_id)

    def get_refund_by_ebay_id(self, ebay_refund_id: str) -> Optional[EbayRefund]:
        """Get refund by eBay refund ID."""
        return EbayRefundRepository.get_by_ebay_refund_id(self.db, ebay_refund_id)

    def get_refunds_for_order(self, order_id: str) -> List[EbayRefund]:
        """Get all refunds for an order."""
        return EbayRefundRepository.get_by_order_id(self.db, order_id)

    def get_refunds_for_return(self, return_id: str) -> List[EbayRefund]:
        """Get all refunds for a return."""
        return EbayRefundRepository.get_by_return_id(self.db, return_id)

    def get_refunds_for_cancellation(self, cancel_id: str) -> List[EbayRefund]:
        """Get all refunds for a cancellation."""
        return EbayRefundRepository.get_by_cancel_id(self.db, cancel_id)

    def list_refunds(
        self,
        page: int = 1,
        page_size: int = 50,
        status: Optional[str] = None,
        source: Optional[str] = None,
        order_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        List refunds with pagination.

        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page
            status: Filter by status
            source: Filter by source
            order_id: Filter by order ID

        Returns:
            Dict with pagination info:
            {
                "items": List[EbayRefund],
                "total": int,
                "page": int,
                "page_size": int,
                "total_pages": int
            }
        """
        skip = (page - 1) * page_size

        refunds, total = EbayRefundRepository.list_refunds(
            self.db,
            skip=skip,
            limit=page_size,
            status=status,
            source=source,
            order_id=order_id,
        )

        total_pages = (total + page_size - 1) // page_size

        return {
            "items": refunds,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    def list_pending_refunds(self, limit: int = 100) -> List[EbayRefund]:
        """Get pending refunds."""
        return EbayRefundRepository.list_pending(self.db, limit)

    def list_failed_refunds(self, limit: int = 100) -> List[EbayRefund]:
        """Get failed refunds."""
        return EbayRefundRepository.list_failed(self.db, limit)
