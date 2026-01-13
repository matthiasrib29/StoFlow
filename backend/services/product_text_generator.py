"""
Product Text Generator Service

Service for generating SEO-optimized titles and descriptions for clothing products.
Uses Python templates only - no LLM or external API calls.

Key features:
- 3 title formats (Ultra Complete, Technical, Style & Trend)
- 3 description styles (Professional, Storytelling, Minimalist)
- Intelligent handling of missing attributes (silent skip)
- Max 80 chars for titles, 5000 chars for descriptions
- Response time < 100ms (pure Python string formatting)

Business Rules:
- Titles: max 80 characters (Vinted/eBay limit)
- Descriptions: max 5000 characters
- Missing attributes are silently skipped (no "None" in output)
- No double spaces or orphan punctuation
"""

from enum import IntEnum
from typing import Any, Optional

from shared.logging_setup import get_logger

logger = get_logger(__name__)


# Condition score (0-10) to French text mapping
CONDITION_MAP = {
    10: "Neuf",
    9: "Comme neuf",
    8: "Excellent état",
    7: "Très bon état",
    6: "Bon état",
    5: "État correct",
    4: "État acceptable",
    3: "État passable",
    2: "Mauvais état",
    1: "Pour pièces",
    0: "Défauts majeurs",
}


class TitleFormat(IntEnum):
    """Title format options for SEO optimization."""

    ULTRA_COMPLETE = 1  # brand, category, gender, size, color, material, fit, condition, decade
    TECHNICAL = 2  # brand, category, size, color, material, fit, rise, closure, unique_feature, condition
    STYLE_TREND = 3  # brand, category, gender, size, color, pattern, material, fit, trend, season, origin, condition


class DescriptionStyle(IntEnum):
    """Description style options for different tones."""

    PROFESSIONAL = 1  # E-commerce tone, flowing sentences
    STORYTELLING = 2  # Narrative, emotional, lifestyle
    MINIMALIST = 3  # Bullet list, technical specs


