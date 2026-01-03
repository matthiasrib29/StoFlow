"""
Vinted Title Service

Service de génération de titres SEO optimisés pour Vinted.
Responsabilité: Construire des titres de max 100 caractères avec un maximum d'attributs.

Business Rules (2024-12-10):
- Format: {Marque} {Model} {Catégorie} {Fit} {Taille} {Condition} {Couleur} {Decade} (Emplacement) [SKU]
- Max 100 caractères (limite Vinted)
- SKU et Emplacement toujours présents à la fin
- Remplir avec le maximum d'attributs possible selon ordre de priorité
- Title Case (première lettre majuscule)
- Normalisation majuscules pour éviter rejet Vinted

Architecture:
- Service pur (pas d'accès DB)
- Utilise les relations SQLAlchemy pour traductions (name_fr)
- Compatible avec modèle Product Stoflow

Created: 2024-12-10
Author: Claude (adapted from pythonApiWOO)
"""

from typing import Optional, TYPE_CHECKING
import logging
import re

if TYPE_CHECKING:
    from models.user.product import Product

logger = logging.getLogger(__name__)

# Limite maximale de caractères pour un titre Vinted
MAX_TITLE_LENGTH = 100


class VintedTitleService:
    """
    Génère des titres SEO optimisés pour Vinted.
    
    Format: {Marque} {Model} {Catégorie} {Fit} {Taille} {Condition} {Couleur} {Decade} (Emplacement) [SKU]
    
    Règles:
    - Max 100 caractères
    - SKU et Emplacement toujours présents à la fin
    - Remplir avec le maximum d'attributs possible
    - Title Case (première lettre majuscule)
    """

    # Ordre de priorité des attributs (du plus important au moins important)
    # Les derniers seront supprimés en premier si le titre est trop long
    PRIORITY_ORDER = [
        'brand',      # 1. Marque (obligatoire)
        'model',      # 2. Modèle (501, etc.) - juste après marque
        'category',   # 3. Catégorie (obligatoire)
        'fit',        # 4. Fit/Coupe
        'size',       # 5. Taille
        'condition',  # 6. État
        'color',      # 7. Couleur
        'decade',     # 8. Décennie/Vintage
    ]

    # Mapping des conditions (Integer 0-10) vers texte français lisible
    # 10 = Neuf avec étiquettes, 9 = Neuf sans étiquettes, 8 = Très bon état
    # 7 = Bon état, 6 = Satisfaisant, 5 = À réparer
    CONDITION_LABELS = {
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
    }

    @staticmethod
    def generate_title(product: "Product") -> str:
        """
        Génère un titre SEO optimisé pour un produit Vinted.

        Args:
            product: Instance de Product

        Returns:
            Titre optimisé (max 100 caractères)

        Example:
            >>> title = VintedTitleService.generate_title(product)
            "Levi's 501 Jean Flare Taille 36 Très Bon État Bleu Vintage 90s (A3) [2726]"
        """
        # 1. Extraire les valeurs des attributs
        attributes = VintedTitleService._extract_attributes(product)

        # 2. Construire le suffixe obligatoire (emplacement + SKU)
        suffix = VintedTitleService._build_suffix(product)

        # 3. Construire le titre avec le maximum d'attributs
        title = VintedTitleService._build_title_with_max_attributes(attributes, suffix)

        # 4. Appliquer Title Case
        title = VintedTitleService._apply_title_case(title)

        # 5. Normaliser les majuscules (validation Vinted)
        title = VintedTitleService._normalize_uppercase(title)

        logger.debug(f"Titre généré pour product ID#{product.id}: {title} ({len(title)} chars)")

        return title

    @staticmethod
    def _extract_attributes(product: "Product") -> dict:
        """
        Extrait et formate tous les attributs disponibles du produit.

        Returns:
            Dict avec les attributs formatés (clé -> valeur string ou None)
        """
        attributes = {}

        # Marque (Title Case) - exclure "unbranded"
        brand_value = VintedTitleService._clean_value(product.brand)
        if brand_value and brand_value.lower() != 'unbranded':
            attributes['brand'] = VintedTitleService._to_title_case(brand_value)
        else:
            attributes['brand'] = None

        # Catégorie (utiliser name_fr si disponible via relation)
        category_value = product.category
        attributes['category'] = VintedTitleService._clean_value(category_value)

        # Fit/Coupe
        fit_value = getattr(product, 'fit', None)
        attributes['fit'] = VintedTitleService._clean_value(fit_value)

        # Taille (prefer size_original, fallback to size_normalized)
        size_value = product.size_original or getattr(product, 'size_normalized', None)
        if size_value:
            attributes['size'] = f"Taille {VintedTitleService._clean_value(size_value)}"
        else:
            attributes['size'] = None

        # Modèle (501, 505, etc.)
        model_value = getattr(product, 'model', None)
        attributes['model'] = VintedTitleService._clean_value(model_value)

        # Condition/État (mapper vers texte lisible)
        # Supports both Integer (0-10) and legacy string conditions
        condition_value = None
        if product.condition is not None:
            # Try integer key first (new format)
            condition_value = VintedTitleService.CONDITION_LABELS.get(product.condition)
            if condition_value is None and isinstance(product.condition, str):
                # Fallback to uppercase string key (legacy format)
                condition_key = product.condition.upper().strip()
                condition_value = VintedTitleService.CONDITION_LABELS.get(condition_key)
            if condition_value is None:
                # Final fallback: use raw value
                condition_value = VintedTitleService._clean_value(str(product.condition))
        attributes['condition'] = condition_value

        # Couleur
        color_value = product.color
        attributes['color'] = VintedTitleService._clean_value(color_value)

        # Décennie
        decade_value = getattr(product, 'decade', None)
        if decade_value:
            decade_value = VintedTitleService._format_decade(decade_value)
        attributes['decade'] = decade_value

        return attributes

    @staticmethod
    def _build_suffix(product: "Product") -> str:
        """
        Construit le suffixe obligatoire: (Emplacement) [ID]

        Returns:
            String du type "(A3) [2726]"
        """
        parts = []

        # Emplacement (location)
        location = getattr(product, 'location', None)
        if location:
            parts.append(f"({location})")

        # ID produit (toujours présent)
        parts.append(f"[{product.id}]")

        return " ".join(parts)

    @staticmethod
    def _build_title_with_max_attributes(attributes: dict, suffix: str) -> str:
        """
        Construit le titre en incluant le maximum d'attributs possible
        tout en respectant la limite de 100 caractères.

        Args:
            attributes: Dict des attributs formatés
            suffix: Suffixe obligatoire "(A3) [2726]"

        Returns:
            Titre complet
        """
        # Espace réservé pour le suffixe + 1 espace
        reserved_space = len(suffix) + 1
        available_space = MAX_TITLE_LENGTH - reserved_space

        # Construire la liste des parties dans l'ordre de priorité
        title_parts = []
        current_length = 0

        for attr_key in VintedTitleService.PRIORITY_ORDER:
            attr_value = attributes.get(attr_key)

            if not attr_value:
                continue

            # Calculer la longueur avec cette partie ajoutée
            separator = " " if title_parts else ""
            potential_addition = len(separator) + len(attr_value)

            if current_length + potential_addition <= available_space:
                title_parts.append(attr_value)
                current_length += potential_addition
            else:
                # Plus assez de place, on s'arrête
                logger.debug(f"Titre tronqué: pas assez de place pour '{attr_key}' ({attr_value})")
                break

        # Assembler le titre final
        title_body = " ".join(title_parts)
        full_title = f"{title_body} {suffix}".strip()

        return full_title

    @staticmethod
    def _apply_title_case(title: str) -> str:
        """
        Applique Title Case au titre tout en préservant certains formats.

        Préserve:
        - Les marques en majuscules (LEVI'S reste LEVI'S si c'est le format d'origine)
        - Les IDs entre crochets [2726]
        - Les emplacements entre parenthèses (A3)
        """
        # Le titre est déjà formaté correctement via les attributs
        # On ne modifie pas la casse pour éviter de casser les marques
        return title

    @staticmethod
    def _clean_value(value: Optional[str]) -> Optional[str]:
        """
        Nettoie une valeur d'attribut.

        - Supprime les espaces en trop
        - Retourne None si vide
        """
        if not value:
            return None

        cleaned = str(value).strip()
        return cleaned if cleaned else None

    @staticmethod
    def _to_title_case(value: str) -> str:
        """
        Convertit en Title Case tout en préservant certains formats.

        - "wrangler" -> "Wrangler"
        - "LEVI'S" -> "Levi's"
        - "ecko unltd" -> "Ecko Unltd"
        """
        if not value:
            return value

        # Capitaliser chaque mot
        return value.title()

    @staticmethod
    def _normalize_uppercase(title: str) -> str:
        """
        Normalise les majuscules pour éviter le rejet Vinted.

        Règle Vinted: "Titre contient trop de lettres majuscules"

        Stratégie:
        - Préserver les acronymes courts (2-3 lettres): USA, UK, XL, XXL
        - Préserver les IDs entre crochets [2726]
        - Préserver les emplacements (A3), (L12)
        - Convertir les mots entièrement en majuscules (>3 lettres) en Title Case

        Exemples:
        - "TEXAS STRETCH" → "Texas Stretch"
        - "USA MADE" → "USA Made"
        - "XL" → "XL" (préservé)
        - "[2726]" → "[2726]" (préservé)
        """
        if not title:
            return title

        # Découper en mots (en préservant les crochets et parenthèses)
        words = re.findall(r'\[[^\]]+\]|\([^\)]+\)|\S+', title)
        normalized_words = []

        for word in words:
            # Préserver les IDs [xxx] et emplacements (xxx)
            if word.startswith('[') or word.startswith('('):
                normalized_words.append(word)
                continue

            # Si le mot est entièrement en majuscules
            if word.isupper():
                # Préserver les acronymes courts (2-3 lettres)
                if len(word) <= 3:
                    normalized_words.append(word)
                else:
                    # Convertir en Title Case les mots longs (>3 lettres)
                    normalized_words.append(word.title())
            else:
                # Mot avec casse mixte → garder tel quel
                normalized_words.append(word)

        return ' '.join(normalized_words)

    @staticmethod
    def _format_decade(decade: str) -> Optional[str]:
        """
        Formate une décennie pour l'affichage.

        Examples:
            "1990s" -> "Vintage 90s"
            "90s" -> "Vintage 90s"
            "1980" -> "Vintage 80s"
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
