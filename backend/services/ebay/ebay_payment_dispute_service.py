"""
eBay Payment Dispute Service.

Service for managing eBay payment disputes:
- Sync disputes from Fulfillment API
- Accept disputes (concede to buyer)
- Contest disputes (fight buyer's claim)
- Add evidence before contesting
- Track dispute statistics

Architecture:
- Uses EbayFulfillmentClient for API calls
- Uses EbayPaymentDisputeRepository for database operations
- Requires sell.payment.dispute OAuth scope

Documentation:
- https://developer.ebay.com/api-docs/sell/fulfillment/resources/payment_dispute/methods/

Created: 2026-01-14
Author: Claude
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from models.user.ebay_payment_dispute import EbayPaymentDispute
from repositories.ebay_payment_dispute_repository import EbayPaymentDisputeRepository
from services.ebay.ebay_fulfillment_client import EbayFulfillmentClient
from shared.exceptions import EbayError
from shared.logging import get_logger

logger = get_logger(__name__)


class EbayPaymentDisputeService:
    """
    Service for managing eBay payment disputes.

    Provides:
    - sync_disputes(): Sync all disputes from eBay API
    - accept_dispute(): Accept a dispute (concede to buyer)
    - contest_dispute(): Contest a dispute (fight the claim)
    - add_evidence(): Add evidence before contesting
    - get_statistics(): Get dispute statistics

    Usage:
        >>> service = EbayPaymentDisputeService(db, user_id)
        >>> await service.sync_disputes()
        >>> service.contest_dispute("5********0")
    """

    def __init__(self, db: Session, user_id: int):
        """
        Initialize the payment dispute service.

        Args:
            db: SQLAlchemy session (already set to user schema)
            user_id: User ID for API client initialization
        """
        self.db = db
        self.user_id = user_id
        self.repository = EbayPaymentDisputeRepository(db)
        self._client: Optional[EbayFulfillmentClient] = None

    @property
    def client(self) -> EbayFulfillmentClient:
        """Lazy-load the fulfillment client."""
        if self._client is None:
            self._client = EbayFulfillmentClient(self.db, self.user_id)
        return self._client

    # =========================================================================
    # SYNC OPERATIONS
    # =========================================================================

    def sync_disputes(self, days_back: int = 90) -> Dict[str, int]:
        """
        Sync all payment disputes from eBay API.

        Fetches disputes opened in the last N days (max 90).

        Args:
            days_back: Number of days to look back (max 90)

        Returns:
            Dict with sync results:
            {
                "created": int,
                "updated": int,
                "total_fetched": int,
                "errors": int
            }
        """
        days_back = min(days_back, 90)  # eBay API limit
        logger.info(
            f"[EbayPaymentDisputeService] Syncing disputes from last {days_back} days"
        )

        created = 0
        updated = 0
        errors = 0
        total_fetched = 0

        try:
            # Fetch all disputes from API
            disputes = self.client.get_all_payment_disputes(days_back=days_back)
            total_fetched = len(disputes)

            logger.info(
                f"[EbayPaymentDisputeService] Fetched {total_fetched} disputes from API"
            )

            for dispute_data in disputes:
                try:
                    result = self._process_dispute_data(dispute_data)
                    if result == "created":
                        created += 1
                    elif result == "updated":
                        updated += 1
                except Exception as e:
                    logger.error(
                        f"[EbayPaymentDisputeService] Error processing dispute "
                        f"{dispute_data.get('paymentDisputeId')}: {e}",
                        exc_info=True,
                    )
                    errors += 1

            self.db.commit()

        except EbayError as e:
            logger.error(f"[EbayPaymentDisputeService] API error during sync: {e}", exc_info=True)
            errors += 1

        logger.info(
            f"[EbayPaymentDisputeService] Sync complete: "
            f"fetched={total_fetched}, created={created}, "
            f"updated={updated}, errors={errors}"
        )

        return {
            "created": created,
            "updated": updated,
            "total_fetched": total_fetched,
            "errors": errors,
        }

    def sync_dispute(self, payment_dispute_id: str) -> Optional[EbayPaymentDispute]:
        """
        Sync a single dispute from eBay API.

        Args:
            payment_dispute_id: eBay payment dispute ID

        Returns:
            Updated dispute record or None if error
        """
        logger.info(
            f"[EbayPaymentDisputeService] Syncing dispute {payment_dispute_id}"
        )

        try:
            dispute_data = self.client.get_payment_dispute(payment_dispute_id)

            if not dispute_data:
                logger.warning(
                    f"[EbayPaymentDisputeService] No data returned for {payment_dispute_id}"
                )
                return None

            result = self._process_dispute_data(dispute_data)
            self.db.commit()

            dispute = self.repository.get_by_payment_dispute_id(payment_dispute_id)
            logger.info(
                f"[EbayPaymentDisputeService] Dispute {payment_dispute_id} "
                f"synced ({result})"
            )
            return dispute

        except EbayError as e:
            logger.error(
                f"[EbayPaymentDisputeService] Error syncing dispute "
                f"{payment_dispute_id}: {e}"
            )
            return None

    def _process_dispute_data(self, dispute_data: Dict[str, Any]) -> str:
        """
        Process dispute data from API (create or update local record).

        Args:
            dispute_data: Dispute data from eBay API

        Returns:
            "created" or "updated"
        """
        payment_dispute_id = dispute_data.get("paymentDisputeId")

        if not payment_dispute_id:
            raise ValueError("Dispute data missing paymentDisputeId")

        existing = self.repository.get_by_payment_dispute_id(payment_dispute_id)

        if existing:
            self._update_dispute_from_api(existing, dispute_data)
            self.repository.update(existing)
            return "updated"
        else:
            dispute = self._create_dispute_from_api(dispute_data)
            self.repository.create(dispute)
            return "created"

    def _create_dispute_from_api(
        self, dispute_data: Dict[str, Any]
    ) -> EbayPaymentDispute:
        """Create a new dispute record from API data."""
        return self.repository._create_from_api(dispute_data)

    def _update_dispute_from_api(
        self, dispute: EbayPaymentDispute, dispute_data: Dict[str, Any]
    ) -> None:
        """Update existing dispute from API data."""
        self.repository._update_from_api(dispute, dispute_data)

    # =========================================================================
    # DISPUTE ACTIONS
    # =========================================================================

    def accept_dispute(
        self,
        payment_dispute_id: str,
        return_address: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Accept a payment dispute (concede to buyer).

        The seller agrees the buyer's claim is valid. A refund will be issued.

        Args:
            payment_dispute_id: eBay payment dispute ID
            return_address: Optional return address if buyer should return item

        Returns:
            Dict with result:
            {
                "success": bool,
                "message": str | None,
                "dispute": EbayPaymentDispute | None
            }
        """
        logger.info(
            f"[EbayPaymentDisputeService] Accepting dispute {payment_dispute_id}"
        )

        # Get current dispute to get revision
        dispute = self.repository.get_by_payment_dispute_id(payment_dispute_id)

        if not dispute:
            # Try to sync first
            dispute = self.sync_dispute(payment_dispute_id)

        if not dispute:
            return {
                "success": False,
                "message": f"Dispute {payment_dispute_id} not found",
                "dispute": None,
            }

        if dispute.dispute_state == "CLOSED":
            return {
                "success": False,
                "message": "Dispute is already closed",
                "dispute": dispute,
            }

        if not dispute.can_accept:
            return {
                "success": False,
                "message": "ACCEPT is not available for this dispute",
                "dispute": dispute,
            }

        revision = dispute.revision or 1

        try:
            success = self.client.accept_payment_dispute(
                payment_dispute_id=payment_dispute_id,
                revision=revision,
                return_address=return_address,
            )

            if success:
                # Refresh dispute from API to get updated state
                self.sync_dispute(payment_dispute_id)
                dispute = self.repository.get_by_payment_dispute_id(payment_dispute_id)

                logger.info(
                    f"[EbayPaymentDisputeService] Dispute {payment_dispute_id} accepted"
                )

                return {
                    "success": True,
                    "message": None,
                    "dispute": dispute,
                }
            else:
                return {
                    "success": False,
                    "message": "API call returned failure",
                    "dispute": dispute,
                }

        except EbayError as e:
            logger.error(
                f"[EbayPaymentDisputeService] Error accepting dispute: {e}"
            )
            return {
                "success": False,
                "message": str(e),
                "dispute": dispute,
            }

    def contest_dispute(
        self,
        payment_dispute_id: str,
        note: Optional[str] = None,
        return_address: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Contest a payment dispute (fight buyer's claim).

        IMPORTANT: Evidence should be added BEFORE calling this method.
        Once contested, no more evidence can be added.

        Args:
            payment_dispute_id: eBay payment dispute ID
            note: Optional note (max 1000 chars)
            return_address: Optional return address

        Returns:
            Dict with result:
            {
                "success": bool,
                "message": str | None,
                "dispute": EbayPaymentDispute | None
            }
        """
        logger.info(
            f"[EbayPaymentDisputeService] Contesting dispute {payment_dispute_id}"
        )

        # Get current dispute to get revision
        dispute = self.repository.get_by_payment_dispute_id(payment_dispute_id)

        if not dispute:
            dispute = self.sync_dispute(payment_dispute_id)

        if not dispute:
            return {
                "success": False,
                "message": f"Dispute {payment_dispute_id} not found",
                "dispute": None,
            }

        if dispute.dispute_state == "CLOSED":
            return {
                "success": False,
                "message": "Dispute is already closed",
                "dispute": dispute,
            }

        if not dispute.can_contest:
            return {
                "success": False,
                "message": "CONTEST is not available for this dispute",
                "dispute": dispute,
            }

        revision = dispute.revision or 1

        try:
            success = self.client.contest_payment_dispute(
                payment_dispute_id=payment_dispute_id,
                revision=revision,
                note=note,
                return_address=return_address,
            )

            if success:
                # Update local record
                dispute.seller_response = "CONTEST"
                if note:
                    dispute.note = note
                self.repository.update(dispute)
                self.db.commit()

                # Refresh from API
                self.sync_dispute(payment_dispute_id)
                dispute = self.repository.get_by_payment_dispute_id(payment_dispute_id)

                logger.info(
                    f"[EbayPaymentDisputeService] Dispute {payment_dispute_id} contested"
                )

                return {
                    "success": True,
                    "message": None,
                    "dispute": dispute,
                }
            else:
                return {
                    "success": False,
                    "message": "API call returned failure",
                    "dispute": dispute,
                }

        except EbayError as e:
            logger.error(
                f"[EbayPaymentDisputeService] Error contesting dispute: {e}"
            )
            return {
                "success": False,
                "message": str(e),
                "dispute": dispute,
            }

    def add_evidence(
        self,
        payment_dispute_id: str,
        evidence_type: str,
        files: Optional[List[Dict[str, str]]] = None,
        line_items: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Add evidence to a payment dispute.

        IMPORTANT: Evidence must be added BEFORE contesting.
        Once the dispute is contested, no more evidence can be added.

        Evidence Types:
        - PROOF_OF_DELIVERY: Delivery confirmation
        - PROOF_OF_AUTHENTICITY: Item authenticity proof
        - PROOF_OF_ITEM_AS_DESCRIBED: Item matches description
        - PROOF_OF_PICKUP: Buyer picked up item
        - TRACKING_INFORMATION: Shipping tracking info

        Args:
            payment_dispute_id: eBay payment dispute ID
            evidence_type: Type of evidence being submitted
            files: List of file dicts with fileId and content type
            line_items: Line items the evidence applies to

        Returns:
            Dict with result:
            {
                "success": bool,
                "message": str | None,
                "evidence_id": str | None
            }
        """
        logger.info(
            f"[EbayPaymentDisputeService] Adding {evidence_type} evidence "
            f"to dispute {payment_dispute_id}"
        )

        # Verify dispute exists and can receive evidence
        dispute = self.repository.get_by_payment_dispute_id(payment_dispute_id)

        if not dispute:
            dispute = self.sync_dispute(payment_dispute_id)

        if not dispute:
            return {
                "success": False,
                "message": f"Dispute {payment_dispute_id} not found",
                "evidence_id": None,
            }

        if dispute.dispute_state == "CLOSED":
            return {
                "success": False,
                "message": "Cannot add evidence to closed dispute",
                "evidence_id": None,
            }

        if dispute.seller_response == "CONTEST":
            return {
                "success": False,
                "message": "Cannot add evidence after contesting",
                "evidence_id": None,
            }

        try:
            result = self.client.add_evidence(
                payment_dispute_id=payment_dispute_id,
                evidence_type=evidence_type,
                files=files,
                line_items=line_items,
            )

            evidence_id = result.get("evidenceId")

            # Refresh dispute to get updated evidence list
            self.sync_dispute(payment_dispute_id)

            logger.info(
                f"[EbayPaymentDisputeService] Evidence added: "
                f"type={evidence_type}, id={evidence_id}"
            )

            return {
                "success": True,
                "message": None,
                "evidence_id": evidence_id,
            }

        except EbayError as e:
            logger.error(
                f"[EbayPaymentDisputeService] Error adding evidence: {e}"
            )
            return {
                "success": False,
                "message": str(e),
                "evidence_id": None,
            }

    # =========================================================================
    # QUERY METHODS
    # =========================================================================

    def get_dispute(self, payment_dispute_id: str) -> Optional[EbayPaymentDispute]:
        """Get a dispute by eBay payment dispute ID."""
        return self.repository.get_by_payment_dispute_id(payment_dispute_id)

    def get_dispute_by_id(self, dispute_id: int) -> Optional[EbayPaymentDispute]:
        """Get a dispute by internal database ID."""
        return self.repository.get_by_id(dispute_id)

    def get_disputes_for_order(self, order_id: str) -> List[EbayPaymentDispute]:
        """Get all disputes for an order."""
        return self.repository.get_by_order_id(order_id)

    def list_disputes(
        self,
        page: int = 1,
        page_size: int = 50,
        state: Optional[str] = None,
        reason: Optional[str] = None,
        order_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        List disputes with pagination and filters.

        Args:
            page: Page number (1-indexed)
            page_size: Items per page
            state: Filter by state (OPEN, ACTION_NEEDED, CLOSED)
            reason: Filter by reason
            order_id: Filter by order ID

        Returns:
            Dict with:
            {
                "items": List[EbayPaymentDispute],
                "total": int,
                "page": int,
                "page_size": int,
                "total_pages": int
            }
        """
        return self.repository.get_all(
            page=page,
            page_size=page_size,
            state=state,
            reason=reason,
            order_id=order_id,
        )

    def get_open_disputes(self, limit: int = 100) -> List[EbayPaymentDispute]:
        """Get all open disputes (OPEN or ACTION_NEEDED)."""
        return self.repository.get_open_disputes(limit)

    def get_action_needed_disputes(self, limit: int = 100) -> List[EbayPaymentDispute]:
        """Get disputes requiring seller action."""
        return self.repository.get_action_needed_disputes(limit)

    def get_past_deadline_disputes(self) -> List[EbayPaymentDispute]:
        """Get disputes past their response deadline."""
        return self.repository.get_past_deadline_disputes()

    def get_closed_disputes(self, limit: int = 100) -> List[EbayPaymentDispute]:
        """Get closed disputes."""
        return self.repository.get_closed_disputes(limit)

    # =========================================================================
    # STATISTICS
    # =========================================================================

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get payment dispute statistics.

        Returns:
            Dict with:
            {
                "open": int,
                "action_needed": int,
                "closed": int,
                "past_deadline": int,
                "total_amount": float,
                "by_reason": Dict[str, int]
            }
        """
        return self.repository.get_statistics()

    # =========================================================================
    # ALERTS / URGENT DISPUTES
    # =========================================================================

    def get_urgent_disputes(self, days_threshold: int = 3) -> List[EbayPaymentDispute]:
        """
        Get disputes that need urgent attention.

        Returns disputes that:
        - Are ACTION_NEEDED and deadline is within N days
        - Are past deadline but not closed

        Args:
            days_threshold: Number of days until deadline to consider urgent

        Returns:
            List of urgent disputes ordered by deadline
        """
        urgent = []

        # Get action needed disputes
        action_needed = self.repository.get_action_needed_disputes(limit=100)

        threshold_date = datetime.now(timezone.utc) + timedelta(days=days_threshold)

        for dispute in action_needed:
            if dispute.respond_by_date:
                if dispute.respond_by_date <= threshold_date:
                    urgent.append(dispute)
            else:
                # No deadline but needs action - include it
                urgent.append(dispute)

        # Sort by deadline (soonest first, None last)
        urgent.sort(
            key=lambda d: d.respond_by_date if d.respond_by_date else datetime.max
        )

        return urgent
