"""
eBay Inquiry Client.

Client for Post-Order API v2 inquiry endpoints (Item Not Received).
Handles searching, retrieving, and managing INR inquiries.

Endpoints:
- GET /inquiry/search - Search inquiries with filters
- GET /inquiry/{inquiryId} - Get inquiry details
- POST /inquiry/{inquiryId}/provide_shipment_info - Provide tracking
- POST /inquiry/{inquiryId}/provide_refund - Issue refund for inquiry
- POST /inquiry/{inquiryId}/send_message - Send message
- POST /inquiry/{inquiryId}/escalate - Escalate to case

Documentation:
https://developer.ebay.com/devzone/post-order/index.html

Author: Claude
Date: 2026-01-14
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from services.ebay.ebay_post_order_client import EbayPostOrderClient
from shared.logging_setup import get_logger

logger = get_logger(__name__)


class EbayInquiryClient(EbayPostOrderClient):
    """
    Client for eBay Post-Order API inquiry management (INR - Item Not Received).

    Extends EbayPostOrderClient with inquiry-specific methods.

    Inquiry States:
        - OPEN: Inquiry is active and needs resolution
        - CLOSED: Inquiry has been resolved

    Inquiry Statuses:
        - INR_WAITING_FOR_SELLER: Waiting for seller response
        - INR_WAITING_FOR_BUYER: Waiting for buyer confirmation
        - INR_CLOSED_SELLER_PROVIDED_INFO: Closed - tracking provided
        - INR_CLOSED_REFUND: Closed - refund issued
        - INR_CLOSED_NO_RESPONSE: Closed - no response from seller
        - INR_ESCALATED: Escalated to eBay case

    Usage:
        >>> client = EbayInquiryClient(db_session, user_id=1)
        >>>
        >>> # Search inquiries
        >>> inquiries = client.search_inquiries(inquiry_state="OPEN")
        >>>
        >>> # Get inquiry details
        >>> inquiry_data = client.get_inquiry("5000012345")
        >>>
        >>> # Provide shipment info
        >>> client.provide_shipment_info(
        ...     "5000012345",
        ...     tracking_number="1Z999AA10123456784",
        ...     carrier="UPS"
        ... )
    """

    def __init__(
        self,
        db: Session,
        user_id: int,
        marketplace_id: Optional[str] = None,
        sandbox: bool = False,
    ):
        """Initialize inquiry client."""
        super().__init__(db, user_id, marketplace_id, sandbox)

    def search_inquiries(
        self,
        order_id: Optional[str] = None,
        inquiry_state: Optional[str] = None,
        inquiry_status: Optional[str] = None,
        creation_date_range_from: Optional[datetime] = None,
        creation_date_range_to: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Search for INR inquiries with filters.

        Args:
            order_id: Filter by legacy order ID
            inquiry_state: Filter by state (OPEN, CLOSED)
            inquiry_status: Filter by specific status
            creation_date_range_from: Start date for creation filter
            creation_date_range_to: End date for creation filter
            limit: Max results per page (default 50, max 200)
            offset: Pagination offset

        Returns:
            Dict with structure:
            {
                "inquiries": [
                    {
                        "inquiryId": "5000012345",
                        "inquiryState": "OPEN",
                        "inquiryStatus": "INR_WAITING_FOR_SELLER",
                        "legacyOrderId": "123456789012",
                        ...
                    }
                ],
                "total": 100,
                "limit": 50,
                "offset": 0
            }

        Examples:
            >>> # Get all open inquiries
            >>> result = client.search_inquiries(inquiry_state="OPEN")
            >>> inquiries = result.get("inquiries", [])
            >>>
            >>> # Get inquiries for a specific order
            >>> result = client.search_inquiries(order_id="123456789012")
        """
        params = {
            "limit": min(limit, 200),
            "offset": offset,
        }

        if order_id:
            params["legacy_order_id"] = order_id

        if inquiry_state:
            params["inquiry_state"] = inquiry_state

        if inquiry_status:
            params["inquiry_status"] = inquiry_status

        if creation_date_range_from:
            params["creation_date_range_from"] = creation_date_range_from.strftime(
                "%Y-%m-%dT%H:%M:%S.000Z"
            )

        if creation_date_range_to:
            params["creation_date_range_to"] = creation_date_range_to.strftime(
                "%Y-%m-%dT%H:%M:%S.000Z"
            )

        result = self.api_call_post_order("GET", "/inquiry/search", params=params)
        return result or {"inquiries": [], "total": 0}

    def get_inquiry(self, inquiry_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific inquiry.

        Args:
            inquiry_id: eBay inquiry ID (e.g., "5000012345")

        Returns:
            Dict with full inquiry details:
            {
                "inquiryId": "5000012345",
                "inquiryState": "OPEN",
                "inquiryStatus": "INR_WAITING_FOR_SELLER",
                "inquiryType": "INR",
                "legacyOrderId": "123456789012",
                "buyer": {...},
                "seller": {...},
                "creationDate": "2026-01-13T10:00:00.000Z",
                "respondByDate": "2026-01-16T10:00:00.000Z",
                ...
            }

        Raises:
            EbayAPIError: If inquiry not found or API error

        Examples:
            >>> inquiry_data = client.get_inquiry("5000012345")
            >>> print(f"Status: {inquiry_data['inquiryStatus']}")
        """
        result = self.api_call_post_order("GET", f"/inquiry/{inquiry_id}")
        return result or {}

    def provide_shipment_info(
        self,
        inquiry_id: str,
        tracking_number: str,
        carrier: str,
        shipped_date: Optional[datetime] = None,
        comments: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Provide shipment information to resolve an INR inquiry.

        This is the primary response for "Item Not Received" inquiries
        when the seller has already shipped the item.

        Args:
            inquiry_id: eBay inquiry ID
            tracking_number: Shipment tracking number
            carrier: Shipping carrier (e.g., "UPS", "FEDEX", "DHL")
            shipped_date: Date item was shipped (defaults to now)
            comments: Optional seller comments

        Returns:
            Dict with response result

        Raises:
            EbayAPIError: If providing shipment info fails

        Examples:
            >>> client.provide_shipment_info(
            ...     "5000012345",
            ...     tracking_number="1Z999AA10123456784",
            ...     carrier="UPS",
            ...     comments="Item was shipped on Jan 10"
            ... )
        """
        from datetime import timezone

        payload: Dict[str, Any] = {
            "trackingNumber": tracking_number,
            "shippingCarrierCode": carrier,
        }

        if shipped_date:
            payload["shippedDate"] = shipped_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        else:
            payload["shippedDate"] = datetime.now(timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%S.000Z"
            )

        if comments:
            payload["comments"] = comments

        result = self.api_call_post_order(
            "POST", f"/inquiry/{inquiry_id}/provide_shipment_info", json_data=payload
        )
        return result or {}

    def provide_refund(
        self,
        inquiry_id: str,
        refund_amount: Optional[float] = None,
        currency: Optional[str] = None,
        comments: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Issue a refund to resolve an INR inquiry.

        Use this when the item was not shipped or cannot be delivered.

        Args:
            inquiry_id: eBay inquiry ID
            refund_amount: Optional partial refund amount (if None, full refund)
            currency: Currency code (e.g., "EUR", "USD")
            comments: Optional refund comments

        Returns:
            Dict with refund result

        Raises:
            EbayAPIError: If refund fails

        Examples:
            >>> # Full refund
            >>> client.provide_refund("5000012345")
            >>>
            >>> # Partial refund
            >>> client.provide_refund(
            ...     "5000012345",
            ...     refund_amount=25.00,
            ...     currency="EUR",
            ...     comments="Refund for missing item"
            ... )
        """
        payload: Dict[str, Any] = {}

        if refund_amount is not None:
            payload["refundAmount"] = {
                "value": str(refund_amount),
                "currency": currency or "EUR",
            }

        if comments:
            payload["comments"] = comments

        result = self.api_call_post_order(
            "POST", f"/inquiry/{inquiry_id}/provide_refund", json_data=payload or None
        )
        return result or {}

    def send_message(
        self,
        inquiry_id: str,
        message: str,
    ) -> Dict[str, Any]:
        """
        Send a message to the buyer about an inquiry.

        Args:
            inquiry_id: eBay inquiry ID
            message: Message text

        Returns:
            Dict with result

        Examples:
            >>> client.send_message(
            ...     "5000012345",
            ...     message="Your package is on its way. Please allow 3-5 days for delivery."
            ... )
        """
        payload = {
            "message": message,
        }

        result = self.api_call_post_order(
            "POST", f"/inquiry/{inquiry_id}/send_message", json_data=payload
        )
        return result or {}

    def escalate(
        self,
        inquiry_id: str,
        comments: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Escalate an inquiry to an eBay case.

        Use with caution - escalation may impact seller metrics.

        Args:
            inquiry_id: eBay inquiry ID
            comments: Optional escalation comments

        Returns:
            Dict with escalation result

        Examples:
            >>> client.escalate(
            ...     "5000012345",
            ...     comments="Buyer is not responding"
            ... )
        """
        payload: Dict[str, Any] = {}

        if comments:
            payload["comments"] = comments

        result = self.api_call_post_order(
            "POST", f"/inquiry/{inquiry_id}/escalate", json_data=payload or None
        )
        return result or {}

    def get_all_inquiries(
        self,
        inquiry_state: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all inquiries with optional state filter (handles pagination).

        Args:
            inquiry_state: Filter by state (OPEN, CLOSED)

        Returns:
            List of all inquiry records

        Examples:
            >>> # Get all open inquiries
            >>> open_inquiries = client.get_all_inquiries(inquiry_state="OPEN")
            >>> print(f"Found {len(open_inquiries)} open inquiries")
        """
        all_inquiries: List[Dict[str, Any]] = []
        offset = 0
        limit = 200  # Max per request

        while True:
            result = self.search_inquiries(
                inquiry_state=inquiry_state,
                limit=limit,
                offset=offset,
            )

            members = result.get("inquiries", [])
            if not members:
                break

            all_inquiries.extend(members)

            # Check if more results
            total = result.get("total", 0)
            if offset + len(members) >= total:
                break

            offset += limit

        return all_inquiries

    def get_inquiries_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        inquiry_state: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get inquiries within a date range (handles pagination).

        Args:
            start_date: Start date (UTC)
            end_date: End date (UTC)
            inquiry_state: Optional state filter

        Returns:
            List of inquiries within date range

        Examples:
            >>> from datetime import datetime, timedelta, timezone
            >>> now = datetime.now(timezone.utc)
            >>> week_ago = now - timedelta(days=7)
            >>> recent = client.get_inquiries_by_date_range(week_ago, now)
        """
        all_inquiries: List[Dict[str, Any]] = []
        offset = 0
        limit = 200

        while True:
            result = self.search_inquiries(
                inquiry_state=inquiry_state,
                creation_date_range_from=start_date,
                creation_date_range_to=end_date,
                limit=limit,
                offset=offset,
            )

            members = result.get("inquiries", [])
            if not members:
                break

            all_inquiries.extend(members)

            total = result.get("total", 0)
            if offset + len(members) >= total:
                break

            offset += limit

        return all_inquiries

    def get_pending_inquiries(self) -> List[Dict[str, Any]]:
        """
        Get inquiries that are waiting for seller response.

        Returns:
            List of inquiries needing seller action

        Examples:
            >>> pending = client.get_pending_inquiries()
            >>> for inquiry in pending:
            ...     print(f"Pending: {inquiry['inquiryId']}")
        """
        all_inquiries = self.get_all_inquiries(inquiry_state="OPEN")

        # Filter to only those needing seller action
        pending_statuses = ["INR_WAITING_FOR_SELLER"]

        return [
            inquiry for inquiry in all_inquiries
            if inquiry.get("inquiryStatus") in pending_statuses
        ]
