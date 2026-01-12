"""
eBay Order Sync Service

Service pour synchroniser les commandes eBay depuis l'API Fulfillment vers la DB locale.
Responsabilité: Orchestrer le fetch, mapping et création/update des commandes.

Architecture:
- Fetch orders via EbayFulfillmentClient
- Map API data → DB models
- Create or update via EbayOrderRepository
- Handle pagination and errors gracefully
- Return detailed statistics

Created: 2026-01-07
Author: Claude
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from models.user.ebay_order import EbayOrder, EbayOrderProduct
from repositories.ebay_order_repository import EbayOrderRepository
from services.ebay.ebay_fulfillment_client import EbayFulfillmentClient
from shared.logging_setup import get_logger

logger = get_logger(__name__)


class EbayOrderSyncService:
    """
    Service pour synchroniser les commandes eBay.

    Workflow:
    1. Calculate date range (now - N hours)
    2. Fetch orders from eBay Fulfillment API
    3. For each order: check if exists, map data, create or update
    4. Return statistics (created, updated, errors)

    Usage:
        >>> service = EbayOrderSyncService(db_session, user_id=1)
        >>> stats = service.sync_orders(modified_since_hours=24)
        >>> print(f"Created: {stats['created']}, Updated: {stats['updated']}")
    """

    def __init__(self, db: Session, user_id: int):
        """
        Initialize sync service.

        Args:
            db: Session SQLAlchemy (avec search_path déjà défini)
            user_id: ID utilisateur pour authentification eBay
        """
        self.db = db
        self.user_id = user_id
        self.fulfillment_client = EbayFulfillmentClient(db, user_id)

        logger.info(f"[EbayOrderSyncService] Initialized for user_id={user_id}")
    # ===== HELPER METHODS FOR sync_orders() (Refactored 2026-01-12 Phase 3.2e) =====

    @staticmethod
    def _validate_sync_parameters(modified_since_hours: Optional[int]) -> bool:
        """
        Validate sync parameters and determine if syncing all orders.

        Args:
            modified_since_hours: Hours to look back (1-720, 0/None for all)

        Returns:
            True if syncing all orders, False if date range

        Raises:
            ValueError: If hours out of valid range
        """
        sync_all = modified_since_hours is None or modified_since_hours == 0

        if not sync_all and not (1 <= modified_since_hours <= 720):
            raise ValueError(
                "modified_since_hours must be between 1 and 720 (30 days), or 0 for all orders"
            )

        return sync_all

    def _fetch_orders_from_ebay(
        self,
        sync_all: bool,
        modified_since_hours: Optional[int],
        status_filter: Optional[str],
    ) -> list[dict]:
        """
        Fetch orders from eBay API (all or date range).

        Args:
            sync_all: If True, fetch all orders (no date filter)
            modified_since_hours: Hours to look back (ignored if sync_all)
            status_filter: Optional fulfillment status filter

        Returns:
            List of order dicts from eBay API
        """
        if sync_all:
            logger.debug("[EbayOrderSyncService] Fetching ALL orders (no date filter)")
            return self.fulfillment_client.get_all_orders(status=status_filter)

        # Date range fetch
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(hours=modified_since_hours)

        logger.debug(
            f"[EbayOrderSyncService] Fetching orders from {start_date.isoformat()} "
            f"to {end_date.isoformat()}"
        )

        return self.fulfillment_client.get_orders_by_date_range(
            start_date=start_date,
            end_date=end_date,
            status=status_filter,
        )

    def _process_orders_batch(self, api_orders: list[dict]) -> dict:
        """
        Process batch of orders and collect statistics.

        Args:
            api_orders: List of orders from eBay API

        Returns:
            Statistics dict with created/updated/skipped/errors counts
        """
        stats = {
            "created": 0,
            "updated": 0,
            "skipped": 0,
            "errors": 0,
            "details": [],
        }

        for idx, api_order in enumerate(api_orders, start=1):
            order_id = api_order.get("orderId", "unknown")

            try:
                result = self._process_single_order(api_order)

                # Update stats
                action = result.get("action", "error")
                if action == "created":
                    stats["created"] += 1
                elif action == "updated":
                    stats["updated"] += 1
                elif action == "skipped":
                    stats["skipped"] += 1

                stats["details"].append(result)

                # Log progress every 50 orders
                if idx % 50 == 0:
                    logger.info(
                        f"[EbayOrderSyncService] Progress: {idx}/{len(api_orders)} "
                        f"orders processed"
                    )

            except Exception as e:
                stats["errors"] += 1
                error_msg = str(e)

                logger.error(
                    f"[EbayOrderSyncService] Error processing order {order_id}: {e}",
                    exc_info=True,
                )

                stats["details"].append({
                    "order_id": order_id,
                    "action": "error",
                    "error": error_msg,
                })

        return stats

    def _finalize_sync(self, start_time: datetime, stats: dict) -> None:
        """
        Commit transaction and log summary.

        Args:
            start_time: Sync start timestamp
            stats: Statistics dict
        """
        self.db.commit()

        elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()

        logger.info(
            f"[EbayOrderSyncService] Sync completed: user_id={self.user_id}, "
            f"created={stats['created']}, updated={stats['updated']}, "
            f"skipped={stats['skipped']}, errors={stats['errors']}, "
            f"total_fetched={stats['total_fetched']}, duration={elapsed:.2f}s"
        )


    def sync_orders(
        self,
        modified_since_hours: Optional[int] = 24,
        status_filter: Optional[str] = None,
    ) -> dict:
        """
        Synchronize orders modified in the last N hours, or ALL orders if hours=0/None.

        Refactored 2026-01-12 Phase 3.2e: Extracted 4 helper methods for clarity.

        Args:
            modified_since_hours: Number of hours to look back (1-720)
                                 If 0 or None: fetch ALL orders (no date filter)
            status_filter: Optional filter by fulfillment status
                          (NOT_STARTED, IN_PROGRESS, FULFILLED)

        Returns:
            Statistics dict:
            {
                "created": int,        # New orders created
                "updated": int,        # Existing orders updated
                "skipped": int,        # Orders skipped (unchanged)
                "errors": int,         # Number of errors
                "total_fetched": int,  # Total orders fetched from eBay
                "details": [           # Per-order details
                    {
                        "order_id": str,
                        "action": "created|updated|skipped|error",
                        "error": str (if action == "error")
                    }
                ]
            }

        Raises:
            ValueError: If modified_since_hours out of range
        """
        start_time = datetime.now(timezone.utc)

        # 1. Validate parameters
        sync_all = self._validate_sync_parameters(modified_since_hours)

        logger.info(
            f"[EbayOrderSyncService] Starting sync: user_id={self.user_id}, "
            f"hours={modified_since_hours if not sync_all else 'ALL'}, status_filter={status_filter}"
        )

        try:
            # 2. Fetch orders from eBay API
            api_orders = self._fetch_orders_from_ebay(sync_all, modified_since_hours, status_filter)

            logger.info(
                f"[EbayOrderSyncService] Fetched {len(api_orders)} orders from eBay API"
            )

            # 3. Process orders batch and collect statistics
            stats = self._process_orders_batch(api_orders)
            stats["total_fetched"] = len(api_orders)

            # 4. Commit and log summary
            self._finalize_sync(start_time, stats)

        except Exception as e:
            self.db.rollback()
            logger.error(
                f"[EbayOrderSyncService] Sync failed for user {self.user_id}: {e}",
                exc_info=True,
            )
            raise

        return stats



    def _process_single_order(self, api_order: dict) -> dict:
        """
        Process a single order from eBay API.

        Args:
            api_order: Order dict from eBay Fulfillment API

        Returns:
            Result dict: {"order_id": str, "action": "created|updated|skipped"}

        Raises:
            Exception: If processing fails
        """
        order_id = api_order.get("orderId")

        if not order_id:
            raise ValueError("Order missing orderId field")

        logger.debug(f"[EbayOrderSyncService] Processing order: {order_id}")

        # Check if order already exists
        existing_order = EbayOrderRepository.get_by_ebay_order_id(self.db, order_id)

        # Map API data to model fields
        order_data = self._map_api_order_to_model(api_order)

        if existing_order:
            # Update existing order
            for key, value in order_data.items():
                setattr(existing_order, key, value)

            existing_order.updated_at = datetime.now(timezone.utc)

            EbayOrderRepository.update(self.db, existing_order)

            # Update line items (simple approach: delete and recreate)
            # Delete existing products
            for product in existing_order.products:
                self.db.delete(product)

            # Create new products
            line_items = api_order.get("lineItems", [])
            new_products = self._map_line_items(line_items, order_id)

            for product in new_products:
                EbayOrderRepository.create_order_product(self.db, product)

            action = "updated"

        else:
            # Create new order
            new_order = EbayOrder(**order_data)
            created_order = EbayOrderRepository.create(self.db, new_order)

            # Create line items
            line_items = api_order.get("lineItems", [])
            products = self._map_line_items(line_items, order_id)

            for product in products:
                EbayOrderRepository.create_order_product(self.db, product)

            action = "created"

        logger.debug(
            f"[EbayOrderSyncService] Order {order_id} {action} successfully"
        )

        return {"order_id": order_id, "action": action}

    def _map_api_order_to_model(self, api_order: dict) -> dict:
        """
        Map eBay API order data to EbayOrder model fields.

        Args:
            api_order: Order dict from eBay Fulfillment API

        Returns:
            Dict of fields for EbayOrder constructor
        """
        # Extract buyer info
        buyer = api_order.get("buyer", {})
        buyer_username = buyer.get("username")
        buyer_email = buyer.get("taxAddress", {}).get("email")

        # Extract shipping address from fulfillmentStartInstructions
        fulfillment_instructions = api_order.get("fulfillmentStartInstructions", [])
        shipping_info = {}

        if fulfillment_instructions:
            first_instruction = fulfillment_instructions[0]
            shipping_step = first_instruction.get("shippingStep", {})
            ship_to = shipping_step.get("shipTo", {})
            contact_address = ship_to.get("contactAddress", {})

            shipping_info = {
                "shipping_name": ship_to.get("fullName"),
                "shipping_address": self._format_address(contact_address),
                "shipping_city": contact_address.get("city"),
                "shipping_postal_code": contact_address.get("postalCode"),
                "shipping_country": contact_address.get("countryCode"),
            }

        # Extract pricing info
        pricing_summary = api_order.get("pricingSummary", {})
        total = pricing_summary.get("total", {})
        delivery_cost = pricing_summary.get("deliveryCost", {})

        # Parse dates
        creation_date = self._parse_date(api_order.get("creationDate"))
        paid_date = self._parse_date(api_order.get("paidDate"))

        # Build order data
        order_data = {
            "order_id": api_order.get("orderId"),
            "marketplace_id": api_order.get("listingMarketplaceId"),
            "buyer_username": buyer_username,
            "buyer_email": buyer_email,
            "total_price": self._parse_float(total.get("value")),
            "currency": total.get("currency"),
            "shipping_cost": self._parse_float(delivery_cost.get("value")),
            "order_fulfillment_status": api_order.get("orderFulfillmentStatus"),
            "order_payment_status": api_order.get("orderPaymentStatus"),
            "creation_date": creation_date,
            "paid_date": paid_date,
            **shipping_info,
        }

        return order_data

    def _map_line_items(
        self, line_items: List[dict], order_id: str
    ) -> List[EbayOrderProduct]:
        """
        Map eBay lineItems to EbayOrderProduct models.

        Args:
            line_items: List of lineItem dicts from eBay API
            order_id: eBay order ID

        Returns:
            List of EbayOrderProduct instances
        """
        products = []

        for item in line_items:
            # Extract SKU info
            sku = item.get("sku")
            legacy_item_id = item.get("legacyItemId")

            # Derive sku_original from sku (format: "12345-FR" -> "12345")
            sku_original = None
            if sku and "-" in sku:
                sku_original = sku.split("-")[0]

            # Extract pricing
            line_item_cost = item.get("lineItemCost", {})
            total = item.get("total", {})

            product = EbayOrderProduct(
                order_id=order_id,
                line_item_id=item.get("lineItemId"),
                sku=sku,
                sku_original=sku_original,
                title=item.get("title"),
                quantity=item.get("quantity", 1),
                unit_price=self._parse_float(line_item_cost.get("value")),
                total_price=self._parse_float(total.get("value")),
                currency=line_item_cost.get("currency"),
                legacy_item_id=legacy_item_id,
            )

            products.append(product)

        return products

    # =============================================================================
    # Helper Methods
    # =============================================================================

    @staticmethod
    def _format_address(contact_address: dict) -> Optional[str]:
        """
        Format contact address into single string.

        Args:
            contact_address: Dict with addressLine1, addressLine2, etc.

        Returns:
            Formatted address string or None
        """
        if not contact_address:
            return None

        lines = []

        if address_line1 := contact_address.get("addressLine1"):
            lines.append(address_line1)

        if address_line2 := contact_address.get("addressLine2"):
            lines.append(address_line2)

        return ", ".join(lines) if lines else None

    @staticmethod
    def _parse_date(date_str: Optional[str]) -> Optional[datetime]:
        """
        Parse ISO 8601 date string to datetime.

        Args:
            date_str: ISO 8601 date string (e.g., "2024-12-10T10:30:00.000Z")

        Returns:
            Datetime object or None
        """
        if not date_str:
            return None

        try:
            # Parse ISO 8601 format
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            logger.warning(
                f"[EbayOrderSyncService] Failed to parse date: {date_str}"
            )
            return None

    @staticmethod
    def _parse_float(value_str: Optional[str]) -> Optional[float]:
        """
        Parse string value to float.

        Args:
            value_str: String representation of float (e.g., "50.00")

        Returns:
            Float value or None
        """
        if not value_str:
            return None

        try:
            return float(value_str)
        except (ValueError, TypeError):
            logger.warning(
                f"[EbayOrderSyncService] Failed to parse float: {value_str}"
            )
            return None
