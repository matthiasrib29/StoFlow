"""
Size Resolution Service

Parses and resolves raw size labels to normalized sizes and leg lengths.
Handles composite sizes like "W32/L34" by splitting waist and length.

Business Rules (Created: 2026-01-28):
- W32/L34 → size_normalized = "W32", size_length = "34"
- 32/34 → size_normalized = "32", size_length = "34"
- M, L, XL → size_normalized = "M", size_length = None
- One Size → size_normalized = "One Size", size_length = None

Categories that use size_length (bottoms):
- jeans, pants, chinos, cargo-pants, joggers
- shorts, bermuda, dress-pants, culottes, leggings
"""

import re
import logging
from typing import TypedDict

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class ParsedSize(TypedDict):
    """Result of parsing a composite size label."""
    waist: str | None  # e.g., "W32" or "32"
    length: str | None  # e.g., "34"
    normalized: str | None  # Clean size value for size_normalized
    original: str  # Original input


# Categories that have leg length attribute
BOTTOMS_CATEGORIES = frozenset([
    'jeans', 'pants', 'chinos', 'cargo-pants', 'joggers',
    'shorts', 'bermuda', 'dress-pants', 'culottes', 'leggings'
])

# Valid leg length values
VALID_LENGTHS = frozenset(['26', '28', '30', '32', '34', '36', '38'])


class SizeResolutionService:
    """
    Service for parsing and resolving size labels.

    Handles:
    - Composite sizes: W32/L34, 32/34, 32x34
    - Simple sizes: M, L, XL, 40, 42
    - One size: "One Size", "Unique", "TAILLE UNIQUE"
    """

    # Patterns for composite sizes (waist/length)
    # Match: W32/L34, W32xL34, W32-L34, W32 L34, 32/34, etc.
    WAIST_LENGTH_PATTERN = re.compile(
        r'^[Ww]?(\d{2})\s*[/xX\-\s]\s*[Ll]?(\d{2})$'
    )

    # Pattern for standalone length: L34, L 34
    STANDALONE_LENGTH_PATTERN = re.compile(r'^[Ll]\s*(\d{2})$')

    # Pattern for letter sizes
    LETTER_PATTERN = re.compile(
        r'^(XXS|XS|S|M|L|XL|XXL|XXXL|4XL|5XL)$',
        re.IGNORECASE
    )

    # One size patterns
    ONE_SIZE_PATTERNS = frozenset([
        'one size', 'unique', 'taille unique', 'os', 'u'
    ])

    @classmethod
    def parse_composite_size(cls, raw_label: str) -> ParsedSize:
        """
        Parse a raw size label into components.

        Args:
            raw_label: Raw size string (e.g., "W32/L34", "M", "42")

        Returns:
            ParsedSize with waist, length, normalized, and original

        Examples:
            >>> SizeResolutionService.parse_composite_size("W32/L34")
            {'waist': 'W32', 'length': '34', 'normalized': 'W32', 'original': 'W32/L34'}

            >>> SizeResolutionService.parse_composite_size("M")
            {'waist': None, 'length': None, 'normalized': 'M', 'original': 'M'}

            >>> SizeResolutionService.parse_composite_size("32/34")
            {'waist': '32', 'length': '34', 'normalized': '32', 'original': '32/34'}
        """
        if not raw_label:
            return ParsedSize(waist=None, length=None, normalized=None, original='')

        clean_label = raw_label.strip()

        # Check for waist/length pattern
        match = cls.WAIST_LENGTH_PATTERN.match(clean_label)
        if match:
            waist_num = match.group(1)
            length = match.group(2)

            # Determine if original had W prefix
            has_w_prefix = clean_label.upper().startswith('W')
            waist = f"W{waist_num}" if has_w_prefix else waist_num

            return ParsedSize(
                waist=waist,
                length=length if length in VALID_LENGTHS else None,
                normalized=waist,
                original=clean_label
            )

        # Check for standalone length (L34)
        match = cls.STANDALONE_LENGTH_PATTERN.match(clean_label)
        if match:
            length = match.group(1)
            return ParsedSize(
                waist=None,
                length=length if length in VALID_LENGTHS else None,
                normalized=None,
                original=clean_label
            )

        # Check for letter sizes
        if cls.LETTER_PATTERN.match(clean_label):
            return ParsedSize(
                waist=None,
                length=None,
                normalized=clean_label.upper(),
                original=clean_label
            )

        # Check for one size
        if clean_label.lower() in cls.ONE_SIZE_PATTERNS:
            return ParsedSize(
                waist=None,
                length=None,
                normalized='One Size',
                original=clean_label
            )

        # Default: return as-is
        return ParsedSize(
            waist=None,
            length=None,
            normalized=clean_label,
            original=clean_label
        )

    @classmethod
    def is_bottoms_category(cls, category: str | None) -> bool:
        """
        Check if a category is a bottoms category (has leg length).

        Args:
            category: Category name_en

        Returns:
            True if category uses leg length
        """
        if not category:
            return False
        return category.lower() in BOTTOMS_CATEGORIES

    @classmethod
    def resolve_size_for_product(
        cls,
        size_label: str | None,
        category: str | None
    ) -> tuple[str | None, str | None]:
        """
        Resolve a size label for a product, extracting size_length if applicable.

        Args:
            size_label: Raw size label from user input
            category: Product category

        Returns:
            Tuple of (size_normalized, size_length)
            - size_length is only set for bottoms categories with valid length

        Examples:
            >>> SizeResolutionService.resolve_size_for_product("W32/L34", "jeans")
            ('W32', '34')

            >>> SizeResolutionService.resolve_size_for_product("W32/L34", "t-shirts")
            ('W32/L34', None)  # Not a bottoms category, keep original

            >>> SizeResolutionService.resolve_size_for_product("M", "jeans")
            ('M', None)  # No length in label
        """
        if not size_label:
            return None, None

        parsed = cls.parse_composite_size(size_label)

        # Only extract length for bottoms categories
        if cls.is_bottoms_category(category):
            return parsed['normalized'], parsed['length']

        # For non-bottoms, return original label as normalized
        return parsed['original'], None

    @classmethod
    def extract_length_from_existing(
        cls,
        size_normalized: str | None,
        size_original: str | None,
        category: str | None
    ) -> str | None:
        """
        Extract size_length from existing product data.

        Used for data migration - tries size_normalized first, then size_original.

        Args:
            size_normalized: Current size_normalized value
            size_original: Current size_original value
            category: Product category

        Returns:
            Extracted length or None
        """
        if not cls.is_bottoms_category(category):
            return None

        # Try size_normalized first
        if size_normalized:
            parsed = cls.parse_composite_size(size_normalized)
            if parsed['length']:
                return parsed['length']

        # Try size_original as fallback
        if size_original:
            parsed = cls.parse_composite_size(size_original)
            if parsed['length']:
                return parsed['length']

        return None

    @classmethod
    def validate_size_length(cls, size_length: str | None) -> bool:
        """
        Validate that a size_length value is valid.

        Args:
            size_length: Length value to validate

        Returns:
            True if valid, False otherwise
        """
        if size_length is None:
            return True
        return size_length in VALID_LENGTHS
