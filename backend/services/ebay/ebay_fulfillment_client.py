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

from datetime import datetime, timezone
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
