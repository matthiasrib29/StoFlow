"""
Vinted Data Extractor - Extraction de donnees depuis l'API Vinted

Module principal pour l'extraction et normalisation des donnees
retournees par l'API Vinted.

Modules associes:
- vinted_attribute_extractor.py: Extraction des attributs produit
- vinted_item_upload_parser.py: Parse JSON de /api/v2/item_upload/items/{id}

Author: Claude
Date: 2025-12-17
Updated: 2025-12-22 - Refactored into multiple modules
Updated: 2026-01-05 - Removed HTML parsing, use VintedItemUploadParser instead
"""

from datetime import datetime
from decimal import Decimal
from typing import Any

from shared.logging import get_logger
from services.vinted.vinted_attribute_extractor import VintedAttributeExtractor

logger = get_logger(__name__)

__all__ = [
    'VintedDataExtractor',
    'VintedAttributeExtractor',
]


class VintedDataExtractor:
    """
    Extracteur de donnees pour l'API Vinted.

    Normalise les differents formats de reponse API en types Python standards.

    Pour l'enrichissement produit, utiliser VintedItemUploadParser.
    Pour l'extraction d'attributs texte, utiliser VintedAttributeExtractor.
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
    def map_api_status(is_draft: bool, is_closed: bool) -> str:
        """
        Mappe le statut API vers statut DB.

        Args:
            is_draft: True si brouillon
            is_closed: True si fermé (= vendu sur Vinted)

        Returns:
            str: 'draft', 'published' ou 'sold'
        """
        if is_draft:
            return 'draft'
        if is_closed:
            return 'sold'
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
        except (ValueError, TypeError):
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

                # Photos - use full_size_url for original quality
                photos = item.get('photos', [])
                photo_url = (
                    photos[0].get('full_size_url') or photos[0].get('url')
                ) if photos else None

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
    # ATTRIBUTE EXTRACTION (delegated to VintedAttributeExtractor)
    # =========================================================================

    @staticmethod
    def extract_attributes_from_description(description: str) -> dict:
        """
        Extract product attributes from structured description text.

        Delegated to VintedAttributeExtractor.
        """
        return VintedAttributeExtractor.extract_attributes_from_description(
            description
        )
