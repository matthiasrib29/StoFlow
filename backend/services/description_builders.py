"""
Description Builders - Template-based description generators for clothing products

Contains 5 description styles and shared utility functions.
Extracted from product_text_generator.py for better separation.

Styles:
1. Catalogue Structure - Sections with emojis, grouped by theme
2. Descriptif Redige - Flowing prose, e-commerce tone
3. Fiche Technique - Pure list, CSV-ready, for pro marketplaces
4. Vendeur Pro - Hybrid, condition & measures upfront
5. Visuel Emoji - One emoji per attribute, scannable

Author: Claude
Date: 2026-01-27 - Extracted from product_text_generator.py
"""

from typing import Any, Optional


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


def get_condition_text(condition: Optional[int]) -> str:
    """Map condition score (0-10) to French text."""
    if condition is None:
        return ""
    return CONDITION_MAP.get(condition, "")


def safe_get(product: Any, attr: str, default: str = "") -> str:
    """
    Safely get attribute value from product object.

    Handles None, lists (colors, unique_feature), and type conversion.
    """
    value = getattr(product, attr, None)

    if value is None:
        return default

    if isinstance(value, list):
        if not value:
            return default
        if attr == "colors":
            return "/".join(str(v) for v in value[:2])
        return str(value[0])

    return str(value)


# =========================================================================
# STYLE 1: CATALOGUE STRUCTURE
# =========================================================================

def build_catalogue_structure(product: Any) -> str:
    """
    Catalogue Structure - Sections with emojis, grouped by theme.

    Structure: INFOS GENERALES -> STYLE & DESIGN -> MATIERES -> ETAT -> MESURES
    """
    sections = []

    # INFORMATIONS GENERALES
    general = []
    brand = safe_get(product, "brand")
    if brand:
        general.append(f"Marque : {brand}")
    model = safe_get(product, "model")
    if model:
        general.append(f"Modèle : {model}")
    category = safe_get(product, "category")
    if category:
        general.append(f"Type : {category}")
    gender = safe_get(product, "gender")
    if gender:
        general.append(f"Genre : {gender}")
    decade = safe_get(product, "decade")
    if decade:
        general.append(f"Époque : {decade}")
    origin = safe_get(product, "origin")
    if origin:
        general.append(f"Origine : {origin}")
    location = safe_get(product, "location")
    if location:
        general.append(f"Localisation : {location}")
    if general:
        sections.append("📋 INFORMATIONS GÉNÉRALES\n" + "\n".join(general))

    # STYLE & DESIGN
    style = []
    colors = getattr(product, "colors", None)
    if colors and isinstance(colors, list) and colors:
        style.append(f"Couleur(s) : {', '.join(str(c) for c in colors)}")
    trend = safe_get(product, "trend")
    if trend:
        style.append(f"Tendance : {trend}")
    pattern = safe_get(product, "pattern")
    if pattern:
        style.append(f"Motif : {pattern}")
    season = safe_get(product, "season")
    if season:
        style.append(f"Saison : {season}")
    sport = safe_get(product, "sport")
    if sport:
        style.append(f"Sport : {sport}")
    fit = safe_get(product, "fit")
    if fit:
        style.append(f"Coupe : {fit}")
    rise = safe_get(product, "rise")
    if rise:
        style.append(f"Taille : {rise}")
    length = safe_get(product, "length")
    if length:
        style.append(f"Longueur : {length}")
    sleeve_length = safe_get(product, "sleeve_length")
    if sleeve_length:
        style.append(f"Manches : {sleeve_length}")
    neckline = safe_get(product, "neckline")
    if neckline:
        style.append(f"Col : {neckline}")
    closure = safe_get(product, "closure")
    if closure:
        style.append(f"Fermeture : {closure}")
    if style:
        sections.append("🎨 STYLE & DESIGN\n" + "\n".join(style))

    # MATIERES & FABRICATION
    materials = []
    material = safe_get(product, "material")
    if material:
        materials.append(f"Matière principale : {material}")
    lining = safe_get(product, "lining")
    if lining:
        materials.append(f"Doublure : {lining}")
    stretch = safe_get(product, "stretch")
    if stretch:
        materials.append(f"Élasticité : {stretch}")
    unique_features = getattr(product, "unique_feature", None)
    if unique_features and isinstance(unique_features, list) and unique_features:
        materials.append(f"Caractéristiques : {', '.join(str(f) for f in unique_features)}")
    marking = safe_get(product, "marking")
    if marking:
        materials.append(f"Marquage : {marking}")
    if materials:
        sections.append("🧵 MATIÈRES & FABRICATION\n" + "\n".join(materials))

    # ETAT
    condition_lines = []
    condition = getattr(product, "condition", None)
    condition_text = get_condition_text(condition)
    if condition_text:
        condition_lines.append(f"État général : {condition_text}")
    condition_sup = getattr(product, "condition_sup", None)
    if condition_sup and isinstance(condition_sup, list) and condition_sup:
        condition_lines.append(f"Détails : {', '.join(str(s) for s in condition_sup)}")
    if condition_lines:
        sections.append("💎 ÉTAT\n" + "\n".join(condition_lines))

    # MESURES
    measures = _build_measures_list(product)
    if measures:
        sections.append("📏 MESURES (en cm)\n" + "\n".join(measures))

    return "\n\n".join(sections)


