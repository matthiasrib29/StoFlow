"""
Product Text Generator Service

Service for generating SEO-optimized titles and descriptions for clothing products.
Uses Python templates only - no LLM or external API calls.

Key features:
- 5 title formats (Minimaliste, Standard Vinted, SEO & Mots-clés, Vintage & Collectionneur, Technique & Professionnel)
- 5 description styles (Catalogue Structuré, Descriptif Rédigé, Fiche Technique, Vendeur Pro, Visuel Emoji)
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

    MINIMALISTE = 1  # Focus marque & modèle - Idéal luxe, articles connus
    STANDARD_VINTED = 2  # Équilibré avec matière et coupe - Passe-partout fast fashion
    SEO_MOTS_CLES = 3  # Optimisé recherche - Capture requêtes spécifiques (col, manches, motif)
    VINTAGE_COLLECTIONNEUR = 4  # Inclut époque, origine et spécificités - Pour collectionneurs
    TECHNIQUE_PROFESSIONNEL = 5  # Maximaliste avec dimensions - Pour eBay et marketplace pro


class DescriptionStyle(IntEnum):
    """Description style options for different tones."""

    CATALOGUE_STRUCTURE = 1  # Sections avec emojis, groupé par thématique
    DESCRIPTIF_REDIGE = 2  # Phrases fluides, ton humain e-commerce
    FICHE_TECHNIQUE = 3  # Liste pure, export CSV, plateformes pro
    VENDEUR_PRO = 4  # Hybride, état + mesures en avant
    VISUEL_EMOJI = 5  # Emoji par attribut, facile à scanner


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
    def generate_title(product: Any, format: TitleFormat = TitleFormat.MINIMALISTE) -> str:
        """
        Generate SEO-optimized title for a product.

        Args:
            product: Product model instance with attributes (brand, category, etc.)
            format: TitleFormat enum (1=Minimaliste, 2=Standard Vinted, 3=SEO & Mots-clés,
                    4=Vintage & Collectionneur, 5=Technique & Professionnel)

        Returns:
            Clean title string (max 80 chars), missing attributes silently skipped
        """
        service = ProductTextGeneratorService
        parts = []

        if format == TitleFormat.MINIMALISTE:
            # Format 1: Focus marque & modèle - Idéal luxe, articles connus
            # Ex: "Levi's 501 Jeans Homme W32L32 Dark indigo"
            parts = [
                service._safe_get(product, "brand"),
                service._safe_get(product, "model"),
                service._safe_get(product, "category"),
                service._safe_get(product, "gender"),
                service._safe_get(product, "size_normalized"),
                service._safe_get(product, "colors"),
            ]

        elif format == TitleFormat.STANDARD_VINTED:
            # Format 2: Équilibré avec matière et coupe - Passe-partout fast fashion
            # Ex: "Levi's Jeans Slim Denim Dark indigo W32L32 Très bon état"
            parts = [
                service._safe_get(product, "brand"),
                service._safe_get(product, "category"),
                service._safe_get(product, "fit"),
                service._safe_get(product, "material"),
                service._safe_get(product, "colors"),
                service._safe_get(product, "size_normalized"),
                service._get_condition_text(getattr(product, "condition", None)),
            ]

        elif format == TitleFormat.SEO_MOTS_CLES:
            # Format 3: Optimisé recherche - Capture requêtes spécifiques
            # Ex: "Jeans Levi's Homme Uni Mid-rise Button fly Cotton W32L32"
            parts = [
                service._safe_get(product, "category"),
                service._safe_get(product, "brand"),
                service._safe_get(product, "gender"),
                service._safe_get(product, "pattern"),
                service._safe_get(product, "neckline"),
                service._safe_get(product, "sleeve_length"),
                service._safe_get(product, "material"),
                service._safe_get(product, "size_normalized"),
            ]

        elif format == TitleFormat.VINTAGE_COLLECTIONNEUR:
            # Format 4: Inclut époque, origine et spécificités - Pour collectionneurs
            # Ex: "Vintage 90s Levi's Jeans USA Selvedge denim W32L32 Vintage Americana"
            parts = [
                "Vintage" if service._safe_get(product, "decade") else "",
                service._safe_get(product, "decade"),
                service._safe_get(product, "brand"),
                service._safe_get(product, "category"),
                service._safe_get(product, "origin"),
                service._safe_get(product, "unique_feature"),
                service._safe_get(product, "size_normalized"),
                service._safe_get(product, "trend"),
            ]

        elif format == TitleFormat.TECHNIQUE_PROFESSIONNEL:
            # Format 5: Maximaliste avec dimensions - Pour eBay et marketplace pro
            # Ex: "Levi's Jeans 501 Cotton Dark indigo W32L32 Très bon état PTP 55cm"
            parts = [
                service._safe_get(product, "brand"),
                service._safe_get(product, "category"),
                service._safe_get(product, "model"),
                service._safe_get(product, "material"),
                service._safe_get(product, "colors"),
                service._safe_get(product, "size_normalized"),
                service._get_condition_text(getattr(product, "condition", None)),
                f"PTP {getattr(product, 'dim1', '')}cm" if getattr(product, "dim1", None) else "",
            ]

        # Filter out empty parts and join
        non_empty_parts = [p for p in parts if p]
        raw_title = " ".join(non_empty_parts)

        return service._clean_title(raw_title)

    # ===== DESCRIPTION GENERATION =====

    @staticmethod
    def _build_catalogue_structure_description(product: Any) -> str:
        """
        Style 1: Catalogue Structuré - Sections avec emojis, groupé par thématique.

        Structure: INFOS GÉNÉRALES → STYLE & DESIGN → MATIÈRES → ÉTAT → MESURES
        """
        service = ProductTextGeneratorService
        sections = []

        # 📋 INFORMATIONS GÉNÉRALES
        general = []
        brand = service._safe_get(product, "brand")
        if brand:
            general.append(f"Marque : {brand}")
        model = service._safe_get(product, "model")
        if model:
            general.append(f"Modèle : {model}")
        category = service._safe_get(product, "category")
        if category:
            general.append(f"Type : {category}")
        gender = service._safe_get(product, "gender")
        if gender:
            general.append(f"Genre : {gender}")
        decade = service._safe_get(product, "decade")
        if decade:
            general.append(f"Époque : {decade}")
        origin = service._safe_get(product, "origin")
        if origin:
            general.append(f"Origine : {origin}")
        location = service._safe_get(product, "location")
        if location:
            general.append(f"Localisation : {location}")
        if general:
            sections.append("📋 INFORMATIONS GÉNÉRALES\n" + "\n".join(general))

        # 🎨 STYLE & DESIGN
        style = []
        colors = getattr(product, "colors", None)
        if colors and isinstance(colors, list) and colors:
            style.append(f"Couleur(s) : {', '.join(str(c) for c in colors)}")
        trend = service._safe_get(product, "trend")
        if trend:
            style.append(f"Tendance : {trend}")
        pattern = service._safe_get(product, "pattern")
        if pattern:
            style.append(f"Motif : {pattern}")
        season = service._safe_get(product, "season")
        if season:
            style.append(f"Saison : {season}")
        sport = service._safe_get(product, "sport")
        if sport:
            style.append(f"Sport : {sport}")
        fit = service._safe_get(product, "fit")
        if fit:
            style.append(f"Coupe : {fit}")
        rise = service._safe_get(product, "rise")
        if rise:
            style.append(f"Taille : {rise}")
        length = service._safe_get(product, "length")
        if length:
            style.append(f"Longueur : {length}")
        sleeve_length = service._safe_get(product, "sleeve_length")
        if sleeve_length:
            style.append(f"Manches : {sleeve_length}")
        neckline = service._safe_get(product, "neckline")
        if neckline:
            style.append(f"Col : {neckline}")
        closure = service._safe_get(product, "closure")
        if closure:
            style.append(f"Fermeture : {closure}")
        if style:
            sections.append("🎨 STYLE & DESIGN\n" + "\n".join(style))

        # 🧵 MATIÈRES & FABRICATION
        materials = []
        material = service._safe_get(product, "material")
        if material:
            materials.append(f"Matière principale : {material}")
        lining = service._safe_get(product, "lining")
        if lining:
            materials.append(f"Doublure : {lining}")
        stretch = service._safe_get(product, "stretch")
        if stretch:
            materials.append(f"Élasticité : {stretch}")
        unique_features = getattr(product, "unique_feature", None)
        if unique_features and isinstance(unique_features, list) and unique_features:
            materials.append(f"Caractéristiques : {', '.join(str(f) for f in unique_features)}")
        marking = service._safe_get(product, "marking")
        if marking:
            materials.append(f"Marquage : {marking}")
        if materials:
            sections.append("🧵 MATIÈRES & FABRICATION\n" + "\n".join(materials))

        # 💎 ÉTAT
        condition_lines = []
        condition = getattr(product, "condition", None)
        condition_text = service._get_condition_text(condition)
        if condition_text:
            condition_lines.append(f"État général : {condition_text}")
        condition_sup = getattr(product, "condition_sup", None)
        if condition_sup and isinstance(condition_sup, list) and condition_sup:
            condition_lines.append(f"Détails : {', '.join(str(s) for s in condition_sup)}")
        if condition_lines:
            sections.append("💎 ÉTAT\n" + "\n".join(condition_lines))

        # 📏 MESURES (en cm)
        measures = []
        size = service._safe_get(product, "size_normalized")
        if size:
            measures.append(f"Taille : {size}")
        dim1 = getattr(product, "dim1", None)
        if dim1:
            measures.append(f"Poitrine (PTP) : {dim1} cm")
        dim2 = getattr(product, "dim2", None)
        if dim2:
            measures.append(f"Longueur : {dim2} cm")
        dim3 = getattr(product, "dim3", None)
        if dim3:
            measures.append(f"Épaules : {dim3} cm")
        dim4 = getattr(product, "dim4", None)
        if dim4:
            measures.append(f"Manches : {dim4} cm")
        dim5 = getattr(product, "dim5", None)
        if dim5:
            measures.append(f"Tour de taille : {dim5} cm")
        dim6 = getattr(product, "dim6", None)
        if dim6:
            measures.append(f"Entrejambe : {dim6} cm")
        if measures:
            sections.append("📏 MESURES (en cm)\n" + "\n".join(measures))

        return "\n\n".join(sections)

    @staticmethod
    def _build_descriptif_redige_description(product: Any) -> str:
        """
        Style 2: Descriptif Rédigé - Phrases fluides, ton humain e-commerce.

        Structure: Introduction → Style → Détails techniques → État et taille → Mesures
        Each section is only added if it has meaningful content.
        """
        service = ProductTextGeneratorService
        paragraphs = []

        # Introduction
        brand = service._safe_get(product, "brand")
        model = service._safe_get(product, "model")
        category = service._safe_get(product, "category")
        gender = service._safe_get(product, "gender")

        if category:
            intro_parts = []
            if brand:
                intro_parts.append(f"de la marque {brand}")
            if model:
                intro_parts.append(f"modèle {model}")
            article = "cette" if category.endswith("e") else "ce"
            intro = f"Voici {article} {category}"
            if intro_parts:
                intro += " " + ", ".join(intro_parts)
            if gender:
                intro += f", pour {gender.lower()}"
            intro += "."
            paragraphs.append(intro)

        # Style & Design - build a proper sentence only if we have style elements
        trend = service._safe_get(product, "trend")
        pattern = service._safe_get(product, "pattern")
        fit = service._safe_get(product, "fit")
        colors = getattr(product, "colors", None)
        season = service._safe_get(product, "season")

        # Only create style paragraph if we have at least trend, fit, or pattern
        has_style_anchor = trend or fit or (pattern and pattern.lower() != "uni")

        if has_style_anchor:
            style_parts = []
            if trend:
                style_parts.append(f"s'inscrit dans la tendance {trend.lower()}")
            if pattern and pattern.lower() != "uni":
                style_parts.append(f"avec un motif {pattern.lower()}")
            if fit:
                style_parts.append(f"coupe {fit.lower()}")
            if colors and isinstance(colors, list) and colors:
                color_text = " et ".join(str(c) for c in colors[:2])
                style_parts.append(f"dans des tons {color_text.lower()}")
            if season:
                style_parts.append(f"parfait pour {season.lower()}")
            paragraphs.append("Cette pièce " + ", ".join(style_parts) + ".")
        elif colors and isinstance(colors, list) and colors:
            # Only colors available - make a standalone sentence
            color_text = " et ".join(str(c) for c in colors[:2])
            paragraphs.append(f"Coloris : {color_text}.")

        # Détails techniques
        material = service._safe_get(product, "material")
        lining = service._safe_get(product, "lining")
        stretch = service._safe_get(product, "stretch")
        closure = service._safe_get(product, "closure")
        unique_features = getattr(product, "unique_feature", None)

        tech_sentences = []
        if material:
            tech_sentences.append(f"La matière principale est le {material.lower()}")
        if lining:
            tech_sentences.append(f"Doublure en {lining.lower()}")
        if stretch:
            tech_sentences.append(f"Élasticité {stretch.lower()}")
        if closure:
            tech_sentences.append(f"Fermeture {closure.lower()}")
        if unique_features and isinstance(unique_features, list) and unique_features:
            features_text = ", ".join(str(f) for f in unique_features)
            tech_sentences.append(f"Caractéristiques notables : {features_text}")

        if tech_sentences:
            paragraphs.append(". ".join(tech_sentences) + ".")

        # Origine et époque
        origin = service._safe_get(product, "origin")
        decade = service._safe_get(product, "decade")
        if origin or decade:
            origin_parts = []
            if decade:
                origin_parts.append(f"des années {decade}")
            if origin:
                origin_parts.append(f"origine {origin}")
            paragraphs.append("Pièce " + ", ".join(origin_parts) + ".")

        # État et taille - separate sentences for clarity
        condition = getattr(product, "condition", None)
        condition_text = service._get_condition_text(condition)
        condition_sup = getattr(product, "condition_sup", None)
        size = service._safe_get(product, "size_normalized")

        state_sentences = []
        if condition_text:
            state_sentence = f"État : {condition_text}"
            if condition_sup and isinstance(condition_sup, list) and condition_sup:
                state_sentence += f" ({', '.join(str(s) for s in condition_sup)})"
            state_sentences.append(state_sentence)
        if size:
            state_sentences.append(f"Taille : {size}")

        if state_sentences:
            paragraphs.append(". ".join(state_sentences) + ".")

        # Mesures
        dim1 = getattr(product, "dim1", None)
        dim2 = getattr(product, "dim2", None)
        dim3 = getattr(product, "dim3", None)
        dim4 = getattr(product, "dim4", None)
        dim5 = getattr(product, "dim5", None)
        dim6 = getattr(product, "dim6", None)

        measures = []
        if dim1:
            measures.append(f"Poitrine : {dim1} cm")
        if dim2:
            measures.append(f"Longueur : {dim2} cm")
        if dim3:
            measures.append(f"Épaules : {dim3} cm")
        if dim4:
            measures.append(f"Manches : {dim4} cm")
        if dim5:
            measures.append(f"Tour de taille : {dim5} cm")
        if dim6:
            measures.append(f"Entrejambe : {dim6} cm")

        if measures:
            paragraphs.append("Mesures : " + " | ".join(measures) + ".")

        return "\n\n".join(paragraphs)

    @staticmethod
    def _build_fiche_technique_description(product: Any) -> str:
        """
        Style 3: Fiche Technique - Liste pure pour export/CSV et marketplaces pro.

        Format: Une ligne par attribut, pas de sections, pas d'emojis.
        """
        service = ProductTextGeneratorService
        lines = []

        # All attributes in a flat list format
        attribute_map = [
            ("brand", "Marque"),
            ("model", "Modèle"),
            ("category", "Type"),
            ("gender", "Genre"),
            ("size_normalized", "Taille"),
            ("colors", "Couleur(s)"),
            ("material", "Matière"),
            ("lining", "Doublure"),
            ("stretch", "Élasticité"),
            ("fit", "Coupe"),
            ("rise", "Taille haute/basse"),
            ("length", "Longueur vêtement"),
            ("sleeve_length", "Longueur manches"),
            ("neckline", "Col"),
            ("closure", "Fermeture"),
            ("pattern", "Motif"),
            ("trend", "Tendance"),
            ("season", "Saison"),
            ("sport", "Sport"),
            ("condition", "État"),
            ("condition_sup", "Détails état"),
            ("unique_feature", "Caractéristiques"),
            ("marking", "Marquage"),
            ("origin", "Origine"),
            ("decade", "Époque"),
            ("location", "Localisation"),
            ("dim1", "PTP (cm)"),
            ("dim2", "Longueur (cm)"),
            ("dim3", "Épaules (cm)"),
            ("dim4", "Manches (cm)"),
            ("dim5", "Tour taille (cm)"),
            ("dim6", "Entrejambe (cm)"),
        ]

        for attr, label in attribute_map:
            if attr == "condition":
                condition = getattr(product, "condition", None)
                condition_text = service._get_condition_text(condition)
                if condition_text:
                    lines.append(f"{label} : {condition_text}")
            elif attr == "condition_sup":
                sup = getattr(product, "condition_sup", None)
                if sup and isinstance(sup, list) and sup:
                    lines.append(f"{label} : {', '.join(str(s) for s in sup)}")
            elif attr == "unique_feature":
                features = getattr(product, "unique_feature", None)
                if features and isinstance(features, list) and features:
                    lines.append(f"{label} : {', '.join(str(f) for f in features)}")
            elif attr == "colors":
                colors = getattr(product, "colors", None)
                if colors and isinstance(colors, list) and colors:
                    lines.append(f"{label} : {', '.join(str(c) for c in colors)}")
            elif attr.startswith("dim"):
                dim_value = getattr(product, attr, None)
                if dim_value:
                    lines.append(f"{label} : {dim_value}")
            else:
                value = service._safe_get(product, attr)
                if value:
                    lines.append(f"{label} : {value}")

        return "\n".join(lines)

    @staticmethod
    def _build_vendeur_pro_description(product: Any) -> str:
        """
        Style 4: Vendeur Pro - Hybride avec état et mesures en avant.

        Structure: MARQUE & MODÈLE → ÉTAT DÉTAILLÉ → DIMENSIONS → CARACTÉRISTIQUES → INFOS
        """
        service = ProductTextGeneratorService
        sections = []

        # ⭐ MARQUE & MODÈLE (en haut)
        header = []
        brand = service._safe_get(product, "brand")
        if brand:
            header.append(f"Marque : {brand}")
        model = service._safe_get(product, "model")
        if model:
            header.append(f"Modèle : {model}")
        category = service._safe_get(product, "category")
        if category:
            header.append(f"Type : {category}")
        if header:
            sections.append("⭐ MARQUE & MODÈLE\n" + "\n".join(header))

        # 🔎 ÉTAT DÉTAILLÉ (mis en avant)
        condition_lines = []
        condition = getattr(product, "condition", None)
        condition_text = service._get_condition_text(condition)
        if condition_text:
            condition_lines.append(f"État général : {condition_text}")
        condition_sup = getattr(product, "condition_sup", None)
        if condition_sup and isinstance(condition_sup, list) and condition_sup:
            for detail in condition_sup:
                condition_lines.append(f"  → {detail}")
        if condition_lines:
            sections.append("🔎 ÉTAT DÉTAILLÉ\n" + "\n".join(condition_lines))

        # 📏 DIMENSIONS (mis en avant)
        measures = []
        size = service._safe_get(product, "size_normalized")
        if size:
            measures.append(f"Taille étiquette : {size}")
        dim1 = getattr(product, "dim1", None)
        if dim1:
            measures.append(f"Poitrine (PTP) : {dim1} cm")
        dim2 = getattr(product, "dim2", None)
        if dim2:
            measures.append(f"Longueur : {dim2} cm")
        dim3 = getattr(product, "dim3", None)
        if dim3:
            measures.append(f"Épaules : {dim3} cm")
        dim4 = getattr(product, "dim4", None)
        if dim4:
            measures.append(f"Manches : {dim4} cm")
        dim5 = getattr(product, "dim5", None)
        if dim5:
            measures.append(f"Tour de taille : {dim5} cm")
        dim6 = getattr(product, "dim6", None)
        if dim6:
            measures.append(f"Entrejambe : {dim6} cm")
        if measures:
            sections.append("📏 DIMENSIONS\n" + "\n".join(measures))

        # 🧵 CARACTÉRISTIQUES TECHNIQUES
        tech = []
        material = service._safe_get(product, "material")
        if material:
            tech.append(f"Matière : {material}")
        lining = service._safe_get(product, "lining")
        if lining:
            tech.append(f"Doublure : {lining}")
        stretch = service._safe_get(product, "stretch")
        if stretch:
            tech.append(f"Élasticité : {stretch}")
        fit = service._safe_get(product, "fit")
        if fit:
            tech.append(f"Coupe : {fit}")
        closure = service._safe_get(product, "closure")
        if closure:
            tech.append(f"Fermeture : {closure}")
        colors = getattr(product, "colors", None)
        if colors and isinstance(colors, list) and colors:
            tech.append(f"Couleur(s) : {', '.join(str(c) for c in colors)}")
        pattern = service._safe_get(product, "pattern")
        if pattern:
            tech.append(f"Motif : {pattern}")
        unique_features = getattr(product, "unique_feature", None)
        if unique_features and isinstance(unique_features, list) and unique_features:
            tech.append(f"Spécificités : {', '.join(str(f) for f in unique_features)}")
        if tech:
            sections.append("🧵 CARACTÉRISTIQUES TECHNIQUES\n" + "\n".join(tech))

        # ✨ INFOS SUPPLÉMENTAIRES
        info = []
        gender = service._safe_get(product, "gender")
        if gender:
            info.append(f"Genre : {gender}")
        trend = service._safe_get(product, "trend")
        if trend:
            info.append(f"Style : {trend}")
        season = service._safe_get(product, "season")
        if season:
            info.append(f"Saison : {season}")
        decade = service._safe_get(product, "decade")
        if decade:
            info.append(f"Époque : {decade}")
        origin = service._safe_get(product, "origin")
        if origin:
            info.append(f"Origine : {origin}")
        location = service._safe_get(product, "location")
        if location:
            info.append(f"Localisation : {location}")
        if info:
            sections.append("✨ INFOS SUPPLÉMENTAIRES\n" + "\n".join(info))

        return "\n\n".join(sections)

    @staticmethod
    def _build_visuel_emoji_description(product: Any) -> str:
        """
        Style 5: Visuel Emoji - Un emoji par attribut, facile à scanner.

        Format: Une ligne par attribut avec emoji unique.
        """
        service = ProductTextGeneratorService
        lines = []

        # Emoji mapping for each attribute
        brand = service._safe_get(product, "brand")
        if brand:
            lines.append(f"🏷️ Marque : {brand}")

        model = service._safe_get(product, "model")
        if model:
            lines.append(f"🆔 Modèle : {model}")

        category = service._safe_get(product, "category")
        if category:
            lines.append(f"👕 Type : {category}")

        gender = service._safe_get(product, "gender")
        if gender:
            lines.append(f"👤 Genre : {gender}")

        size = service._safe_get(product, "size_normalized")
        if size:
            lines.append(f"📐 Taille : {size}")

        colors = getattr(product, "colors", None)
        if colors and isinstance(colors, list) and colors:
            lines.append(f"🎨 Couleur(s) : {', '.join(str(c) for c in colors)}")

        material = service._safe_get(product, "material")
        if material:
            lines.append(f"🧵 Matière : {material}")

        lining = service._safe_get(product, "lining")
        if lining:
            lines.append(f"🪡 Doublure : {lining}")

        fit = service._safe_get(product, "fit")
        if fit:
            lines.append(f"✂️ Coupe : {fit}")

        rise = service._safe_get(product, "rise")
        if rise:
            lines.append(f"📍 Hauteur : {rise}")

        length = service._safe_get(product, "length")
        if length:
            lines.append(f"📏 Longueur : {length}")

        sleeve_length = service._safe_get(product, "sleeve_length")
        if sleeve_length:
            lines.append(f"💪 Manches : {sleeve_length}")

        neckline = service._safe_get(product, "neckline")
        if neckline:
            lines.append(f"👔 Col : {neckline}")

        closure = service._safe_get(product, "closure")
        if closure:
            lines.append(f"🔘 Fermeture : {closure}")

        pattern = service._safe_get(product, "pattern")
        if pattern:
            lines.append(f"🔲 Motif : {pattern}")

        stretch = service._safe_get(product, "stretch")
        if stretch:
            lines.append(f"🔄 Élasticité : {stretch}")

        condition = getattr(product, "condition", None)
        condition_text = service._get_condition_text(condition)
        if condition_text:
            lines.append(f"💎 État : {condition_text}")

        condition_sup = getattr(product, "condition_sup", None)
        if condition_sup and isinstance(condition_sup, list) and condition_sup:
            lines.append(f"🔍 Détails : {', '.join(str(s) for s in condition_sup)}")

        unique_features = getattr(product, "unique_feature", None)
        if unique_features and isinstance(unique_features, list) and unique_features:
            lines.append(f"⭐ Spécial : {', '.join(str(f) for f in unique_features)}")

        marking = service._safe_get(product, "marking")
        if marking:
            lines.append(f"🏷️ Marquage : {marking}")

        trend = service._safe_get(product, "trend")
        if trend:
            lines.append(f"📈 Tendance : {trend}")

        season = service._safe_get(product, "season")
        if season:
            lines.append(f"🌤️ Saison : {season}")

        sport = service._safe_get(product, "sport")
        if sport:
            lines.append(f"⚽ Sport : {sport}")

        decade = service._safe_get(product, "decade")
        if decade:
            lines.append(f"📅 Époque : {decade}")

        origin = service._safe_get(product, "origin")
        if origin:
            lines.append(f"🌍 Origine : {origin}")

        location = service._safe_get(product, "location")
        if location:
            lines.append(f"📍 Localisation : {location}")

        # Mesures
        dim1 = getattr(product, "dim1", None)
        if dim1:
            lines.append(f"📊 PTP : {dim1} cm")

        dim2 = getattr(product, "dim2", None)
        if dim2:
            lines.append(f"📊 Longueur : {dim2} cm")

        dim3 = getattr(product, "dim3", None)
        if dim3:
            lines.append(f"📊 Épaules : {dim3} cm")

        dim4 = getattr(product, "dim4", None)
        if dim4:
            lines.append(f"📊 Manches : {dim4} cm")

        dim5 = getattr(product, "dim5", None)
        if dim5:
            lines.append(f"📊 Tour taille : {dim5} cm")

        dim6 = getattr(product, "dim6", None)
        if dim6:
            lines.append(f"📊 Entrejambe : {dim6} cm")

        return "\n".join(lines)

    @staticmethod
    def generate_description(
        product: Any, style: DescriptionStyle = DescriptionStyle.CATALOGUE_STRUCTURE
    ) -> str:
        """
        Generate dynamic description for a product.

        Args:
            product: Product model instance
            style: DescriptionStyle enum (1=Catalogue Structuré, 2=Descriptif Rédigé,
                   3=Fiche Technique, 4=Vendeur Pro, 5=Visuel Emoji)

        Returns:
            Description string (max 5000 chars), segments with missing attributes removed
        """
        service = ProductTextGeneratorService

        if style == DescriptionStyle.CATALOGUE_STRUCTURE:
            description = service._build_catalogue_structure_description(product)
        elif style == DescriptionStyle.DESCRIPTIF_REDIGE:
            description = service._build_descriptif_redige_description(product)
        elif style == DescriptionStyle.FICHE_TECHNIQUE:
            description = service._build_fiche_technique_description(product)
        elif style == DescriptionStyle.VENDEUR_PRO:
            description = service._build_vendeur_pro_description(product)
        elif style == DescriptionStyle.VISUEL_EMOJI:
            description = service._build_visuel_emoji_description(product)
        else:
            description = service._build_catalogue_structure_description(product)

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
                    "minimaliste": "...",
                    "standard_vinted": "...",
                    "seo_mots_cles": "...",
                    "vintage_collectionneur": "...",
                    "technique_professionnel": "..."
                },
                "descriptions": {
                    "catalogue_structure": "...",
                    "descriptif_redige": "...",
                    "fiche_technique": "...",
                    "vendeur_pro": "...",
                    "visuel_emoji": "..."
                }
            }
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
            "model",
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
            "marking",
            "location",
            "dim1",
            "dim2",
            "dim3",
            "dim4",
            "dim5",
            "dim6",
        ]

        for attr in default_attrs:
            if not hasattr(preview, attr):
                setattr(preview, attr, None)

        return ProductTextGeneratorService.generate_all(preview)
