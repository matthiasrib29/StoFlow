"""
eBay Return Client.

Client for Post-Order API v2 returns endpoints.
Handles searching, retrieving, and managing return requests.

Endpoints:
- GET /return/search - Search returns with filters
- GET /return/{returnId} - Get return details
- POST /return/{returnId}/decide - Accept/decline return
- POST /return/{returnId}/issue_refund - Issue refund
- POST /return/{returnId}/mark_as_received - Mark item received
- POST /return/{returnId}/send_message - Send message

Documentation:
https://developer.ebay.com/devzone/post-order/index.html

Author: Claude
Date: 2026-01-13
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from services.ebay.ebay_post_order_client import EbayPostOrderClient
from shared.logging_setup import get_logger

logger = get_logger(__name__)


class EbayReturnClient(EbayPostOrderClient):
    """
    Client for eBay Post-Order API returns management.

    Extends EbayPostOrderClient with return-specific methods.

    Usage:
        >>> client = EbayReturnClient(db_session, user_id=1)
        >>>
        >>> # Search all open returns
        >>> returns = client.search_returns(return_state="OPEN")
        >>>
        >>> # Get return details
        >>> return_data = client.get_return("5000012345")
        >>>
        >>> # Accept a return
        >>> client.decide_return("5000012345", decision="ACCEPT")
    """

    def __init__(
        self,
        db: Session,
        user_id: int,
        marketplace_id: Optional[str] = None,
        sandbox: bool = False,
    ):
        """Initialize return client."""
        super().__init__(db, user_id, marketplace_id, sandbox)

    def search_returns(
        self,
        order_id: Optional[str] = None,
        return_state: Optional[str] = None,
        creation_date_range_from: Optional[datetime] = None,
        creation_date_range_to: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Search for return requests with filters.

        Args:
            order_id: Filter by specific order ID
            return_state: Filter by state (OPEN, CLOSED)
            creation_date_range_from: Start date for creation filter
            creation_date_range_to: End date for creation filter
            limit: Max results per page (default 50, max 200)
            offset: Pagination offset

        Returns:
            Dict with structure:
            {
                "members": [
                    {
                        "returnId": "5000012345",
                        "state": "OPEN",
                        "status": "RETURN_REQUESTED",
                        ...
                    }
                ],
                "total": 100,
                "limit": 50,
                "offset": 0
            }

        Examples:
            >>> # Get all open returns
            >>> result = client.search_returns(return_state="OPEN")
            >>> returns = result.get("members", [])
            >>>
            >>> # Get returns for a specific order
            >>> result = client.search_returns(order_id="12-34567-89012")
        """
        params = {
            "limit": min(limit, 200),
            "offset": offset,
        }

        if order_id:
            params["order_id"] = order_id

        if return_state:
            params["return_state"] = return_state

        if creation_date_range_from:
            params["creation_date_range_from"] = creation_date_range_from.strftime(
                "%Y-%m-%dT%H:%M:%S.000Z"
            )

        if creation_date_range_to:
            params["creation_date_range_to"] = creation_date_range_to.strftime(
                "%Y-%m-%dT%H:%M:%S.000Z"
            )

        result = self.api_call_post_order("GET", "/return/search", params=params)
        return result or {"members": [], "total": 0}

    def get_return(self, return_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific return.

        Args:
            return_id: eBay return ID (e.g., "5000012345")

        Returns:
            Dict with full return details:
            {
                "returnId": "5000012345",
                "state": "OPEN",
                "status": "RETURN_REQUESTED",
                "returnReason": "NOT_AS_DESCRIBED",
                "refundAmount": {"value": "50.00", "currency": "EUR"},
                "buyer": {...},
                "seller": {...},
                "orderDetails": {...},
                "creationDate": "2026-01-13T10:00:00.000Z",
                ...
            }

        Raises:
            EbayAPIError: If return not found or API error

        Examples:
            >>> return_data = client.get_return("5000012345")
            >>> print(f"Status: {return_data['status']}")
            >>> print(f"Reason: {return_data['returnReason']}")
        """
        result = self.api_call_post_order("GET", f"/return/{return_id}")
        return result or {}

    def decide_return(
        self,
        return_id: str,
        decision: str,
        comments: Optional[str] = None,
        rma_number: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Accept or decline a return request.

        Args:
            return_id: eBay return ID
            decision: Decision action:
                - "ACCEPT" - Accept the return
                - "DECLINE" - Decline the return (requires valid reason)
            comments: Optional seller comments
            rma_number: Optional RMA number for accepted returns

        Returns:
            Dict with decision result

        Raises:
            EbayAPIError: If decision fails

        Examples:
            >>> # Accept return
            >>> client.decide_return(
            ...     "5000012345",
            ...     decision="ACCEPT",
            ...     comments="Please ship the item back",
            ...     rma_number="RMA-2026-001"
            ... )
            >>>
            >>> # Decline return (use with caution - impacts seller metrics)
            >>> client.decide_return(
            ...     "5000012345",
            ...     decision="DECLINE",
            ...     comments="Item was as described"
            ... )
        """
        payload: Dict[str, Any] = {
            "decision": decision,
        }

        if comments:
            payload["comments"] = comments

        if rma_number and decision == "ACCEPT":
            payload["RMANumber"] = rma_number

        result = self.api_call_post_order(
            "POST", f"/return/{return_id}/decide", json_data=payload
        )
        return result or {}

    def issue_refund(
        self,
        return_id: str,
        refund_amount: Optional[float] = None,
        currency: Optional[str] = None,
        comments: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Issue a refund for a return.

        Args:
            return_id: eBay return ID
            refund_amount: Optional partial refund amount (if None, full refund)
            currency: Currency code (e.g., "EUR", "USD")
            comments: Optional refund comments

        Returns:
            Dict with refund result

        Raises:
            EbayAPIError: If refund fails

        Examples:
            >>> # Full refund
            >>> client.issue_refund("5000012345")
            >>>
            >>> # Partial refund
            >>> client.issue_refund(
            ...     "5000012345",
            ...     refund_amount=25.00,
            ...     currency="EUR",
            ...     comments="Partial refund for damaged item"
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
            "POST", f"/return/{return_id}/issue_refund", json_data=payload or None
        )
        return result or {}

    def mark_as_received(
        self,
        return_id: str,
        comments: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Mark a return item as received by seller.

        Args:
            return_id: eBay return ID
            comments: Optional comments about item condition

        Returns:
            Dict with result

        Examples:
            >>> client.mark_as_received(
            ...     "5000012345",
            ...     comments="Item received in good condition"
            ... )
        """
        payload: Dict[str, Any] = {}

        if comments:
            payload["comments"] = comments

        result = self.api_call_post_order(
            "POST",
            f"/return/{return_id}/mark_as_received",
            json_data=payload or None,
        )
        return result or {}

    def send_message(
        self,
        return_id: str,
        message: str,
    ) -> Dict[str, Any]:
        """
        Send a message to the buyer about a return.

        Args:
            return_id: eBay return ID
            message: Message text

        Returns:
            Dict with result

        Examples:
            >>> client.send_message(
            ...     "5000012345",
            ...     message="I've received your return request. Please ship the item."
            ... )
        """
        payload = {
            "message": message,
        }

        result = self.api_call_post_order(
            "POST", f"/return/{return_id}/send_message", json_data=payload
        )
        return result or {}

    def get_all_returns(
        self,
        return_state: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all returns with optional state filter (handles pagination).

        Args:
            return_state: Filter by state (OPEN, CLOSED)

        Returns:
            List of all return records

        Examples:
            >>> # Get all open returns
            >>> open_returns = client.get_all_returns(return_state="OPEN")
            >>> print(f"Found {len(open_returns)} open returns")
        """
        all_returns: List[Dict[str, Any]] = []
        offset = 0
        limit = 200  # Max per request

        while True:
            result = self.search_returns(
                return_state=return_state,
                limit=limit,
                offset=offset,
            )

            members = result.get("members", [])
            if not members:
                break

            all_returns.extend(members)

            # Check if more results
            total = result.get("total", 0)
            if offset + len(members) >= total:
                break

            offset += limit

        return all_returns

    def get_returns_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        return_state: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get returns within a date range (handles pagination).

        Args:
            start_date: Start date (UTC)
            end_date: End date (UTC)
            return_state: Optional state filter

        Returns:
            List of returns within date range

        Examples:
            >>> from datetime import datetime, timedelta, timezone
            >>> now = datetime.now(timezone.utc)
            >>> week_ago = now - timedelta(days=7)
            >>> recent_returns = client.get_returns_by_date_range(week_ago, now)
        """
        all_returns: List[Dict[str, Any]] = []
        offset = 0
        limit = 200

        while True:
            result = self.search_returns(
                return_state=return_state,
                creation_date_range_from=start_date,
                creation_date_range_to=end_date,
                limit=limit,
                offset=offset,
            )

            members = result.get("members", [])
            if not members:
                break

            all_returns.extend(members)

            total = result.get("total", 0)
            if offset + len(members) >= total:
                break

            offset += limit

        return all_returns