# =========================================================================
# STYLE 2: DESCRIPTIF REDIGE
# =========================================================================

def build_descriptif_redige(product: Any) -> str:
    """
    Descriptif Redige - Flowing prose, e-commerce tone.

    Structure: Introduction -> Style -> Technical details -> Condition & size -> Measures
    """
    paragraphs = []

    # Introduction
    brand = safe_get(product, "brand")
    model = safe_get(product, "model")
    category = safe_get(product, "category")
    gender = safe_get(product, "gender")

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

    # Style & Design
    trend = safe_get(product, "trend")
    pattern = safe_get(product, "pattern")
    fit = safe_get(product, "fit")
    colors = getattr(product, "colors", None)
    season = safe_get(product, "season")

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
        color_text = " et ".join(str(c) for c in colors[:2])
        paragraphs.append(f"Coloris : {color_text}.")

    # Technical details
    material = safe_get(product, "material")
    lining = safe_get(product, "lining")
    stretch = safe_get(product, "stretch")
    closure = safe_get(product, "closure")
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

    # Origin & era
    origin = safe_get(product, "origin")
    decade = safe_get(product, "decade")
    if origin or decade:
        origin_parts = []
        if decade:
            origin_parts.append(f"des années {decade}")
        if origin:
            origin_parts.append(f"origine {origin}")
        paragraphs.append("Pièce " + ", ".join(origin_parts) + ".")

    # Condition & size
    condition = getattr(product, "condition", None)
    condition_text = get_condition_text(condition)
    condition_sup = getattr(product, "condition_sup", None)
    size = safe_get(product, "size_normalized")

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

    # Measures
    dim_labels = [
        ("dim1", "Poitrine"), ("dim2", "Longueur"), ("dim3", "Épaules"),
        ("dim4", "Manches"), ("dim5", "Tour de taille"), ("dim6", "Entrejambe"),
    ]
    measures = []
    for attr, label in dim_labels:
        val = getattr(product, attr, None)
        if val:
            measures.append(f"{label} : {val} cm")

    if measures:
        paragraphs.append("Mesures : " + " | ".join(measures) + ".")

    return "\n\n".join(paragraphs)


# =========================================================================
# STYLE 3: FICHE TECHNIQUE
# =========================================================================

def build_fiche_technique(product: Any) -> str:
    """
    Fiche Technique - Pure list for export/CSV and pro marketplaces.

    One line per attribute, no sections, no emojis.
    """
    lines = []

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
            condition_text = get_condition_text(condition)
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
            value = safe_get(product, attr)
            if value:
                lines.append(f"{label} : {value}")

    return "\n".join(lines)


# =========================================================================
# STYLE 4: VENDEUR PRO
# =========================================================================

def build_vendeur_pro(product: Any) -> str:
    """
    Vendeur Pro - Hybrid with condition and measures upfront.

    Structure: MARQUE & MODELE -> ETAT DETAILLE -> DIMENSIONS -> CARACTERISTIQUES -> INFOS
    """
    sections = []

    # MARQUE & MODELE
    header = []
    brand = safe_get(product, "brand")
    if brand:
        header.append(f"Marque : {brand}")
    model = safe_get(product, "model")
    if model:
        header.append(f"Modèle : {model}")
    category = safe_get(product, "category")
    if category:
        header.append(f"Type : {category}")
    if header:
        sections.append("⭐ MARQUE & MODÈLE\n" + "\n".join(header))

    # ETAT DETAILLE
    condition_lines = []
    condition = getattr(product, "condition", None)
    condition_text = get_condition_text(condition)
    if condition_text:
        condition_lines.append(f"État général : {condition_text}")
    condition_sup = getattr(product, "condition_sup", None)
    if condition_sup and isinstance(condition_sup, list) and condition_sup:
        for detail in condition_sup:
            condition_lines.append(f"  → {detail}")
    if condition_lines:
        sections.append("🔎 ÉTAT DÉTAILLÉ\n" + "\n".join(condition_lines))

    # DIMENSIONS
    measures = []
    size = safe_get(product, "size_normalized")
    if size:
        measures.append(f"Taille étiquette : {size}")
    measures.extend(_build_measures_list(product))
    if measures:
        sections.append("📏 DIMENSIONS\n" + "\n".join(measures))

    # CARACTERISTIQUES TECHNIQUES
    tech = []
    material = safe_get(product, "material")
    if material:
        tech.append(f"Matière : {material}")
    lining = safe_get(product, "lining")
    if lining:
        tech.append(f"Doublure : {lining}")
    stretch = safe_get(product, "stretch")
    if stretch:
        tech.append(f"Élasticité : {stretch}")
    fit = safe_get(product, "fit")
    if fit:
        tech.append(f"Coupe : {fit}")
    closure = safe_get(product, "closure")
    if closure:
        tech.append(f"Fermeture : {closure}")
    colors = getattr(product, "colors", None)
    if colors and isinstance(colors, list) and colors:
        tech.append(f"Couleur(s) : {', '.join(str(c) for c in colors)}")
    pattern = safe_get(product, "pattern")
    if pattern:
        tech.append(f"Motif : {pattern}")
    unique_features = getattr(product, "unique_feature", None)
    if unique_features and isinstance(unique_features, list) and unique_features:
        tech.append(f"Spécificités : {', '.join(str(f) for f in unique_features)}")
    if tech:
        sections.append("🧵 CARACTÉRISTIQUES TECHNIQUES\n" + "\n".join(tech))

    # INFOS SUPPLEMENTAIRES
    info = []
    gender = safe_get(product, "gender")
    if gender:
        info.append(f"Genre : {gender}")
    trend = safe_get(product, "trend")
    if trend:
        info.append(f"Style : {trend}")
    season = safe_get(product, "season")
    if season:
        info.append(f"Saison : {season}")
    decade = safe_get(product, "decade")
    if decade:
        info.append(f"Époque : {decade}")
    origin = safe_get(product, "origin")
    if origin:
        info.append(f"Origine : {origin}")
    location = safe_get(product, "location")
    if location:
        info.append(f"Localisation : {location}")
    if info:
        sections.append("✨ INFOS SUPPLÉMENTAIRES\n" + "\n".join(info))

    return "\n\n".join(sections)


