"""
Vinted Order Sync Service - Synchronisation des commandes Vinted

Service dedie a la synchronisation des commandes depuis l'API Vinted.

Methodes disponibles:
- sync_orders(): DEFAULT - Sync via /my_orders (captures ALL orders)
- sync_orders_by_month(): OPTIONAL - Sync via /wallet/invoices (wallet only)

sync_orders() is the default because /wallet/invoices only shows wallet
transactions, not direct card payments.

Author: Claude
Date: 2025-12-17
Updated: 2026-01-13 - Restauration sync_orders() comme methode par defaut
"""

from typing import Any

from sqlalchemy.orm import Session

from models.vinted.vinted_order import VintedOrder, VintedOrderProduct
from services.plugin_websocket_helper import PluginWebSocketHelper  # WebSocket architecture (2026-01-12)
from services.vinted.vinted_data_extractor import VintedDataExtractor
from shared.schema_utils import SchemaManager, commit_and_restore_path
from shared.vinted_constants import VintedOrderAPI, VintedConversationAPI
from shared.logging_setup import get_logger
from shared.config import settings

logger = get_logger(__name__)

# Entity types for invoice filtering
# Note: Vinted uses "user_msg_thread" for sales, with title="Vente"
ENTITY_TYPE_THREAD = "user_msg_thread"
TITLE_VENTE = "Vente"


