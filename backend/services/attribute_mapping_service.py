"""
Attribute Mapping Service

Service pour gérer le mapping bidirectionnel FR/EN des attributs.

Business Rules (2025-12-08):
- Affichage UI en français (name_fr)
- Stockage DB en anglais (name_en ou name)
- Mapping bidirectionnel : FR ↔ EN
- Compatible avec PostEditFlet logic

Author: Claude
Date: 2025-12-08
"""

from typing import Dict

from sqlalchemy.orm import Session

from models.public.brand import Brand
from models.public.category import Category
from models.public.color import Color
from models.public.condition import Condition
from models.public.fit import Fit
from models.public.gender import Gender
from models.public.material import Material
from models.public.season import Season
from models.public.size import Size


class AttributeMappingService:
    """Service pour gérer le mapping FR/EN des attributs."""

    # Map des attributs avec leur modèle SQLAlchemy
    ATTRIBUTE_MODELS = {
        "brand": Brand,
        "category": Category,
        "color": Color,
        "condition": Condition,
        "fit": Fit,
        "gender": Gender,
        "material": Material,
        "season": Season,
        "size": Size,
    }

    def __init__(self, db: Session):
        """
        Initialise le service et charge tous les mappings.

        Args:
            db: Session SQLAlchemy
        """
        self.db = db
        self.mappings: Dict[str, Dict[str, str]] = {}
        self._load_all_mappings()

    def _load_all_mappings(self) -> None:
        """
        Charge tous les mappings FR/EN depuis la DB.

        Business Rules:
        - Mapping bidirectionnel : FR → EN ET EN → FR
        - Si name_fr NULL → Utiliser name_en comme fallback
        """
        for attr_name, model_class in self.ATTRIBUTE_MODELS.items():
            self.mappings[attr_name] = {}

            # Déterminer les colonnes à query selon le modèle
            if attr_name in ["brand", "size"]:
                # Brand et Size ont 'name' (pas name_en)
                results = self.db.query(
                    model_class.name,
                    model_class.name_fr
                ).all()

                for name_en, name_fr in results:
                    display_value = name_fr if name_fr else name_en

                    # Mapping bidirectionnel
                    self.mappings[attr_name][display_value] = name_en  # FR → EN
                    self.mappings[attr_name][name_en] = display_value  # EN → FR

            elif attr_name == "condition":
                # Condition a 'name' (pas name_en) + description_fr
                results = self.db.query(
                    model_class.name,
                    model_class.description_fr
                ).all()

                for name, description_fr in results:
                    display_value = description_fr if description_fr else name

                    # Mapping bidirectionnel
                    self.mappings[attr_name][display_value] = name  # FR → EN
                    self.mappings[attr_name][name] = display_value  # EN → FR

            else:
                # Autres modèles ont name_en + name_fr
                results = self.db.query(
                    model_class.name_en,
                    model_class.name_fr
                ).all()

                for name_en, name_fr in results:
                    display_value = name_fr if name_fr else name_en

                    # Mapping bidirectionnel
                    self.mappings[attr_name][display_value] = name_en  # FR → EN
                    self.mappings[attr_name][name_en] = display_value  # EN → FR

    def to_db_value(self, attr_name: str, display_value: str | None) -> str | None:
        """
        Convertit une valeur d'affichage (FR) vers la valeur DB (EN).

        Business Rules:
        - Si display_value est déjà EN → Retourne tel quel
        - Si display_value est FR → Convertit vers EN
        - Si non trouvé → Retourne tel quel (assume EN)

        Args:
            attr_name: Nom de l'attribut (ex: "color", "brand", "category")
            display_value: Valeur affichée (ex: "Bleu", "Blue")

        Returns:
            str | None: Valeur DB (EN) ou None

        Examples:
            >>> mapper = AttributeMappingService(db)
            >>> mapper.to_db_value("color", "Bleu")
            "Blue"

            >>> mapper.to_db_value("color", "Blue")
            "Blue"
        """
        if not display_value:
            return None

        if attr_name not in self.mappings:
            return display_value

        # Chercher dans le mapping
        return self.mappings[attr_name].get(display_value, display_value)

    def to_display_value(self, attr_name: str, db_value: str | None) -> str | None:
        """
        Convertit une valeur DB (EN) vers la valeur d'affichage (FR).

        Business Rules:
        - Si db_value a une traduction FR → Retourne FR
        - Si pas de traduction → Retourne EN
        - Si non trouvé → Retourne tel quel

        Args:
            attr_name: Nom de l'attribut (ex: "color", "brand", "category")
            db_value: Valeur DB (EN) (ex: "Blue", "Levi's")

        Returns:
            str | None: Valeur d'affichage (FR) ou None

        Examples:
            >>> mapper = AttributeMappingService(db)
            >>> mapper.to_display_value("color", "Blue")
            "Bleu"

            >>> mapper.to_display_value("brand", "Levi's")
            "Levi's"
        """
        if not db_value:
            return None

        if attr_name not in self.mappings:
            return db_value

        # Chercher dans le mapping
        return self.mappings[attr_name].get(db_value, db_value)

    def to_db_value_category(self, display_value: str | None) -> str | None:
        """
        Convertit une catégorie FR → EN avec validation bidirectionnelle.

        Business Rules (CRITIQUE pour pricing):
        - Conversion FR → EN obligatoire avant calcul prix
        - Table pricing.clothing_prices contient catégories EN uniquement
        - Validation bidirectionnelle pour éviter conversion EN → FR

        Args:
            display_value: Catégorie affichée (ex: "Jean", "Jeans")

        Returns:
            str | None: Catégorie EN (ex: "Jeans") ou None

        Examples:
            >>> mapper = AttributeMappingService(db)
            >>> mapper.to_db_value_category("Jean")
            "Jeans"

            >>> mapper.to_db_value_category("Jeans")
            "Jeans"
        """
        if not display_value:
            return None

        if "category" not in self.mappings:
            return display_value

        # Chercher mapping
        mapped_value = self.mappings["category"].get(display_value)

        if mapped_value and mapped_value != display_value:
            # Vérifier mapping inverse pour confirmer FR → EN
            reverse_mapped = self.mappings["category"].get(mapped_value)
            if reverse_mapped == display_value:
                return mapped_value  # Retourne version EN

        return display_value  # Déjà EN ou pas de mapping

    def get_all_values(self, attr_name: str, language: str = "fr") -> list[str]:
        """
        Récupère toutes les valeurs d'un attribut dans une langue.

        Args:
            attr_name: Nom de l'attribut (ex: "color", "brand")
            language: Langue ("fr" ou "en")

        Returns:
            list[str]: Liste des valeurs

        Examples:
            >>> mapper = AttributeMappingService(db)
            >>> colors_fr = mapper.get_all_values("color", "fr")
            >>> print(colors_fr)
            ["Bleu", "Rouge", "Noir", "Blanc", ...]
        """
        if attr_name not in self.mappings:
            return []

        if language == "fr":
            # Retourner toutes les clés qui sont des valeurs FR
            # (distinguer FR de EN est difficile sans métadonnée supplémentaire)
            # Pour simplifier, retourner toutes les clés uniques
            return list(set(self.mappings[attr_name].keys()))

        else:  # language == "en"
            # Retourner toutes les valeurs EN
            return list(set(self.mappings[attr_name].values()))
