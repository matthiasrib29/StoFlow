"""
Vinted Item Upload API Parser

Parses the JSON response from /api/v2/item_upload/items/{id} endpoint.
This endpoint returns structured product data for the seller's own items.

Much more reliable than HTML parsing as it returns clean JSON data.
"""
import logging
from typing import Any, Optional
from decimal import Decimal

logger = logging.getLogger(__name__)


class VintedItemUploadParser:
    """
    Parser for Vinted item_upload API responses.

    The /api/v2/item_upload/items/{id} endpoint returns complete product data
    in a structured JSON format, making it the preferred method for getting
    product details.
    """

    @staticmethod
    def parse_item_response(response_data: dict) -> Optional[dict]:
        """
        Parse the full response from /api/v2/item_upload/items/{id}.

        Args:
            response_data: The raw API response containing {"item": {...}}

        Returns:
            Parsed product data dict ready for VintedProduct model, or None if invalid
        """
        if not response_data:
            logger.warning("Empty response data")
            return None

        item = response_data.get("item")
        if not item:
            logger.warning("No 'item' key in response")
            return None

        return VintedItemUploadParser.parse_item(item)

    @staticmethod
    def parse_item(item: dict) -> Optional[dict]:
        """
        Parse a single item from the item_upload API.

        Args:
            item: The item dict from the API response

        Returns:
            Parsed product data dict ready for VintedProduct model
        """
        if not item:
            return None

        try:
            vinted_id = item.get("id")
            if not vinted_id:
                logger.warning("Item has no id")
                return None

            # Parse price
            price_data = item.get("price", {})
            price = VintedItemUploadParser._parse_price(price_data)
            currency = price_data.get("currency_code", "EUR") if isinstance(price_data, dict) else "EUR"

            # Parse brand
            brand_dto = item.get("brand_dto", {})
            brand_name = brand_dto.get("title") if brand_dto else None

            # Parse photos
            photos = item.get("photos", [])
            photos_data = VintedItemUploadParser._parse_photos(photos)
            # Use full_size_url for original quality (not f800 resized)
            photo_url = (
                photos[0].get("full_size_url") or photos[0].get("url")
            ) if photos else None

            # Build parsed data dict matching VintedProduct model fields
            parsed = {
                # Core identifiers
                "vinted_id": vinted_id,

                # Basic info
                "title": item.get("title"),
                "description": item.get("description"),
                "price": price,
                "currency": currency,

                # Categorization with Vinted IDs
                "brand": brand_name,
                "brand_id": item.get("brand_id"),
                "size_id": item.get("size_id"),
                "catalog_id": item.get("catalog_id"),

                # Colors (new fields from item_upload API)
                "color": item.get("color1"),
                "color1_id": item.get("color1_id"),
                "color2": item.get("color2"),
                "color2_id": item.get("color2_id"),

                # Condition/Status
                "condition": item.get("status"),  # API "status" = our "condition"
                "status_id": item.get("status_id"),

                # Dimensions
                "measurement_width": item.get("measurement_width"),
                "measurement_length": item.get("measurement_length"),
                "measurement_unit": item.get("measurement_unit"),

                # Additional fields from item_upload API
                "is_unisex": bool(item.get("is_unisex", 0)),
                "is_draft": item.get("is_draft", False),
                "manufacturer": item.get("manufacturer"),
                "manufacturer_labelling": item.get("manufacturer_labelling"),
                "model": item.get("model"),
                "item_attributes": item.get("item_attributes", []),

                # Photos
                "photo_url": photo_url,
                "photos_data": photos_data,

                # URL (constructed)
                "url": f"https://www.vinted.fr/items/{vinted_id}",
            }

            # Add brand_dto info if available
            if brand_dto:
                parsed["brand_slug"] = brand_dto.get("slug")

            logger.debug(f"Parsed item {vinted_id}: {parsed.get('title', 'No title')}")
            return parsed

        except Exception as e:
            logger.error(f"Error parsing item: {e}", exc_info=True)
            return None

    @staticmethod
    def _parse_price(price_data: Any) -> Optional[Decimal]:
        """
        Parse price from various formats.

        Args:
            price_data: Can be dict {"amount": "20.9", "currency_code": "EUR"}
                        or direct numeric value

        Returns:
            Decimal price or None
        """
        if not price_data:
            return None

        try:
            if isinstance(price_data, dict):
                amount = price_data.get("amount")
                if amount is not None:
                    return Decimal(str(amount))
            elif isinstance(price_data, (int, float, str)):
                return Decimal(str(price_data))
        except Exception as e:
            logger.warning(f"Failed to parse price {price_data}: {e}")

        return None

    @staticmethod
    def _parse_photos(photos: list) -> list:
        """
        Parse photos array, extracting essential data.

        Args:
            photos: Array of photo objects from API

        Returns:
            Simplified photos array with essential fields
        """
        if not photos:
            return []

        parsed_photos = []
        for photo in photos:
            if not isinstance(photo, dict):
                continue

            parsed_photo = {
                "id": photo.get("id"),
                "url": photo.get("url"),
                "full_size_url": photo.get("full_size_url"),
                "is_main": photo.get("is_main", False),
                "image_no": photo.get("image_no"),
                "width": photo.get("width"),
                "height": photo.get("height"),
                "dominant_color": photo.get("dominant_color"),
            }

            # Add high resolution info if available
            high_res = photo.get("high_resolution")
            if high_res:
                parsed_photo["high_resolution"] = {
                    "id": high_res.get("id"),
                    "timestamp": high_res.get("timestamp"),
                }

            # Add thumbnails if present
            thumbnails = photo.get("thumbnails")
            if thumbnails:
                parsed_photo["thumbnails"] = [
                    {
                        "type": t.get("type"),
                        "url": t.get("url"),
                        "width": t.get("width"),
                        "height": t.get("height"),
                    }
                    for t in thumbnails if isinstance(t, dict)
                ]

            parsed_photos.append(parsed_photo)

        return parsed_photos

    @staticmethod
    def extract_published_at(photos: list) -> Optional[str]:
        """
        Extract publication date from photo timestamps.

        The first photo's high_resolution.timestamp often indicates when
        the item was first listed.

        Args:
            photos: Array of photo objects

        Returns:
            ISO timestamp string or None
        """
        if not photos:
            return None

        for photo in photos:
            if not isinstance(photo, dict):
                continue
            high_res = photo.get("high_resolution", {})
            timestamp = high_res.get("timestamp")
            if timestamp:
                # Vinted uses Unix timestamps
                try:
                    from datetime import datetime, timezone
                    dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
                    return dt.isoformat()
                except Exception:
                    pass

        return None
