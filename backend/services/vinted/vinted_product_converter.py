"""
Vinted Product Converter - Builder de payloads pour l'API Vinted

Convertit un Product Stoflow vers le format exact attendu par l'API Vinted.
Basé sur pythonApiWOO/services/vinted/vinted_product_converter.py.

Business Rules (2025-12-18):
- Payload structure identique à celle découverte par reverse engineering
- UUID temporaire généré pour chaque requête
- Photos assignées avec orientation=0
- Prix en EUR avec 2 décimales
- package_size_id=1 (petit colis) par défaut
- item_attributes: Liste des attributs structurés (material, etc.)

Author: Claude
Date: 2025-12-12
Updated: 2025-12-18 - Added item_attributes support for materials
Source: pythonApiWOO reverse engineering
"""

import uuid
from typing import Any, List

from models.user.product import Product
from models.user.vinted_product import VintedProduct
from shared.logging import get_logger

logger = get_logger(__name__)


class VintedProductConverter:
    """
    Convertit un Product vers le format payload API Vinted.

    Usage:
        mapped_attrs = VintedMappingService.map_all_attributes(db, product)
        prix_vinted = VintedPricingService.calculate_price(product)
        payload = VintedProductConverter.build_create_payload(
            product, photo_ids, mapped_attrs, prix_vinted
        )
    """

    # Package sizes (IDs Vinted)
    PACKAGE_SMALL = 1      # Petit colis (< 1kg)
    PACKAGE_MEDIUM = 2     # Moyen colis (1-2kg)
    PACKAGE_LARGE = 3      # Grand colis (2-5kg)
    PACKAGE_EXTRA = 5      # Très grand colis (> 5kg)

    @staticmethod
    def build_create_payload(
        product: Product,
        photo_ids: list[int],
        mapped_attrs: dict[str, Any],
        prix_vinted: float,
        title: str,
        description: str
    ) -> dict[str, Any]:
        """
        Construit le payload pour créer un produit Vinted.

        Args:
            product: Instance Product Stoflow
            photo_ids: Liste des IDs photos uploadées sur Vinted
            mapped_attrs: Attributs mappés depuis VintedMappingService:
                - brand_id: int | None
                - color_id: int | None
                - condition_id: int | None (status_id Vinted)
                - size_id: int | None
                - category_id: int (catalog_id Vinted)
                - gender: str
                - is_bottom: bool
                - material_ids: list[int] (for item_attributes)
            prix_vinted: Prix calculé pour Vinted
            title: Titre généré (max 100 caractères)
            description: Description générée (max 2000 caractères)

        Returns:
            dict: Payload prêt pour POST /api/v2/item_upload/items

        Raises:
            ValueError: Si attributs requis manquants

        Example:
            >>> payload = VintedProductConverter.build_create_payload(
            ...     product, [123, 456], mapped_attrs, 27.90, title, desc
            ... )
            >>> # Envoyer via plugin: POST /api/v2/item_upload/items
        """
        # Validation des attributs requis
        if not mapped_attrs.get('category_id'):
            raise ValueError("category_id (catalog_id) requis pour publication Vinted")

        # Marque: ID si mappé, sinon texte libre
        brand_id = mapped_attrs.get('brand_id')
        brand_text = product.brand if not brand_id else ""

        # Déterminer si unisex (lunettes = category 98)
        is_unisex = mapped_attrs.get('category_id') == 98

        # Dimensions (uniquement pour hauts)
        dim_width, dim_length = VintedProductConverter._get_dimensions(
            product, mapped_attrs.get('is_bottom', False)
        )

        # Build item_attributes (materials, etc.)
        item_attributes = VintedProductConverter._build_item_attributes(mapped_attrs)

        return {
            "item": {
                "id": None,
                "currency": "EUR",
                "temp_uuid": str(uuid.uuid4()),
                "title": title,
                "description": description,
                "brand_id": int(brand_id) if brand_id else None,
                "brand": brand_text or "",
                "size_id": int(mapped_attrs['size_id']) if mapped_attrs.get('size_id') else None,
                "catalog_id": int(mapped_attrs['category_id']),
                "isbn": None,
                "is_unisex": is_unisex,
                "status_id": int(mapped_attrs['condition_id']) if mapped_attrs.get('condition_id') else None,
                "video_game_rating_id": None,
                "price": round(prix_vinted, 2),
                "package_size_id": VintedProductConverter.PACKAGE_SMALL,
                "shipment_prices": {
                    "domestic": None,
                    "international": None
                },
                "color_ids": [int(mapped_attrs['color_id'])] if mapped_attrs.get('color_id') else [],
                "assigned_photos": [
                    {"id": photo_id, "orientation": 0}
                    for photo_id in photo_ids
                ],
                "measurement_length": dim_length,
                "measurement_width": dim_width,
                "item_attributes": item_attributes,
                "manufacturer": None,
                "manufacturer_labelling": None
            },
            "feedback_id": None,
            "push_up": False,
            "parcel": None,
            "upload_session_id": str(uuid.uuid4())
        }

    @staticmethod
    def build_update_payload(
        product: Product,
        vinted_product: VintedProduct,
        mapped_attrs: dict[str, Any],
        prix_vinted: float,
        title: str,
        description: str
    ) -> dict[str, Any]:
        """
        Construit le payload pour mettre à jour un produit Vinted.

        Args:
            product: Instance Product Stoflow
            vinted_product: Instance VintedProduct existante
            mapped_attrs: Attributs mappés
            prix_vinted: Prix calculé
            title: Titre généré
            description: Description générée

        Returns:
            dict: Payload prêt pour PUT /api/v2/item_upload/items/{vinted_id}
        """
        if not vinted_product.vinted_id:
            raise ValueError("vinted_id requis pour mise à jour")

        # Récupérer les photo IDs existants
        photo_ids = vinted_product.image_ids_list

        # Marque
        brand_id = mapped_attrs.get('brand_id')
        brand_text = product.brand or ""

        # Unisex
        is_unisex = mapped_attrs.get('category_id') == 98

        # Dimensions
        dim_width, dim_length = VintedProductConverter._get_dimensions(
            product, mapped_attrs.get('is_bottom', False)
        )

        # Build item_attributes (materials, etc.)
        item_attributes = VintedProductConverter._build_item_attributes(mapped_attrs)

        return {
            "feedback_id": None,
            "item": {
                "id": vinted_product.vinted_id,
                "currency": "EUR",
                "temp_uuid": str(uuid.uuid4()),
                "title": title,
                "description": description,
                "brand_id": int(brand_id) if brand_id else None,
                "brand": brand_text,
                "size_id": int(mapped_attrs['size_id']) if mapped_attrs.get('size_id') else None,
                "catalog_id": int(mapped_attrs['category_id']) if mapped_attrs.get('category_id') else None,
                "isbn": None,
                "is_unisex": is_unisex,
                "status_id": int(mapped_attrs['condition_id']) if mapped_attrs.get('condition_id') else None,
                "video_game_rating_id": None,
                "price": round(prix_vinted, 2),
                "package_size_id": VintedProductConverter.PACKAGE_SMALL,
                "shipment_prices": {
                    "domestic": None,
                    "international": None
                },
                "color_ids": [int(mapped_attrs['color_id'])] if mapped_attrs.get('color_id') else [],
                "assigned_photos": [
                    {"id": photo_id, "orientation": 0}
                    for photo_id in photo_ids
                ],
                "measurement_length": dim_length,
                "measurement_width": dim_width,
                "item_attributes": item_attributes,
                "manufacturer": None,
                "manufacturer_labelling": "Article complet avec étiquetage, conseils d'entretien et certifications."
            },
            "push_up": False,
            "parcel": None,
            "upload_session_id": str(uuid.uuid4())
        }

    @staticmethod
    def build_price_update_payload(
        vinted_id: int,
        new_price: float
    ) -> dict[str, Any]:
        """
        Construit un payload minimal pour mise à jour du prix uniquement.

        Args:
            vinted_id: ID Vinted du produit
            new_price: Nouveau prix

        Returns:
            dict: Payload pour PUT /api/v2/item_upload/items/{vinted_id}
        """
        return {
            "item": {
                "id": vinted_id,
                "price": round(new_price, 2)
            }
        }

    @staticmethod
    def _get_dimensions(product: Product, is_bottom: bool) -> tuple[int | None, int | None]:
        """
        Extrait les dimensions pour les hauts uniquement.

        Business Rules (pythonApiWOO):
        - Dimensions affichées uniquement pour: Sweat-shirt & Pull, T-shirt
        - Pas de dimensions pour bas (jeans, pantalons)

        Args:
            product: Instance Product
            is_bottom: True si c'est un bas

        Returns:
            tuple: (width, length) en cm ou (None, None)
        """
        # Pas de dimensions pour les bas
        if is_bottom:
            return None, None

        # Catégories éligibles aux dimensions
        categories_with_dimensions = [
            'Sweat-shirt',
            'Pull',
            'T-shirt',
            'Sweatshirt',
            'Sweater'
        ]

        # Vérifier si catégorie éligible
        category = getattr(product, 'category', None)
        if category:
            category_name = category if isinstance(category, str) else getattr(category, 'name_en', '')
            if not any(cat.lower() in category_name.lower() for cat in categories_with_dimensions):
                return None, None

        # Extraire dimensions depuis product
        dim1 = getattr(product, 'dim1', None)
        dim2 = getattr(product, 'dim2', None)

        # Convertir en entiers si présents
        width = int(dim1) if dim1 else None
        length = int(dim2) if dim2 else None

        return width, length

    @staticmethod
    def _build_item_attributes(mapped_attrs: dict[str, Any]) -> List[dict[str, Any]]:
        """
        Construit la liste item_attributes pour Vinted.

        Format Vinted: [{"code": "material", "ids": [44, 45]}]

        Args:
            mapped_attrs: Attributs mappés contenant material_ids, etc.

        Returns:
            Liste de dicts au format Vinted item_attributes

        Example:
            >>> attrs = {'material_ids': [44, 303]}
            >>> VintedProductConverter._build_item_attributes(attrs)
            [{'code': 'material', 'ids': [44, 303]}]
        """
        item_attributes = []

        # Materials (max 3)
        material_ids = mapped_attrs.get('material_ids', [])
        if material_ids:
            item_attributes.append({
                "code": "material",
                "ids": material_ids
            })

        # Future: Add other item_attributes here (pattern, etc.) if Vinted supports them

        return item_attributes

    @staticmethod
    def build_image_upload_payload(
        image_url: str | None = None,
        image_base64: str | None = None,
        filename: str = "photo.jpg"
    ) -> dict[str, Any]:
        """
        Construit le payload pour upload d'image Vinted.

        Note: L'API Vinted attend un multipart/form-data.
        Ce payload est adapté pour le plugin qui gère la conversion.

        Args:
            image_url: URL de l'image à uploader (option 1)
            image_base64: Image encodée en base64 (option 2)
            filename: Nom du fichier

        Returns:
            dict: Payload pour POST /api/v2/photos
        """
        payload = {
            "photo": {
                "type": "item",
                "temp_uuid": ""
            }
        }

        if image_url:
            payload["image_url"] = image_url
        elif image_base64:
            payload["image_base64"] = image_base64
            payload["filename"] = filename

        return payload