class VintedOrderSyncService:
    """
    Service de synchronisation des commandes Vinted.

    Utilise /wallet/invoices pour recuperer les commandes avec le prix reel.
    """

    def __init__(self, user_id: int | None = None):
        """
        Initialize VintedOrderSyncService.

        Args:
            user_id: ID utilisateur (requis pour WebSocket) (2026-01-12)
        """
        self.user_id = user_id
        self.extractor = VintedDataExtractor()
        self._schema_manager = SchemaManager()

    def _order_exists(self, db: Session, transaction_id: int) -> bool:
        """Check if order already exists in database."""
        return db.query(VintedOrder).filter(
            VintedOrder.transaction_id == transaction_id
        ).first() is not None

    # =========================================================================
    # SYNC BY MONTH (via /wallet/invoices + /conversations)
    # =========================================================================


    # ===== HELPER METHODS FOR sync_orders_by_month() (Refactored 2026-01-12 Phase 3.2) =====

    async def _fetch_invoices_page(
        self, db: Session, year: int, month: int, page: int
    ) -> dict | None:
        """Fetch single page of invoices. Returns None on error."""
        try:
            result = await PluginWebSocketHelper.call_plugin_http(
                db=db,
                user_id=self.user_id,
                http_method="GET",
                path=VintedOrderAPI.get_wallet_invoices(year, month, page),
                timeout=settings.plugin_timeout_order,
                description=f"Sync invoices {year}-{month:02d} page {page}"
            )
            return result
        except Exception as e:
            logger.error(f"Erreur invoices p{page}: {type(e).__name__}: {e}")
            return None

    @staticmethod
    def _extract_invoice_pricing(line: dict) -> tuple[float | None, str]:
        """Extract invoice price and currency from invoice line."""
        invoice_amount = line.get('amount', {})
        invoice_price = None
        invoice_currency = 'EUR'

        if isinstance(invoice_amount, dict):
            try:
                invoice_price = float(invoice_amount.get('amount', 0))
            except (ValueError, TypeError):
                pass
            invoice_currency = invoice_amount.get('currency_code', 'EUR')

        return invoice_price, invoice_currency

    async def _fetch_transaction_id_from_conversation(
        self, db: Session, conversation_id: int
    ) -> int | None:
        """
        Fetch transaction_id from conversation (1 API call).

        Returns:
            transaction_id or None on error
        """
        try:
            conv_result = await PluginWebSocketHelper.call_plugin_http(
                db=db,
                user_id=self.user_id,
                http_method="GET",
                path=VintedConversationAPI.get_conversation(conversation_id),
                timeout=settings.plugin_timeout_order,
                description=f"Get conversation {conversation_id}"
            )

            conversation = conv_result.get('conversation', {})
            conv_transaction = conversation.get('transaction', {})
            transaction_id = conv_transaction.get('id')

            if not transaction_id:
                logger.warning(f"Conv {conversation_id}: pas de transaction_id")
                return None

            return transaction_id

        except Exception as e:
            logger.error(f"Erreur conv {conversation_id}: {type(e).__name__}: {e}")
            return None

    async def _fetch_transaction_details(
        self, db: Session, transaction_id: int
    ) -> dict | None:
        """
        Fetch full transaction details (1 API call).

        Only call this AFTER checking for duplicates to save API calls.

        Returns:
            Transaction dict or None on error
        """
        try:
            tx_result = await PluginWebSocketHelper.call_plugin_http(
                db=db,
                user_id=self.user_id,
                http_method="GET",
                path=VintedOrderAPI.get_transaction(transaction_id),
                timeout=settings.plugin_timeout_order,
                description=f"Get transaction details {transaction_id}"
            )

            transaction = tx_result.get('transaction', {})

            if not transaction.get('id'):
                logger.warning(f"  [WARN] TX {transaction_id}: transaction dict has no 'id' field")
                return None

            return transaction

        except Exception as e:
            logger.error(f"Erreur tx {transaction_id}: {type(e).__name__}: {e}")
            return None

    def _process_and_save_order(
        self, db: Session, transaction: dict, invoice_price: float | None, invoice_currency: str
    ) -> bool:
        """
        Extract order data and save to DB.

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            order_data = self._extract_order_from_transaction(
                transaction, invoice_price, invoice_currency
            )
            products_data = self._extract_products_from_transaction(transaction)

            if order_data:
                self._save_order(db, order_data, products_data)
                commit_and_restore_path(db)
                logger.info(f"  [OK] Saved order #{order_data['transaction_id']}")
                return True

            # Debug: Log why extraction failed
            tx_id = transaction.get('id') if isinstance(transaction, dict) else None
            logger.warning(f"  [SKIP] Transaction {tx_id}: extraction returned None")
            logger.debug(f"  [DEBUG] Transaction keys: {list(transaction.keys()) if isinstance(transaction, dict) else type(transaction)}")
            return False

        except Exception as e:
            logger.error(f"Erreur save order: {type(e).__name__}: {e}")
            db.rollback()
            self._schema_manager.restore_after_rollback(db)
            logger.debug(f"Search path restored to {self._schema_manager.schema}")
            return False


    async def sync_orders_by_month(self, db: Session, year: int, month: int) -> dict[str, Any]:
        """
        Synchronise les commandes d'un mois (refactored 2026-01-12).

        Flow:
        1. GET /wallet/invoices/{year}/{month} (paginated)
        2. Filter entity_type = "order" or "sale"
        3. GET /conversations/{entity_id} + /transactions/{id}
        4. Save with invoice pricing (real amount)

        Returns:
            {"synced": int, "duplicates": int, "errors": int, "pages": int, "month": str}
        """
        month_str = f"{year}-{month:02d}"
        logger.info(f"Sync commandes: {month_str}")

        self._schema_manager.capture(db)
        stats = {"synced": 0, "duplicates": 0, "errors": 0, "pages": 0}
        processed_ids = set()
        page = 1

        while True:
            # Fetch invoices page
            result = await self._fetch_invoices_page(db, year, month, page)
            if not result:
                break

            invoice_lines = result.get('invoice_lines', [])
            if not invoice_lines:
                logger.info(f"  Page {page}: aucune ligne")
                break

            # Log page stats
            sales_count = sum(
                1 for line in invoice_lines
                if line.get('entity_type') == ENTITY_TYPE_THREAD
                and line.get('title') == TITLE_VENTE
            )
            logger.info(f"  Page {page}: {len(invoice_lines)} lignes, {sales_count} ventes")

            # Process each sale
            for line in invoice_lines:
                entity_type = line.get('entity_type')
                title = line.get('title', '')
                conversation_id = line.get('entity_id')

                # Filter: only sales (entity_type=user_msg_thread + title=Vente)
                if entity_type != ENTITY_TYPE_THREAD or title != TITLE_VENTE:
                    continue
                if not conversation_id or conversation_id in processed_ids:
                    continue

                processed_ids.add(conversation_id)

                # Step 1: Get transaction_id from conversation (1 API call)
                transaction_id = await self._fetch_transaction_id_from_conversation(
                    db, conversation_id
                )

                if not transaction_id:
                    stats["errors"] += 1
                    continue

                # Step 2: Check duplicate BEFORE fetching transaction details
                # This saves 1 API call per duplicate!
                if self._order_exists(db, transaction_id):
                    stats["duplicates"] += 1
                    logger.debug(f"  [SKIP] TX {transaction_id} already exists (saved 1 API call)")
                    continue

                # Step 3: Only fetch transaction details if not a duplicate (1 API call)
                transaction = await self._fetch_transaction_details(db, transaction_id)

                if not transaction:
                    stats["errors"] += 1
                    continue

                # Step 4: Extract invoice pricing and save
                invoice_price, invoice_currency = self._extract_invoice_pricing(line)

                if self._process_and_save_order(db, transaction, invoice_price, invoice_currency):
                    stats["synced"] += 1
                else:
                    stats["errors"] += 1

            # Pagination check
            pagination = result.get('invoice_lines_pagination', {})
            if page >= pagination.get('total_pages', 1):
                break
            page += 1

        stats["pages"] = page
        stats["month"] = month_str
        logger.info(
            f"Sync {month_str}: {stats['synced']} new, "
            f"{stats['duplicates']} dup, {stats['errors']} err"
        )
        return stats

    # =========================================================================
    # SYNC CLASSIC (via /my_orders - DEFAULT)
    # =========================================================================

    async def sync_orders(self, db: Session) -> dict[str, Any]:
        """
        Synchronise les commandes vendues depuis /my_orders (default method).

        Flow:
        1. GET /my_orders?type=sold&status=completed (paginated)
        2. For each order, check if exists (duplicate)
        3. If not duplicate, GET /transactions/{id} for details
        4. Save order with products

        This method captures ALL completed orders, including direct card payments.
        Use sync_orders_by_month() only for wallet/invoice-specific data.

        Returns:
            {"synced": int, "duplicates": int, "errors": int, "pages": int}
        """
        logger.info("Sync commandes (via /my_orders)")

        self._schema_manager.capture(db)
        stats = {"synced": 0, "duplicates": 0, "errors": 0, "pages": 0}
        page = 1

        while True:
            # Fetch orders page
            result = await self._fetch_orders_page(db, page)
            if not result:
                break

            orders = result.get('my_orders', [])
            if not orders:
                logger.info(f"  Page {page}: no orders")
                break

            logger.info(f"  Page {page}: {len(orders)} orders")

            # Process each order
            for order in orders:
                transaction_id = order.get('transaction_id')

                if not transaction_id:
                    logger.warning("  [SKIP] Order without transaction_id")
                    stats["errors"] += 1
                    continue

                # Check duplicate BEFORE fetching transaction details
                if self._order_exists(db, transaction_id):
                    stats["duplicates"] += 1
                    logger.debug(f"  [SKIP] TX {transaction_id} already exists")
                    continue

                # Fetch transaction details (1 API call)
                transaction = await self._fetch_transaction_details(db, transaction_id)

                if not transaction:
                    stats["errors"] += 1
                    continue

                # Save order (no invoice pricing for classic sync)
                if self._process_and_save_order(db, transaction, None, 'EUR'):
                    stats["synced"] += 1
                else:
                    stats["errors"] += 1

            # Pagination check
            pagination = result.get('pagination', {})
            total_pages = pagination.get('total_pages', 1)
            if page >= total_pages:
                break
            page += 1

        stats["pages"] = page
        logger.info(
            f"Sync orders: {stats['synced']} new, "
            f"{stats['duplicates']} dup, {stats['errors']} err"
        )
        return stats

    async def _fetch_orders_page(
        self, db: Session, page: int
    ) -> dict | None:
        """Fetch single page of sold orders (status=all). Returns None on error."""
        try:
            result = await PluginWebSocketHelper.call_plugin_http(
                db=db,
                user_id=self.user_id,
                http_method="GET",
                path=VintedOrderAPI.get_orders(
                    order_type="sold",
                    status="all",
                    page=page,
                    per_page=20
                ),
                timeout=settings.plugin_timeout_order,
                description=f"Sync orders page {page}"
            )
            return result
        except Exception as e:
            logger.error(f"Erreur orders p{page}: {type(e).__name__}: {e}")
            return None


    # =========================================================================
    # DATA EXTRACTION (from /transactions/{id} response)
    # =========================================================================

    def _extract_order_from_transaction(
        self,
        transaction: dict,
        invoice_price: float | None,
        invoice_currency: str
    ) -> dict | None:
        """
        Extract order data from transaction response.

        Args:
            transaction: Transaction dict from /transactions/{id} API
            invoice_price: Real amount from invoice (seller_revenue)
            invoice_currency: Currency code

        Returns:
            Order data dict or None
        """
        try:
            transaction_id = transaction.get('id')
            if not transaction_id:
                return None

            # Buyer and seller info
            buyer = transaction.get('buyer', {}) or {}
            seller = transaction.get('seller', {}) or {}

            # Shipment info (tracking, carrier, shipping dates)
            shipment = transaction.get('shipment', {}) or {}
            shipment_status = shipment.get('status', 0)

            # Prices from offer
            offer = transaction.get('offer', {}) or {}
            offer_price = offer.get('price', {})
            total_price = self._parse_amount(offer_price)

            # Shipping price from shipment
            shipping_price = self._parse_amount(shipment.get('price'))

            # Service fee
            service_fee = self._parse_amount(transaction.get('service_fee'))

            # Buyer protection fee from offer
            buyer_protection_fee = self._parse_amount(offer.get('buyer_protection_fee'))

            # Tracking info from shipment
            tracking_number = shipment.get('tracking_code')
            carrier = shipment.get('carrier_name') or shipment.get('carrier')

            # Status mapping: >= 400 = completed
            status_code = transaction.get('status', 0)
            status = 'completed' if status_code >= 400 else 'pending'

            # Dates based on shipment status
            # 200+ = shipped, 400+ = delivered
            shipped_at = None
            delivered_at = None
            if shipment_status >= 200:
                shipped_at = shipment.get('shipped_at') or shipment.get('status_updated_at')
            if shipment_status >= 400:
                delivered_at = shipment.get('delivered_at') or shipment.get('status_updated_at')

            return {
                'transaction_id': int(transaction_id),
                'buyer_id': buyer.get('id'),
                'buyer_login': buyer.get('login'),
                'seller_id': seller.get('id'),
                'seller_login': seller.get('login'),
                'status': status,
                'total_price': total_price,
                'currency': invoice_currency,
                'shipping_price': shipping_price,
                'service_fee': service_fee,
                'buyer_protection_fee': buyer_protection_fee,
                'seller_revenue': invoice_price,
                'tracking_number': tracking_number,
                'carrier': carrier,
                'created_at_vinted': transaction.get('debit_processed_at'),
                'shipped_at': shipped_at,
                'delivered_at': delivered_at,
                'completed_at': transaction.get('status_updated_at')
            }
        except (ValueError, KeyError, TypeError):
            return None

    def _extract_products_from_transaction(self, transaction: dict) -> list[dict]:
        """
        Extract products from transaction response.

        Handles both single items and bundles (order.items[]).

        Args:
            transaction: Transaction dict from /transactions/{id} API

        Returns:
            List of product dicts
        """
        products = []
        transaction_id = transaction.get('id')
        if not transaction_id:
            return products

        try:
            # Get items from order (works for bundles)
            order = transaction.get('order', {}) or {}
            items = order.get('items', [])

            if items:
                # Bundle or single item with order.items
                for item in items:
                    photos = item.get('photos', [])
                    photo_url = photos[0].get('url') if photos else None
                    price = self._parse_amount(item.get('price'))

                    # Brand from brand_title or brand object
                    brand = item.get('brand_title')
                    if not brand:
                        brand_obj = item.get('brand', {}) or {}
                        brand = brand_obj.get('title') or brand_obj.get('name')

                    products.append({
                        'transaction_id': transaction_id,
                        'vinted_item_id': item.get('id'),
                        'product_id': None,
                        'title': item.get('title'),
                        'price': price,
                        'size': item.get('size_title'),
                        'brand': brand,
                        'photo_url': photo_url
                    })
            else:
                # Fallback: single item without order.items
                item_id = transaction.get('item_id')
                if item_id:
                    products.append({
                        'transaction_id': transaction_id,
                        'vinted_item_id': item_id,
                        'product_id': None,
                        'title': transaction.get('item_title'),
                        'price': None,
                        'size': None,
                        'brand': None,
                        'photo_url': None
                    })
        except (ValueError, KeyError, TypeError):
            pass

        return products

    def _parse_amount(self, price_obj: dict | str | None) -> float | None:
        """Parse price amount from various formats."""
        if price_obj is None:
            return None
        if isinstance(price_obj, dict):
            try:
                return float(price_obj.get('amount', 0))
            except (ValueError, TypeError):
                return None
        if isinstance(price_obj, str):
            try:
                return float(price_obj)
            except (ValueError, TypeError):
                return None
        return None

    # =========================================================================
    # DATABASE SAVE
    # =========================================================================

    def _save_order(
        self,
        db: Session,
        order_data: dict,
        products_data: list[dict]
    ) -> None:
        """
        Save order and products to database.

        Args:
            db: SQLAlchemy session
            order_data: Order data dict
            products_data: List of product dicts
        """
        vinted_order = VintedOrder(
            transaction_id=order_data['transaction_id'],
            buyer_id=order_data.get('buyer_id'),
            buyer_login=order_data.get('buyer_login'),
            seller_id=order_data.get('seller_id'),
            seller_login=order_data.get('seller_login'),
            status=order_data.get('status'),
            total_price=order_data.get('total_price'),
            currency=order_data.get('currency', 'EUR'),
            shipping_price=order_data.get('shipping_price'),
            service_fee=order_data.get('service_fee'),
            buyer_protection_fee=order_data.get('buyer_protection_fee'),
            seller_revenue=order_data.get('seller_revenue'),
            tracking_number=order_data.get('tracking_number'),
            carrier=order_data.get('carrier'),
            # shipping_tracking_code: deprecated, use tracking_number
            created_at_vinted=VintedDataExtractor.parse_date(
                order_data.get('created_at_vinted')
            ),
            shipped_at=VintedDataExtractor.parse_date(order_data.get('shipped_at')),
            delivered_at=VintedDataExtractor.parse_date(order_data.get('delivered_at')),
            completed_at=VintedDataExtractor.parse_date(order_data.get('completed_at'))
        )
        db.add(vinted_order)

        for prod in products_data:
            order_product = VintedOrderProduct(
                transaction_id=prod['transaction_id'],
                vinted_item_id=prod.get('vinted_item_id'),
                product_id=prod.get('product_id'),
                title=prod.get('title'),
                price=prod.get('price'),
                size=prod.get('size'),
                brand=prod.get('brand'),
                photo_url=prod.get('photo_url')
            )
            db.add(order_product)
