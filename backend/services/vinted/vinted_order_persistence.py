"""
Vinted Order Persistence - Database persistence for Vinted orders

Handles saving, creating, updating, and enriching orders in the database.
Extracted from vinted_order_sync.py for separation of concerns.

Methods grouped by sync flow:
- sync_orders_by_month flow: process_and_save_order() -> extract + save
- sync_orders/sync_purchases flow: create/update/enrich methods

Author: Claude
Date: 2026-01-27 - Extracted from vinted_order_sync.py
"""

from sqlalchemy.orm import Session

from models.vinted.vinted_order import VintedOrder, VintedOrderProduct
from services.vinted.vinted_data_extractor import VintedDataExtractor
from shared.logging import get_logger

logger = get_logger(__name__)


def _parse_amount(price_obj: dict | str | None) -> float | None:
    """Parse price amount as float, delegating to VintedDataExtractor.extract_price()."""
    result = VintedDataExtractor.extract_price(price_obj)
    return float(result) if result is not None else None


class VintedOrderPersistence:
    """
    Handles database persistence for Vinted orders.

    Two main flows:
    1. sync_orders_by_month: process_and_save_order() extracts from /transactions + saves
    2. sync_orders/purchases: create/update/enrich from /my_orders + /transactions
    """

    # =========================================================================
    # SYNC BY MONTH FLOW (extract from /transactions + save)
    # =========================================================================

    def process_and_save_order(
        self, db: Session, transaction: dict,
        invoice_price: float | None, invoice_currency: str
    ) -> bool:
        """
        Extract order data from transaction and save to DB.

        Used by sync_orders_by_month flow.

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

            tx_id = transaction.get('id') if isinstance(transaction, dict) else None
            logger.warning(f"  [SKIP] Transaction {tx_id}: extraction returned None")
            logger.debug(
                f"  [DEBUG] Transaction keys: "
                f"{list(transaction.keys()) if isinstance(transaction, dict) else type(transaction)}"
            )
            return False

        except Exception as e:
            logger.error(f"Erreur save order: {type(e).__name__}: {e}", exc_info=True)
            db.rollback()
            return False

    @staticmethod
    def _extract_order_from_transaction(
        transaction: dict,
        invoice_price: float | None,
        invoice_currency: str
    ) -> dict | None:
        """
        Extract order data from /transactions/{id} response.

        Args:
            transaction: Transaction dict from API
            invoice_price: Real amount from invoice (seller_revenue)
            invoice_currency: Currency code

        Returns:
            Order data dict or None
        """
        try:
            transaction_id = transaction.get('id')
            if not transaction_id:
                return None

            buyer = transaction.get('buyer', {}) or {}
            seller = transaction.get('seller', {}) or {}
            buyer_photo = buyer.get('photo', {}) or {}
            shipment = transaction.get('shipment', {}) or {}
            shipment_status = shipment.get('status', 0)
            offer = transaction.get('offer', {}) or {}
            offer_price = offer.get('price', {})

            # Item count from order.items
            order_obj = transaction.get('order', {}) or {}
            items = order_obj.get('items', [])
            item_count = len(items) if items else 1

            # Status mapping: >= 400 = completed
            status_code = transaction.get('status', 0)
            status = 'completed' if status_code >= 400 else 'pending'

            # Dates based on shipment status (200+ = shipped, 400+ = delivered)
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
                'total_price': _parse_amount(offer_price),
                'currency': invoice_currency,
                'shipping_price': _parse_amount(shipment.get('price')),
                'service_fee': _parse_amount(transaction.get('service_fee')),
                'buyer_protection_fee': _parse_amount(offer.get('buyer_protection_fee')),
                'seller_revenue': invoice_price,
                # Shipping
                'shipment_id': shipment.get('id'),
                'tracking_number': shipment.get('tracking_code'),
                'carrier': shipment.get('carrier_name') or shipment.get('carrier'),
                # Dates
                'created_at_vinted': transaction.get('debit_processed_at'),
                'shipped_at': shipped_at,
                'delivered_at': delivered_at,
                'completed_at': transaction.get('status_updated_at')
            }
        except (ValueError, KeyError, TypeError):
            return None

    @staticmethod
    def _extract_products_from_transaction(transaction: dict) -> list[dict]:
        """
        Extract products from /transactions/{id} response.

        Handles both single items and bundles (order.items[]).
        """
        products = []
        transaction_id = transaction.get('id')
        if not transaction_id:
            return products

        try:
            order = transaction.get('order', {}) or {}
            items = order.get('items', [])

            if items:
                for item in items:
                    photos = item.get('photos', [])
                    photo_url = photos[0].get('url') if photos else None

                    brand = item.get('brand_title')
                    if not brand:
                        brand_obj = item.get('brand', {}) or {}
                        brand = brand_obj.get('title') or brand_obj.get('name')

                    products.append({
                        'transaction_id': transaction_id,
                        'vinted_item_id': item.get('id'),
                        'product_id': None,
                        'title': item.get('title'),
                        'price': _parse_amount(item.get('price')),
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

    @staticmethod
    def _save_order(db: Session, order_data: dict, products_data: list[dict]) -> None:
        """Save order and products to database."""
        vinted_order = VintedOrder(
            transaction_id=order_data['transaction_id'],
            conversation_id=order_data.get('conversation_id'),
            offer_id=order_data.get('offer_id'),
            buyer_id=order_data.get('buyer_id'),
            buyer_login=order_data.get('buyer_login'),
            buyer_photo_url=order_data.get('buyer_photo_url'),
            buyer_country_code=order_data.get('buyer_country_code'),
            buyer_city=order_data.get('buyer_city'),
            buyer_feedback_reputation=order_data.get('buyer_feedback_reputation'),
            seller_id=order_data.get('seller_id'),
            seller_login=order_data.get('seller_login'),
            status=order_data.get('status'),
            vinted_status_code=order_data.get('vinted_status_code'),
            vinted_status_text=order_data.get('vinted_status_text'),
            transaction_user_status=order_data.get('transaction_user_status'),
            item_count=order_data.get('item_count', 1),
            total_price=order_data.get('total_price'),
            currency=order_data.get('currency', 'EUR'),
            shipping_price=order_data.get('shipping_price'),
            service_fee=order_data.get('service_fee'),
            buyer_protection_fee=order_data.get('buyer_protection_fee'),
            seller_revenue=order_data.get('seller_revenue'),
            shipment_id=order_data.get('shipment_id'),
            tracking_number=order_data.get('tracking_number'),
            carrier=order_data.get('carrier'),
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

    # =========================================================================
    # SYNC ORDERS/PURCHASES FLOW (create/update/enrich from /my_orders)
    # =========================================================================

    @staticmethod
    def create_order_from_my_orders(db: Session, order_data: dict) -> VintedOrder | None:
        """
        Create order with data from /my_orders response.

        API fields captured: transaction_id, conversation_id, title, price,
        status, date, photo, transaction_user_status
        """
        try:
            transaction_id = order_data.get('transaction_id')
            if not transaction_id:
                return None

            conversation_id = order_data.get('conversation_id')

            # Extract price
            price_obj = order_data.get('price', {})
            total_price = _parse_amount(price_obj)
            currency = price_obj.get('currency_code', 'EUR')

            # Extract status
            user_status = order_data.get('transaction_user_status', '')
            status_text = order_data.get('status', '')

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

            vinted_order = VintedOrder(
                transaction_id=int(transaction_id),
                conversation_id=conversation_id,
                status=status,
                vinted_status_text=status_text,
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
            logger.error(f"Error creating order from my_orders: {e}", exc_info=True)
            db.rollback()
            return None

    @staticmethod
    def update_order_from_my_orders(
        db: Session, order: VintedOrder, order_data: dict
    ) -> bool:
        """
        Update existing order with fresh data from /my_orders.

        Updates: status, vinted_status_text, transaction_user_status
        """
        try:
            user_status = order_data.get('transaction_user_status', '')
            status_text = order_data.get('status', '')

            if user_status == 'completed':
                new_status = 'completed'
            elif user_status == 'failed':
                new_status = 'refunded'
            else:
                new_status = 'pending'

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
            logger.error(f"Error updating order: {e}", exc_info=True)
            db.rollback()
            return False

    @staticmethod
    def enrich_order_from_transaction(
        db: Session, order: VintedOrder, transaction: dict
    ) -> None:
        """
        Enrich order with detailed data from /transactions/{id}.

        Adds: buyer (with photo, country, city, reputation), seller, shipment,
        service_fee, items (for bundles), conversation_id, offer_id, status codes
        """
        try:
            # Vinted IDs
            order.conversation_id = (
                transaction.get('user_msg_thread_id') or transaction.get('msg_thread_id')
            )
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
                order.total_price = _parse_amount(offer_price)
                order.currency = offer_price.get('currency_code', order.currency)

            # Shipping price
            order.shipping_price = _parse_amount(shipment.get('price'))

            # Service fee
            order.service_fee = _parse_amount(transaction.get('service_fee'))

            # Buyer protection fee
            order.buyer_protection_fee = _parse_amount(
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

            # Update products for bundles
            VintedOrderPersistence._update_products_from_transaction(
                db, order.transaction_id, transaction
            )

        except Exception as e:
            logger.error(f"Error enriching order: {e}", exc_info=True)

    @staticmethod
    def _update_products_from_transaction(
        db: Session, transaction_id: int, transaction: dict
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
                price = _parse_amount(item.get('price'))

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
            logger.error(f"Error updating products: {e}", exc_info=True)
