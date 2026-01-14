"""
eBay Payment Dispute Repository.

Data access layer for eBay payment dispute records.
Handles CRUD operations and queries for the ebay_payment_disputes table.

Author: Claude
Date: 2026-01-14
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from models.user.ebay_payment_dispute import EbayPaymentDispute


class EbayPaymentDisputeRepository:
    """
    Repository for eBay payment dispute data access.

    Usage:
        >>> repo = EbayPaymentDisputeRepository(db_session)
        >>> disputes = repo.get_all()
        >>> dispute = repo.get_by_payment_dispute_id("5********0")
    """

    def __init__(self, db: Session):
        """
        Initialize repository.

        Args:
            db: SQLAlchemy session with user schema set
        """
        self.db = db

    # =========================================================================
    # CRUD OPERATIONS
    # =========================================================================

    def create(self, dispute: EbayPaymentDispute) -> EbayPaymentDispute:
        """
        Create a new payment dispute record.

        Args:
            dispute: EbayPaymentDispute instance to create

        Returns:
            Created payment dispute with ID
        """
        self.db.add(dispute)
        self.db.commit()
        self.db.refresh(dispute)
        return dispute

    def update(self, dispute: EbayPaymentDispute) -> EbayPaymentDispute:
        """
        Update an existing payment dispute record.

        Args:
            dispute: EbayPaymentDispute instance with updates

        Returns:
            Updated payment dispute
        """
        self.db.commit()
        self.db.refresh(dispute)
        return dispute

    def delete(self, dispute: EbayPaymentDispute) -> None:
        """
        Delete a payment dispute record.

        Args:
            dispute: EbayPaymentDispute instance to delete
        """
        self.db.delete(dispute)
        self.db.commit()

    # =========================================================================
    # QUERY METHODS
    # =========================================================================

    def get_by_id(self, dispute_id: int) -> Optional[EbayPaymentDispute]:
        """
        Get a payment dispute by internal ID.

        Args:
            dispute_id: Internal database ID

        Returns:
            Payment dispute or None if not found
        """
        return (
            self.db.query(EbayPaymentDispute)
            .filter(EbayPaymentDispute.id == dispute_id)
            .first()
        )

    def get_by_payment_dispute_id(
        self, payment_dispute_id: str
    ) -> Optional[EbayPaymentDispute]:
        """
        Get a payment dispute by eBay payment dispute ID.

        Args:
            payment_dispute_id: eBay payment dispute ID

        Returns:
            Payment dispute or None if not found
        """
        return (
            self.db.query(EbayPaymentDispute)
            .filter(EbayPaymentDispute.payment_dispute_id == payment_dispute_id)
            .first()
        )

    def get_by_order_id(self, order_id: str) -> List[EbayPaymentDispute]:
        """
        Get all payment disputes for an order.

        Args:
            order_id: eBay order ID

        Returns:
            List of payment disputes for the order
        """
        return (
            self.db.query(EbayPaymentDispute)
            .filter(EbayPaymentDispute.order_id == order_id)
            .order_by(desc(EbayPaymentDispute.open_date))
            .all()
        )

    def get_all(
        self,
        page: int = 1,
        page_size: int = 50,
        state: Optional[str] = None,
        reason: Optional[str] = None,
        order_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get all payment disputes with pagination and filters.

        Args:
            page: Page number (1-indexed)
            page_size: Items per page
            state: Optional dispute state filter (OPEN, ACTION_NEEDED, CLOSED)
            reason: Optional reason filter
            order_id: Optional order ID filter

        Returns:
            Dict with items, total, page, page_size, total_pages
        """
        query = self.db.query(EbayPaymentDispute)

        # Apply filters
        if state:
            query = query.filter(EbayPaymentDispute.dispute_state == state)
        if reason:
            query = query.filter(EbayPaymentDispute.reason == reason)
        if order_id:
            query = query.filter(EbayPaymentDispute.order_id == order_id)

        # Get total count
        total = query.count()

        # Calculate pagination
        total_pages = (total + page_size - 1) // page_size
        offset = (page - 1) * page_size

        # Fetch items
        items = (
            query.order_by(desc(EbayPaymentDispute.open_date))
            .offset(offset)
            .limit(page_size)
            .all()
        )

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    def get_open_disputes(self, limit: int = 100) -> List[EbayPaymentDispute]:
        """
        Get all open disputes (OPEN or ACTION_NEEDED).

        Args:
            limit: Maximum number to return

        Returns:
            List of open payment disputes
        """
        return (
            self.db.query(EbayPaymentDispute)
            .filter(EbayPaymentDispute.dispute_state.in_(["OPEN", "ACTION_NEEDED"]))
            .order_by(EbayPaymentDispute.respond_by_date.asc().nulls_last())
            .limit(limit)
            .all()
        )

    def get_action_needed_disputes(self, limit: int = 100) -> List[EbayPaymentDispute]:
        """
        Get disputes requiring seller action.

        Args:
            limit: Maximum number to return

        Returns:
            List of disputes needing action
        """
        return (
            self.db.query(EbayPaymentDispute)
            .filter(EbayPaymentDispute.dispute_state == "ACTION_NEEDED")
            .order_by(EbayPaymentDispute.respond_by_date.asc().nulls_last())
            .limit(limit)
            .all()
        )

    def get_past_deadline_disputes(self) -> List[EbayPaymentDispute]:
        """
        Get disputes that are past their response deadline.

        Returns:
            List of disputes past deadline
        """
        return (
            self.db.query(EbayPaymentDispute)
            .filter(EbayPaymentDispute.dispute_state == "ACTION_NEEDED")
            .filter(EbayPaymentDispute.respond_by_date < datetime.utcnow())
            .order_by(EbayPaymentDispute.respond_by_date.asc())
            .all()
        )

    def get_closed_disputes(
        self, limit: int = 100
    ) -> List[EbayPaymentDispute]:
        """
        Get closed disputes.

        Args:
            limit: Maximum number to return

        Returns:
            List of closed payment disputes
        """
        return (
            self.db.query(EbayPaymentDispute)
            .filter(EbayPaymentDispute.dispute_state == "CLOSED")
            .order_by(desc(EbayPaymentDispute.closed_date))
            .limit(limit)
            .all()
        )

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get payment dispute statistics.

        Returns:
            Dict with:
            - open: Count of open disputes
            - action_needed: Count of disputes needing action
            - closed: Count of closed disputes
            - past_deadline: Count of disputes past deadline
            - total_amount: Total dispute amount (open disputes)
            - by_reason: Dict of counts by reason
        """
        # Count by state
        open_count = (
            self.db.query(EbayPaymentDispute)
            .filter(EbayPaymentDispute.dispute_state == "OPEN")
            .count()
        )

        action_needed_count = (
            self.db.query(EbayPaymentDispute)
            .filter(EbayPaymentDispute.dispute_state == "ACTION_NEEDED")
            .count()
        )

        closed_count = (
            self.db.query(EbayPaymentDispute)
            .filter(EbayPaymentDispute.dispute_state == "CLOSED")
            .count()
        )

        # Past deadline count
        past_deadline_count = (
            self.db.query(EbayPaymentDispute)
            .filter(EbayPaymentDispute.dispute_state == "ACTION_NEEDED")
            .filter(EbayPaymentDispute.respond_by_date < datetime.utcnow())
            .count()
        )

        # Total amount of open disputes
        total_amount = (
            self.db.query(func.coalesce(func.sum(EbayPaymentDispute.dispute_amount), 0))
            .filter(EbayPaymentDispute.dispute_state.in_(["OPEN", "ACTION_NEEDED"]))
            .scalar()
        ) or 0.0

        # Count by reason
        reason_counts = (
            self.db.query(
                EbayPaymentDispute.reason, func.count(EbayPaymentDispute.id)
            )
            .filter(EbayPaymentDispute.reason.isnot(None))
            .group_by(EbayPaymentDispute.reason)
            .all()
        )
        by_reason = {reason: count for reason, count in reason_counts}

        return {
            "open": open_count,
            "action_needed": action_needed_count,
            "closed": closed_count,
            "past_deadline": past_deadline_count,
            "total_amount": float(total_amount),
            "by_reason": by_reason,
        }

    # =========================================================================
    # UPSERT OPERATIONS
    # =========================================================================

    def upsert_from_api(self, api_data: Dict[str, Any]) -> EbayPaymentDispute:
        """
        Create or update a payment dispute from API data.

        Args:
            api_data: Payment dispute data from eBay API

        Returns:
            Created or updated payment dispute
        """
        payment_dispute_id = api_data.get("paymentDisputeId")

        # Try to find existing
        existing = self.get_by_payment_dispute_id(payment_dispute_id)

        if existing:
            # Update existing record
            self._update_from_api(existing, api_data)
            return self.update(existing)
        else:
            # Create new record
            dispute = self._create_from_api(api_data)
            return self.create(dispute)

    def _create_from_api(self, api_data: Dict[str, Any]) -> EbayPaymentDispute:
        """Create a new payment dispute from API data."""
        dispute = EbayPaymentDispute(
            payment_dispute_id=api_data.get("paymentDisputeId"),
            order_id=api_data.get("orderId"),
            dispute_state=api_data.get("paymentDisputeStatus"),
            reason=api_data.get("reason"),
            reason_for_closure=api_data.get("reasonForClosure"),
            seller_response=api_data.get("sellerResponse"),
            note=api_data.get("note"),
            revision=api_data.get("revision"),
            available_choices=api_data.get("availableChoices"),
            evidence=api_data.get("evidence"),
            evidence_requests=api_data.get("evidenceRequests"),
            line_items=api_data.get("lineItems"),
            resolution=api_data.get("resolution"),
            return_address=api_data.get("returnAddress"),
            buyer_username=api_data.get("buyerUsername"),
        )

        # Parse amount
        amount_data = api_data.get("amount", {})
        if amount_data:
            try:
                dispute.dispute_amount = float(amount_data.get("value", 0))
            except (ValueError, TypeError):
                dispute.dispute_amount = None
            dispute.dispute_currency = amount_data.get("currency")

        # Parse dates
        dispute.open_date = self._parse_datetime(api_data.get("openDate"))
        dispute.respond_by_date = self._parse_datetime(api_data.get("respondByDate"))
        dispute.closed_date = self._parse_datetime(api_data.get("closedDate"))

        return dispute

    def _update_from_api(
        self, dispute: EbayPaymentDispute, api_data: Dict[str, Any]
    ) -> None:
        """Update an existing payment dispute from API data."""
        dispute.order_id = api_data.get("orderId", dispute.order_id)
        dispute.dispute_state = api_data.get(
            "paymentDisputeStatus", dispute.dispute_state
        )
        dispute.reason = api_data.get("reason", dispute.reason)
        dispute.reason_for_closure = api_data.get(
            "reasonForClosure", dispute.reason_for_closure
        )
        dispute.seller_response = api_data.get("sellerResponse", dispute.seller_response)
        dispute.note = api_data.get("note", dispute.note)
        dispute.revision = api_data.get("revision", dispute.revision)
        dispute.available_choices = api_data.get(
            "availableChoices", dispute.available_choices
        )
        dispute.evidence = api_data.get("evidence", dispute.evidence)
        dispute.evidence_requests = api_data.get(
            "evidenceRequests", dispute.evidence_requests
        )
        dispute.line_items = api_data.get("lineItems", dispute.line_items)
        dispute.resolution = api_data.get("resolution", dispute.resolution)
        dispute.return_address = api_data.get("returnAddress", dispute.return_address)
        dispute.buyer_username = api_data.get("buyerUsername", dispute.buyer_username)

        # Parse amount
        amount_data = api_data.get("amount")
        if amount_data:
            try:
                dispute.dispute_amount = float(amount_data.get("value", 0))
            except (ValueError, TypeError):
                pass
            dispute.dispute_currency = amount_data.get("currency", dispute.dispute_currency)

        # Parse dates
        if api_data.get("openDate"):
            dispute.open_date = self._parse_datetime(api_data.get("openDate"))
        if api_data.get("respondByDate"):
            dispute.respond_by_date = self._parse_datetime(api_data.get("respondByDate"))
        if api_data.get("closedDate"):
            dispute.closed_date = self._parse_datetime(api_data.get("closedDate"))

    def _parse_datetime(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse ISO 8601 datetime string."""
        if not date_str:
            return None
        try:
            # Handle various ISO formats
            date_str = date_str.replace("Z", "+00:00")
            return datetime.fromisoformat(date_str.replace("+00:00", ""))
        except (ValueError, TypeError):
            return None