class ProductTextGeneratorService:
    """
    Service for generating SEO-optimized product titles and descriptions.

    All methods are static - no database or external API dependencies.
    Pure Python string formatting for fast response times (<100ms).
    """

    @staticmethod
    def _get_condition_text(condition: Optional[int]) -> str:
        """
        Map condition score (0-10) to French text.

        Args:
            condition: Condition score (0-10) or None

        Returns:
            French condition text or empty string if None/invalid
        """
        if condition is None:
            return ""
        return CONDITION_MAP.get(condition, "")

    @staticmethod
    def _clean_title(title: str, max_length: int = 80) -> str:
        """
        Clean title string: remove double spaces, trim, truncate.

        Args:
            title: Raw title string
            max_length: Maximum allowed length (default 80)

        Returns:
            Cleaned title, truncated at word boundary if needed
        """
        # Remove leading/trailing whitespace
        title = title.strip()

        # Remove double spaces
        while "  " in title:
            title = title.replace("  ", " ")

        # Truncate if needed (at word boundary)
        if len(title) > max_length:
            # Find last space before max_length
            truncate_at = title.rfind(" ", 0, max_length)
            if truncate_at > 0:
                title = title[:truncate_at]
            else:
                # No space found, hard truncate
                title = title[:max_length]

        return title.strip()

    @staticmethod
    def _safe_get(product: Any, attr: str, default: str = "") -> str:
        """
        Safely get attribute value from product object.

        Args:
            product: Product model instance or any object with attributes
            attr: Attribute name to retrieve
            default: Default value if attribute is None or missing

        Returns:
            String value of attribute, or default if None/missing
        """
        value = getattr(product, attr, None)

        if value is None:
            return default

        # Handle list attributes (colors, unique_feature)
        if isinstance(value, list):
            if not value:
                return default
            # For colors: join with "/" if multiple
            if attr == "colors":
                return "/".join(str(v) for v in value[:2])  # Max 2 colors for title
            # For unique_feature: use first only
            return str(value[0])

        return str(value)

    @staticmethod
    def generate_title(product: Any, format: TitleFormat = TitleFormat.ULTRA_COMPLETE) -> str:
        """
        Generate SEO-optimized title for a product.

        Args:
            product: Product model instance with attributes (brand, category, etc.)
            format: TitleFormat enum (1=Ultra Complete, 2=Technical, 3=Style & Trend)

        Returns:
            Clean title string (max 80 chars), missing attributes silently skipped
        """
        service = ProductTextGeneratorService
        parts = []

        if format == TitleFormat.ULTRA_COMPLETE:
            # Format 1: brand, category, gender, size, color, material, fit, condition, decade
            parts = [
                service._safe_get(product, "brand"),
                service._safe_get(product, "category"),
                service._safe_get(product, "gender"),
                service._safe_get(product, "size_normalized"),
                service._safe_get(product, "colors"),
                service._safe_get(product, "material"),
                service._safe_get(product, "fit"),
                service._get_condition_text(getattr(product, "condition", None)),
                service._safe_get(product, "decade"),
            ]

        elif format == TitleFormat.TECHNICAL:
            # Format 2: brand, category, size, color, material, fit, rise, closure, unique_feature, condition
            parts = [
                service._safe_get(product, "brand"),
                service._safe_get(product, "category"),
                service._safe_get(product, "size_normalized"),
                service._safe_get(product, "colors"),
                service._safe_get(product, "material"),
                service._safe_get(product, "fit"),
                service._safe_get(product, "rise"),
                service._safe_get(product, "closure"),
                service._safe_get(product, "unique_feature"),
                service._get_condition_text(getattr(product, "condition", None)),
            ]

        elif format == TitleFormat.STYLE_TREND:
            # Format 3: brand, category, gender, size, color, pattern, material, fit, trend, season, origin, condition
            parts = [
                service._safe_get(product, "brand"),
                service._safe_get(product, "category"),
                service._safe_get(product, "gender"),
                service._safe_get(product, "size_normalized"),
                service._safe_get(product, "colors"),
                service._safe_get(product, "pattern"),
                service._safe_get(product, "material"),
                service._safe_get(product, "fit"),
                service._safe_get(product, "trend"),
                service._safe_get(product, "season"),
                service._safe_get(product, "origin"),
                service._get_condition_text(getattr(product, "condition", None)),
            ]

        # Filter out empty parts and join
        non_empty_parts = [p for p in parts if p]
        raw_title = " ".join(non_empty_parts)

        return service._clean_title(raw_title)

    # ===== DESCRIPTION GENERATION =====

    @staticmethod
    def _build_professional_description(product: Any) -> str:
        """
        Build professional/e-commerce style description.

        Structure: intro → characteristics → condition → origin/decade → call-to-action
        Tone: Commercial, flowing sentences.
        """
        service = ProductTextGeneratorService
        segments = []

        # Intro: "Découvrez ce/cette {category} {brand}..."
        category = service._safe_get(product, "category")
        brand = service._safe_get(product, "brand")

        if category:
            # Determine article (ce/cette) - simple heuristic
            article = "cette" if category.endswith("e") else "ce"
            if brand:
                segments.append(f"Découvrez {article} {category} {brand} de qualité.")
            else:
                segments.append(f"Découvrez {article} {category} de qualité.")

        # Characteristics: material, fit, size
        chars = []
        material = service._safe_get(product, "material")
        if material:
            chars.append(f"en {material.lower()}")

        fit = service._safe_get(product, "fit")
        if fit:
            chars.append(f"coupe {fit.lower()}")

        size = service._safe_get(product, "size_normalized")
        if size:
            chars.append(f"taille {size}")

        if chars:
            segments.append(" ".join(chars).capitalize() + ".")

        # Condition
        condition = getattr(product, "condition", None)
        condition_text = service._get_condition_text(condition)
        condition_sup = getattr(product, "condition_sup", None)

        if condition_text:
            condition_phrase = f"En {condition_text.lower()}"
            if condition_sup and isinstance(condition_sup, list) and condition_sup:
                details = ", ".join(str(d) for d in condition_sup[:2])
                condition_phrase += f" ({details})"
            condition_phrase += "."
            segments.append(condition_phrase)

        # Origin/decade
        origin = service._safe_get(product, "origin")
        decade = service._safe_get(product, "decade")

        if origin or decade:
            origin_phrase_parts = []
            if decade:
                origin_phrase_parts.append(f"pièce des années {decade}")
            if origin:
                origin_phrase_parts.append(f"origine {origin}")
            if origin_phrase_parts:
                segments.append("Une " + ", ".join(origin_phrase_parts) + ".")

        # Call-to-action (only if trend exists)
        trend = service._safe_get(product, "trend")
        if trend:
            segments.append(f"Une pièce {trend.lower()} à ne pas manquer.")

        return " ".join(segments)

    @staticmethod
    def _build_storytelling_description(product: Any) -> str:
        """
        Build storytelling/lifestyle style description.

        Structure: hook → story → details → invitation
        Tone: Narrative, emotional, paragraphs.
        """
        service = ProductTextGeneratorService
        segments = []

        # Hook: "Pour les amateurs de {trend/style}..."
        trend = service._safe_get(product, "trend")
        category = service._safe_get(product, "category")

        if trend:
            segments.append(f"Pour les amateurs de {trend.lower()} authentique.")
        elif category:
            segments.append(f"Pour les amateurs de mode et de style.")

        # Story: "Ce/Cette {category} {brand} {decade}..."
        brand = service._safe_get(product, "brand")
        decade = service._safe_get(product, "decade")

        if category:
            article = "Cette" if category.endswith("e") else "Ce"
            story_parts = [f"{article} {category}"]
            if brand:
                story_parts.append(brand)
            if decade:
                story_parts.append(f"des années {decade}")

            story = " ".join(story_parts)
            material = service._safe_get(product, "material")
            if material:
                story += f" incarne l'esprit du {material.lower()}"
            else:
                story += " incarne un style intemporel"
            story += "."
            segments.append(story)

        # Details: material quality, fit description, unique features
        details = []
        fit = service._safe_get(product, "fit")
        if fit:
            details.append(f"Sa coupe {fit.lower()}")

        material = service._safe_get(product, "material")
        if material:
            details.append(f"son {material.lower()} de qualité")

        unique_features = getattr(product, "unique_feature", None)
        if unique_features and isinstance(unique_features, list) and unique_features:
            features_text = ", ".join(str(f) for f in unique_features[:2])
            details.append(f"ses détails uniques ({features_text})")

        if details:
            segments.append(" et ".join(details) + " témoignent d'un savoir-faire authentique.")

        # Condition mention
        condition = getattr(product, "condition", None)
        condition_text = service._get_condition_text(condition)
        if condition_text:
            segments.append(f"Article en {condition_text.lower()}.")

        # Invitation (only if season exists)
        season = service._safe_get(product, "season")
        if season:
            segments.append(f"Adoptez ce style {season.lower()}.")
        else:
            segments.append("Adoptez ce style unique.")

        return " ".join(segments)

    @staticmethod
    def _build_minimalist_description(product: Any) -> str:
        """
        Build minimalist/technical spec style description.

        Format: Bullet list with categories.
        Only include lines where attribute exists.
        """
        service = ProductTextGeneratorService
        lines = []

        # Define attribute order and labels
        attribute_map = [
            ("brand", "Marque"),
            ("category", "Type"),
            ("gender", "Genre"),
            ("size_normalized", "Taille"),
            ("colors", "Couleur(s)"),
            ("material", "Matière"),
            ("fit", "Coupe"),
            ("rise", "Taille haute/basse"),
            ("closure", "Fermeture"),
            ("pattern", "Motif"),
            ("condition", "État"),
            ("condition_sup", "Détails état"),
            ("unique_feature", "Caractéristiques"),
            ("trend", "Tendance"),
            ("season", "Saison"),
            ("origin", "Origine"),
            ("decade", "Époque"),
        ]

        for attr, label in attribute_map:
            if attr == "condition":
                # Special handling for condition (use text mapping)
                condition = getattr(product, "condition", None)
                condition_text = service._get_condition_text(condition)
                if condition_text:
                    lines.append(f"• {label}: {condition_text}")
            elif attr == "condition_sup":
                # Special handling for condition_sup (list)
                sup = getattr(product, "condition_sup", None)
                if sup and isinstance(sup, list) and sup:
                    lines.append(f"• {label}: {', '.join(str(s) for s in sup)}")
            elif attr == "unique_feature":
                # Special handling for unique_feature (list)
                features = getattr(product, "unique_feature", None)
                if features and isinstance(features, list) and features:
                    lines.append(f"• {label}: {', '.join(str(f) for f in features)}")
            elif attr == "colors":
                # Special handling for colors (list)
                colors = getattr(product, "colors", None)
                if colors and isinstance(colors, list) and colors:
                    lines.append(f"• {label}: {', '.join(str(c) for c in colors)}")
            else:
                # Standard attribute
                value = service._safe_get(product, attr)
                if value:
                    lines.append(f"• {label}: {value}")

        return "\n".join(lines)

    @staticmethod
    def generate_description(
        product: Any, style: DescriptionStyle = DescriptionStyle.PROFESSIONAL
    ) -> str:
        """
        Generate dynamic description for a product.

        Args:
            product: Product model instance
            style: DescriptionStyle enum (1=Professional, 2=Storytelling, 3=Minimalist)

        Returns:
            Description string (max 5000 chars), segments with missing attributes removed
        """
        service = ProductTextGeneratorService

        if style == DescriptionStyle.PROFESSIONAL:
            description = service._build_professional_description(product)
        elif style == DescriptionStyle.STORYTELLING:
            description = service._build_storytelling_description(product)
        elif style == DescriptionStyle.MINIMALIST:
            description = service._build_minimalist_description(product)
        else:
            description = service._build_professional_description(product)

        # Clean up: remove double spaces, trim
        description = description.strip()
        while "  " in description:
            description = description.replace("  ", " ")

        # Truncate if exceeds max length (5000 chars)
        if len(description) > 5000:
            description = description[:4997] + "..."

        return description

    # ===== AGGREGATE METHODS =====

    @staticmethod
    def generate_all(product: Any) -> dict:
        """
        Generate all title formats and description styles for a product.

        Args:
            product: Product model instance

        Returns:
            dict with structure:
            {
                "titles": {
                    "ultra_complete": "...",
                    "technical": "...",
                    "style_trend": "..."
                },
                "descriptions": {
                    "professional": "...",
                    "storytelling": "...",
                    "minimalist": "..."
                }
            }
        """
        service = ProductTextGeneratorService

        return {
            "titles": {
                "ultra_complete": service.generate_title(product, TitleFormat.ULTRA_COMPLETE),
                "technical": service.generate_title(product, TitleFormat.TECHNICAL),
                "style_trend": service.generate_title(product, TitleFormat.STYLE_TREND),
            },
            "descriptions": {
                "professional": service.generate_description(
                    product, DescriptionStyle.PROFESSIONAL
                ),
                "storytelling": service.generate_description(
                    product, DescriptionStyle.STORYTELLING
                ),
                "minimalist": service.generate_description(
                    product, DescriptionStyle.MINIMALIST
                ),
            },
        }

    @staticmethod
    def generate_preview(attributes: dict) -> dict:
        """
        Generate preview from raw attributes dict (for form preview before save).

        Args:
            attributes: dict with product attributes (brand, category, colors, etc.)

        Returns:
            Same structure as generate_all()
        """

        # Create a simple object from dict attributes
        class PreviewProduct:
            pass

        preview = PreviewProduct()

        # Map all possible attributes
        for key, value in attributes.items():
            setattr(preview, key, value)

        # Set defaults for missing attributes to avoid AttributeError
        default_attrs = [
            "brand",
            "category",
            "gender",
            "size_normalized",
            "colors",
            "material",
            "fit",
            "condition",
            "decade",
            "rise",
            "closure",
            "unique_feature",
            "pattern",
            "trend",
            "season",
            "origin",
            "condition_sup",
            "stretch",
            "length",
            "neckline",
            "sleeve_length",
            "lining",
            "sport",
        ]

        for attr in default_attrs:
            if not hasattr(preview, attr):
                setattr(preview, attr, None)

        return ProductTextGeneratorService.generate_all(preview)
