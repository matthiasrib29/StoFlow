"""
Vinted HTML Parser - Extraction depuis les pages HTML Vinted

Parse le HTML Next.js Flight data pour extraire les donnees produit,
photos, et informations vendeur.

Author: Claude
Date: 2025-12-22
"""

import json
import re
from datetime import datetime
from typing import Any

from shared.logging_setup import get_logger
from services.vinted.vinted_attribute_extractor import VintedAttributeExtractor

logger = get_logger(__name__)


class VintedHtmlParser:
    """
    Parser HTML pour les pages produit Vinted.

    Extrait les donnees depuis le format Next.js Flight data (RSC).
    """

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

        pattern = r'self\.__next_f\.push\(\s*\[(.*?)\]\s*\)'
        matches = re.findall(pattern, html, re.DOTALL)

        for match in matches:
            try:
                clean_match = match.strip()

                if ',"' in clean_match:
                    json_start = clean_match.index(',"') + 2
                    json_content = clean_match[json_start:-1]
                    json_content = json_content.encode().decode('unicode_escape')

                    if (json_content.strip().startswith('{') or
                            json_content.strip().startswith('[')):
                        try:
                            parsed = json.loads(json_content)
                            chunks.append(parsed)
                        except json.JSONDecodeError:
                            pass
            except Exception:
                continue

        return chunks

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
            normalized = VintedAttributeExtractor.normalize_html_content(html)

            # Try JSON pattern in Next.js flight data
            item_pattern = r'"item":\s*\{[^}]*"id":\s*(\d+)[^}]*"title"'
            item_match = re.search(item_pattern, normalized)

            if not item_match:
                logger.debug("No JSON item pattern, trying meta tags extraction")
                return VintedHtmlParser._extract_from_meta_tags(normalized)

            item_id = item_match.group(1)

            result = VintedHtmlParser._init_result_dict(int(item_id))

            # Extract basic fields
            result = VintedHtmlParser._extract_basic_fields(html, item_id, result)

            # Extract seller info
            result = VintedHtmlParser._extract_seller_info(html, result)

            # Extract fees
            result = VintedHtmlParser._extract_fees(html, result)

            # Extract status flags
            result = VintedHtmlParser._extract_status_flags(html, result)

            # Extract photos (with timestamps)
            photos = VintedHtmlParser.extract_photos_from_html(html)
            if photos:
                result['photos'] = photos
                published_at = VintedHtmlParser._extract_published_at_from_photos(
                    photos
                )
                if published_at:
                    result['published_at'] = published_at

            # Extract attributes (size, condition, color)
            attributes = VintedAttributeExtractor.extract_attributes_from_html(html)
            if attributes.get('upload_date'):
                result['upload_date_text'] = attributes.pop('upload_date')
            result.update(attributes)

            # Extract description
            description = VintedAttributeExtractor.extract_description_from_html(
                html, title=result.get('title')
            )
            if description:
                result['description'] = description

            # Fallback: Extract attributes from description text
            desc_attrs = VintedAttributeExtractor.extract_attributes_from_description(
                result.get('description', '')
            )
            for key, value in desc_attrs.items():
                if value and not result.get(key):
                    result[key] = value
                    logger.debug(f"Filled {key} from description: {value}")

            logger.debug(
                f"Extracted product {item_id}: {result.get('title', 'N/A')}"
            )
            return result

        except Exception as e:
            logger.error(f"Error extracting product from HTML: {e}")
            return None

    @staticmethod
    def _init_result_dict(vinted_id: int) -> dict:
        """Initialize the result dictionary with default values."""
        return {
            'vinted_id': vinted_id,
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

    @staticmethod
    def _extract_basic_fields(html: str, item_id: str, result: dict) -> dict:
        """Extract basic product fields from HTML."""
        # Title
        title_pattern = rf'"id":{item_id},"title":"([^"]+)"'
        title_match = re.search(title_pattern, html)
        if title_match:
            result['title'] = title_match.group(1)

        # Catalog ID
        catalog_pattern = r'"catalog_id\\?":\s*(\d+)'
        catalog_match = re.search(catalog_pattern, html)
        if catalog_match:
            result['catalog_id'] = int(catalog_match.group(1))

        # Price
        price_pattern = r'"price":\s*\{\s*"amount":\s*"([^"]+)"'
        price_match = re.search(price_pattern, html)
        if price_match:
            try:
                result['price'] = float(price_match.group(1))
            except ValueError:
                pass

        # Currency
        currency_pattern = r'"currency_code":\s*"([A-Z]{3})"'
        currency_match = re.search(currency_pattern, html)
        if currency_match:
            result['currency'] = currency_match.group(1)

        # Brand
        brand_dto_pattern = (
            r'"brand_dto\\?":\s*\{[^}]*"id\\?":\s*(\d+)[^}]*'
            r'"title\\?":\s*"([^"\\]+)'
        )
        brand_match = re.search(brand_dto_pattern, html)
        if brand_match:
            result['brand_id'] = int(brand_match.group(1))
            result['brand_name'] = brand_match.group(2)
        else:
            brand_id_pattern = r'"brand_id\\?":\s*(\d+)'
            brand_id_match = re.search(brand_id_pattern, html)
            if brand_id_match:
                result['brand_id'] = int(brand_id_match.group(1))

        return result

    @staticmethod
    def _extract_seller_info(html: str, result: dict) -> dict:
        """Extract seller information from HTML."""
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

        return result

    @staticmethod
    def _extract_fees(html: str, result: dict) -> dict:
        """Extract fee information from HTML."""
        # Service fee
        service_fee_pattern = r'"service_fee\\?":\s*\{[^}]*"amount\\?":\s*"?([0-9.]+)'
        service_fee_match = re.search(service_fee_pattern, html)
        if service_fee_match:
            try:
                result['service_fee'] = float(service_fee_match.group(1))
            except ValueError:
                pass

        # Buyer protection fee
        bp_pattern = (
            r'"buyerProtection\\?"[^}]*"finalPrice\\?"[^}]*'
            r'"amount\\?":\s*"?([0-9.]+)'
        )
        bp_match = re.search(bp_pattern, html)
        if bp_match:
            try:
                result['buyer_protection_fee'] = float(bp_match.group(1))
            except ValueError:
                pass

        # Shipping price
        shipping_pattern = (
            r'"shippingDetails\\?"[^}]*"price\\?"[^}]*"amount\\?":\s*"?([\d.]+)'
        )
        shipping_match = re.search(shipping_pattern, html)
        if shipping_match:
            try:
                result['shipping_price'] = float(shipping_match.group(1))
            except ValueError:
                pass

        # Total item price
        total_price_pattern = (
            r'"total_item_price\\?":\s*\{[^}]*"amount\\?":\s*"?([0-9.]+)'
        )
        total_price_match = re.search(total_price_pattern, html)
        if total_price_match:
            try:
                result['total_item_price'] = float(total_price_match.group(1))
            except ValueError:
                pass

        return result

    @staticmethod
    def _extract_status_flags(html: str, result: dict) -> dict:
        """Extract status flags from HTML."""
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
        return result

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
        result = VintedHtmlParser._init_result_dict(None)

        # Extract from meta tags
        result = VintedHtmlParser._extract_from_og_meta(html, result)

        # Extract attributes
        attributes = VintedAttributeExtractor.extract_attributes_from_html(html)
        if attributes.get('upload_date'):
            result['upload_date_text'] = attributes.pop('upload_date')
        result.update(attributes)

        # Extract description from plugins section
        plugins_desc = VintedAttributeExtractor.extract_description_from_html(
            html, title=result.get('title')
        )
        if plugins_desc:
            result['description'] = plugins_desc

        # Fallback: Extract attributes from description text
        desc_attrs = VintedAttributeExtractor.extract_attributes_from_description(
            result.get('description', '')
        )
        for key, value in desc_attrs.items():
            if value and not result.get(key):
                result[key] = value
                logger.debug(f"Meta fallback - filled {key} from description: {value}")

        # Extract photos with timestamps
        photos = VintedHtmlParser.extract_photos_from_html(html)
        if photos:
            result['photos'] = photos
            published_at = VintedHtmlParser._extract_published_at_from_photos(photos)
            if published_at:
                result['published_at'] = published_at

        # Extract price, brand, seller from JSON patterns
        result = VintedHtmlParser._extract_basic_fields_fallback(html, result)

        # Only return if we got meaningful data
        has_data = (
            result['description'] or
            result['material'] or
            result['color'] or
            result['size_title']
        )

        if has_data:
            logger.info(
                f"Meta/attributes extraction for product "
                f"{result.get('vinted_id', 'unknown')}: "
                f"description={'Yes' if result['description'] else 'No'}, "
                f"material={result.get('material', 'No')}, "
                f"color={result.get('color', 'No')}, "
                f"size={result.get('size_title', 'No')}"
            )
            return result

        logger.warning(
            f"Meta extraction failed for product {result.get('vinted_id', 'unknown')} - "
            f"title={result.get('title', 'No')}, "
            f"description={'Yes' if result.get('description') else 'No'}, "
            f"price={result.get('price', 'No')}"
        )
        return None

    @staticmethod
    def _extract_from_og_meta(html: str, result: dict) -> dict:
        """Extract data from Open Graph meta tags."""
        # Description
        desc_pattern = r'<meta\s+name="description"\s+content="([^"]+)"'
        desc_match = re.search(desc_pattern, html, re.IGNORECASE)
        if desc_match:
            result['description'] = desc_match.group(1)
            logger.debug(f"Extracted description from meta: {result['description'][:50]}...")

        if not result['description']:
            og_desc_pattern = r'<meta\s+property="og:description"\s+content="([^"]+)"'
            og_desc_match = re.search(og_desc_pattern, html, re.IGNORECASE)
            if og_desc_match:
                result['description'] = og_desc_match.group(1)

        # Title
        og_title_pattern = r'<meta\s+property="og:title"\s+content="([^"]+)"'
        og_title_match = re.search(og_title_pattern, html, re.IGNORECASE)
        if og_title_match:
            result['title'] = og_title_match.group(1)

        # Vinted ID from URL
        og_url_pattern = r'<meta\s+property="og:url"\s+content="[^"]*items/(\d+)-[^"]*"'
        og_url_match = re.search(og_url_pattern, html, re.IGNORECASE)
        if og_url_match:
            result['vinted_id'] = int(og_url_match.group(1))

        # Image
        og_image_pattern = r'<meta\s+property="og:image"\s+content="([^"]+)"'
        og_image_match = re.search(og_image_pattern, html, re.IGNORECASE)
        if og_image_match:
            result['photo_url'] = og_image_match.group(1)

        return result

    @staticmethod
    def _extract_basic_fields_fallback(html: str, result: dict) -> dict:
        """Extract basic fields as fallback."""
        normalized = VintedAttributeExtractor.normalize_html_content(html)

        # Price
        price_pattern = r'"price\\?":\s*\{[^}]*"amount\\?":\s*"?([0-9.]+)'
        price_match = re.search(price_pattern, normalized)
        if price_match:
            try:
                result['price'] = float(price_match.group(1))
            except ValueError:
                pass

        # Brand
        brand_dto_pattern = (
            r'"brand_dto\\?":\s*\{[^}]*"id\\?":\s*(\d+)[^}]*'
            r'"title\\?":\s*"([^"\\]+)'
        )
        brand_match = re.search(brand_dto_pattern, normalized)
        if brand_match:
            result['brand_id'] = int(brand_match.group(1))
            result['brand_name'] = brand_match.group(2)
        else:
            brand_id_pattern = r'"brand_id\\?":\s*(\d+)'
            brand_id_match = re.search(brand_id_pattern, normalized)
            if brand_id_match:
                result['brand_id'] = int(brand_id_match.group(1))

        # Seller
        seller_pattern = r'"seller_id\\?":\s*(\d+)'
        seller_match = re.search(seller_pattern, normalized)
        if seller_match:
            result['seller_id'] = int(seller_match.group(1))

        login_pattern = r'"login\\?":\s*"([^"\\]+)'
        login_match = re.search(login_pattern, normalized)
        if login_match:
            result['seller_login'] = login_match.group(1)

        # Status flags
        if '"is_draft\\":true' in normalized or '"is_draft":true' in normalized:
            result['is_draft'] = True
        if '"is_closed\\":true' in normalized or '"is_closed":true' in normalized:
            result['is_closed'] = True

        # Catalog ID
        catalog_pattern = r'"catalog_id\\?":\s*(\d+)'
        catalog_match = re.search(catalog_pattern, normalized)
        if catalog_match:
            result['catalog_id'] = int(catalog_match.group(1))

        return result

    @staticmethod
    def extract_photos_from_html(html: str) -> list[dict]:
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

        normalized = VintedAttributeExtractor.normalize_html_content(html)

        # Strategy 1: full_size_url pattern (best quality)
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
                    logger.debug(
                        f"Strategy 1 - Found {len(photos)} photos via full_size_url"
                    )
                    break

        # Strategy 2: Photo block pattern with timestamps
        if not photos:
            photo_block_pattern = (
                r'\{"id":\d+[^}]*"url":"(https://images1\.vinted\.net[^"]+)"[^}]*\}'
            )
            photo_blocks = re.findall(photo_block_pattern, normalized)

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

                if i < len(timestamps):
                    try:
                        photo['timestamp'] = int(timestamps[i])
                    except ValueError:
                        pass

                photos.append(photo)

            if photos:
                logger.debug(
                    f"Strategy 2 - Found {len(photos)} photos via block pattern"
                )

        # Strategy 3: Simple URL fallback
        if not photos:
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
                    logger.debug(
                        f"Strategy 3 - Found {len(photos)} photos via simple URL"
                    )
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

        first_photo = photos[0] if photos else None
        if first_photo and first_photo.get('timestamp'):
            try:
                timestamp = first_photo['timestamp']
                return datetime.fromtimestamp(timestamp)
            except (ValueError, OSError, OverflowError) as e:
                logger.debug(f"Failed to parse timestamp {timestamp}: {e}")
                return None

        for photo in photos:
            if photo.get('timestamp'):
                try:
                    return datetime.fromtimestamp(photo['timestamp'])
                except (ValueError, OSError, OverflowError):
                    continue

        return None
