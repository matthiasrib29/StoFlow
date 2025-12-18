"""
Section Builder for Vinted Descriptions

Construit les différentes sections d'une description Vinted.

Author: Claude
Date: 2025-12-11
"""

from typing import Optional, List, TYPE_CHECKING

from .translation_helper import TranslationHelper
from .measurement_extractor import MeasurementExtractor
from .hashtag_config import HashtagConfig

if TYPE_CHECKING:
    from models.user.product import Product


class SectionBuilder:
    """
    Construit les sections individuelles d'une description Vinted.

    Sections:
    - Hook (accroche)
    - Product Info (informations produit)
    - Condition (état)
    - Measurements (mesures)
    - Shipping (expédition)
    - Hashtags
    """

    @staticmethod
    def _safe_get(obj, attr: str) -> Optional[str]:
        """Récupère un attribut de manière sûre."""
        value = getattr(obj, attr, None)
        if value:
            return str(value).strip()
        return None

    @classmethod
    def build_hook(cls, product: "Product") -> str:
        """
        Construit un hook accrocheur pour commencer la description.

        Examples:
            "Découvrez ce magnifique jean Levi's 501 vintage des années 90s !"
            "Superbe veste en cuir vintage, une pièce unique !"
        """
        brand = cls._safe_get(product, 'brand')
        category = cls._safe_get(product, 'category')
        decade = cls._safe_get(product, 'decade')

        parts = []

        if brand and brand.lower() != 'unbranded':
            parts.append(brand)

        if hasattr(product, 'model') and product.model:
            parts.append(product.model)

        if category:
            category_fr = TranslationHelper.translate_category(category)
            parts.append(category_fr)

        if decade:
            decade_str = TranslationHelper.format_decade_fr(decade)
            if decade_str:
                parts.append(decade_str)

        if parts:
            hook_text = " ".join(parts)
            return f"Découvrez ce magnifique {hook_text} !"

        return "Découvrez cette pièce unique !"

    @classmethod
    def build_product_info(cls, product: "Product") -> Optional[str]:
        """
        Construit la section d'informations produit.

        Format:
        Informations:
        * Marque: Levi's
        * Modèle: 501
        * Catégorie: Jean
        * Coupe: Regular
        * Taille: 32
        * Couleur: Bleu
        * Matière: 100% Coton
        * Décennie: Vintage 90s
        """
        lines = ["Informations:"]

        # Marque
        brand = cls._safe_get(product, 'brand')
        if brand and brand.lower() != 'unbranded':
            lines.append(f"* Marque: {brand}")

        # Modèle
        model = cls._safe_get(product, 'model')
        if model:
            lines.append(f"* Modèle: {model}")

        # Catégorie
        category = cls._safe_get(product, 'category')
        if category:
            category_fr = TranslationHelper.translate_category(category)
            lines.append(f"* Catégorie: {category_fr}")

        # Fit/Coupe
        fit = cls._safe_get(product, 'fit')
        if fit:
            lines.append(f"* Coupe: {fit}")

        # Taille
        size = cls._safe_get(product, 'size')
        if size:
            lines.append(f"* Taille: {size}")

        # Couleur (en français)
        color = cls._safe_get(product, 'color')
        if color:
            color_fr = TranslationHelper.translate_color(color)
            lines.append(f"* Couleur: {color_fr}")

        # Matière
        material = cls._safe_get(product, 'material')
        if material:
            lines.append(f"* Matière: {material}")

        # Décennie
        decade = cls._safe_get(product, 'decade')
        if decade:
            decade_str = TranslationHelper.format_decade_fr(decade)
            if decade_str:
                lines.append(f"* Époque: {decade_str}")

        if len(lines) > 1:  # Au moins une info en plus du titre
            return "\n".join(lines)

        return None

    @classmethod
    def build_condition(cls, product: "Product") -> Optional[str]:
        """
        Construit la section état/condition.

        Format:
        État: Très bon état
        Quelques signes d'usure légers mais rien de grave.
        """
        condition = cls._safe_get(product, 'condition')
        if not condition:
            return None

        lines = []

        # Mapper la condition vers texte lisible
        condition_text = TranslationHelper.get_condition_text(condition)
        lines.append(f"État: {condition_text}")

        # Ajouter détails supplémentaires si disponibles
        condition_details = getattr(product, 'condition_details', None)
        if condition_details:
            lines.append(condition_details)
        else:
            # Ajouter un texte par défaut selon la condition
            default_text = TranslationHelper.get_condition_default_text(condition)
            if default_text:
                lines.append(default_text)

        return "\n".join(lines)

    @classmethod
    def build_measurements(cls, product: "Product") -> Optional[str]:
        """
        Construit la section mesures selon le type de produit.
        """
        measurements = MeasurementExtractor.extract(product)

        if not measurements:
            return None

        lines = ["Mesures (cm):"]
        lines.extend([f"* {name}: {value} cm" for name, value in measurements])

        return "\n".join(lines)

    @classmethod
    def build_shipping(cls) -> str:
        """
        Construit la section expédition (standard).
        """
        return (
            "Expédition soignée sous 1-2 jours ouvrés.\n"
            "N'hésitez pas à me contacter pour toute question !"
        )

    @classmethod
    def build_hashtags(cls, product: "Product") -> str:
        """
        Construit la liste de hashtags (max 40).

        Priorité:
        1. Hashtags fixes (5)
        2. Hashtags marque (si applicable)
        3. Hashtags catégorie
        4. Hashtags fit/coupe
        5. Hashtags décennie
        6. Hashtags matière
        7. Hashtags saison
        8. Hashtags tendance
        """
        all_hashtags: List[str] = []

        # 1. Hashtags fixes (toujours présents)
        all_hashtags.extend(HashtagConfig.FIXED)

        # 2. Hashtags marque
        brand = cls._safe_get(product, 'brand')
        if brand and brand in HashtagConfig.BY_BRAND:
            all_hashtags.extend(HashtagConfig.BY_BRAND[brand])

        # 3. Hashtags catégorie
        category = cls._safe_get(product, 'category')
        if category and category in HashtagConfig.BY_CATEGORY:
            all_hashtags.extend(HashtagConfig.BY_CATEGORY[category])

        # 4. Hashtags fit
        fit = cls._safe_get(product, 'fit')
        if fit and fit in HashtagConfig.BY_FIT:
            all_hashtags.extend(HashtagConfig.BY_FIT[fit])

        # 5. Hashtags décennie
        decade = cls._safe_get(product, 'decade')
        if decade:
            decade_normalized = TranslationHelper.normalize_decade(decade)
            if decade_normalized in HashtagConfig.BY_DECADE:
                all_hashtags.extend(HashtagConfig.BY_DECADE[decade_normalized])

        # 6. Hashtags matière
        material = cls._safe_get(product, 'material')
        if material and material in HashtagConfig.BY_MATERIAL:
            all_hashtags.extend(HashtagConfig.BY_MATERIAL[material])

        # 7. Hashtags saison
        season = cls._safe_get(product, 'season')
        if season and season in HashtagConfig.BY_SEASON:
            all_hashtags.extend(HashtagConfig.BY_SEASON[season])

        # 8. Hashtags tendance (compléter jusqu'à 40)
        remaining_slots = HashtagConfig.MAX_HASHTAGS - len(all_hashtags)
        if remaining_slots > 0:
            all_hashtags.extend(HashtagConfig.TRENDING[:remaining_slots])

        # Dédupliquer et limiter à 40
        unique_hashtags: List[str] = []
        seen: set = set()
        for tag in all_hashtags:
            tag_lower = tag.lower()
            if tag_lower not in seen:
                unique_hashtags.append(tag)
                seen.add(tag_lower)
                if len(unique_hashtags) >= HashtagConfig.MAX_HASHTAGS:
                    break

        return " ".join(unique_hashtags)


__all__ = ["SectionBuilder"]
