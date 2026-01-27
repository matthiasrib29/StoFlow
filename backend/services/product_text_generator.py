"""
Product Text Generator Service

Service for generating SEO-optimized titles and descriptions for clothing products.
Uses Python templates only - no LLM or external API calls.

Key features:
- 5 title formats (Minimaliste, Standard Vinted, SEO & Mots-cles, Vintage & Collectionneur, Technique & Professionnel)
- 5 description styles (Catalogue Structure, Descriptif Redige, Fiche Technique, Vendeur Pro, Visuel Emoji)
- Intelligent handling of missing attributes (silent skip)
- Max 80 chars for titles, 5000 chars for descriptions
- Response time < 100ms (pure Python string formatting)

Business Rules:
- Titles: max 80 characters (Vinted/eBay limit)
- Descriptions: max 5000 characters
- Missing attributes are silently skipped (no "None" in output)
- No double spaces or orphan punctuation

Updated: 2026-01-27 - Extracted description builders to description_builders.py
"""

from enum import IntEnum
from typing import Any

from services.description_builders import (
    build_catalogue_structure,
    build_descriptif_redige,
    build_fiche_technique,
    build_vendeur_pro,
    build_visuel_emoji,
    get_condition_text,
    safe_get,
)
from shared.logging import get_logger

logger = get_logger(__name__)


class TitleFormat(IntEnum):
    """Title format options for SEO optimization."""

    MINIMALISTE = 1
    STANDARD_VINTED = 2
    SEO_MOTS_CLES = 3
    VINTAGE_COLLECTIONNEUR = 4
    TECHNIQUE_PROFESSIONNEL = 5


class DescriptionStyle(IntEnum):
    """Description style options for different tones."""

    CATALOGUE_STRUCTURE = 1
    DESCRIPTIF_REDIGE = 2
    FICHE_TECHNIQUE = 3
    VENDEUR_PRO = 4
    VISUEL_EMOJI = 5


