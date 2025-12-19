"""
Vinted Data Extractor - Extraction de donnees depuis l'API Vinted

Fonctions utilitaires pour extraire et normaliser les donnees
retournees par l'API Vinted.

=============================================================================
FORMAT DES DONNEES HTML VINTED (2025-12-19)
=============================================================================

La page HTML d'un produit Vinted contient des donnees Next.js Flight
dans des balises <script> avec le pattern:
    self.__next_f.push([1, "...JSON_DATA..."])

STRUCTURE DES DONNEES PRINCIPALES:

1. BLOC "item" (donnees produit):
   {
     "id": 7751078047,
     "title": "Wrangler Jeans regular...",
     "catalog_id": 1819,              # ID categorie Vinted
     "currency": "EUR",
     "is_hidden": false,
     "is_reserved": false,
     "is_closed": false,
     "is_draft": false,
     "price": {"amount": "18.9", "currency_code": "EUR"},
     "brand_dto": {"id": 259, "title": "Wrangler"},  # Marque avec ID
     "service_fee": {"amount": "1.37", "currency_code": "EUR"},
     "total_item_price": {"amount": "20.27", "currency_code": "EUR"},
     "seller_id": 29535217,
     "login": "shop.ton.outfit",
     "photos": [{"high_resolution": {"timestamp": 1765557915}}]
   }

2. BLOC "attributes" (dans plugins):
   {
     "name": "attributes",
     "data": {
       "attributes": [
         {"code": "brand", "data": {"id": 259, "value": "Wrangler"}},
         {"code": "size", "data": {"id": 1233, "value": "W26 | FR 36"}},
         {"code": "status", "data": {"id": 50, "value": "Bon etat"}},
         {"code": "color", "data": {"value": "Bleu"}},  # PAS d'ID !
         {"code": "upload_date", "data": {"value": "Il y a 6 jours"}}
       ]
     }
   }

3. BLOC "description" (dans plugins):
   {
     "name": "description",
     "data": {"description": "Texte de la description..."}
   }

NOTES IMPORTANTES:
- L'ID "status" dans HTML (ex: 50) est DIFFERENT du status_id API (1-6)
- Le champ "color" n'a PAS d'ID dans le HTML, seulement le texte
- Le timestamp published_at vient de photos[0].high_resolution.timestamp

Includes:
- API response parsing (extract_price, extract_text_field, etc.)
- Next.js Flight data extraction from HTML pages
- Order/transaction data extraction

Author: Claude
Date: 2025-12-17
Updated: 2025-12-19 - Added detailed format documentation
"""

import json
import re
from datetime import datetime
from decimal import Decimal
from typing import Any

from shared.logging_setup import get_logger

logger = get_logger(__name__)


