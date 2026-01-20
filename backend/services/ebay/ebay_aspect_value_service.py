"""
eBay Aspect Value Service

Translates aspect values to marketplace-specific languages.

Process:
1. Product has a value (e.g., color='bleu', size='M')
2. Lookup GB reference value from product_attributes tables
3. Translate GB value to target marketplace via ebay.aspect_* tables

Example:
    >>> service = EbayAspectValueService(session)
    >>> service.get_aspect_value('bleu', 'color', 'EBAY_DE')
    'Blau'

Author: Claude
Date: 2025-12-22
"""

from typing import Dict, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from models.ebay.aspect_value import (
    AspectColour,
    AspectClosure,
    AspectDepartment,
    AspectFeatures,
    AspectFit,
    AspectInsideLeg,
    AspectMaterial,
    AspectNeckline,
    AspectOccasion,
    AspectPattern,
    AspectRise,
    AspectSize,
    AspectSleeveLength,
    AspectStyle,
    AspectType,
    AspectWaistSize,
)
from shared.logging import get_logger

logger = get_logger(__name__)


class EbayAspectValueService:
    """
    Service for translating aspect values to eBay marketplace languages.

    Two-step process:
    1. Lookup in product_attributes.* → get ebay_gb_* (GB reference value)
    2. Lookup in ebay.aspect_* → get translated value for marketplace

    Usage:
        >>> service = EbayAspectValueService(session)
        >>> service.get_aspect_value('bleu', 'color', 'EBAY_FR')
        'Bleu'
        >>> service.get_aspect_value('bleu', 'color', 'EBAY_DE')
        'Blau'
    """

    # Mapping aspect_key → configuration
    # attribut_table: Table in product_attributes schema
    # search_columns: Columns to search for the value (OR logic)
    # gb_column: Column containing the GB reference value
    # aspect_model: SQLAlchemy model for ebay.aspect_* table
    ASPECT_CONFIG = {
        'color': {
            'attribut_table': 'colors',
            'search_columns': ['name_fr', 'name_en', 'name'],
            'gb_column': 'ebay_gb_color',
            'aspect_model': AspectColour,
        },
        'colour': {  # Alias
            'attribut_table': 'colors',
            'search_columns': ['name_fr', 'name_en', 'name'],
            'gb_column': 'ebay_gb_color',
            'aspect_model': AspectColour,
        },
        'size': {
            'attribut_table': 'sizes',
            'search_columns': ['name', 'label'],
            'gb_column': 'ebay_gb_size',
            'aspect_model': AspectSize,
        },
        'material': {
            'attribut_table': 'materials',
            'search_columns': ['name_fr', 'name_en', 'name'],
            'gb_column': 'ebay_gb_material',
            'aspect_model': AspectMaterial,
        },
        'fit': {
            'attribut_table': 'fits',
            'search_columns': ['name_fr', 'name_en', 'name'],
            'gb_column': 'ebay_gb_fit',
            'aspect_model': AspectFit,
        },
        'closure': {
            'attribut_table': 'closures',
            'search_columns': ['name_fr', 'name_en', 'name'],
            'gb_column': 'ebay_gb_closure',
            'aspect_model': AspectClosure,
        },
        'rise': {
            'attribut_table': 'rises',
            'search_columns': ['name_fr', 'name_en', 'name'],
            'gb_column': 'ebay_gb_rise',
            'aspect_model': AspectRise,
        },
        'condition': {
            'attribut_table': 'conditions',
            'search_columns': ['name', 'description_en', 'description_fr'],
            'gb_column': 'ebay_condition',
            'aspect_model': None,  # No translation needed for condition
        },
        'pattern': {
            'attribut_table': None,  # Direct lookup in aspect table
            'aspect_model': AspectPattern,
        },
        'neckline': {
            'attribut_table': None,
            'aspect_model': AspectNeckline,
        },
        'sleeve_length': {
            'attribut_table': None,
            'aspect_model': AspectSleeveLength,
        },
        'occasion': {
            'attribut_table': None,
            'aspect_model': AspectOccasion,
        },
        'style': {
            'attribut_table': None,
            'aspect_model': AspectStyle,
        },
        'features': {
            'attribut_table': None,
            'aspect_model': AspectFeatures,
        },
        'department': {
            'attribut_table': None,  # Direct value from gender mapping
            'aspect_model': AspectDepartment,
        },
        'type': {
            'attribut_table': None,  # Direct value from category mapping
            'aspect_model': AspectType,
        },
        'waist_size': {
            'attribut_table': 'sizes',
            'search_columns': ['name', 'label'],
            'gb_column': 'ebay_gb_waist_size',
            'aspect_model': AspectWaistSize,
        },
        'inside_leg': {
            'attribut_table': 'sizes',
            'search_columns': ['name', 'label'],
            'gb_column': 'ebay_gb_inside_leg',
            'aspect_model': AspectInsideLeg,
        },
    }

    def __init__(self, session: Session):
        """
        Initialize the service.

        Args:
            session: SQLAlchemy session
        """
        self.session = session
        self._cache: Dict[str, str] = {}

    def get_aspect_value(
        self,
        field_value: str,
        aspect_key: str,
        marketplace_id: str
    ) -> Optional[str]:
        """
        Get translated aspect value for a marketplace.

        Args:
            field_value: Product field value (e.g., 'bleu', 'M', 'coton')
            aspect_key: Aspect key (e.g., 'color', 'size', 'material')
            marketplace_id: Target marketplace (e.g., 'EBAY_FR', 'EBAY_DE')

        Returns:
            Translated value or None if not found

        Examples:
            >>> service.get_aspect_value('bleu', 'color', 'EBAY_FR')
            'Bleu'
            >>> service.get_aspect_value('bleu', 'color', 'EBAY_DE')
            'Blau'
        """
        if not field_value:
            return None

        aspect_key_lower = aspect_key.lower()
        if aspect_key_lower not in self.ASPECT_CONFIG:
            logger.warning(f"Unknown aspect key: {aspect_key}")
            return None

        # Check cache
        cache_key = f"{aspect_key_lower}:{field_value}:{marketplace_id}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        config = self.ASPECT_CONFIG[aspect_key_lower]

        try:
            # Step 1: Get GB reference value
            if config.get('attribut_table'):
                gb_value = self._get_gb_value_from_attribut(
                    field_value,
                    config['attribut_table'],
                    config['search_columns'],
                    config['gb_column']
                )
            else:
                # Direct value (assume it's already in GB format)
                gb_value = field_value

            if not gb_value:
                logger.debug(f"No GB value found for {aspect_key}='{field_value}'")
                return None

            logger.debug(f"{aspect_key}='{field_value}' → GB='{gb_value}'")

            # Special case: condition has no translations
            if aspect_key_lower == 'condition':
                self._cache[cache_key] = gb_value
                return gb_value

            # Step 2: Get translation from ebay.aspect_* table
            aspect_model = config.get('aspect_model')
            if not aspect_model:
                self._cache[cache_key] = gb_value
                return gb_value

            translated = self._get_translation(gb_value, aspect_model, marketplace_id)

            if translated:
                logger.debug(
                    f"{aspect_key}='{field_value}' → {marketplace_id}='{translated}'"
                )
                self._cache[cache_key] = translated
                return translated
            else:
                # Fallback to GB value
                logger.debug(
                    f"No translation for '{gb_value}' ({marketplace_id}), using GB"
                )
                self._cache[cache_key] = gb_value
                return gb_value

        except Exception as e:
            logger.error(
                f"Error getting aspect value ({field_value}, {aspect_key}, "
                f"{marketplace_id}): {e}"
            )
            return None

    def _get_gb_value_from_attribut(
        self,
        field_value: str,
        table_name: str,
        search_columns: list,
        gb_column: str
    ) -> Optional[str]:
        """
        Step 1: Get GB reference value from product_attributes table.

        Args:
            field_value: Value to search for
            table_name: Table name in product_attributes schema
            search_columns: Columns to search in (OR logic)
            gb_column: Column containing the GB value

        Returns:
            GB reference value or None
        """
        # Build OR conditions for search columns
        conditions = " OR ".join([
            f"LOWER({col}) = LOWER(:field_value)"
            for col in search_columns
        ])

        query = text(f"""
            SELECT {gb_column}
            FROM product_attributes.{table_name}
            WHERE {conditions}
            LIMIT 1
        """)

        try:
            result = self.session.execute(
                query, {'field_value': field_value}
            ).fetchone()

            if result and result[0]:
                return result[0]
        except Exception as e:
            logger.debug(f"Attribut lookup failed for {table_name}: {e}")

        return None

    def _get_translation(
        self,
        gb_value: str,
        aspect_model,
        marketplace_id: str
    ) -> Optional[str]:
        """
        Step 2: Get translation from ebay.aspect_* table.

        Args:
            gb_value: GB reference value
            aspect_model: SQLAlchemy model class
            marketplace_id: Target marketplace

        Returns:
            Translated value or None
        """
        aspect = self.session.query(aspect_model).filter(
            aspect_model.ebay_gb == gb_value
        ).first()

        if aspect:
            return aspect.get_translation(marketplace_id)

        return None

    def translate_direct(
        self,
        gb_value: str,
        aspect_key: str,
        marketplace_id: str
    ) -> str:
        """
        Directly translate a GB value without attribut lookup.

        Used for values like Department and Type that come from
        category mapping, not from product attributes.

        Args:
            gb_value: GB reference value (e.g., 'Men', 'Jeans')
            aspect_key: Aspect key (e.g., 'department', 'type')
            marketplace_id: Target marketplace

        Returns:
            Translated value or gb_value as fallback

        Examples:
            >>> service.translate_direct('Men', 'department', 'EBAY_FR')
            'Homme'
            >>> service.translate_direct('Jeans', 'type', 'EBAY_FR')
            'Jean'
        """
        if not gb_value:
            return gb_value

        # GB marketplace: no translation needed
        if marketplace_id == 'EBAY_GB':
            return gb_value

        aspect_key_lower = aspect_key.lower()
        config = self.ASPECT_CONFIG.get(aspect_key_lower)

        if not config or not config.get('aspect_model'):
            return gb_value

        try:
            translated = self._get_translation(
                gb_value,
                config['aspect_model'],
                marketplace_id
            )
            return translated or gb_value
        except Exception as e:
            logger.error(f"Error translating {gb_value}: {e}")
            return gb_value

    def get_waist_size(self, size_value: str) -> Optional[str]:
        """
        Get waist size for a given size value.

        Args:
            size_value: Size value (e.g., 'W32/L30', 'W32')

        Returns:
            Waist size (e.g., '82 cm') or None
        """
        query = text("""
            SELECT ebay_gb_waist_size
            FROM product_attributes.sizes_normalized
            WHERE LOWER(name_en) = LOWER(:size_value)
            LIMIT 1
        """)

        try:
            result = self.session.execute(
                query, {'size_value': size_value}
            ).fetchone()

            if result and result[0]:
                return result[0]
        except Exception as e:
            logger.debug(f"Waist size lookup failed: {e}")

        return None

    def get_inside_leg(self, size_value: str) -> Optional[str]:
        """
        Get inside leg measurement for a given size value.

        Args:
            size_value: Size value (e.g., 'W32/L30')

        Returns:
            Inside leg (e.g., '77 cm') or None
        """
        query = text("""
            SELECT ebay_gb_inside_leg
            FROM product_attributes.sizes_normalized
            WHERE LOWER(name_en) = LOWER(:size_value)
            LIMIT 1
        """)

        try:
            result = self.session.execute(
                query, {'size_value': size_value}
            ).fetchone()

            if result and result[0]:
                return result[0]
        except Exception as e:
            logger.debug(f"Inside leg lookup failed: {e}")

        return None

    def clear_cache(self):
        """Clear the internal translation cache."""
        self._cache.clear()


# Singleton-style cached instance for performance
_service_cache: Dict[int, EbayAspectValueService] = {}


def get_aspect_value_service(session: Session) -> EbayAspectValueService:
    """
    Get or create an EbayAspectValueService for a session.

    Args:
        session: SQLAlchemy session

    Returns:
        EbayAspectValueService instance
    """
    session_id = id(session)
    if session_id not in _service_cache:
        _service_cache[session_id] = EbayAspectValueService(session)
    return _service_cache[session_id]
