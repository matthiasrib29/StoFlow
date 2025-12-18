"""
Vinted Product Validator

Service de validation des produits pour Vinted.
Responsabilité: Validation business rules avant publication.

Business Rules (2024-12-10):
- Stock > 0 (requis pour création et update)
- Prix > 0 (requis pour création et update)
- Marque présente (requis)
- Catégorie présente (requis)
- Attributs mappés: brand_id, color_id, condition_id, size_id, category_id (tous requis sauf size pour lunettes)
- Images: minimum 1, maximum 20

Architecture:
- Validation pure (pas d'accès DB)
- Retourne tuple (is_valid, error_message)
- Utilisé avant toute opération Vinted (create/update)

Created: 2024-12-10
Author: Claude
"""

from typing import Tuple, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from models.user.product import Product


class VintedProductValidator:
    """
    Valide qu'un produit peut être publié sur Vinted.
    
    Vérifie toutes les business rules requises par Vinted.
    """

    @staticmethod
    def validate_for_creation(product: "Product") -> Tuple[bool, Optional[str]]:
        """
        Valide qu'un produit peut être créé sur Vinted.

        Règles de validation:
        - Stock > 0
        - Prix > 0
        - Marque présente
        - Catégorie présente
        - Genre présent

        Args:
            product: Instance de Product

        Returns:
            Tuple (is_valid, error_message)
            - (True, None) si valide
            - (False, "raison") si invalide

        Examples:
            >>> product = Product(stock_quantity=0, price=25.0)
            >>> valid, error = VintedProductValidator.validate_for_creation(product)
            >>> print(valid, error)
            False "Stock insuffisant: 0"

            >>> product = Product(stock_quantity=1, price=25.0, brand="Levi's", category="Jeans")
            >>> valid, error = VintedProductValidator.validate_for_creation(product)
            >>> print(valid, error)
            True None
        """
        # Vérifier stock
        if not hasattr(product, 'stock_quantity') or product.stock_quantity is None:
            return False, "Stock non défini"

        if product.stock_quantity <= 0:
            return False, f"Stock insuffisant: {product.stock_quantity}"

        # Vérifier prix
        if not hasattr(product, 'price') or product.price is None:
            return False, "Prix non défini"

        try:
            price_float = float(product.price)
            if price_float <= 0:
                return False, f"Prix invalide: {product.price}"
        except (ValueError, TypeError):
            return False, f"Prix invalide (format): {product.price}"

        # Vérifier marque
        if not hasattr(product, 'brand') or not product.brand:
            return False, "Marque manquante"

        # Vérifier catégorie
        if not hasattr(product, 'category') or not product.category:
            return False, "Catégorie manquante"

        # Vérifier genre (pour mapping taille)
        if not hasattr(product, 'gender') or not product.gender:
            return False, "Genre manquant"

        return True, None

    @staticmethod
    def validate_for_update(product: "Product") -> Tuple[bool, Optional[str]]:
        """
        Valide qu'un produit peut être mis à jour sur Vinted.

        Règles identiques à validate_for_creation:
        - Stock > 0 (obligatoire pour update)
        - Prix > 0
        - Marque présente
        - Catégorie présente

        Args:
            product: Instance de Product

        Returns:
            Tuple (is_valid, error_message)

        Examples:
            >>> product = Product(stock_quantity=0, price=25.0)
            >>> valid, error = VintedProductValidator.validate_for_update(product)
            >>> print(valid, error)
            False "Stock insuffisant: 0"
        """
        # Pour l'instant, les règles d'update sont identiques à create
        return VintedProductValidator.validate_for_creation(product)

    @staticmethod
    def validate_mapped_attributes(mapped_attrs: dict, product_id: Optional[int] = None) -> Tuple[bool, Optional[str]]:
        """
        Valide que tous les attributs requis sont mappés.

        Règles:
        - brand_id requis
        - color_id requis
        - condition_id requis
        - category_id requis (TODO: quand mapping catégories implémenté)
        - size_id requis (sauf lunettes category_id=98)

        Args:
            mapped_attrs: Dictionnaire des attributs mappés
            product_id: ID produit (pour logs, optionnel)

        Returns:
            Tuple (is_valid, error_message)
            - (True, None) si tous les attributs requis sont présents
            - (False, "attributs_manquants") si manquants

        Examples:
            >>> mapped = {'brand_id': 123, 'color_id': None}
            >>> valid, error = VintedProductValidator.validate_mapped_attributes(mapped)
            >>> print(valid, error)
            False "Attributs manquants: color_id, condition_id"

            >>> mapped = {'brand_id': 123, 'color_id': 12, 'condition_id': 1, 'size_id': 207}
            >>> valid, error = VintedProductValidator.validate_mapped_attributes(mapped)
            >>> print(valid, error)
            True None
        """
        required = ['brand_id', 'color_id', 'condition_id']

        # category_id sera requis quand le mapping sera implémenté
        # required.append('category_id')

        # size_id requis sauf pour lunettes (category_id = 98)
        # Pour l'instant, on le rend toujours requis car pas de mapping catégories
        if mapped_attrs.get('category_id') != 98:
            required.append('size_id')

        missing = [attr for attr in required if not mapped_attrs.get(attr)]

        if missing:
            missing_str = ', '.join(missing)
            return False, f"Attributs manquants: {missing_str}"

        return True, None

    @staticmethod
    def validate_images(image_ids: list) -> Tuple[bool, Optional[str]]:
        """
        Valide que les images sont présentes et conformes.

        Règles:
        - Au moins 1 image (BLOQUANT)
        - Maximum 20 images (limite Vinted)

        Args:
            image_ids: Liste des IDs images uploadées

        Returns:
            Tuple (is_valid, error_message)

        Examples:
            >>> valid, error = VintedProductValidator.validate_images([])
            >>> print(valid, error)
            False "Aucune image uploadée"

            >>> valid, error = VintedProductValidator.validate_images([123, 456])
            >>> print(valid, error)
            True None

            >>> valid, error = VintedProductValidator.validate_images([1]*21)
            >>> print(valid, error)
            False "Trop d'images: 21 (max 20)"
        """
        if not image_ids or len(image_ids) == 0:
            return False, "Aucune image uploadée"

        if len(image_ids) > 20:
            return False, f"Trop d'images: {len(image_ids)} (max 20)"

        return True, None
