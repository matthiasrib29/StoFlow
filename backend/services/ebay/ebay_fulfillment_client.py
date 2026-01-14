"""
eBay Fulfillment API Client.

Client pour gérer les commandes (orders) eBay via l'API Fulfillment.

Endpoints implémentés:
- GET /sell/fulfillment/v1/order - Liste des commandes
- GET /sell/fulfillment/v1/order/{orderId} - Détails d'une commande

Documentation officielle:
https://developer.ebay.com/api-docs/sell/fulfillment/overview.html

Author: Claude
Date: 2025-12-10
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from services.ebay.ebay_base_client import EbayBaseClient


class EbayFulfillmentClient(EbayBaseClient):
    """
    Client eBay Fulfillment API (commandes).

    Usage:
        >>> client = EbayFulfillmentClient(db_session, user_id=1)
        >>>
        >>> # Récupérer toutes les commandes
        >>> orders = client.get_orders(filter="orderfulfillmentstatus:{NOT_STARTED}")
        >>>
        >>> # Récupérer une commande spécifique
        >>> order = client.get_order("12-34567-89012")
    """

    def get_orders(
        self,
        filter: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Récupère la liste des commandes eBay.

        Args:
            filter: Filtre de recherche eBay.
                   Exemples:
                   - "orderfulfillmentstatus:{NOT_STARTED}" - Commandes non traitées
                   - "orderfulfillmentstatus:{IN_PROGRESS}" - En cours
                   - "orderfulfillmentstatus:{FULFILLED}" - Complétées
                   - "creationdate:[2024-01-01T00:00:00.000Z..2024-12-31T23:59:59.999Z]" - Par date
            limit: Nombre max de résultats (max 200, défaut 50)
            offset: Offset pagination (défaut 0)

        Returns:
            Dict avec structure:
            {
                "orders": [
                    {
                        "orderId": "12-34567-89012",
                        "orderFulfillmentStatus": "NOT_STARTED",
                        "buyer": {...},
                        "pricingSummary": {...},
                        "lineItems": [...]
                    }
                ],
                "total": 100,
                "limit": 50,
                "offset": 0
            }

        Examples:
            >>> # Récupérer commandes non traitées
            >>> client = EbayFulfillmentClient(db, user_id=1)
            >>> result = client.get_orders(
            ...     filter="orderfulfillmentstatus:{NOT_STARTED}",
            ...     limit=50
            ... )
            >>> orders = result.get("orders", [])
            >>> print(f"Trouvé {len(orders)} commandes non traitées")
        """
        params = {
            "limit": min(limit, 200),  # eBay max = 200
            "offset": offset,
        }

        if filter:
            params["filter"] = filter

        # Scopes requis pour Fulfillment API
        scopes = ["sell.fulfillment", "sell.fulfillment.readonly"]

        result = self.api_call(
            "GET",
            "/sell/fulfillment/v1/order",
            params=params,
            scopes=scopes,
        )

        return result or {"orders": [], "total": 0}

    def get_order(self, order_id: str) -> Dict[str, Any]:
        """
        Récupère les détails d'une commande spécifique.

        Args:
            order_id: ID de la commande eBay (ex: "12-34567-89012")

        Returns:
            Dict avec détails complets de la commande:
            {
                "orderId": "12-34567-89012",
                "orderFulfillmentStatus": "NOT_STARTED",
                "buyer": {
                    "username": "buyer123",
                    "taxAddress": {...}
                },
                "pricingSummary": {
                    "total": {"value": "50.00", "currency": "EUR"},
                    "priceSubtotal": {"value": "45.00", "currency": "EUR"},
                    "deliveryCost": {"value": "5.00", "currency": "EUR"}
                },
                "lineItems": [
                    {
                        "lineItemId": "123456789012",
                        "sku": "SKU-123",
                        "title": "T-shirt Nike",
                        "quantity": 1,
                        "lineItemCost": {"value": "45.00", "currency": "EUR"}
                    }
                ],
                "creationDate": "2024-12-10T10:30:00.000Z",
                "lastModifiedDate": "2024-12-10T10:30:00.000Z"
            }

        Raises:
            RuntimeError: Si commande introuvable ou erreur API

        Examples:
            >>> client = EbayFulfillmentClient(db, user_id=1)
            >>> order = client.get_order("12-34567-89012")
            >>> print(f"Commande {order['orderId']}: {order['orderFulfillmentStatus']}")
            >>> print(f"Total: {order['pricingSummary']['total']['value']} {order['pricingSummary']['total']['currency']}")
        """
        scopes = ["sell.fulfillment", "sell.fulfillment.readonly"]

        result = self.api_call(
            "GET",
            f"/sell/fulfillment/v1/order/{order_id}",
            scopes=scopes,
        )

        return result

    def get_orders_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Récupère les commandes dans une plage de dates.

        Helper method qui construit automatiquement le filtre de date.

        Args:
            start_date: Date début (datetime UTC)
            end_date: Date fin (datetime UTC)
            status: Statut optionnel (NOT_STARTED, IN_PROGRESS, FULFILLED)

        Returns:
            Liste de commandes

        Examples:
            >>> from datetime import datetime, timedelta, timezone
            >>>
            >>> # Commandes des 7 derniers jours
            >>> now = datetime.now(timezone.utc)
            >>> week_ago = now - timedelta(days=7)
            >>> orders = client.get_orders_by_date_range(week_ago, now)
            >>>
            >>> # Commandes non traitées des 24h
            >>> day_ago = now - timedelta(days=1)
            >>> pending_orders = client.get_orders_by_date_range(
            ...     day_ago, now, status="NOT_STARTED"
            ... )
        """
        # Construire filtre date
        # NOTE: Using lastmodifieddate instead of creationdate to catch all orders
        # that were updated/modified in the time range (not just newly created ones)
        start_str = start_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        end_str = end_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        date_filter = f"lastmodifieddate:[{start_str}..{end_str}]"

        # Ajouter filtre statut si fourni
        if status:
            date_filter = f"{date_filter} AND orderfulfillmentstatus:{{{status}}}"

        # Récupérer toutes les pages
        all_orders = []
        offset = 0
        limit = 200  # Max eBay

        while True:
            result = self.get_orders(filter=date_filter, limit=limit, offset=offset)
            orders = result.get("orders", [])

            if not orders:
                break

            all_orders.extend(orders)

            # Vérifier si plus de résultats
            total = result.get("total", 0)
            if offset + len(orders) >= total:
                break

            offset += limit

        return all_orders

    def get_all_orders(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Récupère TOUTES les commandes eBay (sans filtre de date).

        ATTENTION: Peut retourner beaucoup de données. Utilisé pour la sync initiale.

        Args:
            status: Statut optionnel (NOT_STARTED, IN_PROGRESS, FULFILLED)

        Returns:
            Liste de toutes les commandes

        Examples:
            >>> client = EbayFulfillmentClient(db, user_id=1)
            >>> # Toutes les commandes
            >>> all_orders = client.get_all_orders()
            >>> # Toutes les commandes non traitées
            >>> pending = client.get_all_orders(status="NOT_STARTED")
        """
        # Construire filtre (status uniquement, pas de date)
        filter_str = None
        if status:
            filter_str = f"orderfulfillmentstatus:{{{status}}}"

        # Récupérer toutes les pages
        all_orders = []
        offset = 0
        limit = 200  # Max eBay

        while True:
            result = self.get_orders(filter=filter_str, limit=limit, offset=offset)
            orders = result.get("orders", [])

            if not orders:
                break

            all_orders.extend(orders)

            # Vérifier si plus de résultats
            total = result.get("total", 0)
            if offset + len(orders) >= total:
                break

            offset += limit

        return all_orders

    def create_shipping_fulfillment(
        self, order_id: str, payload: dict
    ) -> Dict[str, Any]:
        """
        Create shipping fulfillment (add tracking to order).

        POST /sell/fulfillment/v1/order/{orderId}/shipping_fulfillment

        **Important:**
        - Tracking number must be alphanumeric only (no spaces, dashes, special chars)
        - Order must be in PAID status
        - This marks the order as shipped on eBay

        Args:
            order_id: eBay order ID (e.g., "12-34567-89012")
            payload: Fulfillment payload:
                {
                    "lineItems": [
                        {"lineItemId": str, "quantity": int}
                    ],
                    "shippedDate": "2024-12-10T10:00:00.000Z",  # ISO 8601
                    "shippingCarrierCode": "COLISSIMO",  # Carrier code
                    "trackingNumber": "1234567890"  # Alphanumeric only
                }

        Returns:
            Dict with fulfillment ID:
            {
                "fulfillmentId": "abc123xyz"
            }

        Raises:
            RuntimeError: If API call fails (invalid order, already shipped, etc.)

        Examples:
            >>> client = EbayFulfillmentClient(db, user_id=1)
            >>> payload = {
            ...     "lineItems": [{"lineItemId": "123456789012", "quantity": 1}],
            ...     "shippedDate": "2024-12-10T10:00:00.000Z",
            ...     "shippingCarrierCode": "COLISSIMO",
            ...     "trackingNumber": "1234567890"
            ... }
            >>> result = client.create_shipping_fulfillment("12-34567-89012", payload)
            >>> print(result["fulfillmentId"])
            abc123xyz
        """
        scopes = ["sell.fulfillment"]

        result = self.api_call(
            "POST",
            f"/sell/fulfillment/v1/order/{order_id}/shipping_fulfillment",
            json=payload,
            scopes=scopes,
        )

        return result or {}

    def issue_refund(
        self,
        order_id: str,
        reason_for_refund: str,
        refund_amount: float,
        currency: str = "EUR",
        line_item_id: Optional[str] = None,
        comment: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Issue a refund for an order or specific line item.

        POST /sell/fulfillment/v1/order/{orderId}/issue_refund

        This can be used to:
        - Issue a full or partial refund for an order
        - Refund a specific line item
        - Issue goodwill refunds

        Args:
            order_id: eBay order ID (e.g., "12-34567-89012")
            reason_for_refund: Reason code for the refund. Valid values:
                - BUYER_CANCEL: Buyer cancelled the order
                - BUYER_RETURN: Buyer returned the item
                - ITEM_NOT_RECEIVED: Item was not received
                - SELLER_WRONG_ITEM: Wrong item sent
                - SELLER_OUT_OF_STOCK: Item out of stock
                - SELLER_FOUND_ISSUE: Seller found issue with item
                - OTHER: Other reason
            refund_amount: Amount to refund
            currency: Currency code (default: EUR)
            line_item_id: Optional line item ID for item-specific refund
            comment: Optional comment explaining the refund

        Returns:
            Dict with refund details:
            {
                "refundId": "5********0",
                "refundStatus": "PENDING",
                "refundedAmount": {"value": "50.00", "currency": "EUR"}
            }

        Raises:
            RuntimeError: If API call fails

        Examples:
            >>> client = EbayFulfillmentClient(db, user_id=1)
            >>> # Full order refund
            >>> result = client.issue_refund(
            ...     order_id="12-34567-89012",
            ...     reason_for_refund="BUYER_CANCEL",
            ...     refund_amount=50.00
            ... )
            >>> # Partial line item refund
            >>> result = client.issue_refund(
            ...     order_id="12-34567-89012",
            ...     reason_for_refund="SELLER_FOUND_ISSUE",
            ...     refund_amount=10.00,
            ...     line_item_id="123456789012",
            ...     comment="Partial refund for damaged item"
            ... )
        """
        scopes = ["sell.fulfillment"]

        # Build payload
        payload: Dict[str, Any] = {
            "reasonForRefund": reason_for_refund,
        }

        if comment:
            payload["comment"] = comment

        # Either line item refund or order-level refund
        if line_item_id:
            payload["refundItems"] = [
                {
                    "refundAmount": {
                        "value": str(refund_amount),
                        "currency": currency,
                    },
                    "lineItemId": line_item_id,
                }
            ]
        else:
            payload["orderLevelRefundAmount"] = {
                "value": str(refund_amount),
                "currency": currency,
            }

        result = self.api_call(
            "POST",
            f"/sell/fulfillment/v1/order/{order_id}/issue_refund",
            json=payload,
            scopes=scopes,
        )

        return result or {}

    def get_order_refunds(self, order_id: str) -> List[Dict[str, Any]]:
        """
        Get refunds associated with an order.

        This retrieves the order and extracts refund information from it.
        eBay doesn't have a dedicated refund search endpoint, so we get
        refund data from the order's payment summary.

        Args:
            order_id: eBay order ID

        Returns:
            List of refund records from the order:
            [
                {
                    "refundId": "5********0",
                    "refundDate": "2024-12-10T10:30:00.000Z",
                    "refundAmount": {"value": "50.00", "currency": "EUR"},
                    "refundStatus": "REFUNDED",
                    "refundReferenceId": "ABC123"
                }
            ]

        Examples:
            >>> client = EbayFulfillmentClient(db, user_id=1)
            >>> refunds = client.get_order_refunds("12-34567-89012")
            >>> for r in refunds:
            ...     print(f"Refund {r['refundId']}: {r['refundAmount']['value']}")
        """
        order = self.get_order(order_id)

        # Extract refunds from payment summary
        payment_summary = order.get("paymentSummary", {})
        refunds = payment_summary.get("refunds", [])

        return refunds

    # =========================================================================
    # PAYMENT DISPUTES
    # =========================================================================

    def get_payment_dispute_summaries(
        self,
        order_id: Optional[str] = None,
        buyer_username: Optional[str] = None,
        payment_dispute_status: Optional[List[str]] = None,
        open_date_from: Optional[str] = None,
        open_date_to: Optional[str] = None,
        limit: int = 200,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Get a list of payment dispute summaries.

        GET /sell/fulfillment/v1/payment_dispute_summary

        Args:
            order_id: Filter by order ID
            buyer_username: Filter by buyer username
            payment_dispute_status: Filter by dispute states. Values:
                - OPEN: Dispute is active with no seller action required
                - ACTION_NEEDED: Dispute requires seller response by deadline
                - CLOSED: Dispute has been resolved
            open_date_from: Beginning date (ISO 8601 format)
            open_date_to: Ending date (ISO 8601 format, max 90 days from start)
            limit: Max results (1-200, default 200)
            offset: Number of records to skip (default 0)

        Returns:
            Dict with structure:
            {
                "paymentDisputeSummaries": [
                    {
                        "paymentDisputeId": "5********0",
                        "paymentDisputeStatus": "ACTION_NEEDED",
                        "reason": "ITEM_NOT_RECEIVED",
                        "orderId": "12-34567-89012",
                        "amount": {"value": "50.00", "currency": "EUR"},
                        "buyerUsername": "buyer123",
                        "openDate": "2024-12-10T10:30:00.000Z",
                        "respondByDate": "2024-12-20T10:30:00.000Z"
                    }
                ],
                "total": 10,
                "limit": 200,
                "offset": 0
            }

        Examples:
            >>> client = EbayFulfillmentClient(db, user_id=1)
            >>> # Get disputes needing action
            >>> result = client.get_payment_dispute_summaries(
            ...     payment_dispute_status=["ACTION_NEEDED"]
            ... )
            >>> disputes = result.get("paymentDisputeSummaries", [])
        """
        scopes = ["sell.payment.dispute"]

        params: Dict[str, Any] = {
            "limit": min(limit, 200),
            "offset": offset,
        }

        if order_id:
            params["order_id"] = order_id
        if buyer_username:
            params["buyer_username"] = buyer_username
        if payment_dispute_status:
            # eBay expects multiple params for status
            params["payment_dispute_status"] = ",".join(payment_dispute_status)
        if open_date_from:
            params["open_date_from"] = open_date_from
        if open_date_to:
            params["open_date_to"] = open_date_to

        result = self.api_call(
            "GET",
            "/sell/fulfillment/v1/payment_dispute_summary",
            params=params,
            scopes=scopes,
        )

        return result or {"paymentDisputeSummaries": [], "total": 0}

    def get_payment_dispute(self, payment_dispute_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific payment dispute.

        GET /sell/fulfillment/v1/payment_dispute/{payment_dispute_id}

        Args:
            payment_dispute_id: The payment dispute ID

        Returns:
            Dict with full dispute details:
            {
                "paymentDisputeId": "5********0",
                "paymentDisputeStatus": "ACTION_NEEDED",
                "reason": "ITEM_NOT_RECEIVED",
                "orderId": "12-34567-89012",
                "amount": {"value": "50.00", "currency": "EUR"},
                "openDate": "2024-12-10T10:30:00.000Z",
                "respondByDate": "2024-12-20T10:30:00.000Z",
                "revision": 1,
                "buyerUsername": "buyer123",
                "sellerResponse": null,
                "availableChoices": ["CONTEST", "ACCEPT"],
                "evidenceRequests": [
                    {
                        "evidenceType": "PROOF_OF_DELIVERY",
                        "requestDate": "2024-12-10T10:30:00.000Z"
                    }
                ],
                "evidence": [],
                "lineItems": [...],
                "resolution": null
            }

        Raises:
            RuntimeError: If dispute not found or API error

        Examples:
            >>> client = EbayFulfillmentClient(db, user_id=1)
            >>> dispute = client.get_payment_dispute("5********0")
            >>> print(f"Status: {dispute['paymentDisputeStatus']}")
        """
        scopes = ["sell.payment.dispute"]

        result = self.api_call(
            "GET",
            f"/sell/fulfillment/v1/payment_dispute/{payment_dispute_id}",
            scopes=scopes,
        )

        return result

    def accept_payment_dispute(
        self,
        payment_dispute_id: str,
        revision: int,
        return_address: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Accept a payment dispute (seller concedes to buyer).

        POST /sell/fulfillment/v1/payment_dispute/{payment_dispute_id}/accept

        When accepting a dispute, the seller agrees to refund the buyer.
        This is typically done when the seller cannot contest the dispute
        or acknowledges the buyer's claim.

        Args:
            payment_dispute_id: The payment dispute ID
            revision: Current revision number (from getPaymentDispute)
            return_address: Optional return address if buyer should return item

        Returns:
            True if successful (204 response)

        Raises:
            RuntimeError: If API call fails

        Examples:
            >>> client = EbayFulfillmentClient(db, user_id=1)
            >>> # Get current revision
            >>> dispute = client.get_payment_dispute("5********0")
            >>> # Accept the dispute
            >>> success = client.accept_payment_dispute(
            ...     "5********0",
            ...     revision=dispute["revision"]
            ... )
        """
        scopes = ["sell.payment.dispute"]

        payload: Dict[str, Any] = {
            "revision": revision,
        }

        if return_address:
            payload["returnAddress"] = return_address

        # This endpoint returns 204 No Content on success
        result = self.api_call(
            "POST",
            f"/sell/fulfillment/v1/payment_dispute/{payment_dispute_id}/accept",
            json=payload,
            scopes=scopes,
        )

        # api_call returns None for 204 responses
        return True

    def contest_payment_dispute(
        self,
        payment_dispute_id: str,
        revision: int,
        return_address: Optional[Dict[str, Any]] = None,
        note: Optional[str] = None,
    ) -> bool:
        """
        Contest a payment dispute (seller disputes buyer's claim).

        POST /sell/fulfillment/v1/payment_dispute/{payment_dispute_id}/contest

        Before contesting, the seller should provide evidence using
        add_evidence or update_evidence methods. Once contested, evidence
        can no longer be added.

        Args:
            payment_dispute_id: The payment dispute ID
            revision: Current revision number (from getPaymentDispute)
            return_address: Return address if expecting item return
            note: Optional note explaining the contest (max 1000 chars)

        Returns:
            True if successful (204 response)

        Raises:
            RuntimeError: If API call fails

        Examples:
            >>> client = EbayFulfillmentClient(db, user_id=1)
            >>> # First add evidence, then contest
            >>> success = client.contest_payment_dispute(
            ...     "5********0",
            ...     revision=1,
            ...     note="Item was delivered as confirmed by tracking"
            ... )
        """
        scopes = ["sell.payment.dispute"]

        payload: Dict[str, Any] = {
            "revision": revision,
        }

        if return_address:
            payload["returnAddress"] = return_address
        if note:
            payload["note"] = note[:1000]  # Max 1000 characters

        # This endpoint returns 204 No Content on success
        result = self.api_call(
            "POST",
            f"/sell/fulfillment/v1/payment_dispute/{payment_dispute_id}/contest",
            json=payload,
            scopes=scopes,
        )

        return True

    def add_evidence(
        self,
        payment_dispute_id: str,
        evidence_type: str,
        files: Optional[List[Dict[str, str]]] = None,
        line_items: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Add evidence to a payment dispute before contesting.

        POST /sell/fulfillment/v1/payment_dispute/{payment_dispute_id}/add_evidence

        Evidence can only be added before calling contest_payment_dispute.
        Once contested, use update_evidence to modify existing evidence sets.

        Args:
            payment_dispute_id: The payment dispute ID
            evidence_type: Type of evidence being provided:
                - PROOF_OF_DELIVERY: Tracking/delivery confirmation
                - PROOF_OF_AUTHENTICITY: Item authenticity proof
                - PROOF_OF_ITEM_AS_DESCRIBED: Item matches listing
                - PROOF_OF_PICKUP: Documentation for buyer pickup
                - TRACKING_INFORMATION: Shipping tracking data
            files: List of evidence files:
                [{"fileId": "abc123"}]  # File IDs from upload
            line_items: Line items the evidence applies to:
                [{"lineItemId": "123456789012"}]

        Returns:
            Dict with evidence ID:
            {
                "evidenceId": "xyz789"
            }

        Examples:
            >>> client = EbayFulfillmentClient(db, user_id=1)
            >>> result = client.add_evidence(
            ...     "5********0",
            ...     evidence_type="PROOF_OF_DELIVERY",
            ...     line_items=[{"lineItemId": "123456789012"}]
            ... )
        """
        scopes = ["sell.payment.dispute"]

        payload: Dict[str, Any] = {
            "evidenceType": evidence_type,
        }

        if files:
            payload["files"] = files
        if line_items:
            payload["lineItems"] = line_items

        result = self.api_call(
            "POST",
            f"/sell/fulfillment/v1/payment_dispute/{payment_dispute_id}/add_evidence",
            json=payload,
            scopes=scopes,
        )

        return result or {}

    def get_all_payment_disputes(
        self,
        status: Optional[List[str]] = None,
        days_back: int = 90,
    ) -> List[Dict[str, Any]]:
        """
        Get all payment disputes with pagination.

        Helper method that fetches all disputes across pages.

        Args:
            status: Filter by dispute states (OPEN, ACTION_NEEDED, CLOSED)
            days_back: Number of days to look back (max 90)

        Returns:
            List of all dispute summaries

        Examples:
            >>> client = EbayFulfillmentClient(db, user_id=1)
            >>> # Get all disputes needing action
            >>> disputes = client.get_all_payment_disputes(
            ...     status=["ACTION_NEEDED", "OPEN"]
            ... )
        """
        # Calculate date range
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=min(days_back, 90))

        open_date_from = start_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        open_date_to = end_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")

        all_disputes = []
        offset = 0
        limit = 200

        while True:
            result = self.get_payment_dispute_summaries(
                payment_dispute_status=status,
                open_date_from=open_date_from,
                open_date_to=open_date_to,
                limit=limit,
                offset=offset,
            )

            disputes = result.get("paymentDisputeSummaries", [])

            if not disputes:
                break

            all_disputes.extend(disputes)

            total = result.get("total", 0)
            if offset + len(disputes) >= total:
                break

            offset += limit

        return all_disputes
