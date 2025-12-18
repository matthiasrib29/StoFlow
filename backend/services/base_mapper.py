"""
Base Marketplace Mapper

Classe de base abstraite pour les mappers de marketplaces.
Définit l'interface commune et les méthodes utilitaires partagées.

Business Rules (2025-12-10):
- Chaque mapper doit pouvoir convertir dans les deux sens
- Format Stoflow standardisé pour tous les imports
- Métadonnées d'intégration pour traçabilité

Author: Claude
Date: 2025-12-10
"""

from abc import ABC, abstractmethod
from typing import Optional


class BaseMarketplaceMapper(ABC):
    """
    Classe de base abstraite pour les mappers de marketplaces.

    Chaque marketplace (Vinted, eBay, Etsy) doit implémenter cette interface.

    Attributes:
        PLATFORM_NAME: Nom de la plateforme (ex: "vinted", "ebay", "etsy")
        CONDITION_MAP: Mapping condition plateforme → Stoflow
        CATEGORY_MAP: Mapping catégorie plateforme → Stoflow
        REVERSE_CONDITION_MAP: Mapping condition Stoflow → plateforme
        REVERSE_CATEGORY_MAP: Mapping catégorie Stoflow → plateforme
    """

    PLATFORM_NAME: str = ""
    CONDITION_MAP: dict = {}
    CATEGORY_MAP: dict = {}
    REVERSE_CONDITION_MAP: dict = {}
    REVERSE_CATEGORY_MAP: dict = {}

    # ===== MÉTHODES ABSTRAITES (à implémenter) =====

    @staticmethod
    @abstractmethod
    def platform_to_stoflow(platform_item: dict) -> dict:
        """
        Convertit un produit de la plateforme en format Stoflow.

        Args:
            platform_item: Objet item de l'API de la plateforme

        Returns:
            dict: Données produit format Stoflow standardisé:
                {
                    "title": str,
                    "description": str,
                    "price": float,
                    "brand": str | None,
                    "category": str,
                    "condition": str,  # NEW, EXCELLENT, GOOD, FAIR, POOR
                    "label_size": str | None,
                    "color": str | None,
                    "images": list[str],
                    "stock_quantity": int,
                    "integration_metadata": {
                        "source": str,
                        "imported_at": datetime | None,
                        ...platform-specific fields
                    }
                }
        """
        pass

    @staticmethod
    @abstractmethod
    def stoflow_to_platform(stoflow_product: dict) -> dict:
        """
        Convertit un produit Stoflow en format plateforme pour publication.

        Args:
            stoflow_product: Données produit Stoflow

        Returns:
            dict: Payload pour API de la plateforme

        Raises:
            ValueError: Si mapping impossible (catégorie non supportée, etc.)
        """
        pass

    # ===== MÉTHODES COMMUNES (helpers) =====

    @classmethod
    def get_supported_categories(cls) -> list[str]:
        """
        Retourne la liste des catégories Stoflow supportées par cette plateforme.

        Returns:
            list[str]: Liste unique des catégories supportées
        """
        return list(set(cls.CATEGORY_MAP.values()))

    @classmethod
    def is_category_supported(cls, category: str) -> bool:
        """
        Vérifie si une catégorie Stoflow est supportée pour cette plateforme.

        Args:
            category: Nom de la catégorie Stoflow

        Returns:
            bool: True si supportée
        """
        return category in cls.REVERSE_CATEGORY_MAP

    @classmethod
    def get_platform_category_id(cls, stoflow_category: str) -> Optional[int]:
        """
        Retourne l'ID de catégorie de la plateforme pour une catégorie Stoflow.

        Args:
            stoflow_category: Nom catégorie Stoflow (ex: "Jeans")

        Returns:
            int | None: Category ID plateforme ou None si non trouvé
        """
        return cls.REVERSE_CATEGORY_MAP.get(stoflow_category)

    @classmethod
    def get_stoflow_category(cls, platform_category_id: int) -> str:
        """
        Retourne la catégorie Stoflow pour un ID de catégorie plateforme.

        Args:
            platform_category_id: ID catégorie plateforme

        Returns:
            str: Catégorie Stoflow ou "Other" si non trouvé
        """
        return cls.CATEGORY_MAP.get(platform_category_id, "Other")

    @classmethod
    def map_condition_to_stoflow(cls, platform_condition_id) -> str:
        """
        Mappe une condition plateforme vers Stoflow.

        Args:
            platform_condition_id: ID ou valeur condition plateforme

        Returns:
            str: Condition Stoflow (défaut: "GOOD")
        """
        return cls.CONDITION_MAP.get(platform_condition_id, "GOOD")

    @classmethod
    def map_condition_to_platform(cls, stoflow_condition: str):
        """
        Mappe une condition Stoflow vers la plateforme.

        Args:
            stoflow_condition: Condition Stoflow

        Returns:
            ID ou valeur condition plateforme (défaut: valeur pour "GOOD")
        """
        default_value = cls.REVERSE_CONDITION_MAP.get("GOOD")
        return cls.REVERSE_CONDITION_MAP.get(stoflow_condition, default_value)

    @classmethod
    def build_integration_metadata(
        cls,
        platform_id,
        platform_url: Optional[str] = None,
        **extra_fields
    ) -> dict:
        """
        Construit les métadonnées d'intégration standardisées.

        Args:
            platform_id: ID unique sur la plateforme
            platform_url: URL du produit sur la plateforme
            **extra_fields: Champs supplémentaires spécifiques à la plateforme

        Returns:
            dict: Métadonnées d'intégration formatées
        """
        metadata = {
            "source": cls.PLATFORM_NAME,
            f"{cls.PLATFORM_NAME}_id": platform_id,
            f"{cls.PLATFORM_NAME}_url": platform_url,
            "imported_at": None,  # Sera rempli par le service d'import
        }

        # Ajouter les champs supplémentaires avec préfixe plateforme
        for key, value in extra_fields.items():
            metadata[f"{cls.PLATFORM_NAME}_{key}"] = value

        return metadata

    @staticmethod
    def extract_images(
        item: dict,
        image_field: str = "photos",
        url_field: str = "url"
    ) -> list[str]:
        """
        Extrait les URLs d'images d'un item.

        Args:
            item: Item de la plateforme
            image_field: Nom du champ contenant les images
            url_field: Nom du champ URL dans chaque image

        Returns:
            list[str]: Liste des URLs d'images
        """
        images = []
        image_list = item.get(image_field, [])

        if isinstance(image_list, list):
            for img in image_list:
                if isinstance(img, dict):
                    url = img.get(url_field)
                    if url:
                        images.append(url)
                elif isinstance(img, str):
                    images.append(img)

        return images


__all__ = ["BaseMarketplaceMapper"]