# =========================================================================
# STYLE 5: VISUEL EMOJI
# =========================================================================

def build_visuel_emoji(product: Any) -> str:
    """
    Visuel Emoji - One emoji per attribute, easy to scan.

    One line per attribute with unique emoji.
    """
    lines = []

    # Emoji mapping for each attribute
    emoji_attrs = [
        ("brand", "🏷️ Marque"),
        ("model", "🆔 Modèle"),
        ("category", "👕 Type"),
        ("gender", "👤 Genre"),
        ("size_normalized", "📐 Taille"),
    ]
    for attr, label in emoji_attrs:
        val = safe_get(product, attr)
        if val:
            lines.append(f"{label} : {val}")

    colors = getattr(product, "colors", None)
    if colors and isinstance(colors, list) and colors:
        lines.append(f"🎨 Couleur(s) : {', '.join(str(c) for c in colors)}")

    simple_emoji_attrs = [
        ("material", "🧵 Matière"),
        ("lining", "🪡 Doublure"),
        ("fit", "✂️ Coupe"),
        ("rise", "📍 Hauteur"),
        ("length", "📏 Longueur"),
        ("sleeve_length", "💪 Manches"),
        ("neckline", "👔 Col"),
        ("closure", "🔘 Fermeture"),
        ("pattern", "🔲 Motif"),
        ("stretch", "🔄 Élasticité"),
    ]
    for attr, label in simple_emoji_attrs:
        val = safe_get(product, attr)
        if val:
            lines.append(f"{label} : {val}")

    # Condition
    condition = getattr(product, "condition", None)
    condition_text = get_condition_text(condition)
    if condition_text:
        lines.append(f"💎 État : {condition_text}")

    condition_sup = getattr(product, "condition_sup", None)
    if condition_sup and isinstance(condition_sup, list) and condition_sup:
        lines.append(f"🔍 Détails : {', '.join(str(s) for s in condition_sup)}")

    unique_features = getattr(product, "unique_feature", None)
    if unique_features and isinstance(unique_features, list) and unique_features:
        lines.append(f"⭐ Spécial : {', '.join(str(f) for f in unique_features)}")

    extra_emoji_attrs = [
        ("marking", "🏷️ Marquage"),
        ("trend", "📈 Tendance"),
        ("season", "🌤️ Saison"),
        ("sport", "⚽ Sport"),
        ("decade", "📅 Époque"),
        ("origin", "🌍 Origine"),
        ("location", "📍 Localisation"),
    ]
    for attr, label in extra_emoji_attrs:
        val = safe_get(product, attr)
        if val:
            lines.append(f"{label} : {val}")

    # Measures
    dim_labels = [
        ("dim1", "📊 PTP"), ("dim2", "📊 Longueur"), ("dim3", "📊 Épaules"),
        ("dim4", "📊 Manches"), ("dim5", "📊 Tour taille"), ("dim6", "📊 Entrejambe"),
    ]
    for attr, label in dim_labels:
        val = getattr(product, attr, None)
        if val:
            lines.append(f"{label} : {val} cm")

    return "\n".join(lines)


# =========================================================================
# SHARED HELPERS
# =========================================================================

def _build_measures_list(product: Any) -> list[str]:
    """Build list of measurement strings from product dimensions."""
    dim_labels = [
        ("dim1", "Poitrine (PTP)"), ("dim2", "Longueur"), ("dim3", "Épaules"),
        ("dim4", "Manches"), ("dim5", "Tour de taille"), ("dim6", "Entrejambe"),
    ]
    measures = []
    for attr, label in dim_labels:
        val = getattr(product, attr, None)
        if val:
            measures.append(f"{label} : {val} cm")
    return measures
