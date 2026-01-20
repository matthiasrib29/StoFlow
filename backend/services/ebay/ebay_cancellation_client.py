"""
eBay Cancellation Client.

Client for Post-Order API v2 cancellation endpoints.
Handles searching, retrieving, and managing order cancellations.

Endpoints:
- GET /cancellation/search - Search cancellations with filters
- GET /cancellation/{cancelId} - Get cancellation details
- POST /cancellation/ - Create seller-initiated cancellation
- POST /cancellation/check_eligibility - Check if order can be cancelled
- POST /cancellation/{cancelId}/approve - Approve buyer's cancellation
- POST /cancellation/{cancelId}/reject - Reject cancellation

Documentation:
https://developer.ebay.com/devzone/post-order/index.html

Author: Claude
Date: 2026-01-14
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from services.ebay.ebay_post_order_client import EbayPostOrderClient
from shared.logging import get_logger

logger = get_logger(__name__)


class EbayCancellationClient(EbayPostOrderClient):
    """
    Client for eBay Post-Order API cancellation management.

    Extends EbayPostOrderClient with cancellation-specific methods.

    Cancel States:
        - CLOSED: Cancellation completed

    Cancel Statuses:
        - CANCEL_REQUESTED: Buyer requested cancellation
        - CANCEL_PENDING: Awaiting seller response
        - CANCEL_CLOSED_WITH_REFUND: Cancelled and refunded
        - CANCEL_CLOSED_UNKNOWN_REFUND: Closed with unknown refund status
        - CANCEL_CLOSED_FOR_COMMITMENT: Cancelled due to commitment issues
        - CANCEL_REJECTED: Seller rejected cancellation

    Cancel Reasons:
        - BUYER_ASKED_CANCEL: Buyer requested cancellation
        - ORDER_UNPAID: Order not paid by buyer
        - ADDRESS_ISSUES: Shipping address problems
        - OUT_OF_STOCK: Item no longer available
        - OTHER_SELLER_CANCEL_REASON: Other seller reason

    Usage:
        >>> client = EbayCancellationClient(db_session, user_id=1)
        >>>
        >>> # Search cancellations
        >>> cancels = client.search_cancellations(cancel_state="CLOSED")
        >>>
        >>> # Get cancellation details
        >>> cancel_data = client.get_cancellation("5000012345")
        >>>
        >>> # Approve a buyer's cancellation request
        >>> client.approve_cancellation("5000012345")
    """

    def __init__(
        self,
        db: Session,
        user_id: int,
        marketplace_id: Optional[str] = None,
        sandbox: bool = False,
    ):
        """Initialize cancellation client."""
        super().__init__(db, user_id, marketplace_id, sandbox)

    def search_cancellations(
        self,
        order_id: Optional[str] = None,
        cancel_id: Optional[str] = None,
        cancel_state: Optional[str] = None,
        creation_date_range_from: Optional[datetime] = None,
        creation_date_range_to: Optional[datetime] = None,
        role: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Search for cancellation requests with filters.

        Args:
            order_id: Filter by legacy order ID
            cancel_id: Filter by cancellation ID
            cancel_state: Filter by state (currently only CLOSED is supported)
            creation_date_range_from: Start date for creation filter
            creation_date_range_to: End date for creation filter
            role: Filter by role (SELLER or BUYER)
            limit: Max results per page (default 50, max 200)
            offset: Pagination offset

        Returns:
            Dict with structure:
            {
                "cancellations": [
                    {
                        "cancelId": "5000012345",
                        "cancelState": "CLOSED",
                        "cancelStatus": "CANCEL_CLOSED_WITH_REFUND",
                        "legacyOrderId": "123456789012",
                        ...
                    }
                ],
                "total": 100,
                "limit": 50,
                "offset": 0
            }

        Examples:
            >>> # Get all cancellations
            >>> result = client.search_cancellations()
            >>> cancels = result.get("cancellations", [])
            >>>
            >>> # Get cancellations for a specific order
            >>> result = client.search_cancellations(order_id="123456789012")
        """
        params = {
            "limit": min(limit, 200),
            "offset": offset,
        }

        if order_id:
            params["legacy_order_id"] = order_id

        if cancel_id:
            params["cancel_id"] = cancel_id

        if cancel_state:
            params["cancel_state"] = cancel_state

        if role:
            params["role"] = role

        if creation_date_range_from:
            params["creation_date_range_from"] = creation_date_range_from.strftime(
                "%Y-%m-%dT%H:%M:%S.000Z"
            )

        if creation_date_range_to:
            params["creation_date_range_to"] = creation_date_range_to.strftime(
                "%Y-%m-%dT%H:%M:%S.000Z"
            )

        result = self.api_call_post_order(
            "GET", "/cancellation/search", params=params
        )
        return result or {"cancellations": [], "total": 0}

    def get_cancellation(self, cancel_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific cancellation.

        Args:
            cancel_id: eBay cancellation ID (e.g., "5000012345")

        Returns:
            Dict with full cancellation details:
            {
                "cancelId": "5000012345",
                "cancelState": "CLOSED",
                "cancelStatus": "CANCEL_CLOSED_WITH_REFUND",
                "cancelReason": "BUYER_ASKED_CANCEL",
                "legacyOrderId": "123456789012",
                "orderLineItems": [...],
                "buyerResponse": {...},
                "sellerResponse": {...},
                "creationDate": "2026-01-13T10:00:00.000Z",
                ...
            }

        Raises:
            EbayAPIError: If cancellation not found or API error

        Examples:
            >>> cancel_data = client.get_cancellation("5000012345")
            >>> print(f"Status: {cancel_data['cancelStatus']}")
            >>> print(f"Reason: {cancel_data['cancelReason']}")
        """
        result = self.api_call_post_order("GET", f"/cancellation/{cancel_id}")
        return result or {}

    def check_eligibility(
        self,
        order_id: str,
    ) -> Dict[str, Any]:
        """
        Check if an order is eligible for cancellation.

        Args:
            order_id: Legacy eBay order ID

        Returns:
            Dict with eligibility result:
            {
                "eligible": true,
                "eligibilityStatus": "ELIGIBLE",
                "failureReason": null,
                "legacyOrderId": "123456789012",
                ...
            }

        Examples:
            >>> result = client.check_eligibility("123456789012")
            >>> if result.get("eligible"):
            ...     print("Order can be cancelled")
        """
        payload = {
            "legacyOrderId": order_id,
        }

        result = self.api_call_post_order(
            "POST", "/cancellation/check_eligibility", json_data=payload
        )
        return result or {}

    def create_cancellation(
        self,
        order_id: str,
        reason: str,
        comments: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a seller-initiated cancellation request.

        Args:
            order_id: Legacy eBay order ID
            reason: Cancellation reason code:
                - "OUT_OF_STOCK" - Item no longer available
                - "ADDRESS_ISSUES" - Shipping address problems
                - "BUYER_ASKED_CANCEL" - Buyer requested cancellation
                - "ORDER_UNPAID" - Order not paid
                - "OTHER_SELLER_CANCEL_REASON" - Other reason
            comments: Optional seller comments

        Returns:
            Dict with created cancellation:
            {
                "cancelId": "5000012345",
                "cancelStatus": "CANCEL_PENDING",
                ...
            }

        Raises:
            EbayAPIError: If cancellation creation fails

        Examples:
            >>> result = client.create_cancellation(
            ...     "123456789012",
            ...     reason="OUT_OF_STOCK",
            ...     comments="Item sold on another platform"
            ... )
            >>> cancel_id = result.get("cancelId")
        """
        payload: Dict[str, Any] = {
            "legacyOrderId": order_id,
            "cancelReason": reason,
        }

        if comments:
            payload["buyerResponseText"] = comments

        result = self.api_call_post_order(
            "POST", "/cancellation/", json_data=payload
        )
        return result or {}

    def approve_cancellation(
        self,
        cancel_id: str,
        comments: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Approve a buyer's cancellation request.

        Args:
            cancel_id: eBay cancellation ID
            comments: Optional seller comments

        Returns:
            Dict with approval result

        Examples:
            >>> client.approve_cancellation(
            ...     "5000012345",
            ...     comments="Approved at buyer's request"
            ... )
        """
        payload: Dict[str, Any] = {}

        if comments:
            payload["shipmentDate"] = None  # Not required for approval
            payload["sellerResponseText"] = comments

        result = self.api_call_post_order(
            "POST",
            f"/cancellation/{cancel_id}/approve",
            json_data=payload or None,
        )
        return result or {}

    def reject_cancellation(
        self,
        cancel_id: str,
        reason: str,
        tracking_number: Optional[str] = None,
        carrier: Optional[str] = None,
        shipped_date: Optional[datetime] = None,
        comments: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Reject a buyer's cancellation request.

        Args:
            cancel_id: eBay cancellation ID
            reason: Rejection reason code:
                - "ALREADY_SHIPPED" - Item already shipped (tracking required)
                - "OTHER_SELLER_REJECT_REASON" - Other reason
            tracking_number: Required if reason is "ALREADY_SHIPPED"
            carrier: Shipping carrier (required with tracking_number)
            shipped_date: Date item was shipped
            comments: Optional seller comments

        Returns:
            Dict with rejection result

        Raises:
            EbayAPIError: If rejection fails

        Examples:
            >>> # Reject because already shipped
            >>> client.reject_cancellation(
            ...     "5000012345",
            ...     reason="ALREADY_SHIPPED",
            ...     tracking_number="1Z999AA10123456784",
            ...     carrier="UPS",
            ...     shipped_date=datetime.now(timezone.utc)
            ... )
            >>>
            >>> # Reject for other reason
            >>> client.reject_cancellation(
            ...     "5000012345",
            ...     reason="OTHER_SELLER_REJECT_REASON",
            ...     comments="Cannot cancel, processing already started"
            ... )
        """
        payload: Dict[str, Any] = {
            "rejectReason": reason,
        }

        if tracking_number:
            payload["trackingNumber"] = tracking_number

        if carrier:
            payload["shipmentCarrier"] = carrier

        if shipped_date:
            payload["shipmentDate"] = shipped_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")

        if comments:
            payload["sellerResponseText"] = comments

        result = self.api_call_post_order(
            "POST", f"/cancellation/{cancel_id}/reject", json_data=payload
        )
        return result or {}

    def get_all_cancellations(
        self,
        cancel_state: Optional[str] = None,
        role: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all cancellations with optional filters (handles pagination).

        Args:
            cancel_state: Filter by state
            role: Filter by role (SELLER, BUYER)

        Returns:
            List of all cancellation records

        Examples:
            >>> # Get all cancellations where seller was involved
            >>> cancels = client.get_all_cancellations(role="SELLER")
            >>> print(f"Found {len(cancels)} cancellations")
        """
        all_cancellations: List[Dict[str, Any]] = []
        offset = 0
        limit = 200  # Max per request

        while True:
            result = self.search_cancellations(
                cancel_state=cancel_state,
                role=role,
                limit=limit,
                offset=offset,
            )

            members = result.get("cancellations", [])
            if not members:
                break

            all_cancellations.extend(members)

            # Check if more results
            total = result.get("total", 0)
            if offset + len(members) >= total:
                break

            offset += limit

        return all_cancellations

    def get_cancellations_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        cancel_state: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get cancellations within a date range (handles pagination).

        Args:
            start_date: Start date (UTC)
            end_date: End date (UTC)
            cancel_state: Optional state filter

        Returns:
            List of cancellations within date range

        Examples:
            >>> from datetime import datetime, timedelta, timezone
            >>> now = datetime.now(timezone.utc)
            >>> week_ago = now - timedelta(days=7)
            >>> recent = client.get_cancellations_by_date_range(week_ago, now)
        """
        all_cancellations: List[Dict[str, Any]] = []
        offset = 0
        limit = 200

        while True:
            result = self.search_cancellations(
                cancel_state=cancel_state,
                creation_date_range_from=start_date,
                creation_date_range_to=end_date,
                limit=limit,
                offset=offset,
            )

            members = result.get("cancellations", [])
            if not members:
                break

            all_cancellations.extend(members)

            total = result.get("total", 0)
            if offset + len(members) >= total:
                break

            offset += limit

        return all_cancellations

    def get_pending_cancellations(self) -> List[Dict[str, Any]]:
        """
        Get cancellations that are pending seller response.

        Returns:
            List of cancellations needing seller action

        Examples:
            >>> pending = client.get_pending_cancellations()
            >>> for cancel in pending:
            ...     print(f"Pending: {cancel['cancelId']}")
        """
        all_cancels = self.get_all_cancellations(role="SELLER")

        # Filter to only those needing action (status indicates pending)
        pending_statuses = ["CANCEL_REQUESTED", "CANCEL_PENDING"]

        return [
            cancel for cancel in all_cancels
            if cancel.get("cancelStatus") in pending_statuses
        ]
