"""
Translation Helper for Vinted Descriptions

Gère les traductions FR/EN pour les descriptions Vinted.

Author: Claude
Date: 2025-12-11
"""

import re
from typing import Optional


class TranslationHelper:
    """Helper pour traduire les attributs produit en français."""

    # Traduction catégories EN → FR
    CATEGORIES = {
        'Jeans': 'Jean',
        'Jacket': 'Veste',
        'Coat': 'Manteau',
        'Shirt': 'Chemise',
        'T-shirt': 'T-shirt',
        'Sweatshirt': 'Sweat',
        'Pants': 'Pantalon',
        'Shorts': 'Short',
        'Skirt': 'Jupe',
        'Dress': 'Robe',
        'Sweater': 'Pull',
        'Blazer': 'Blazer',
        'Suit': 'Costume',
        'Accessories': 'Accessoires',
        'Shoes': 'Chaussures',
        'Bag': 'Sac',
        'Sunglasses': 'Lunettes de soleil',
    }

    # Traduction couleurs EN → FR
    COLORS = {
        'Blue': 'Bleu',
        'Red': 'Rouge',
        'Green': 'Vert',
        'Black': 'Noir',
        'White': 'Blanc',
        'Grey': 'Gris',
        'Gray': 'Gris',
        'Brown': 'Marron',
        'Yellow': 'Jaune',
        'Orange': 'Orange',
        'Pink': 'Rose',
        'Purple': 'Violet',
        'Beige': 'Beige',
        'Navy': 'Bleu marine',
        'Khaki': 'Kaki',
        'Olive': 'Olive',
        'Burgundy': 'Bordeaux',
    }

    # Mapping condition (Integer 0-10) → texte lisible
    # 10 = Neuf avec étiquettes, 9 = Neuf sans étiquettes, 8 = Très bon état
    # 7 = Bon état, 6 = Satisfaisant, 5 = À réparer
    CONDITIONS = {
        10: 'Neuf avec étiquettes',
        9: 'Neuf sans étiquettes',
        8: 'Très bon état',
        7: 'Bon état',
        6: 'État correct',
        5: 'À rénover',
        # Legacy string support (fallback)
        'EXCELLENT': 'Très bon état',
        'GOOD': 'Bon état',
        'FAIR': 'État correct',
        'POOR': 'À rénover',
        'NEW': 'Neuf',
    }

    # Texte par défaut selon la condition (Integer 0-10)
    CONDITION_DEFAULTS = {
        10: 'Neuf avec étiquettes, jamais porté.',
        9: 'Neuf sans étiquettes, jamais porté.',
        8: 'Très peu porté, comme neuf.',
        7: "Quelques signes d'usure légers mais rien de grave.",
        6: "Signes d'usure visibles mais encore en bon état d'usage.",
        5: 'Usé, nécessite quelques réparations.',
        # Legacy string support (fallback)
        'NEW': 'Jamais porté, avec ou sans étiquette.',
        'EXCELLENT': 'Très peu porté, comme neuf.',
        'GOOD': "Quelques signes d'usure légers mais rien de grave.",
        'FAIR': "Signes d'usure visibles mais encore en bon état d'usage.",
        'POOR': 'Usé, nécessite quelques réparations.',
    }

    @classmethod
    def translate_category(cls, category: str) -> str:
        """Traduit une catégorie en français."""
        return cls.CATEGORIES.get(category, category)

    @classmethod
    def translate_color(cls, color: str) -> str:
        """Traduit une couleur en français."""
        return cls.COLORS.get(color, color)

    @classmethod
    def get_condition_text(cls, condition: str) -> str:
        """Retourne le texte lisible d'une condition."""
        key = str(condition).upper().strip()
        return cls.CONDITIONS.get(key, condition)

    @classmethod
    def get_condition_default_text(cls, condition: str) -> Optional[str]:
        """Retourne un texte par défaut selon la condition."""
        key = str(condition).upper().strip()
        return cls.CONDITION_DEFAULTS.get(key)

    @classmethod
    def format_decade_fr(cls, decade: str) -> Optional[str]:
        """
        Formate une décennie en français.

        Examples:
            "1990s" → "Vintage 90s"
            "90s" → "Vintage 90s"
            "1980" → "Vintage 80s"
        """
        if not decade:
            return None

        decade_str = str(decade).strip().lower()

        # Extraire les chiffres
        match = re.search(r'(\d{2,4})', decade_str)
        if not match:
            return None

        year = match.group(1)

        # Convertir en format court (90s, 80s, etc.)
        if len(year) == 4:
            short_decade = year[2:] + "s"
        elif len(year) == 2:
            short_decade = year + "s"
        else:
            return None

        return f"Vintage {short_decade}"

    @classmethod
    def normalize_decade(cls, decade: str) -> str:
        """
        Normalise une décennie pour le matching des hashtags.

        Examples:
            "1990s" → "90s"
            "90s" → "90s"
            "1980" → "80s"
        """
        if not decade:
            return ""

        decade_str = str(decade).strip().lower()

        # Extraire les chiffres
        match = re.search(r'(\d{2,4})', decade_str)
        if not match:
            return ""

        year = match.group(1)

        # Convertir en format court
        if len(year) == 4:
            return year[2:] + "s"
        elif len(year) == 2:
            return year + "s"

        return ""


__all__ = ["TranslationHelper"]
