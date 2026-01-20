"""
eBay Inquiry Service

Service for eBay INR inquiry business operations.
Responsibility: Business logic for inquiry management (read, actions, sync, statistics).

Architecture:
- Read operations via EbayInquiryRepository
- Action operations: eBay API call + local DB update
- Sync: Fetch from eBay API → upsert to local DB
- Statistics aggregation

Created: 2026-01-14
Author: Claude
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from dateutil import parser as date_parser
from sqlalchemy.orm import Session

from models.user.ebay_inquiry import EbayInquiry
from repositories.ebay_inquiry_repository import EbayInquiryRepository
from services.ebay.ebay_inquiry_client import EbayInquiryClient
from shared.logging import get_logger

logger = get_logger(__name__)


class EbayInquiryService:
    """
    Service for eBay INR inquiry business operations.

    Provides:
    - Read operations (get, list, filter)
    - Action operations (provide_shipment_info, provide_refund, send_message, escalate)
    - Sync operations (fetch from eBay → local DB)
    - Statistics aggregation

    Usage:
        >>> service = EbayInquiryService(db_session, user_id=1)
        >>> inquiries, total = service.list_inquiries(state="OPEN")
        >>> service.provide_shipment_info(inquiry_id=123, tracking="1Z...", carrier="UPS")
    """

    def __init__(self, db: Session, user_id: int):
        """
        Initialize inquiry service.

        Args:
            db: SQLAlchemy Session (with search_path already set)
            user_id: User ID for eBay authentication
        """
        self.db = db
        self.user_id = user_id
        self.inquiry_client = EbayInquiryClient(db, user_id)

        logger.info(f"[EbayInquiryService] Initialized for user_id={user_id}")

    # =========================================================================
    # Read Operations
    # =========================================================================

    def get_inquiry(self, inquiry_pk: int) -> Optional[EbayInquiry]:
        """
        Get inquiry by internal ID.

        Args:
            inquiry_pk: Internal inquiry ID

        Returns:
            EbayInquiry if found, None otherwise
        """
        return EbayInquiryRepository.get_by_id(self.db, inquiry_pk)

    def get_inquiry_by_ebay_id(self, ebay_inquiry_id: str) -> Optional[EbayInquiry]:
        """
        Get inquiry by eBay inquiry ID.

        Args:
            ebay_inquiry_id: eBay inquiry ID (e.g., "5000012345")

        Returns:
            EbayInquiry if found, None otherwise
        """
        return EbayInquiryRepository.get_by_ebay_inquiry_id(self.db, ebay_inquiry_id)

    def list_inquiries(
        self,
        skip: int = 0,
        limit: int = 50,
        state: Optional[str] = None,
        status: Optional[str] = None,
        order_id: Optional[str] = None,
    ) -> Tuple[List[EbayInquiry], int]:
        """
        List inquiries with pagination and filters.

        Args:
            skip: Number of results to skip
            limit: Max number of results
            state: Filter by state (OPEN, CLOSED)
            status: Filter by status
            order_id: Filter by order ID

        Returns:
            Tuple[List[EbayInquiry], int]: (list of inquiries, total count)
        """
        return EbayInquiryRepository.list_inquiries(
            self.db,
            skip=skip,
            limit=limit,
            state=state,
            status=status,
            order_id=order_id,
        )

    def get_inquiries_needing_action(self, limit: int = 100) -> List[EbayInquiry]:
        """
        Get inquiries requiring seller action.

        Returns:
            List of inquiries needing action (sorted by deadline)
        """
        return EbayInquiryRepository.list_needs_action(self.db, limit)

    def get_inquiries_past_deadline(self, limit: int = 100) -> List[EbayInquiry]:
        """
        Get inquiries past their response deadline (urgent).

        Returns:
            List of inquiries past deadline
        """
        return EbayInquiryRepository.list_past_deadline(self.db, limit)

    def get_inquiries_for_order(self, order_id: str) -> List[EbayInquiry]:
        """
        Get all inquiries for a specific order.

        Args:
            order_id: eBay order ID

        Returns:
            List of inquiries for the order
        """
        return EbayInquiryRepository.get_by_order_id(self.db, order_id)

    def get_escalated_inquiries(self, limit: int = 100) -> List[EbayInquiry]:
        """
        Get inquiries that have been escalated to cases.

        Returns:
            List of escalated inquiries
        """
        return EbayInquiryRepository.list_escalated(self.db, limit)

    # =========================================================================
    # Action Operations
    # =========================================================================

    def provide_shipment_info(
        self,
        inquiry_pk: int,
        tracking_number: str,
        carrier: str,
        shipped_date: Optional[datetime] = None,
        comments: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Provide shipment information to resolve an INR inquiry.

        This is the primary response for "Item Not Received" inquiries
        when the item has been shipped.

        Args:
            inquiry_pk: Internal inquiry ID
            tracking_number: Shipment tracking number
            carrier: Shipping carrier (e.g., "UPS", "FEDEX")
            shipped_date: Optional ship date (defaults to now)
            comments: Optional seller comments

        Returns:
            Result dict: {"success": True, "inquiry_id": str, "new_status": str}

        Raises:
            ValueError: If inquiry not found
            RuntimeError: If API call fails
        """
        logger.info(
            f"[EbayInquiryService] provide_shipment_info: user_id={self.user_id}, "
            f"inquiry_pk={inquiry_pk}, tracking={tracking_number}"
        )

        # Get inquiry
        inquiry_obj = self._get_inquiry_or_raise(inquiry_pk)

        try:
            # Call eBay API
            self.inquiry_client.provide_shipment_info(
                inquiry_id=inquiry_obj.inquiry_id,
                tracking_number=tracking_number,
                carrier=carrier,
                shipped_date=shipped_date,
                comments=comments,
            )

            # Update local DB
            inquiry_obj.inquiry_status = "INR_CLOSED_SELLER_PROVIDED_INFO"
            inquiry_obj.shipment_tracking_number = tracking_number
            inquiry_obj.shipment_carrier = carrier
            inquiry_obj.seller_response = "SHIPMENT_INFO"
            inquiry_obj.updated_at = datetime.now(timezone.utc)

            EbayInquiryRepository.update(self.db, inquiry_obj)
            self.db.commit()

            logger.info(
                f"[EbayInquiryService] Shipment info provided for inquiry {inquiry_obj.inquiry_id}"
            )

            return {
                "success": True,
                "inquiry_id": inquiry_obj.inquiry_id,
                "new_status": "INR_CLOSED_SELLER_PROVIDED_INFO",
            }

        except Exception as e:
            self.db.rollback()
            logger.error(
                f"[EbayInquiryService] Failed to provide shipment info for {inquiry_obj.inquiry_id}: {e}",
                exc_info=True,
            )
            raise RuntimeError(f"Failed to provide shipment info: {str(e)}") from e

    def provide_refund(
        self,
        inquiry_pk: int,
        refund_amount: Optional[float] = None,
        currency: Optional[str] = None,
        comments: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Issue refund to resolve an INR inquiry.

        Use this when the item was not shipped or cannot be delivered.

        Args:
            inquiry_pk: Internal inquiry ID
            refund_amount: Optional partial refund amount (full if None)
            currency: Currency code (e.g., "EUR")
            comments: Optional refund comments

        Returns:
            Result dict: {"success": True, "inquiry_id": str, "new_status": str}

        Raises:
            ValueError: If inquiry not found
            RuntimeError: If API call fails
        """
        logger.info(
            f"[EbayInquiryService] provide_refund: user_id={self.user_id}, "
            f"inquiry_pk={inquiry_pk}, amount={refund_amount}"
        )

        # Get inquiry
        inquiry_obj = self._get_inquiry_or_raise(inquiry_pk)

        try:
            # Call eBay API
            self.inquiry_client.provide_refund(
                inquiry_id=inquiry_obj.inquiry_id,
                refund_amount=refund_amount,
                currency=currency,
                comments=comments,
            )

            # Update local DB
            inquiry_obj.inquiry_status = "INR_CLOSED_REFUND"
            inquiry_obj.seller_response = "REFUND"
            inquiry_obj.closed_date = datetime.now(timezone.utc)
            inquiry_obj.updated_at = datetime.now(timezone.utc)

            EbayInquiryRepository.update(self.db, inquiry_obj)
            self.db.commit()

            logger.info(
                f"[EbayInquiryService] Refund provided for inquiry {inquiry_obj.inquiry_id}"
            )

            return {
                "success": True,
                "inquiry_id": inquiry_obj.inquiry_id,
                "new_status": "INR_CLOSED_REFUND",
            }

        except Exception as e:
            self.db.rollback()
            logger.error(
                f"[EbayInquiryService] Failed to provide refund for {inquiry_obj.inquiry_id}: {e}",
                exc_info=True,
            )
            raise RuntimeError(f"Failed to provide refund: {str(e)}") from e

    def send_message(
        self,
        inquiry_pk: int,
        message: str,
    ) -> Dict[str, Any]:
        """
        Send message to buyer about inquiry.

        Args:
            inquiry_pk: Internal inquiry ID
            message: Message text

        Returns:
            Result dict: {"success": True, "inquiry_id": str}

        Raises:
            ValueError: If inquiry not found or message empty
            RuntimeError: If API call fails
        """
        if not message:
            raise ValueError("Message cannot be empty")

        logger.info(
            f"[EbayInquiryService] send_message: user_id={self.user_id}, "
            f"inquiry_pk={inquiry_pk}"
        )

        # Get inquiry
        inquiry_obj = self._get_inquiry_or_raise(inquiry_pk)

        try:
            # Call eBay API
            self.inquiry_client.send_message(
                inquiry_id=inquiry_obj.inquiry_id,
                message=message,
            )

            # Update local DB
            inquiry_obj.buyer_comments = f"{inquiry_obj.buyer_comments or ''}\n[Seller]: {message}"
            inquiry_obj.updated_at = datetime.now(timezone.utc)

            EbayInquiryRepository.update(self.db, inquiry_obj)
            self.db.commit()

            logger.info(
                f"[EbayInquiryService] Message sent for inquiry {inquiry_obj.inquiry_id}"
            )

            return {
                "success": True,
                "inquiry_id": inquiry_obj.inquiry_id,
            }

        except Exception as e:
            self.db.rollback()
            logger.error(
                f"[EbayInquiryService] Failed to send message for {inquiry_obj.inquiry_id}: {e}",
                exc_info=True,
            )
            raise RuntimeError(f"Failed to send message: {str(e)}") from e

    def escalate_inquiry(
        self,
        inquiry_pk: int,
        comments: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Escalate inquiry to an eBay case.

        **Warning**: Escalation may impact seller metrics.

        Args:
            inquiry_pk: Internal inquiry ID
            comments: Optional escalation comments

        Returns:
            Result dict: {"success": True, "inquiry_id": str, "new_status": str}

        Raises:
            ValueError: If inquiry not found
            RuntimeError: If API call fails
        """
        logger.info(
            f"[EbayInquiryService] escalate_inquiry: user_id={self.user_id}, "
            f"inquiry_pk={inquiry_pk}"
        )

        # Get inquiry
        inquiry_obj = self._get_inquiry_or_raise(inquiry_pk)

        try:
            # Call eBay API
            self.inquiry_client.escalate(
                inquiry_id=inquiry_obj.inquiry_id,
                comments=comments,
            )

            # Update local DB
            inquiry_obj.inquiry_status = "INR_ESCALATED"
            inquiry_obj.escalation_date = datetime.now(timezone.utc)
            inquiry_obj.updated_at = datetime.now(timezone.utc)

            EbayInquiryRepository.update(self.db, inquiry_obj)
            self.db.commit()

            logger.info(
                f"[EbayInquiryService] Inquiry {inquiry_obj.inquiry_id} escalated"
            )

            return {
                "success": True,
                "inquiry_id": inquiry_obj.inquiry_id,
                "new_status": "INR_ESCALATED",
            }

        except Exception as e:
            self.db.rollback()
            logger.error(
                f"[EbayInquiryService] Failed to escalate {inquiry_obj.inquiry_id}: {e}",
                exc_info=True,
            )
            raise RuntimeError(f"Failed to escalate inquiry: {str(e)}") from e

    # =========================================================================
    # Sync Operations
    # =========================================================================

    def sync_inquiries(self, state: Optional[str] = None) -> Dict[str, Any]:
        """
        Sync inquiries from eBay API to local database.

        Fetches all inquiries (optionally filtered by state) and upserts
        them into the local database.

        Args:
            state: Optional filter by state (OPEN, CLOSED)

        Returns:
            Sync result: {
                "success": True,
                "created": int,
                "updated": int,
                "total_fetched": int,
                "errors": List[str]
            }
        """
        logger.info(
            f"[EbayInquiryService] sync_inquiries: user_id={self.user_id}, state={state}"
        )

        created = 0
        updated = 0
        errors: List[str] = []

        try:
            # Fetch inquiries from eBay
            inquiries = self.inquiry_client.get_all_inquiries(inquiry_state=state)

            logger.info(
                f"[EbayInquiryService] Fetched {len(inquiries)} inquiries from eBay API"
            )

            for inquiry_data in inquiries:
                try:
                    inquiry_id = inquiry_data.get("inquiryId")
                    if not inquiry_id:
                        logger.warning(
                            f"[EbayInquiryService] Skipping inquiry without ID: {inquiry_data}"
                        )
                        continue

                    # Check if exists
                    existing = EbayInquiryRepository.get_by_ebay_inquiry_id(
                        self.db, inquiry_id
                    )

                    if existing:
                        # Update
                        self._update_inquiry_from_api(existing, inquiry_data)
                        EbayInquiryRepository.update(self.db, existing)
                        updated += 1
                    else:
                        # Create
                        new_inquiry = self._create_inquiry_from_api(inquiry_data)
                        EbayInquiryRepository.create(self.db, new_inquiry)
                        created += 1

                except Exception as e:
                    error_msg = f"Error processing inquiry {inquiry_data.get('inquiryId', 'unknown')}: {str(e)}"
                    logger.error(f"[EbayInquiryService] {error_msg}", exc_info=True)
                    errors.append(error_msg)

            # Commit all changes
            self.db.commit()

            logger.info(
                f"[EbayInquiryService] Sync complete: created={created}, updated={updated}"
            )

            return {
                "success": True,
                "created": created,
                "updated": updated,
                "total_fetched": len(inquiries),
                "errors": errors,
            }

        except Exception as e:
            self.db.rollback()
            logger.error(
                f"[EbayInquiryService] Sync failed: {e}",
                exc_info=True,
            )
            return {
                "success": False,
                "created": created,
                "updated": updated,
                "total_fetched": 0,
                "errors": [str(e)],
            }

    def _create_inquiry_from_api(self, data: Dict[str, Any]) -> EbayInquiry:
        """
        Create EbayInquiry instance from eBay API response.

        Args:
            data: eBay inquiry API response

        Returns:
            EbayInquiry instance (not yet persisted)
        """
        inquiry = EbayInquiry()
        self._populate_inquiry_from_api(inquiry, data)
        return inquiry

    def _update_inquiry_from_api(
        self, inquiry: EbayInquiry, data: Dict[str, Any]
    ) -> None:
        """
        Update existing EbayInquiry from eBay API response.

        Args:
            inquiry: Existing EbayInquiry instance
            data: eBay inquiry API response
        """
        self._populate_inquiry_from_api(inquiry, data)
        inquiry.updated_at = datetime.now(timezone.utc)

    def _populate_inquiry_from_api(
        self, inquiry: EbayInquiry, data: Dict[str, Any]
    ) -> None:
        """
        Populate EbayInquiry fields from eBay API response.

        Args:
            inquiry: EbayInquiry instance to populate
            data: eBay inquiry API response
        """
        # Identifiers
        inquiry.inquiry_id = data.get("inquiryId", "")
        inquiry.order_id = data.get("legacyOrderId")

        # Status
        inquiry.inquiry_state = data.get("inquiryState")
        inquiry.inquiry_status = data.get("inquiryStatus")
        inquiry.inquiry_type = data.get("inquiryType", "INR")

        # Claim amount
        claim_amount = data.get("claimAmount")
        if claim_amount:
            inquiry.claim_amount = float(claim_amount.get("value", 0))
            inquiry.claim_currency = claim_amount.get("currency")

        # Buyer info
        buyer = data.get("buyer", {})
        inquiry.buyer_username = buyer.get("username")

        # Buyer comments from history
        history = data.get("inquiryHistoryDetails", {}).get("history", [])
        if history:
            buyer_comments = []
            for entry in history:
                if entry.get("actor") == "BUYER" and entry.get("description"):
                    buyer_comments.append(entry.get("description"))
            if buyer_comments:
                inquiry.buyer_comments = "\n".join(buyer_comments)

        # Seller response
        inquiry.seller_response = data.get("sellerMakeItRightByDate", {}).get(
            "responseType"
        )

        # Item info
        item = data.get("item", {})
        inquiry.item_id = item.get("itemId")
        inquiry.item_title = item.get("title")

        # Shipment info (if provided)
        shipment = data.get("shipmentTracking", {})
        if shipment:
            inquiry.shipment_tracking_number = shipment.get("trackingNumber")
            inquiry.shipment_carrier = shipment.get("shippingCarrier")

        # Dates
        if data.get("creationDate"):
            inquiry.creation_date = self._parse_date(data.get("creationDate"))
        if data.get("respondByDate"):
            inquiry.respond_by_date = self._parse_date(data.get("respondByDate"))
        if data.get("closedDate"):
            inquiry.closed_date = self._parse_date(data.get("closedDate"))
        if data.get("escalationDate"):
            inquiry.escalation_date = self._parse_date(data.get("escalationDate"))

        # Raw data for debugging
        inquiry.raw_data = data

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """
        Parse date string from eBay API.

        Args:
            date_str: Date string (ISO 8601 format)

        Returns:
            datetime object or None if parsing fails
        """
        if not date_str:
            return None
        try:
            return date_parser.parse(date_str)
        except Exception:
            return None

    # =========================================================================
    # Statistics
    # =========================================================================

    def get_inquiry_statistics(self) -> Dict[str, Any]:
        """
        Get inquiry statistics.

        Returns:
            Statistics dict:
            {
                "open": int,
                "closed": int,
                "needs_action": int,
                "past_deadline": int,
            }
        """
        stats = {
            "open": EbayInquiryRepository.count_by_state(self.db, "OPEN"),
            "closed": EbayInquiryRepository.count_by_state(self.db, "CLOSED"),
            "needs_action": EbayInquiryRepository.count_needs_action(self.db),
            "past_deadline": EbayInquiryRepository.count_past_deadline(self.db),
        }

        logger.debug(
            f"[EbayInquiryService] Statistics: open={stats['open']}, "
            f"closed={stats['closed']}, needs_action={stats['needs_action']}, "
            f"past_deadline={stats['past_deadline']}"
        )

        return stats

    # =========================================================================
    # Helpers
    # =========================================================================

    def _get_inquiry_or_raise(self, inquiry_pk: int) -> EbayInquiry:
        """
        Get inquiry by ID or raise ValueError.

        Args:
            inquiry_pk: Internal inquiry ID

        Returns:
            EbayInquiry instance

        Raises:
            ValueError: If inquiry not found
        """
        inquiry_obj = EbayInquiryRepository.get_by_id(self.db, inquiry_pk)

        if not inquiry_obj:
            raise ValueError(f"Inquiry {inquiry_pk} not found")

        return inquiry_obj