class ProductTextGeneratorService:
    """
    Service for generating SEO-optimized product titles and descriptions.

    All methods are static - no database or external API dependencies.
    Pure Python string formatting for fast response times (<100ms).

    Description builders are in services/description_builders.py.
    """

    # Re-expose utilities as static methods for backward compatibility
    _get_condition_text = staticmethod(get_condition_text)
    _safe_get = staticmethod(safe_get)

    @staticmethod
    def _clean_title(title: str, max_length: int = 80) -> str:
        """
        Clean title string: remove double spaces, trim, truncate.

        Truncates at word boundary if needed.
        """
        title = title.strip()

        while "  " in title:
            title = title.replace("  ", " ")

        if len(title) > max_length:
            truncate_at = title.rfind(" ", 0, max_length)
            if truncate_at > 0:
                title = title[:truncate_at]
            else:
                title = title[:max_length]

        return title.strip()

    @staticmethod
    def generate_title(product: Any, format: TitleFormat = TitleFormat.MINIMALISTE) -> str:
        """
        Generate SEO-optimized title for a product.

        Args:
            product: Product model instance with attributes (brand, category, etc.)
            format: TitleFormat enum (1-5)

        Returns:
            Clean title string (max 80 chars), missing attributes silently skipped
        """
        parts = []

        if format == TitleFormat.MINIMALISTE:
            parts = [
                safe_get(product, "brand"),
                safe_get(product, "model"),
                safe_get(product, "category"),
                safe_get(product, "gender"),
                safe_get(product, "size_normalized"),
                safe_get(product, "colors"),
            ]

        elif format == TitleFormat.STANDARD_VINTED:
            parts = [
                safe_get(product, "brand"),
                safe_get(product, "category"),
                safe_get(product, "fit"),
                safe_get(product, "material"),
                safe_get(product, "colors"),
                safe_get(product, "size_normalized"),
                get_condition_text(getattr(product, "condition", None)),
            ]

        elif format == TitleFormat.SEO_MOTS_CLES:
            parts = [
                safe_get(product, "category"),
                safe_get(product, "brand"),
                safe_get(product, "gender"),
                safe_get(product, "pattern"),
                safe_get(product, "neckline"),
                safe_get(product, "sleeve_length"),
                safe_get(product, "material"),
                safe_get(product, "size_normalized"),
            ]

        elif format == TitleFormat.VINTAGE_COLLECTIONNEUR:
            parts = [
                "Vintage" if safe_get(product, "decade") else "",
                safe_get(product, "decade"),
                safe_get(product, "brand"),
                safe_get(product, "category"),
                safe_get(product, "origin"),
                safe_get(product, "unique_feature"),
                safe_get(product, "size_normalized"),
                safe_get(product, "trend"),
            ]

        elif format == TitleFormat.TECHNIQUE_PROFESSIONNEL:
            parts = [
                safe_get(product, "brand"),
                safe_get(product, "category"),
                safe_get(product, "model"),
                safe_get(product, "material"),
                safe_get(product, "colors"),
                safe_get(product, "size_normalized"),
                get_condition_text(getattr(product, "condition", None)),
                f"PTP {getattr(product, 'dim1', '')}cm" if getattr(product, "dim1", None) else "",
            ]

        non_empty_parts = [p for p in parts if p]
        raw_title = " ".join(non_empty_parts)

        return ProductTextGeneratorService._clean_title(raw_title)

    @staticmethod
    def generate_description(
        product: Any, style: DescriptionStyle = DescriptionStyle.CATALOGUE_STRUCTURE
    ) -> str:
        """
        Generate dynamic description for a product.

        Args:
            product: Product model instance
            style: DescriptionStyle enum (1-5)

        Returns:
            Description string (max 5000 chars), segments with missing attributes removed
        """
        builders = {
            DescriptionStyle.CATALOGUE_STRUCTURE: build_catalogue_structure,
            DescriptionStyle.DESCRIPTIF_REDIGE: build_descriptif_redige,
            DescriptionStyle.FICHE_TECHNIQUE: build_fiche_technique,
            DescriptionStyle.VENDEUR_PRO: build_vendeur_pro,
            DescriptionStyle.VISUEL_EMOJI: build_visuel_emoji,
        }

        builder = builders.get(style, build_catalogue_structure)
        description = builder(product)

        # Clean up
        description = description.strip()
        while "  " in description:
            description = description.replace("  ", " ")

        if len(description) > 5000:
            description = description[:4997] + "..."

        return description

    @staticmethod
    def generate_all(product: Any) -> dict:
        """
        Generate all title formats and description styles for a product.

        Returns:
            dict with "titles" and "descriptions" sub-dicts
        """
        service = ProductTextGeneratorService

        return {
            "titles": {
                "minimaliste": service.generate_title(product, TitleFormat.MINIMALISTE),
                "standard_vinted": service.generate_title(product, TitleFormat.STANDARD_VINTED),
                "seo_mots_cles": service.generate_title(product, TitleFormat.SEO_MOTS_CLES),
                "vintage_collectionneur": service.generate_title(
                    product, TitleFormat.VINTAGE_COLLECTIONNEUR
                ),
                "technique_professionnel": service.generate_title(
                    product, TitleFormat.TECHNIQUE_PROFESSIONNEL
                ),
            },
            "descriptions": {
                "catalogue_structure": service.generate_description(
                    product, DescriptionStyle.CATALOGUE_STRUCTURE
                ),
                "descriptif_redige": service.generate_description(
                    product, DescriptionStyle.DESCRIPTIF_REDIGE
                ),
                "fiche_technique": service.generate_description(
                    product, DescriptionStyle.FICHE_TECHNIQUE
                ),
                "vendeur_pro": service.generate_description(
                    product, DescriptionStyle.VENDEUR_PRO
                ),
                "visuel_emoji": service.generate_description(
                    product, DescriptionStyle.VISUEL_EMOJI
                ),
            },
        }

    @staticmethod
    def generate_preview(attributes: dict) -> dict:
        """
        Generate preview from raw attributes dict (for form preview before save).

        Returns:
            Same structure as generate_all()
        """

        class PreviewProduct:
            pass

        preview = PreviewProduct()

        for key, value in attributes.items():
            setattr(preview, key, value)

        default_attrs = [
            "brand", "model", "category", "gender", "size_normalized",
            "colors", "material", "fit", "condition", "decade",
            "rise", "closure", "unique_feature", "pattern", "trend",
            "season", "origin", "condition_sup", "stretch", "length",
            "neckline", "sleeve_length", "lining", "sport", "marking",
            "location", "dim1", "dim2", "dim3", "dim4", "dim5", "dim6",
        ]

        for attr in default_attrs:
            if not hasattr(preview, attr):
                setattr(preview, attr, None)

        return ProductTextGeneratorService.generate_all(preview)
