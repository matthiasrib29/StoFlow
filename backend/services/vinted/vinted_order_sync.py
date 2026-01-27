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
Updated: 2026-01-27 - Extracted persistence logic to vinted_order_persistence.py
"""

from typing import Any

from sqlalchemy.orm import Session

from models.vinted.vinted_order import VintedOrder
from services.plugin_websocket_helper import PluginWebSocketHelper
from services.vinted.vinted_data_extractor import VintedDataExtractor
from services.vinted.vinted_order_persistence import VintedOrderPersistence
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

    Delegates database persistence to VintedOrderPersistence.
    """

    def __init__(self, user_id: int | None = None):
        self.user_id = user_id
        self.extractor = VintedDataExtractor()
        self.persistence = VintedOrderPersistence()

    # =========================================================================
    # QUERY HELPERS
    # =========================================================================

    @staticmethod
    def _order_exists(db: Session, transaction_id: int) -> bool:
        """Check if order already exists in database."""
        return db.query(VintedOrder).filter(
            VintedOrder.transaction_id == transaction_id
        ).first() is not None

    @staticmethod
    def _get_order(db: Session, transaction_id: int) -> VintedOrder | None:
        """Get existing order by transaction_id."""
        return db.query(VintedOrder).filter(
            VintedOrder.transaction_id == transaction_id
        ).first()

    # =========================================================================
    # API FETCH HELPERS
    # =========================================================================

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
            logger.error(f"Erreur invoices p{page}: {type(e).__name__}: {e}", exc_info=True)
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
        """Fetch transaction_id from conversation (1 API call)."""
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
            logger.error(f"Erreur conv {conversation_id}: {type(e).__name__}: {e}", exc_info=True)
            return None

    async def _fetch_transaction_details(
        self, db: Session, transaction_id: int
    ) -> dict | None:
        """
        Fetch full transaction details (1 API call).

        Only call this AFTER checking for duplicates to save API calls.
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
            logger.error(f"Erreur tx {transaction_id}: {type(e).__name__}: {e}", exc_info=True)
            return None

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
            logger.error(f"Erreur orders p{page}: {type(e).__name__}: {e}", exc_info=True)
            return None

    # =========================================================================
    # SYNC BY MONTH (via /wallet/invoices + /conversations)
    # =========================================================================

    async def sync_orders_by_month(self, db: Session, year: int, month: int) -> dict[str, Any]:
        """
        Synchronise les commandes d'un mois via /wallet/invoices.

        Flow:
        1. GET /wallet/invoices/{year}/{month} (paginated)
        2. Filter entity_type = "user_msg_thread" + title = "Vente"
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
            result = await self._fetch_invoices_page(db, year, month, page)
            if not result:
                break

            invoice_lines = result.get('invoice_lines', [])
            if not invoice_lines:
                logger.info(f"  Page {page}: aucune ligne")
                break

            sales_count = sum(
                1 for line in invoice_lines
                if line.get('entity_type') == ENTITY_TYPE_THREAD
                and line.get('title') == TITLE_VENTE
            )
            logger.info(f"  Page {page}: {len(invoice_lines)} lignes, {sales_count} ventes")

            for line in invoice_lines:
                entity_type = line.get('entity_type')
                title = line.get('title', '')
                conversation_id = line.get('entity_id')

                if entity_type != ENTITY_TYPE_THREAD or title != TITLE_VENTE:
                    continue
                if not conversation_id or conversation_id in processed_ids:
                    continue

                processed_ids.add(conversation_id)

                # Step 1: Get transaction_id from conversation
                transaction_id = await self._fetch_transaction_id_from_conversation(
                    db, conversation_id
                )
                if not transaction_id:
                    stats["errors"] += 1
                    continue

                # Step 2: Check duplicate BEFORE fetching transaction details
                if self._order_exists(db, transaction_id):
                    stats["duplicates"] += 1
                    logger.debug(f"  [SKIP] TX {transaction_id} already exists (saved 1 API call)")
                    continue

                # Step 3: Fetch transaction details
                transaction = await self._fetch_transaction_details(db, transaction_id)
                if not transaction:
                    stats["errors"] += 1
                    continue

                # Step 4: Extract invoice pricing and save
                invoice_price, invoice_currency = self._extract_invoice_pricing(line)

                if self.persistence.process_and_save_order(
                    db, transaction, invoice_price, invoice_currency
                ):
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

        Returns:
            {"synced": int, "updated": int, "enriched": int, "errors": int, "pages": int}
        """
        return await self._sync_orders_by_type(db, order_type="sold", label="ventes")

    async def sync_purchases(self, db: Session) -> dict[str, Any]:
        """
        Synchronise les ACHATS depuis /my_orders?type=purchased.

        Returns:
            {"synced": int, "updated": int, "enriched": int, "errors": int, "pages": int}
        """
        return await self._sync_orders_by_type(db, order_type="purchased", label="achats")

    async def _sync_orders_by_type(
        self, db: Session, order_type: str, label: str
    ) -> dict[str, Any]:
        """
        Shared implementation for sync_orders() and sync_purchases().

        Flow (2-step approach):
        1. GET /api/v2/my_orders?type={order_type}&status=all&per_page=100 (paginated)
        2. For each order:
           - If NEW: create from /my_orders + enrich with /transactions/{id}
           - If EXISTING + NOT completed: update status + re-enrich
           - If EXISTING + completed: just update status

        Args:
            order_type: "sold" or "purchased"
            label: Human-readable label for logs ("ventes" or "achats")
        """
        logger.info(f"Sync {label} (via /my_orders?type={order_type})")

        stats = {"synced": 0, "updated": 0, "enriched": 0, "errors": 0, "pages": 0}
        page = 1

        while True:
            result = await self._fetch_orders_page(db, page, order_type=order_type)
            if not result:
                break

            orders = result.get('my_orders', [])
            if not orders:
                logger.info(f"  Page {page}: no {label}")
                break

            logger.info(f"  Page {page}: {len(orders)} {label}")

            for order_data in orders:
                transaction_id = order_data.get('transaction_id')

                if not transaction_id:
                    logger.warning(f"  [SKIP] {label.capitalize()} without transaction_id")
                    stats["errors"] += 1
                    continue

                existing_order = self._get_order(db, transaction_id)

                if existing_order:
                    status_changed = self.persistence.update_order_from_my_orders(
                        db, existing_order, order_data
                    )

                    # Re-enrich non-completed orders to track evolution
                    if existing_order.transaction_user_status != 'completed':
                        transaction = await self._fetch_transaction_details(db, transaction_id)
                        if transaction:
                            self.persistence.enrich_order_from_transaction(
                                db, existing_order, transaction
                            )
                            db.commit()
                            stats["enriched"] += 1
                            logger.debug(
                                f"  [ENRICH] TX {transaction_id} re-enriched "
                                f"(status: {existing_order.transaction_user_status})"
                            )
                    elif status_changed:
                        stats["updated"] += 1
                        logger.debug(f"  [UPDATE] TX {transaction_id} status updated")
                    continue

                # NEW order: create from /my_orders then enrich with /transactions
                basic_order = self.persistence.create_order_from_my_orders(db, order_data)
                if not basic_order:
                    stats["errors"] += 1
                    continue

                transaction = await self._fetch_transaction_details(db, transaction_id)
                if transaction:
                    self.persistence.enrich_order_from_transaction(
                        db, basic_order, transaction
                    )

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
            f"Sync {label}: {stats['synced']} new, "
            f"{stats['updated']} updated, {stats['enriched']} enriched, {stats['errors']} err"
        )
        return stats