class VintedDataExtractor:
    """
    Extracteur de donnees pour l'API Vinted.

    Normalise les differents formats de reponse API en types Python standards.
    """

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

            # Extraire prix
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

            # Frais
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

            # Revenu vendeur
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
                'tracking_number': shipment.get('tracking_number') if shipment else None,
                'carrier': shipment.get('carrier', {}).get('name') if shipment else None,
                'shipping_tracking_code': shipment.get('tracking_code') if shipment else None,
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

                # Prix
                price = None
                if 'price' in item:
                    price_obj = item['price']
                    if isinstance(price_obj, dict) and 'amount' in price_obj:
                        price = float(price_obj['amount'])

                # Photos
                photos = item.get('photos', [])
                photo_url = photos[0].get('url') if photos else None

                # Size et Brand
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
    # NEXT.JS FLIGHT DATA EXTRACTION (from HTML pages)
    # =========================================================================

    @staticmethod
    def extract_nextjs_flight_data(html: str) -> list[dict]:
        """
        Extract all Next.js Flight data chunks from HTML page.

        Vinted uses Next.js which embeds structured data in script tags
        with `self.__next_f.push([...])` calls.

        Args:
            html: Full HTML content of a Vinted page

        Returns:
            List of parsed JSON objects from flight data
        """
        chunks = []

        # Find all __next_f.push calls
        pattern = r'self\.__next_f\.push\(\s*\[(.*?)\]\s*\)'
        matches = re.findall(pattern, html, re.DOTALL)

        for match in matches:
            try:
                # Parse the array content: [index, "json_string"]
                # Handle escaped quotes and clean up
                clean_match = match.strip()

                # Try to extract the JSON string part (usually the second element)
                if ',"' in clean_match:
                    # Format: 1,"json_content"
                    json_start = clean_match.index(',"') + 2
                    json_content = clean_match[json_start:-1]  # Remove trailing quote

                    # Unescape the JSON string
                    json_content = json_content.encode().decode('unicode_escape')

                    # Try to parse as JSON
                    if json_content.strip().startswith('{') or json_content.strip().startswith('['):
                        try:
                            parsed = json.loads(json_content)
                            chunks.append(parsed)
                        except json.JSONDecodeError:
                            pass
            except Exception:
                continue

        return chunks

    @staticmethod
    def _normalize_html_content(html: str) -> str:
        """
        Normalize HTML content to standardize escaped characters.

        Vinted uses React Server Components (RSC) with Next.js Flight data
        that may have various escaping formats:
        - \\" -> "
        - \\\\ -> \\
        - \\n -> newline
        - \\t -> tab

        Args:
            html: Raw HTML content

        Returns:
            Normalized content with standard JSON quotes
        """
        # Replace escaped quotes: \" -> "
        normalized = html.replace('\\"', '"')
        # Replace double backslashes: \\\\ -> \\
        normalized = normalized.replace('\\\\', '\\')
        # Keep \\n and \\t as-is for now (will be handled during text extraction)
        return normalized

    @staticmethod
    def extract_product_from_html(html: str) -> dict | None:
        """
        Extract complete product data from a Vinted product HTML page.

        Parses Next.js Flight data to extract:
        - Item details (id, title, price, photos, etc.)
        - Brand information
        - Size, condition, color
        - Description
        - Seller information
        - Fees (service_fee, buyer_protection, shipping)

        Args:
            html: Full HTML content of a Vinted product page

        Returns:
            Dict with product data or None if extraction fails
        """
        try:
            # Normalize HTML to handle escaped quotes
            normalized = VintedDataExtractor._normalize_html_content(html)

            # Try multiple extraction methods
            # Method 1: JSON pattern in Next.js flight data
            item_pattern = r'"item":\s*\{[^}]*"id":\s*(\d+)[^}]*"title"'
            item_match = re.search(item_pattern, normalized)

            # Method 2: Extract from meta tags (fallback)
            if not item_match:
                logger.debug("No JSON item pattern, trying meta tags extraction")
                return VintedDataExtractor._extract_from_meta_tags(normalized)

            # Extract the larger JSON block containing item
            # Find __next_f.push containing this item
            item_id = item_match.group(1)

            result = {
                'vinted_id': int(item_id),
                'title': None,
                'description': None,
                'price': None,
                'currency': 'EUR',
                'brand_id': None,
                'brand_name': None,
                'size_id': None,
                'size_title': None,
                'condition_id': None,
                'condition_title': None,
                'color': None,
                'material': None,
                'measurements': None,
                'measurement_width': None,
                'measurement_length': None,
                'manufacturer_labelling': None,
                'published_at': None,  # From image timestamp (accurate)
                'upload_date_text': None,  # Relative text ("Il y a 2 semaines") - less accurate
                'catalog_id': None,
                'photos': [],
                'seller_id': None,
                'seller_login': None,
                'seller_feedback_count': None,
                'seller_feedback_reputation': None,
                'service_fee': None,
                'buyer_protection_fee': None,
                'shipping_price': None,
                'total_item_price': None,
                'is_draft': False,
                'is_closed': False,
                'is_reserved': False,
                'is_hidden': False,
                'can_edit': False,
                'can_delete': False,
            }

            # Extract title
            title_pattern = rf'"id":{item_id},"title":"([^"]+)"'
            title_match = re.search(title_pattern, html)
            if title_match:
                result['title'] = title_match.group(1)

            # Extract catalog_id (handle escaped quotes: \"catalog_id\": or "catalog_id":)
            catalog_pattern = r'"catalog_id\\?":\s*(\d+)'
            catalog_match = re.search(catalog_pattern, html)
            if catalog_match:
                result['catalog_id'] = int(catalog_match.group(1))

            # Extract price
            price_pattern = r'"price":\s*\{\s*"amount":\s*"([^"]+)"'
            price_match = re.search(price_pattern, html)
            if price_match:
                try:
                    result['price'] = float(price_match.group(1))
                except ValueError:
                    pass

            # Extract currency
            currency_pattern = r'"currency_code":\s*"([A-Z]{3})"'
            currency_match = re.search(currency_pattern, html)
            if currency_match:
                result['currency'] = currency_match.group(1)

            # Extract brand from brand_dto or brand_id (handle escaped quotes)
            # Try brand_dto pattern first
            brand_dto_pattern = r'"brand_dto\\?":\s*\{[^}]*"id\\?":\s*(\d+)[^}]*"title\\?":\s*"([^"\\]+)'
            brand_match = re.search(brand_dto_pattern, html)
            if brand_match:
                result['brand_id'] = int(brand_match.group(1))
                result['brand_name'] = brand_match.group(2)
            else:
                # Fallback: direct brand_id pattern
                brand_id_pattern = r'"brand_id\\?":\s*(\d+)'
                brand_id_match = re.search(brand_id_pattern, html)
                if brand_id_match:
                    result['brand_id'] = int(brand_id_match.group(1))

            # Extract seller info (handle escaped quotes)
            seller_pattern = r'"seller_id\\?":\s*(\d+)'
            seller_match = re.search(seller_pattern, html)
            if seller_match:
                result['seller_id'] = int(seller_match.group(1))

            login_pattern = r'"login\\?":\s*"([^"\\]+)'
            login_match = re.search(login_pattern, html)
            if login_match:
                result['seller_login'] = login_match.group(1)

            feedback_count_pattern = r'"feedback_count\\?":\s*(\d+)'
            feedback_match = re.search(feedback_count_pattern, html)
            if feedback_match:
                result['seller_feedback_count'] = int(feedback_match.group(1))

            feedback_rep_pattern = r'"feedback_reputation\\?":\s*([\d.]+)'
            feedback_rep_match = re.search(feedback_rep_pattern, html)
            if feedback_rep_match:
                result['seller_feedback_reputation'] = float(feedback_rep_match.group(1))

            # Extract service fee (handle escaped quotes)
            service_fee_pattern = r'"service_fee\\?":\s*\{[^}]*"amount\\?":\s*"?([0-9.]+)'
            service_fee_match = re.search(service_fee_pattern, html)
            if service_fee_match:
                try:
                    result['service_fee'] = float(service_fee_match.group(1))
                except ValueError:
                    pass

            # Extract buyer protection fee (handle escaped quotes)
            bp_pattern = r'"buyerProtection\\?"[^}]*"finalPrice\\?"[^}]*"amount\\?":\s*"?([0-9.]+)'
            bp_match = re.search(bp_pattern, html)
            if bp_match:
                try:
                    result['buyer_protection_fee'] = float(bp_match.group(1))
                except ValueError:
                    pass

            # Extract shipping price (handle escaped quotes)
            shipping_pattern = r'"shippingDetails\\?"[^}]*"price\\?"[^}]*"amount\\?":\s*"?([\d.]+)'
            shipping_match = re.search(shipping_pattern, html)
            if shipping_match:
                try:
                    result['shipping_price'] = float(shipping_match.group(1))
                except ValueError:
                    pass

            # Extract total_item_price (handle escaped quotes)
            total_price_pattern = r'"total_item_price\\?":\s*\{[^}]*"amount\\?":\s*"?([0-9.]+)'
            total_price_match = re.search(total_price_pattern, html)
            if total_price_match:
                try:
                    result['total_item_price'] = float(total_price_match.group(1))
                except ValueError:
                    pass

            # Extract status flags
            if '"is_draft":true' in html:
                result['is_draft'] = True
            if '"is_closed":true' in html:
                result['is_closed'] = True
            if '"is_reserved":true' in html:
                result['is_reserved'] = True
            if '"is_hidden":true' in html:
                result['is_hidden'] = True
            if '"can_edit":true' in html:
                result['can_edit'] = True
            if '"can_delete":true' in html:
                result['can_delete'] = True

            # Extract photos (with timestamps)
            photos = VintedDataExtractor._extract_photos_from_html(html)
            if photos:
                result['photos'] = photos
                # Extract published_at from first photo's timestamp
                published_at = VintedDataExtractor._extract_published_at_from_photos(photos)
                if published_at:
                    result['published_at'] = published_at

            # Extract attributes (size, condition, color)
            attributes = VintedDataExtractor._extract_attributes_from_html(html)
            # Store upload_date as text (relative date, less accurate)
            if attributes.get('upload_date'):
                result['upload_date_text'] = attributes.pop('upload_date')
            result.update(attributes)

            # Extract description (pass title for better matching)
            description = VintedDataExtractor._extract_description_from_html(
                html, title=result.get('title')
            )
            if description:
                result['description'] = description

            # ===== FALLBACK: Extract attributes from description text =====
            # If HTML extraction failed, try parsing structured description
            desc_attrs = VintedDataExtractor.extract_attributes_from_description(
                result.get('description', '')
            )
            for key, value in desc_attrs.items():
                if value and not result.get(key):
                    result[key] = value
                    logger.debug(f"Filled {key} from description: {value}")

            logger.debug(f"Extracted product {item_id}: {result.get('title', 'N/A')}")
            return result

        except Exception as e:
            logger.error(f"Error extracting product from HTML: {e}")
            return None

    @staticmethod
    def _extract_from_meta_tags(html: str) -> dict | None:
        """
        Fallback extraction from HTML when JSON item pattern fails.

        This method extracts data from:
        1. Meta tags (description, title, url, image)
        2. Attribute blocks (size, color, material, condition, etc.)
        3. Description from plugins section
        4. Photos with timestamps

        Args:
            html: Full HTML content

        Returns:
            Dict with extracted data or None
        """
        result = {
            'vinted_id': None,
            'title': None,
            'description': None,
            'price': None,
            'currency': 'EUR',
            'brand_id': None,
            'brand_name': None,
            'size_id': None,
            'size_title': None,
            'condition_id': None,
            'condition_title': None,
            'color': None,
            'material': None,
            'measurements': None,
            'measurement_width': None,
            'measurement_length': None,
            'manufacturer_labelling': None,
            'published_at': None,
            'upload_date_text': None,
            'catalog_id': None,
            'photos': [],
            'seller_id': None,
            'seller_login': None,
            'is_draft': False,
            'is_closed': False,
        }

        # ===== 1. Extract from meta tags =====
        # Description from meta tag
        desc_pattern = r'<meta\s+name="description"\s+content="([^"]+)"'
        desc_match = re.search(desc_pattern, html, re.IGNORECASE)
        if desc_match:
            result['description'] = desc_match.group(1)
            logger.debug(f"Extracted description from meta: {result['description'][:50]}...")

        # Also try og:description
        if not result['description']:
            og_desc_pattern = r'<meta\s+property="og:description"\s+content="([^"]+)"'
            og_desc_match = re.search(og_desc_pattern, html, re.IGNORECASE)
            if og_desc_match:
                result['description'] = og_desc_match.group(1)

        # Title from og:title
        og_title_pattern = r'<meta\s+property="og:title"\s+content="([^"]+)"'
        og_title_match = re.search(og_title_pattern, html, re.IGNORECASE)
        if og_title_match:
            result['title'] = og_title_match.group(1)

        # Vinted_id from og:url (e.g., https://www.vinted.fr/items/7736101449-...)
        og_url_pattern = r'<meta\s+property="og:url"\s+content="[^"]*items/(\d+)-[^"]*"'
        og_url_match = re.search(og_url_pattern, html, re.IGNORECASE)
        if og_url_match:
            result['vinted_id'] = int(og_url_match.group(1))

        # Image from og:image
        og_image_pattern = r'<meta\s+property="og:image"\s+content="([^"]+)"'
        og_image_match = re.search(og_image_pattern, html, re.IGNORECASE)
        if og_image_match:
            result['photo_url'] = og_image_match.group(1)

        # ===== 2. Extract attributes (size, color, material, condition) =====
        attributes = VintedDataExtractor._extract_attributes_from_html(html)
        if attributes.get('upload_date'):
            result['upload_date_text'] = attributes.pop('upload_date')
        result.update(attributes)

        # ===== 3. Extract description from plugins section (more complete) =====
        plugins_desc = VintedDataExtractor._extract_description_from_html(
            html, title=result.get('title')
        )
        if plugins_desc:
            result['description'] = plugins_desc  # Override meta description with full one

        # ===== 3b. FALLBACK: Extract attributes from description text =====
        # If HTML extraction didn't find attributes, try parsing description
        desc_attrs = VintedDataExtractor.extract_attributes_from_description(
            result.get('description', '')
        )
        for key, value in desc_attrs.items():
            if value and not result.get(key):
                result[key] = value
                logger.debug(f"Meta fallback - filled {key} from description: {value}")

        # ===== 4. Extract photos with timestamps =====
        photos = VintedDataExtractor._extract_photos_from_html(html)
        if photos:
            result['photos'] = photos
            published_at = VintedDataExtractor._extract_published_at_from_photos(photos)
            if published_at:
                result['published_at'] = published_at

        # ===== 5. Extract price (handle escaped quotes) =====
        price_pattern = r'"price\\?":\s*\{[^}]*"amount\\?":\s*"?([0-9.]+)'
        price_match = re.search(price_pattern, html)
        if price_match:
            try:
                result['price'] = float(price_match.group(1))
            except ValueError:
                pass

        # ===== 6. Extract brand (handle escaped quotes) =====
        brand_dto_pattern = r'"brand_dto\\?":\s*\{[^}]*"id\\?":\s*(\d+)[^}]*"title\\?":\s*"([^"\\]+)'
        brand_match = re.search(brand_dto_pattern, html)
        if brand_match:
            result['brand_id'] = int(brand_match.group(1))
            result['brand_name'] = brand_match.group(2)
        else:
            # Fallback: direct brand_id pattern
            brand_id_pattern = r'"brand_id\\?":\s*(\d+)'
            brand_id_match = re.search(brand_id_pattern, html)
            if brand_id_match:
                result['brand_id'] = int(brand_id_match.group(1))

        # ===== 7. Extract seller info (handle escaped quotes) =====
        seller_pattern = r'"seller_id\\?":\s*(\d+)'
        seller_match = re.search(seller_pattern, html)
        if seller_match:
            result['seller_id'] = int(seller_match.group(1))

        login_pattern = r'"login\\?":\s*"([^"\\]+)'
        login_match = re.search(login_pattern, html)
        if login_match:
            result['seller_login'] = login_match.group(1)

        # ===== 8. Extract status flags (handle escaped quotes) =====
        if '"is_draft\\":true' in html or '"is_draft":true' in html:
            result['is_draft'] = True
        if '"is_closed\\":true' in html or '"is_closed":true' in html:
            result['is_closed'] = True

        # ===== 9. Extract catalog_id (handle escaped quotes) =====
        catalog_pattern = r'"catalog_id\\?":\s*(\d+)'
        catalog_match = re.search(catalog_pattern, html)
        if catalog_match:
            result['catalog_id'] = int(catalog_match.group(1))

        # Only return if we got at least description OR some attributes
        has_data = (
            result['description'] or
            result['material'] or
            result['color'] or
            result['size_title']
        )

        if has_data:
            logger.info(
                f"Meta/attributes extraction for product {result.get('vinted_id', 'unknown')}: "
                f"description={'Yes' if result['description'] else 'No'}, "
                f"material={result.get('material', 'No')}, "
                f"color={result.get('color', 'No')}, "
                f"size={result.get('size_title', 'No')}"
            )
            return result

        # DEBUG: Log what we found to understand the HTML structure
        logger.warning(
            f"Meta extraction failed for product {result.get('vinted_id', 'unknown')} - "
            f"title={result.get('title', 'No')}, "
            f"description={'Yes' if result.get('description') else 'No'}, "
            f"price={result.get('price', 'No')}"
        )
        return None

    @staticmethod
    def _extract_photos_from_html(html: str) -> list[dict]:
        """
        Extract photo URLs and timestamps from HTML.

        Uses multiple strategies:
        1. full_size_url pattern (highest quality, most reliable)
        2. Photo block pattern with id and url
        3. Simple url pattern fallback

        Returns list of photo dicts with:
        - position: 1-indexed position
        - url: Full image URL
        - is_main: True for first photo
        - timestamp: Unix timestamp from high_resolution (if available)
        """
        photos = []
        seen_urls = set()

        # Normalize HTML for consistent quote handling
        normalized = VintedDataExtractor._normalize_html_content(html)

        # ===== Strategy 1: full_size_url pattern (best quality) =====
        # Pattern: "full_size_url":"https://images1.vinted.net/..."
        full_size_patterns = [
            r'"full_size_url":"(https://images1\.vinted\.net[^"]+)"',
            r'full_size_url":"(https://images1\.vinted\.net[^"]+)"',
        ]
        for pattern in full_size_patterns:
            full_size_matches = re.findall(pattern, normalized)
            if full_size_matches:
                for url in full_size_matches:
                    if url not in seen_urls:
                        seen_urls.add(url)
                        photos.append({
                            'position': len(photos) + 1,
                            'url': url,
                            'is_main': len(photos) == 0,
                            'timestamp': None
                        })
                if photos:
                    logger.debug(f"Strategy 1 - Found {len(photos)} photos via full_size_url")
                    break

        # ===== Strategy 2: Photo block pattern with timestamps =====
        if not photos:
            # Look for photo blocks that contain id, url, and potentially timestamps
            photo_block_pattern = r'\{"id":\d+[^}]*"url":"(https://images1\.vinted\.net[^"]+)"[^}]*\}'
            photo_blocks = re.findall(photo_block_pattern, normalized)

            # Also try to extract timestamps from high_resolution
            timestamp_pattern = r'"high_resolution":\s*\{[^}]*"timestamp":\s*(\d+)[^}]*\}'
            timestamps = re.findall(timestamp_pattern, normalized)

            for i, url in enumerate(photo_blocks):
                if url in seen_urls:
                    continue
                seen_urls.add(url)

                photo = {
                    'position': len(photos) + 1,
                    'url': url,
                    'is_main': len(photos) == 0,
                    'timestamp': None
                }

                # Try to get corresponding timestamp
                if i < len(timestamps):
                    try:
                        photo['timestamp'] = int(timestamps[i])
                    except ValueError:
                        pass

                photos.append(photo)

            if photos:
                logger.debug(f"Strategy 2 - Found {len(photos)} photos via block pattern")

        # ===== Strategy 3: Simple URL fallback =====
        if not photos:
            # Try f800 URLs (high resolution)
            url_patterns = [
                r'"url":"(https://images1\.vinted\.net[^"]+f800[^"]+)"',
                r'"url":\s*"(https://images1\.vinted\.net[^"]+)"',
            ]
            for url_pattern in url_patterns:
                url_matches = re.findall(url_pattern, normalized)
                for url in url_matches:
                    if url not in seen_urls:
                        seen_urls.add(url)
                        photos.append({
                            'position': len(photos) + 1,
                            'url': url,
                            'is_main': len(photos) == 0,
                            'timestamp': None
                        })
                if photos:
                    logger.debug(f"Strategy 3 - Found {len(photos)} photos via simple URL")
                    break

        return photos

    @staticmethod
    def _extract_published_at_from_photos(photos: list[dict]) -> datetime | None:
        """
        Extract publication date from the first photo's timestamp.

        Vinted stores the upload timestamp in the high_resolution photo metadata.
        This is more accurate than the relative "Il y a X jours" text.

        Args:
            photos: List of photo dicts with optional 'timestamp' field

        Returns:
            datetime or None if no timestamp found
        """
        if not photos:
            return None

        # Get timestamp from first photo (main photo)
        first_photo = photos[0] if photos else None
        if first_photo and first_photo.get('timestamp'):
            try:
                timestamp = first_photo['timestamp']
                return datetime.fromtimestamp(timestamp)
            except (ValueError, OSError, OverflowError) as e:
                logger.debug(f"Failed to parse timestamp {timestamp}: {e}")
                return None

        # Try to find any timestamp in the photos
        for photo in photos:
            if photo.get('timestamp'):
                try:
                    return datetime.fromtimestamp(photo['timestamp'])
                except (ValueError, OSError, OverflowError):
                    continue

        return None

    @staticmethod
    def _extract_attributes_from_html(html: str) -> dict:
        """
        Extract all product attributes from HTML.

        Uses multiple extraction strategies with normalized content:
        1. RSC format patterns (React Server Components)
        2. JSON attribute blocks with "code"/"data" pattern
        3. Alternative JSON patterns found in Next.js data
        4. Fallback: French label patterns ("Taille", "État", etc.)

        Handles all known attribute types:
        - size: Taille (with id)
        - status: État/Condition (with id)
        - color: Couleur
        - material: Matière
        - measurements: Dimensions (l x L)
        - brand: Marque (with id)
        - manufacturer_labelling: Étiquetage
        - upload_date: Date d'ajout
        """
        attributes = {
            'size_id': None,
            'size_title': None,
            'condition_id': None,
            'condition_title': None,
            'color': None,
            'material': None,
            'measurements': None,
            'measurement_width': None,
            'measurement_length': None,
            'manufacturer_labelling': None,
            'upload_date': None,
        }

        # Normalize HTML to handle escaped quotes from RSC format
        normalized = VintedDataExtractor._normalize_html_content(html)

        # ===== Strategy 1: RSC format patterns (most reliable) =====
        # These patterns match the actual Next.js Flight data format from Vinted
        # Pattern: "code":"size","data":{..."value":"S"..."id":515}

        # Size extraction
        size_patterns = [
            r'"code":"size","data":\{[^}]*"value":"([^"]+)"[^}]*"id":(\d+)',
            r'"code":"size"[^}]*"value":"([^"]+)"[^}]*"id":(\d+)',
            r'code":"size","data":\{"title":"[^"]+","value":"([^"]+)","id":(\d+)',
        ]
        for pattern in size_patterns:
            size_match = re.search(pattern, normalized)
            if size_match:
                attributes['size_title'] = size_match.group(1)
                attributes['size_id'] = int(size_match.group(2))
                logger.debug(f"RSC - Found size: {attributes['size_title']} (id: {attributes['size_id']})")
                break

        # Condition/Status extraction
        status_patterns = [
            r'"code":"status","data":\{[^}]*"value":"([^"]+)"[^}]*"id":(\d+)',
            r'"code":"status"[^}]*"value":"([^"]+)"[^}]*"id":(\d+)',
            r'code":"status","data":\{"title":"[^"]+","value":"([^"]+)","id":(\d+)',
        ]
        for pattern in status_patterns:
            status_match = re.search(pattern, normalized)
            if status_match:
                attributes['condition_title'] = status_match.group(1)
                attributes['condition_id'] = int(status_match.group(2))
                logger.debug(f"RSC - Found condition: {attributes['condition_title']} (id: {attributes['condition_id']})")
                break

        # Color extraction (no ID in Vinted HTML)
        color_patterns = [
            r'"code":"color","data":\{[^}]*"value":"([^"]+)"',
            r'"code":"color"[^}]*"value":"([^"]+)"',
            r'code":"color","data":\{"title":"[^"]+","value":"([^"]+)"',
        ]
        for pattern in color_patterns:
            color_match = re.search(pattern, normalized)
            if color_match:
                attributes['color'] = color_match.group(1)
                logger.debug(f"RSC - Found color: {attributes['color']}")
                break

        # Material extraction
        material_patterns = [
            r'"code":"material","data":\{[^}]*"value":"([^"]+)"',
            r'"code":"material"[^}]*"value":"([^"]+)"',
        ]
        for pattern in material_patterns:
            material_match = re.search(pattern, normalized)
            if material_match:
                attributes['material'] = material_match.group(1)
                logger.debug(f"RSC - Found material: {attributes['material']}")
                break

        # Measurements extraction
        measurements_patterns = [
            r'"code":"measurements","data":\{[^}]*"value":"([^"]+)"',
            r'"code":"measurements"[^}]*"value":"([^"]+)"',
        ]
        for pattern in measurements_patterns:
            measurements_match = re.search(pattern, normalized)
            if measurements_match:
                attributes['measurements'] = measurements_match.group(1)
                dims = VintedDataExtractor._parse_measurements(attributes['measurements'])
                if dims:
                    attributes['measurement_width'] = dims.get('width')
                    attributes['measurement_length'] = dims.get('length')
                logger.debug(f"RSC - Found measurements: {attributes['measurements']}")
                break

        # Upload date extraction
        upload_patterns = [
            r'"code":"upload_date","data":\{[^}]*"value":"([^"]+)"',
            r'"code":"upload_date"[^}]*"value":"([^"]+)"',
        ]
        for pattern in upload_patterns:
            upload_match = re.search(pattern, normalized)
            if upload_match:
                attributes['upload_date'] = upload_match.group(1)
                logger.debug(f"RSC - Found upload_date: {attributes['upload_date']}")
                break

        # Manufacturer labelling extraction
        labelling_patterns = [
            r'"code":"manufacturer_labelling","data":\{[^}]*"value":"([^"]+)"',
            r'"code":"manufacturer_labelling"[^}]*"value":"([^"]+)"',
        ]
        for pattern in labelling_patterns:
            labelling_match = re.search(pattern, normalized)
            if labelling_match:
                attributes['manufacturer_labelling'] = labelling_match.group(1)
                logger.debug(f"RSC - Found manufacturer_labelling: {attributes['manufacturer_labelling']}")
                break

        # ===== Strategy 2: Alternative JSON patterns =====
        # Try direct JSON patterns for common attributes if RSC failed

        if not attributes['size_title']:
            size_pattern = r'"size":\s*\{[^}]*"id":\s*(\d+)[^}]*"title":\s*"([^"]+)'
            size_match = re.search(size_pattern, normalized)
            if size_match:
                attributes['size_id'] = int(size_match.group(1))
                attributes['size_title'] = size_match.group(2)
                logger.debug(f"JSON - Found size: {attributes['size_title']}")
            else:
                size_id_pattern = r'"size_id":\s*(\d+)'
                size_id_match = re.search(size_id_pattern, normalized)
                if size_id_match:
                    attributes['size_id'] = int(size_id_match.group(1))

        if not attributes['condition_title']:
            status_pattern = r'"status":\s*\{[^}]*"id":\s*(\d+)[^}]*"title":\s*"([^"]+)'
            status_match = re.search(status_pattern, normalized)
            if status_match:
                attributes['condition_id'] = int(status_match.group(1))
                attributes['condition_title'] = status_match.group(2)
                logger.debug(f"JSON - Found condition: {attributes['condition_title']}")
            else:
                status_id_pattern = r'"status_id":\s*(\d+)'
                status_id_match = re.search(status_id_pattern, normalized)
                if status_id_match:
                    attributes['condition_id'] = int(status_id_match.group(1))

        if not attributes['color']:
            color_pattern = r'"color1":\s*\{[^}]*"title":\s*"([^"]+)'
            color_match = re.search(color_pattern, normalized)
            if color_match:
                attributes['color'] = color_match.group(1)
                logger.debug(f"JSON - Found color: {attributes['color']}")
            else:
                color_simple = r'"color":\s*"([^"]+)'
                color_simple_match = re.search(color_simple, normalized)
                if color_simple_match:
                    attributes['color'] = color_simple_match.group(1)

        if not attributes['material']:
            material_pattern = r'"material":\s*\{[^}]*"title":\s*"([^"]+)'
            material_match = re.search(material_pattern, normalized)
            if material_match:
                attributes['material'] = material_match.group(1)
                logger.debug(f"JSON - Found material: {attributes['material']}")

        # ===== Strategy 3: French label fallback =====
        # Pattern: "title":"Taille","value":"S"
        if not attributes['size_title'] or not attributes['condition_title'] or not attributes['color']:
            detail_pattern = r'"title":"(Taille|État|Couleur|Marque|Matière)","value":"([^"]+)"'
            detail_matches = re.findall(detail_pattern, normalized)

            for label, value in detail_matches:
                if label == 'Taille' and not attributes['size_title']:
                    attributes['size_title'] = value
                    logger.debug(f"Fallback - Found size: {value}")
                elif label == 'État' and not attributes['condition_title']:
                    attributes['condition_title'] = value
                    logger.debug(f"Fallback - Found condition: {value}")
                elif label == 'Couleur' and not attributes['color']:
                    attributes['color'] = value
                    logger.debug(f"Fallback - Found color: {value}")
                elif label == 'Matière' and not attributes['material']:
                    attributes['material'] = value
                    logger.debug(f"Fallback - Found material: {value}")

        return attributes

    @staticmethod
    def extract_attributes_from_description(description: str) -> dict:
        """
        Extract product attributes from structured description text.

        Vinted sellers often use structured formats in descriptions:
        - 🧵 Matière : Denim
        - 🎨 Couleur : Bleu
        - 📏 Taille : M / W32
        - ✨ État : Très bon état
        - 👔 Marque : Levi's

        This is a FALLBACK when HTML extraction fails.

        Args:
            description: Product description text

        Returns:
            Dict with extracted attributes
        """
        if not description:
            return {}

        attributes = {}

        # Normalize description (handle various line endings)
        text = description.replace('\\n', '\n').replace('\r', '')

        # ===== Pattern definitions =====
        # Each tuple: (attribute_key, list of regex patterns)
        patterns = {
            'material': [
                r'(?:🧵|matière|matiere|composition|tissu)\s*[:\-=]\s*(.+?)(?:\n|$|[,;])',
                r'(?:fabric|material)\s*[:\-=]\s*(.+?)(?:\n|$|[,;])',
                r'en\s+(coton|lin|laine|soie|polyester|denim|cuir|velours|cachemire)',
            ],
            'color': [
                r'(?:🎨|couleur|color)\s*[:\-=]\s*(.+?)(?:\n|$|[,;])',
                r'(?:coloris|teinte)\s*[:\-=]\s*(.+?)(?:\n|$|[,;])',
            ],
            'size_title': [
                r'(?:📏|taille|size)\s*(?:estimée|estimate)?\s*[:\-=]\s*(.+?)(?:\n|$|[,;])',
                r'taille\s+([A-Z]{1,3}|\d{2,3}(?:/\d{2,3})?|W\d+(?:/L\d+)?)',
            ],
            'condition_title': [
                r'(?:✨|état|etat|condition)\s*[:\-=]\s*(.+?)(?:\n|$|[,;])',
                r'(neuf|très bon état|bon état|satisfaisant)',
            ],
            'brand_name': [
                r'(?:👔|🏷️|marque|brand)\s*[:\-=]\s*(.+?)(?:\n|$|[,;])',
            ],
            'measurements': [
                r'(?:📐|dimensions?|mesures?)\s*[:\-=]\s*(.+?)(?:\n|$|[,;])',
                r'(?:longueur|length)\s*[:\-=]\s*(\d+\s*cm)',
                r'(?:largeur|width)\s*[:\-=]\s*(\d+\s*cm)',
            ],
        }

        for attr_key, attr_patterns in patterns.items():
            if attr_key in attributes:
                continue  # Already found

            for pattern in attr_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    value = match.group(1).strip()
                    # Clean up the value
                    value = re.sub(r'\s+', ' ', value)  # Normalize whitespace
                    value = value.strip('.,;:- ')  # Remove trailing punctuation
                    if value and len(value) > 1:  # Avoid single char matches
                        attributes[attr_key] = value
                        logger.debug(
                            f"Extracted {attr_key} from description: '{value}'"
                        )
                        break

        # ===== Special case: parse measurement dimensions =====
        if 'measurements' in attributes:
            dims = VintedDataExtractor._parse_measurements(attributes['measurements'])
            if dims:
                if dims.get('width'):
                    attributes['measurement_width'] = dims['width']
                if dims.get('length'):
                    attributes['measurement_length'] = dims['length']

        # Also try to extract dimensions from full description
        if 'measurement_width' not in attributes:
            width_match = re.search(
                r'(?:largeur|width|l)\s*[:\-=]?\s*(\d+)\s*cm',
                text, re.IGNORECASE
            )
            if width_match:
                attributes['measurement_width'] = int(width_match.group(1))

        if 'measurement_length' not in attributes:
            length_match = re.search(
                r'(?:longueur|length|L)\s*[:\-=]?\s*(\d+)\s*cm',
                text
            )
            if length_match:
                attributes['measurement_length'] = int(length_match.group(1))

        return attributes

    @staticmethod
    def _parse_measurements(measurement_str: str) -> dict | None:
        """
        Parse measurement string like "l 47 cm / L 70 cm".

        Args:
            measurement_str: Measurement string from Vinted

        Returns:
            dict with 'width' and 'length' in cm, or None
        """
        if not measurement_str:
            return None

        result = {}

        # Pattern for "l XX cm" (width/largeur)
        width_match = re.search(r'l\s*(\d+)\s*cm', measurement_str, re.IGNORECASE)
        if width_match:
            result['width'] = int(width_match.group(1))

        # Pattern for "L XX cm" (length/longueur)
        length_match = re.search(r'L\s*(\d+)\s*cm', measurement_str)
        if length_match:
            result['length'] = int(length_match.group(1))

        # Alternative pattern: "XX x YY cm"
        if not result:
            alt_match = re.search(r'(\d+)\s*[xX×]\s*(\d+)\s*cm', measurement_str)
            if alt_match:
                result['width'] = int(alt_match.group(1))
                result['length'] = int(alt_match.group(2))

        return result if result else None

    @staticmethod
    def _extract_description_from_html(html: str, title: str | None = None) -> str | None:
        """
        Extract product description from HTML.

        Uses multiple strategies:
        1. Find "TITLE - DESCRIPTION" pattern matching the product title (most accurate)
        2. Search in RSC push blocks, filtering out HTML content
        3. Standard JSON patterns for description field

        Args:
            html: Full HTML content
            title: Product title (optional, helps find description accurately)

        Returns:
            Description text or None
        """
        # Normalize HTML to handle escaped quotes
        normalized = VintedDataExtractor._normalize_html_content(html)

        # ===== Strategy 1: Match "TITLE - DESCRIPTION" pattern =====
        # The real description in Vinted is often in format:
        # "PRODUCT TITLE - Description text with emojis and hashtags..."
        if title and len(title) > 20:
            title_start = title[:30]
            title_idx = normalized.find(title_start + ' - ')
            if title_idx != -1:
                # Find end of this text block (next quote or end)
                end_idx = normalized.find('"', title_idx + len(title_start) + 10)
                if end_idx != -1 and end_idx - title_idx < 5000:
                    full_text = normalized[title_idx:end_idx]
                    dash_idx = full_text.find(' - ')
                    if dash_idx > 0:
                        description = full_text[dash_idx + 3:]
                        # Clean up description
                        description = description.replace('\\n', '\n')
                        description = description.replace('\\r', '')
                        logger.debug(f"Strategy 1 - Found description via title match: {description[:50]}...")
                        return description

        # ===== Strategy 2: Search RSC push blocks =====
        # Pattern: self.__next_f.push([1,"content"])
        # Filter out HTML content (legal/GDPR text contains \u003c)
        push_pattern = r'self\.__next_f\.push\(\[1,"([^"]+)"\]\)'
        push_matches = re.findall(push_pattern, normalized)

        for text in push_matches:
            # SKIP if contains HTML tags (legal/privacy content)
            if '\\u003c' in text or '<p>' in text or '<ol>' in text:
                continue

            # Look for product description indicators
            has_product_emojis = any(emoji in text for emoji in ['✨', '📦', '🏷️', '📋', '🔥', '👖', '🧵', '👔'])
            has_hashtags = '#' in text
            has_dash = ' - ' in text

            if (has_product_emojis or has_hashtags) and len(text) > 100 and len(text) < 5000:
                # Extract description after title separator
                if has_dash:
                    dash_idx = text.find(' - ')
                    if 20 < dash_idx < 150:
                        description = text[dash_idx + 3:]
                        description = description.replace('\\n', '\n')
                        description = description.replace('\\r', '')
                        logger.debug(f"Strategy 2 - Found description in RSC push: {description[:50]}...")
                        return description

        # ===== Strategy 3: Standard JSON patterns =====
        # Description in plugins section
        desc_pattern = r'"description":\s*\{\s*"section_title"[^}]*"description":\s*"([^"]*)"'
        desc_match = re.search(desc_pattern, normalized)
        if desc_match:
            description = desc_match.group(1)
            description = description.replace('\\n', '\n')
            description = description.replace('\\r', '')
            logger.debug(f"Strategy 3 - Found description in plugins: {description[:50]}...")
            return description

        # Alternative pattern for simple description (at least 10 chars)
        alt_pattern = r'"description":\s*"([^"]{10,})"'
        alt_match = re.search(alt_pattern, normalized)
        if alt_match:
            description = alt_match.group(1)
            # Verify it's not HTML content
            if '\\u003c' not in description and '<p>' not in description:
                description = description.replace('\\n', '\n')
                description = description.replace('\\r', '')
                logger.debug(f"Strategy 3b - Found simple description: {description[:50]}...")
                return description

        return None
