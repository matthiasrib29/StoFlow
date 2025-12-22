"""
Vinted Data Extractor - Extraction de donnees depuis l'API Vinted

Module principal pour l'extraction et normalisation des donnees
retournees par l'API Vinted.

Modules associes:
- vinted_html_parser.py: Extraction depuis HTML Next.js Flight data
- vinted_attribute_extractor.py: Extraction des attributs produit

Author: Claude
Date: 2025-12-17
Updated: 2025-12-22 - Refactored into multiple modules
"""

from datetime import datetime
from decimal import Decimal
from typing import Any

from shared.logging_setup import get_logger

# Re-export classes from submodules for backward compatibility
from services.vinted.vinted_html_parser import VintedHtmlParser
from services.vinted.vinted_attribute_extractor import VintedAttributeExtractor

logger = get_logger(__name__)

# Expose submodule classes at module level
__all__ = [
    'VintedDataExtractor',
    'VintedHtmlParser',
    'VintedAttributeExtractor',
]


class VintedDataExtractor:
    """
    Extracteur de donnees pour l'API Vinted.

    Normalise les differents formats de reponse API en types Python standards.

    Pour l'extraction HTML, utilisez VintedHtmlParser.
    Pour l'extraction d'attributs, utilisez VintedAttributeExtractor.
    """

    # =========================================================================
    # BASIC EXTRACTION METHODS (API responses)
    # =========================================================================

    @staticmethod
    def extract_price(price_obj: Any) -> Decimal | None:
        """
        Extrait le prix depuis differents formats API.

        Args:
            price_obj: Peut etre dict {"amount": X}, str, int, float ou None

        Returns:
            Decimal ou None
        """
        if price_obj is None:
            return None

        try:
            if isinstance(price_obj, dict) and 'amount' in price_obj:
                return Decimal(str(price_obj['amount']))
            elif isinstance(price_obj, (str, int, float)):
                return Decimal(str(price_obj))
        except (ValueError, TypeError):
            pass

        return None

    @staticmethod
    def extract_text_field(obj: Any) -> str | None:
        """
        Extrait un champ texte depuis differents formats API.

        Utilise pour brand, size, color, category.

        Args:
            obj: Peut etre dict {"title": X} ou {"name": X}, str ou None

        Returns:
            str ou None
        """
        if obj is None:
            return None

        if isinstance(obj, dict):
            return obj.get('title') or obj.get('name')
        elif isinstance(obj, str):
            return obj
        elif isinstance(obj, int):
            return str(obj)

        return None

    @staticmethod
    def extract_brand(brand_obj: Any) -> str | None:
        """Extrait le nom de la marque depuis l'API Vinted."""
        return VintedDataExtractor.extract_text_field(brand_obj)

    @staticmethod
    def extract_size(size_obj: Any) -> str | None:
        """Extrait la taille depuis l'API Vinted."""
        return VintedDataExtractor.extract_text_field(size_obj)

    @staticmethod
    def extract_color(color_obj: Any) -> str | None:
        """Extrait la couleur depuis l'API Vinted."""
        return VintedDataExtractor.extract_text_field(color_obj)

    @staticmethod
    def extract_category(catalog_obj: Any) -> str | None:
        """Extrait la categorie depuis l'API Vinted."""
        return VintedDataExtractor.extract_text_field(catalog_obj)

    @staticmethod
    def map_api_status(
        is_draft: bool,
        is_closed: bool,
        closing_action: str | None
    ) -> str:
        """
        Mappe le statut API vers statut DB.

        Args:
            is_draft: True si brouillon
            is_closed: True si ferme
            closing_action: Action de fermeture ('sold', etc.)

        Returns:
            str: 'draft', 'published', 'sold' ou 'deleted'
        """
        if is_draft:
            return 'draft'
        if is_closed:
            if closing_action == 'sold':
                return 'sold'
            return 'deleted'
        return 'published'

    @staticmethod
    def parse_date(date_str: Any) -> datetime | None:
        """
        Parse une date depuis string ou datetime.

        Args:
            date_str: String ISO ou datetime

        Returns:
            datetime ou None
        """
        if not date_str:
            return None
        if isinstance(date_str, datetime):
            return date_str
        try:
            from dateutil import parser as date_parser
            return date_parser.parse(date_str)
        except Exception:
            return None

    # =========================================================================
    # ORDER/TRANSACTION EXTRACTION
    # =========================================================================

    @staticmethod
    def extract_order_data(transaction: dict) -> dict | None:
        """
        Extrait les donnees d'une commande depuis la reponse API.

        Args:
            transaction: Dict de transaction Vinted

        Returns:
            Dict avec donnees normalisees ou None
        """
        try:
            transaction_id = transaction.get('id')
            if not transaction_id:
                return None

            buyer = transaction.get('buyer', {}) or {}
            seller = transaction.get('seller', {}) or {}
            shipment = transaction.get('shipment', {}) or {}

            # Extract prices
            total_price = None
            service_fee = None
            buyer_protection_fee = None
            seller_revenue = None
            shipping_price = None
            currency = 'EUR'

            offer = transaction.get('offer', {})
            if isinstance(offer, dict):
                if 'price' in offer:
                    price_obj = offer['price']
                    if isinstance(price_obj, dict):
                        total_price = float(price_obj.get('amount', 0))
                        currency = price_obj.get('currency_code', 'EUR')

            # Fees
            fees = transaction.get('fees', {}) or {}
            if isinstance(fees, dict):
                if 'service_fee' in fees:
                    fee_obj = fees['service_fee']
                    if isinstance(fee_obj, dict):
                        service_fee = float(fee_obj.get('amount', 0))
                if 'buyer_protection' in fees:
                    fee_obj = fees['buyer_protection']
                    if isinstance(fee_obj, dict):
                        buyer_protection_fee = float(fee_obj.get('amount', 0))

            # Seller revenue
            payout = transaction.get('payout', {}) or {}
            if isinstance(payout, dict) and 'amount' in payout:
                payout_obj = payout['amount']
                if isinstance(payout_obj, dict):
                    seller_revenue = float(payout_obj.get('amount', 0))

            # Shipping
            if isinstance(shipment, dict):
                shipping_obj = shipment.get('price', {})
                if isinstance(shipping_obj, dict):
                    shipping_price = float(shipping_obj.get('amount', 0))

            # Dates
            created_at = transaction.get('created_at')
            shipped_at = shipment.get('shipped_at') if shipment else None
            delivered_at = shipment.get('delivered_at') if shipment else None
            completed_at = transaction.get('completed_at')

            return {
                'transaction_id': int(transaction_id),
                'buyer_id': buyer.get('id'),
                'buyer_login': buyer.get('login'),
                'seller_id': seller.get('id'),
                'seller_login': seller.get('login'),
                'status': transaction.get('status'),
                'total_price': total_price,
                'currency': currency,
                'shipping_price': shipping_price,
                'service_fee': service_fee,
                'buyer_protection_fee': buyer_protection_fee,
                'seller_revenue': seller_revenue,
                'tracking_number': (
                    shipment.get('tracking_number') if shipment else None
                ),
                'carrier': (
                    shipment.get('carrier', {}).get('name') if shipment else None
                ),
                'shipping_tracking_code': (
                    shipment.get('tracking_code') if shipment else None
                ),
                'created_at_vinted': created_at,
                'shipped_at': shipped_at,
                'delivered_at': delivered_at,
                'completed_at': completed_at
            }

        except Exception as e:
            logger.error(f"Erreur extraction order: {e}")
            return None

    @staticmethod
    def extract_order_products(
        transaction: dict,
        transaction_id: int
    ) -> list[dict]:
        """
        Extrait les produits d'une transaction.

        Args:
            transaction: Dict de transaction Vinted
            transaction_id: ID de la transaction

        Returns:
            Liste de dicts produits
        """
        products = []

        try:
            order = transaction.get('order', {})
            items = order.get('items', []) if isinstance(order, dict) else []

            for item in items:
                if not isinstance(item, dict):
                    continue

                # Price
                price = None
                if 'price' in item:
                    price_obj = item['price']
                    if isinstance(price_obj, dict) and 'amount' in price_obj:
                        price = float(price_obj['amount'])

                # Photos
                photos = item.get('photos', [])
                photo_url = photos[0].get('url') if photos else None

                # Size and Brand
                size_obj = item.get('size', {})
                size = size_obj.get('title') if isinstance(size_obj, dict) else None

                brand_obj = item.get('brand', {})
                brand = brand_obj.get('title') if isinstance(brand_obj, dict) else None

                products.append({
                    'transaction_id': transaction_id,
                    'vinted_item_id': item.get('id'),
                    'product_id': None,
                    'title': item.get('title'),
                    'price': price,
                    'size': size,
                    'brand': brand,
                    'photo_url': photo_url
                })

        except Exception as e:
            logger.error(f"Erreur extraction products: {e}")

        return products

    # =========================================================================
    # HTML EXTRACTION (delegated to VintedHtmlParser)
    # =========================================================================

    @staticmethod
    def extract_nextjs_flight_data(html: str) -> list[dict]:
        """
        Extract all Next.js Flight data chunks from HTML page.

        Delegated to VintedHtmlParser for backward compatibility.
        """
        return VintedHtmlParser.extract_nextjs_flight_data(html)

    @staticmethod
    def extract_product_from_html(html: str) -> dict | None:
        """
        Extract complete product data from a Vinted product HTML page.

        Delegated to VintedHtmlParser for backward compatibility.
        """
        return VintedHtmlParser.extract_product_from_html(html)

    # =========================================================================
    # ATTRIBUTE EXTRACTION (delegated to VintedAttributeExtractor)
    # =========================================================================

    @staticmethod
    def extract_attributes_from_description(description: str) -> dict:
        """
        Extract product attributes from structured description text.

        Delegated to VintedAttributeExtractor for backward compatibility.
        """
        return VintedAttributeExtractor.extract_attributes_from_description(
            description
        )

    # =========================================================================
    # PRIVATE METHODS (kept for backward compatibility)
    # =========================================================================

    @staticmethod
    def _normalize_html_content(html: str) -> str:
        """Delegated to VintedAttributeExtractor."""
        return VintedAttributeExtractor.normalize_html_content(html)

    @staticmethod
    def _extract_from_meta_tags(html: str) -> dict | None:
        """Delegated to VintedHtmlParser."""
        return VintedHtmlParser._extract_from_meta_tags(html)

    @staticmethod
    def _extract_photos_from_html(html: str) -> list[dict]:
        """Delegated to VintedHtmlParser."""
        return VintedHtmlParser.extract_photos_from_html(html)

    @staticmethod
    def _extract_published_at_from_photos(photos: list[dict]) -> datetime | None:
        """Delegated to VintedHtmlParser."""
        return VintedHtmlParser._extract_published_at_from_photos(photos)

    @staticmethod
    def _extract_attributes_from_html(html: str) -> dict:
        """Delegated to VintedAttributeExtractor."""
        return VintedAttributeExtractor.extract_attributes_from_html(html)

    @staticmethod
    def _parse_measurements(measurement_str: str) -> dict | None:
        """Delegated to VintedAttributeExtractor."""
        return VintedAttributeExtractor.parse_measurements(measurement_str)

    @staticmethod
    def _extract_description_from_html(
        html: str, title: str | None = None
    ) -> str | None:
        """Delegated to VintedAttributeExtractor."""
        return VintedAttributeExtractor.extract_description_from_html(html, title)
