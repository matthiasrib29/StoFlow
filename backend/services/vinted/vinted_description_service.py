"""
Vinted Description Service

Service de génération de descriptions SEO optimisées pour Vinted.
Responsabilité: Orchestrer la génération de descriptions de max 2000 caractères.

Business Rules (2024-12-10):
- Format structuré: Hook → Info Produit → État → Mesures → Expédition → Hashtags
- Max 2000 caractères (limite Vinted)
- Max 40 hashtags
- Hashtags fixes + dynamiques basés sur attributs

Architecture (Refactored 2025-12-11):
- Service orchestrateur uniquement
- Délègue aux composants spécialisés dans services/vinted/description/

Created: 2024-12-10
Updated: 2025-12-11 - Refactored to use focused classes
Author: Claude
"""

from typing import TYPE_CHECKING
import logging

from .description import SectionBuilder, HashtagConfig, TranslationHelper, MeasurementExtractor

if TYPE_CHECKING:
    from models.user.product import Product

logger = logging.getLogger(__name__)

# Limite maximale de caractères pour une description Vinted
MAX_DESCRIPTION_LENGTH = 2000


class VintedDescriptionService:
    """
    Génère des descriptions SEO optimisées pour Vinted.

    Format:
    - Hook accrocheur
    - Informations produit
    - État/Condition
    - Mesures
    - Expédition
    - Hashtags (max 40)

    Règles:
    - Max 2000 caractères
    - Mesures adaptées par catégorie
    - Hashtags prioritaires + dynamiques

    Example:
        >>> desc = VintedDescriptionService.generate_description(product)
        "Découvrez ce magnifique jean Levi's 501 des années 90s !

        Informations:
        * Marque: Levi's
        * Modèle: 501
        ..."
    """

    # Re-export constants for backward compatibility
    MAX_DESCRIPTION_LENGTH = MAX_DESCRIPTION_LENGTH
    MAX_HASHTAGS = HashtagConfig.MAX_HASHTAGS
    FIXED_HASHTAGS = HashtagConfig.FIXED
    TRENDING_HASHTAGS = HashtagConfig.TRENDING
    CATEGORY_HASHTAGS = HashtagConfig.BY_CATEGORY
    FIT_HASHTAGS = HashtagConfig.BY_FIT
    DECADE_HASHTAGS = HashtagConfig.BY_DECADE
    MATERIAL_HASHTAGS = HashtagConfig.BY_MATERIAL
    BRAND_HASHTAGS = HashtagConfig.BY_BRAND
    SEASON_HASHTAGS = HashtagConfig.BY_SEASON
    OCCASION_HASHTAGS = HashtagConfig.BY_OCCASION

    @staticmethod
    def generate_description(product: "Product") -> str:
        """
        Génère une description SEO optimisée pour un produit Vinted.

        Args:
            product: Instance de Product

        Returns:
            Description complète (max 2000 caractères)
        """
        sections = []

        # 1. Hook accrocheur
        hook = SectionBuilder.build_hook(product)
        if hook:
            sections.append(hook)

        # 2. Informations produit
        product_info = SectionBuilder.build_product_info(product)
        if product_info:
            sections.append(product_info)

        # 3. État/Condition
        condition_section = SectionBuilder.build_condition(product)
        if condition_section:
            sections.append(condition_section)

        # 4. Mesures
        measurements = SectionBuilder.build_measurements(product)
        if measurements:
            sections.append(measurements)

        # 5. Expédition
        shipping = SectionBuilder.build_shipping()
        sections.append(shipping)

        # 6. Hashtags
        hashtags = SectionBuilder.build_hashtags(product)
        if hashtags:
            sections.append(hashtags)

        # Assembler toutes les sections
        full_description = "\n\n".join(sections)

        # Vérifier la longueur et tronquer si nécessaire
        if len(full_description) > MAX_DESCRIPTION_LENGTH:
            logger.warning(
                f"Description trop longue ({len(full_description)} chars) pour product ID#{product.id}, "
                f"troncature à {MAX_DESCRIPTION_LENGTH} chars"
            )
            full_description = full_description[:MAX_DESCRIPTION_LENGTH - 3] + "..."

        logger.debug(f"Description générée pour product ID#{product.id}: {len(full_description)} chars")

        return full_description

    # ===== BACKWARD COMPATIBILITY METHODS =====
    # Ces méthodes sont conservées pour rétrocompatibilité avec le code existant

    @staticmethod
    def _safe_get(obj, attr: str):
        """DEPRECATED: Use SectionBuilder._safe_get instead."""
        return SectionBuilder._safe_get(obj, attr)

    @staticmethod
    def _translate_category(category: str) -> str:
        """DEPRECATED: Use TranslationHelper.translate_category instead."""
        return TranslationHelper.translate_category(category)

    @staticmethod
    def _get_color_name_fr(color_name: str) -> str:
        """DEPRECATED: Use TranslationHelper.translate_color instead."""
        return TranslationHelper.translate_color(color_name)

    @staticmethod
    def _format_decade_fr(decade: str):
        """DEPRECATED: Use TranslationHelper.format_decade_fr instead."""
        return TranslationHelper.format_decade_fr(decade)

    @staticmethod
    def _normalize_decade(decade: str) -> str:
        """DEPRECATED: Use TranslationHelper.normalize_decade instead."""
        return TranslationHelper.normalize_decade(decade)

    @staticmethod
    def _map_condition_text(condition: str) -> str:
        """DEPRECATED: Use TranslationHelper.get_condition_text instead."""
        return TranslationHelper.get_condition_text(condition)

    @staticmethod
    def _get_default_condition_text(condition: str):
        """DEPRECATED: Use TranslationHelper.get_condition_default_text instead."""
        return TranslationHelper.get_condition_default_text(condition)

    @staticmethod
    def _build_hook(product: "Product"):
        """DEPRECATED: Use SectionBuilder.build_hook instead."""
        return SectionBuilder.build_hook(product)

    @staticmethod
    def _build_product_info(product: "Product"):
        """DEPRECATED: Use SectionBuilder.build_product_info instead."""
        return SectionBuilder.build_product_info(product)

    @staticmethod
    def _build_condition_section(product: "Product"):
        """DEPRECATED: Use SectionBuilder.build_condition instead."""
        return SectionBuilder.build_condition(product)

    @staticmethod
    def _build_measurements(product: "Product"):
        """DEPRECATED: Use SectionBuilder.build_measurements instead."""
        return SectionBuilder.build_measurements(product)

    @staticmethod
    def _build_shipping_section() -> str:
        """DEPRECATED: Use SectionBuilder.build_shipping instead."""
        return SectionBuilder.build_shipping()

    @staticmethod
    def _build_hashtags(product: "Product") -> str:
        """DEPRECATED: Use SectionBuilder.build_hashtags instead."""
        return SectionBuilder.build_hashtags(product)

    @staticmethod
    def _get_bottom_measurements(product: "Product"):
        """DEPRECATED: Use MeasurementExtractor._extract_bottom instead."""
        return MeasurementExtractor._extract_bottom(product)

    @staticmethod
    def _get_shorts_measurements(product: "Product"):
        """DEPRECATED: Use MeasurementExtractor._extract_shorts instead."""
        return MeasurementExtractor._extract_shorts(product)

    @staticmethod
    def _get_top_measurements(product: "Product"):
        """DEPRECATED: Use MeasurementExtractor._extract_top instead."""
        return MeasurementExtractor._extract_top(product)

    @staticmethod
    def _get_sunglasses_measurements(product: "Product"):
        """DEPRECATED: Use MeasurementExtractor._extract_eyewear instead."""
        return MeasurementExtractor._extract_eyewear(product)
