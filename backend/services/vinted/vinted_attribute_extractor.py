"""
Vinted Attribute Extractor - Extraction des attributs produit

Extrait les attributs depuis le HTML Vinted (taille, couleur, matiere, etc.)
et depuis les descriptions textuelles structurees.

Author: Claude
Date: 2025-12-22
"""

import re
from typing import Any

from shared.logging_setup import get_logger

logger = get_logger(__name__)


class VintedAttributeExtractor:
    """
    Extracteur d'attributs pour les produits Vinted.

    Gere l'extraction depuis:
    - HTML Next.js Flight data (RSC format)
    - Descriptions textuelles structurees
    """

    @staticmethod
    def normalize_html_content(html: str) -> str:
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
        normalized = html.replace('\\"', '"')
        normalized = normalized.replace('\\\\', '\\')
        return normalized

    @staticmethod
    def extract_attributes_from_html(html: str) -> dict:
        """
        Extract all product attributes from HTML.

        Uses multiple extraction strategies with normalized content:
        1. RSC format patterns (React Server Components)
        2. JSON attribute blocks with "code"/"data" pattern
        3. Alternative JSON patterns found in Next.js data
        4. Fallback: French label patterns ("Taille", "Etat", etc.)

        Handles all known attribute types:
        - size: Taille (with id)
        - status: Etat/Condition (with id)
        - color: Couleur
        - material: Matiere
        - measurements: Dimensions (l x L)
        - brand: Marque (with id)
        - manufacturer_labelling: Etiquetage
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

        normalized = VintedAttributeExtractor.normalize_html_content(html)

        # ===== Strategy 1: RSC format patterns (most reliable) =====
        attributes = VintedAttributeExtractor._extract_rsc_attributes(
            normalized, attributes
        )

        # ===== Strategy 2: Alternative JSON patterns =====
        attributes = VintedAttributeExtractor._extract_json_attributes(
            normalized, attributes
        )

        # ===== Strategy 3: French label fallback =====
        attributes = VintedAttributeExtractor._extract_french_label_attributes(
            normalized, attributes
        )

        return attributes

    @staticmethod
    def _extract_rsc_attributes(normalized: str, attributes: dict) -> dict:
        """Extract attributes from RSC format patterns."""
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
                logger.debug(
                    f"RSC - Found size: {attributes['size_title']} "
                    f"(id: {attributes['size_id']})"
                )
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
                logger.debug(
                    f"RSC - Found condition: {attributes['condition_title']} "
                    f"(id: {attributes['condition_id']})"
                )
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
                dims = VintedAttributeExtractor.parse_measurements(
                    attributes['measurements']
                )
                if dims:
                    attributes['measurement_width'] = dims.get('width')
                    attributes['measurement_length'] = dims.get('length')
                logger.debug(
                    f"RSC - Found measurements: {attributes['measurements']}"
                )
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
                logger.debug(
                    f"RSC - Found manufacturer_labelling: "
                    f"{attributes['manufacturer_labelling']}"
                )
                break

        return attributes

    @staticmethod
    def _extract_json_attributes(normalized: str, attributes: dict) -> dict:
        """Extract attributes from alternative JSON patterns."""
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

        return attributes

    @staticmethod
    def _extract_french_label_attributes(normalized: str, attributes: dict) -> dict:
        """Extract attributes from French label fallback patterns."""
        if (not attributes['size_title'] or not attributes['condition_title']
                or not attributes['color']):
            detail_pattern = (
                r'"title":"(Taille|État|Couleur|Marque|Matière)",'
                r'"value":"([^"]+)"'
            )
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
        - Matiere : Denim
        - Couleur : Bleu
        - Taille : M / W32
        - Etat : Tres bon etat
        - Marque : Levi's

        This is a FALLBACK when HTML extraction fails.

        Args:
            description: Product description text

        Returns:
            Dict with extracted attributes
        """
        if not description:
            return {}

        attributes = {}
        text = description.replace('\\n', '\n').replace('\r', '')

        patterns = {
            'material': [
                r'(?:matière|matiere|composition|tissu)\s*[:\-=]\s*(.+?)(?:\n|$|[,;])',
                r'(?:fabric|material)\s*[:\-=]\s*(.+?)(?:\n|$|[,;])',
                r'en\s+(coton|lin|laine|soie|polyester|denim|cuir|velours|cachemire)',
            ],
            'color': [
                r'(?:couleur|color)\s*[:\-=]\s*(.+?)(?:\n|$|[,;])',
                r'(?:coloris|teinte)\s*[:\-=]\s*(.+?)(?:\n|$|[,;])',
            ],
            'size_title': [
                r'(?:taille|size)\s*(?:estimée|estimate)?\s*[:\-=]\s*(.+?)(?:\n|$|[,;])',
                r'taille\s+([A-Z]{1,3}|\d{2,3}(?:/\d{2,3})?|W\d+(?:/L\d+)?)',
            ],
            'condition_title': [
                r'(?:état|etat|condition)\s*[:\-=]\s*(.+?)(?:\n|$|[,;])',
                r'(neuf|très bon état|bon état|satisfaisant)',
            ],
            'brand_name': [
                r'(?:marque|brand)\s*[:\-=]\s*(.+?)(?:\n|$|[,;])',
            ],
            'measurements': [
                r'(?:dimensions?|mesures?)\s*[:\-=]\s*(.+?)(?:\n|$|[,;])',
                r'(?:longueur|length)\s*[:\-=]\s*(\d+\s*cm)',
                r'(?:largeur|width)\s*[:\-=]\s*(\d+\s*cm)',
            ],
        }

        for attr_key, attr_patterns in patterns.items():
            if attr_key in attributes:
                continue

            for pattern in attr_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    value = match.group(1).strip()
                    value = re.sub(r'\s+', ' ', value)
                    value = value.strip('.,;:- ')
                    if value and len(value) > 1:
                        attributes[attr_key] = value
                        logger.debug(
                            f"Extracted {attr_key} from description: '{value}'"
                        )
                        break

        # Parse measurement dimensions
        if 'measurements' in attributes:
            dims = VintedAttributeExtractor.parse_measurements(
                attributes['measurements']
            )
            if dims:
                if dims.get('width'):
                    attributes['measurement_width'] = dims['width']
                if dims.get('length'):
                    attributes['measurement_length'] = dims['length']

        # Extract dimensions from full description
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
    def parse_measurements(measurement_str: str) -> dict | None:
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
    def extract_description_from_html(html: str, title: str | None = None) -> str | None:
        """
        Extract product description from HTML.

        Uses multiple strategies:
        1. Find "TITLE - DESCRIPTION" pattern matching the product title
        2. Search in RSC push blocks, filtering out HTML content
        3. Standard JSON patterns for description field

        Args:
            html: Full HTML content
            title: Product title (optional, helps find description accurately)

        Returns:
            Description text or None
        """
        normalized = VintedAttributeExtractor.normalize_html_content(html)

        # ===== Strategy 1: Match "TITLE - DESCRIPTION" pattern =====
        if title and len(title) > 20:
            title_start = title[:30]
            title_idx = normalized.find(title_start + ' - ')
            if title_idx != -1:
                end_idx = normalized.find('"', title_idx + len(title_start) + 10)
                if end_idx != -1 and end_idx - title_idx < 5000:
                    full_text = normalized[title_idx:end_idx]
                    dash_idx = full_text.find(' - ')
                    if dash_idx > 0:
                        description = full_text[dash_idx + 3:]
                        description = description.replace('\\n', '\n')
                        description = description.replace('\\r', '')
                        logger.debug(
                            f"Strategy 1 - Found description via title match: "
                            f"{description[:50]}..."
                        )
                        return description

        # ===== Strategy 2: Search RSC push blocks =====
        push_pattern = r'self\.__next_f\.push\(\[1,"([^"]+)"\]\)'
        push_matches = re.findall(push_pattern, normalized)

        for text in push_matches:
            if '\\u003c' in text or '<p>' in text or '<ol>' in text:
                continue

            has_product_indicators = (
                any(char in text for char in ['#']) or
                ' - ' in text
            )

            if has_product_indicators and 100 < len(text) < 5000:
                if ' - ' in text:
                    dash_idx = text.find(' - ')
                    if 20 < dash_idx < 150:
                        description = text[dash_idx + 3:]
                        description = description.replace('\\n', '\n')
                        description = description.replace('\\r', '')
                        logger.debug(
                            f"Strategy 2 - Found description in RSC push: "
                            f"{description[:50]}..."
                        )
                        return description

        # ===== Strategy 3: Standard JSON patterns =====
        desc_pattern = (
            r'"description":\s*\{\s*"section_title"[^}]*'
            r'"description":\s*"([^"]*)"'
        )
        desc_match = re.search(desc_pattern, normalized)
        if desc_match:
            description = desc_match.group(1)
            description = description.replace('\\n', '\n')
            description = description.replace('\\r', '')
            logger.debug(
                f"Strategy 3 - Found description in plugins: {description[:50]}..."
            )
            return description

        # Alternative pattern for simple description
        alt_pattern = r'"description":\s*"([^"]{10,})"'
        alt_match = re.search(alt_pattern, normalized)
        if alt_match:
            description = alt_match.group(1)
            if '\\u003c' not in description and '<p>' not in description:
                description = description.replace('\\n', '\n')
                description = description.replace('\\r', '')
                logger.debug(
                    f"Strategy 3b - Found simple description: {description[:50]}..."
                )
                return description

        return None
