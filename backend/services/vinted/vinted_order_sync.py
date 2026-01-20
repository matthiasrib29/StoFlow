"""
Vinted Order Sync Service - Synchronisation des commandes Vinted

Service dedie a la synchronisation des commandes depuis l'API Vinted.

Methodes disponibles:
- sync_orders(): DEFAULT - Sync VENTES via /my_orders?type=sold
- sync_purchases(): Sync ACHATS via /my_orders?type=purchased
- sync_orders_by_month(): OPTIONAL - Sync via /wallet/invoices (wallet only)

sync_orders() is the default because /wallet/invoices only shows wallet
transactions, not direct card payments.

API endpoint: GET /api/v2/my_orders?type={sold|purchased}&status=all&per_page=100&page=X

Author: Claude
Date: 2025-12-17
Updated: 2026-01-13 - Restauration sync_orders() comme methode par defaut
Updated: 2026-01-20 - Ajout sync_purchases() pour les achats, per_page=100
"""

from typing import Any

from sqlalchemy.orm import Session

from models.vinted.vinted_order import VintedOrder, VintedOrderProduct
from services.plugin_websocket_helper import PluginWebSocketHelper  # WebSocket architecture (2026-01-12)
from services.vinted.vinted_data_extractor import VintedDataExtractor
from shared.vinted import VintedOrderAPI, VintedConversationAPI
from shared.logging import get_logger
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
                db.commit()
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
            # schema_translate_map survives rollback - no need to restore
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
        Synchronise les VENTES depuis /my_orders?type=sold.

        Flow (2-step approach):
        1. GET /api/v2/my_orders?type=sold&status=all&per_page=100 (paginated)
        2. For each order:
           - If NEW: create from /my_orders + enrich with /transactions/{id}
           - If EXISTING + NOT completed: update status + re-enrich with /transactions/{id}
           - If EXISTING + completed: just update status (no API call needed)

        Re-enrichment for non-completed orders captures evolving data:
        - Shipment info (tracking_number, carrier, shipment_id)
        - Dates (shipped_at, delivered_at, completed_at)
        - Status codes and text

        Returns:
            {"synced": int, "updated": int, "enriched": int, "errors": int, "pages": int}
        """
        logger.info("Sync ventes (via /my_orders?type=sold)")

        stats = {"synced": 0, "updated": 0, "enriched": 0, "errors": 0, "pages": 0}
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
            for order_data in orders:
                transaction_id = order_data.get('transaction_id')

                if not transaction_id:
                    logger.warning("  [SKIP] Order without transaction_id")
                    stats["errors"] += 1
                    continue

                # Check if order already exists
                existing_order = self._get_order(db, transaction_id)

                if existing_order:
                    # UPDATE existing order with fresh status from /my_orders
                    status_changed = self._update_order_from_my_orders(db, existing_order, order_data)

                    # Re-enrich non-completed orders to track evolution
                    if existing_order.transaction_user_status != 'completed':
                        transaction = await self._fetch_transaction_details(db, transaction_id)
                        if transaction:
                            self._enrich_order_from_transaction(db, existing_order, transaction)
                            db.commit()
                            stats["enriched"] += 1
                            logger.debug(f"  [ENRICH] TX {transaction_id} re-enriched (status: {existing_order.transaction_user_status})")
                    elif status_changed:
                        stats["updated"] += 1
                        logger.debug(f"  [UPDATE] TX {transaction_id} status updated")
                    continue

                # NEW order: First save basic data, then enrich with /transactions
                # Step 1: Create basic order from /my_orders data
                basic_order = self._create_order_from_my_orders(db, order_data)
                if not basic_order:
                    stats["errors"] += 1
                    continue

                # Step 2: Enrich with /transactions/{id} for full details
                transaction = await self._fetch_transaction_details(db, transaction_id)
                if transaction:
                    self._enrich_order_from_transaction(db, basic_order, transaction)

                db.commit()
                stats["synced"] += 1
                logger.info(f"  [NEW] TX {transaction_id} saved")

            # Pagination check
            pagination = result.get('pagination', {})
            total_pages = pagination.get('total_pages', 1)
            if page >= total_pages:
                break
            page += 1

        stats["pages"] = page
        logger.info(
            f"Sync ventes: {stats['synced']} new, "
            f"{stats['updated']} updated, {stats['enriched']} enriched, {stats['errors']} err"
        )
        return stats

    async def sync_purchases(self, db: Session) -> dict[str, Any]:
        """
        Synchronise les ACHATS depuis /my_orders?type=purchased.

        Flow (2-step approach):
        1. GET /api/v2/my_orders?type=purchased&status=all&per_page=100 (paginated)
        2. For each order:
           - If NEW: create from /my_orders + enrich with /transactions/{id}
           - If EXISTING + NOT completed: update status + re-enrich with /transactions/{id}
           - If EXISTING + completed: just update status (no API call needed)

        Re-enrichment for non-completed orders captures evolving data:
        - Shipment info (tracking_number, carrier, shipment_id)
        - Dates (shipped_at, delivered_at, completed_at)
        - Status codes and text

        Returns:
            {"synced": int, "updated": int, "enriched": int, "errors": int, "pages": int}
        """
        logger.info("Sync achats (via /my_orders?type=purchased)")

        stats = {"synced": 0, "updated": 0, "enriched": 0, "errors": 0, "pages": 0}
        page = 1

        while True:
            # Fetch purchases page
            result = await self._fetch_orders_page(db, page, order_type="purchased")
            if not result:
                break

            orders = result.get('my_orders', [])
            if not orders:
                logger.info(f"  Page {page}: no purchases")
                break

            logger.info(f"  Page {page}: {len(orders)} purchases")

            # Process each purchase
            for order_data in orders:
                transaction_id = order_data.get('transaction_id')

                if not transaction_id:
                    logger.warning("  [SKIP] Purchase without transaction_id")
                    stats["errors"] += 1
                    continue

                # Check if order already exists
                existing_order = self._get_order(db, transaction_id)

                if existing_order:
                    # UPDATE existing order with fresh status
                    status_changed = self._update_order_from_my_orders(db, existing_order, order_data)

                    # Re-enrich non-completed orders to track evolution
                    if existing_order.transaction_user_status != 'completed':
                        transaction = await self._fetch_transaction_details(db, transaction_id)
                        if transaction:
                            self._enrich_order_from_transaction(db, existing_order, transaction)
                            db.commit()
                            stats["enriched"] += 1
                            logger.debug(f"  [ENRICH] TX {transaction_id} re-enriched (status: {existing_order.transaction_user_status})")
                    elif status_changed:
                        stats["updated"] += 1
                        logger.debug(f"  [UPDATE] TX {transaction_id} status updated")
                    continue

                # NEW purchase: First save basic data, then enrich with /transactions
                basic_order = self._create_order_from_my_orders(db, order_data)
                if not basic_order:
                    stats["errors"] += 1
                    continue

                # Enrich with /transactions/{id} for full details
                transaction = await self._fetch_transaction_details(db, transaction_id)
                if transaction:
                    self._enrich_order_from_transaction(db, basic_order, transaction)

                db.commit()
                stats["synced"] += 1
                logger.info(f"  [NEW] TX {transaction_id} saved (purchase)")

            # Pagination check
            pagination = result.get('pagination', {})
            total_pages = pagination.get('total_pages', 1)
            if page >= total_pages:
                break
            page += 1

        stats["pages"] = page
        logger.info(
            f"Sync achats: {stats['synced']} new, "
            f"{stats['updated']} updated, {stats['enriched']} enriched, {stats['errors']} err"
        )
        return stats

    def _get_order(self, db: Session, transaction_id: int) -> VintedOrder | None:
        """Get existing order by transaction_id."""
        return db.query(VintedOrder).filter(
            VintedOrder.transaction_id == transaction_id
        ).first()

    def _create_order_from_my_orders(
        self, db: Session, order_data: dict
    ) -> VintedOrder | None:
        """
        Create order with data from /my_orders response.

        API fields captured:
        - transaction_id (PK)
        - conversation_id
        - title -> VintedOrderProduct.title
        - price.amount -> total_price
        - price.currency_code -> currency
        - status -> vinted_status_text
        - date -> created_at_vinted
        - photo.url -> VintedOrderProduct.photo_url
        - transaction_user_status
        """
        try:
            transaction_id = order_data.get('transaction_id')
            if not transaction_id:
                return None

            # Extract conversation_id
            conversation_id = order_data.get('conversation_id')

            # Extract price
            price_obj = order_data.get('price', {})
            total_price = self._parse_amount(price_obj)
            currency = price_obj.get('currency_code', 'EUR')

            # Extract status (transaction_user_status is more reliable)
            # needs_action, waiting, completed, failed
            user_status = order_data.get('transaction_user_status', '')
            status_text = order_data.get('status', '')  # Full text like "Commande finalisée..."

            # Map to our internal status
            if user_status == 'completed':
                status = 'completed'
            elif user_status == 'failed':
                status = 'refunded'
            else:
                status = 'pending'

            # Parse date
            date_str = order_data.get('date')
            created_at_vinted = VintedDataExtractor.parse_date(date_str)

            # Extract photo URL
            photo = order_data.get('photo', {}) or {}
            photo_url = photo.get('url')

            # Create order with all data from /my_orders
            vinted_order = VintedOrder(
                transaction_id=int(transaction_id),
                conversation_id=conversation_id,
                status=status,
                vinted_status_text=status_text,  # Store full status text from API
                transaction_user_status=user_status,
                total_price=total_price,
                currency=currency,
                created_at_vinted=created_at_vinted,
            )
            db.add(vinted_order)

            # Create single product with basic info from /my_orders
            title = order_data.get('title', '')
            if title:
                order_product = VintedOrderProduct(
                    transaction_id=int(transaction_id),
                    title=title,
                    price=total_price,
                    photo_url=photo_url
                )
                db.add(order_product)

            return vinted_order

        except Exception as e:
            logger.error(f"Error creating order from my_orders: {e}")
            db.rollback()
            return None

    def _update_order_from_my_orders(
        self, db: Session, order: VintedOrder, order_data: dict
    ) -> bool:
        """
        Update existing order with fresh data from /my_orders.

        Updates: status, vinted_status_text, transaction_user_status
        """
        try:
            # Extract status
            user_status = order_data.get('transaction_user_status', '')
            status_text = order_data.get('status', '')

            if user_status == 'completed':
                new_status = 'completed'
            elif user_status == 'failed':
                new_status = 'refunded'
            else:
                new_status = 'pending'

            # Track if anything changed
            changed = False

            if order.status != new_status:
                order.status = new_status
                changed = True

            if order.transaction_user_status != user_status:
                order.transaction_user_status = user_status
                changed = True

            if order.vinted_status_text != status_text:
                order.vinted_status_text = status_text
                changed = True

            if changed:
                db.commit()

            return changed

        except Exception as e:
            logger.error(f"Error updating order: {e}")
            db.rollback()
            return False

    def _enrich_order_from_transaction(
        self, db: Session, order: VintedOrder, transaction: dict
    ) -> None:
        """
        Enrich order with detailed data from /transactions/{id}.

        Adds: buyer (with photo, country, city, reputation), seller, shipment,
        service_fee, items (for bundles), conversation_id, offer_id, status codes
        """
        try:
            # Vinted IDs
            order.conversation_id = transaction.get('user_msg_thread_id') or transaction.get('msg_thread_id')
            offer = transaction.get('offer', {}) or {}
            order.offer_id = offer.get('id')

            # Status codes
            order.vinted_status_code = transaction.get('status')
            order.vinted_status_text = transaction.get('status_title')

            # Buyer info (extended)
            buyer = transaction.get('buyer', {}) or {}
            order.buyer_id = buyer.get('id')
            order.buyer_login = buyer.get('login')
            order.buyer_country_code = buyer.get('country_code')
            order.buyer_city = buyer.get('city')
            order.buyer_feedback_reputation = buyer.get('feedback_reputation')

            # Buyer photo URL
            buyer_photo = buyer.get('photo', {}) or {}
            order.buyer_photo_url = buyer_photo.get('full_size_url') or buyer_photo.get('url')

            # Seller info
            seller = transaction.get('seller', {}) or {}
            order.seller_id = seller.get('id')
            order.seller_login = seller.get('login')

            # Shipment info
            shipment = transaction.get('shipment', {}) or {}
            order.shipment_id = shipment.get('id')
            order.tracking_number = shipment.get('tracking_code')
            order.carrier = shipment.get('carrier_name') or shipment.get('carrier')

            # Shipment dates
            shipment_status = shipment.get('status', 0)
            if shipment_status >= 200:
                order.shipped_at = VintedDataExtractor.parse_date(
                    shipment.get('shipped_at') or shipment.get('status_updated_at')
                )
            if shipment_status >= 400:
                order.delivered_at = VintedDataExtractor.parse_date(
                    shipment.get('delivered_at') or shipment.get('status_updated_at')
                )

            # Prices from offer
            offer = transaction.get('offer', {}) or {}
            offer_price = offer.get('price', {})
            if offer_price:
                order.total_price = self._parse_amount(offer_price)
                order.currency = offer_price.get('currency_code', order.currency)

            # Shipping price
            order.shipping_price = self._parse_amount(shipment.get('price'))

            # Service fee
            service_fee = transaction.get('service_fee')
            order.service_fee = self._parse_amount(service_fee)

            # Buyer protection fee
            order.buyer_protection_fee = self._parse_amount(
                offer.get('buyer_protection_fee')
            )

            # Status from transaction (more precise)
            status_code = transaction.get('status', 0)
            if status_code >= 400:
                order.status = 'completed'
            order.completed_at = VintedDataExtractor.parse_date(
                transaction.get('status_updated_at')
            )

            # Item count (for bundles)
            order_obj = transaction.get('order', {}) or {}
            items = order_obj.get('items', [])
            order.item_count = len(items) if items else 1

            # Update products for bundles (order.items[])
            self._update_products_from_transaction(db, order.transaction_id, transaction)

        except Exception as e:
            logger.error(f"Error enriching order: {e}")

    def _update_products_from_transaction(
        self, db: Session, transaction_id: int, transaction: dict
    ) -> None:
        """
        Update/create products from transaction order.items[].

        For bundles, this adds all individual items.
        """
        try:
            order_obj = transaction.get('order', {}) or {}
            items = order_obj.get('items', [])

            if not items:
                return

            # Delete existing products (they were created with basic info)
            db.query(VintedOrderProduct).filter(
                VintedOrderProduct.transaction_id == transaction_id
            ).delete()

            # Create products from items
            for item in items:
                photos = item.get('photos', [])
                photo_url = photos[0].get('url') if photos else None
                price = self._parse_amount(item.get('price'))

                # Brand
                brand = item.get('brand_title')
                if not brand:
                    brand_obj = item.get('brand', {}) or {}
                    brand = brand_obj.get('title') or brand_obj.get('name')

                order_product = VintedOrderProduct(
                    transaction_id=transaction_id,
                    vinted_item_id=item.get('id'),
                    title=item.get('title'),
                    price=price,
                    size=item.get('size_title'),
                    brand=brand,
                    photo_url=photo_url
                )
                db.add(order_product)

        except Exception as e:
            logger.error(f"Error updating products: {e}")

    async def _fetch_orders_page(
        self, db: Session, page: int, order_type: str = "sold"
    ) -> dict | None:
        """Fetch single page of orders. Returns None on error."""
        try:
            result = await PluginWebSocketHelper.call_plugin_http(
                db=db,
                user_id=self.user_id,
                http_method="GET",
                path=VintedOrderAPI.get_orders(
                    order_type=order_type,
                    status="all",
                    page=page,
                    per_page=100
                ),
                timeout=settings.plugin_timeout_order,
                description=f"Sync {order_type} orders page {page}"
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

            # Buyer and seller info (extended)
            buyer = transaction.get('buyer', {}) or {}
            seller = transaction.get('seller', {}) or {}

            # Buyer photo
            buyer_photo = buyer.get('photo', {}) or {}

            # Shipment info (tracking, carrier, shipping dates)
            shipment = transaction.get('shipment', {}) or {}
            shipment_status = shipment.get('status', 0)

            # Prices from offer
            offer = transaction.get('offer', {}) or {}
            offer_price = offer.get('price', {})
            total_price = self._parse_amount(offer_price)

            # Item count from order.items
            order_obj = transaction.get('order', {}) or {}
            items = order_obj.get('items', [])
            item_count = len(items) if items else 1

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
                # Vinted IDs
                'conversation_id': transaction.get('user_msg_thread_id') or transaction.get('msg_thread_id'),
                'offer_id': offer.get('id'),
                # Buyer info (extended)
                'buyer_id': buyer.get('id'),
                'buyer_login': buyer.get('login'),
                'buyer_photo_url': buyer_photo.get('full_size_url') or buyer_photo.get('url'),
                'buyer_country_code': buyer.get('country_code'),
                'buyer_city': buyer.get('city'),
                'buyer_feedback_reputation': buyer.get('feedback_reputation'),
                # Seller info
                'seller_id': seller.get('id'),
                'seller_login': seller.get('login'),
                # Status
                'status': status,
                'vinted_status_code': status_code,
                'vinted_status_text': transaction.get('status_title'),
                'transaction_user_status': transaction.get('transaction_user_status'),
                # Item count
                'item_count': item_count,
                # Prices
                'total_price': total_price,
                'currency': invoice_currency,
                'shipping_price': shipping_price,
                'service_fee': service_fee,
                'buyer_protection_fee': buyer_protection_fee,
                'seller_revenue': invoice_price,
                # Shipping
                'shipment_id': shipment.get('id'),
                'tracking_number': tracking_number,
                'carrier': carrier,
                # Dates
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
            # Vinted IDs
            conversation_id=order_data.get('conversation_id'),
            offer_id=order_data.get('offer_id'),
            # Buyer info (extended)
            buyer_id=order_data.get('buyer_id'),
            buyer_login=order_data.get('buyer_login'),
            buyer_photo_url=order_data.get('buyer_photo_url'),
            buyer_country_code=order_data.get('buyer_country_code'),
            buyer_city=order_data.get('buyer_city'),
            buyer_feedback_reputation=order_data.get('buyer_feedback_reputation'),
            # Seller info
            seller_id=order_data.get('seller_id'),
            seller_login=order_data.get('seller_login'),
            # Status
            status=order_data.get('status'),
            vinted_status_code=order_data.get('vinted_status_code'),
            vinted_status_text=order_data.get('vinted_status_text'),
            transaction_user_status=order_data.get('transaction_user_status'),
            # Item count
            item_count=order_data.get('item_count', 1),
            # Prices
            total_price=order_data.get('total_price'),
            currency=order_data.get('currency', 'EUR'),
            shipping_price=order_data.get('shipping_price'),
            service_fee=order_data.get('service_fee'),
            buyer_protection_fee=order_data.get('buyer_protection_fee'),
            seller_revenue=order_data.get('seller_revenue'),
            # Shipping
            shipment_id=order_data.get('shipment_id'),
            tracking_number=order_data.get('tracking_number'),
            carrier=order_data.get('carrier'),
            # Dates
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
