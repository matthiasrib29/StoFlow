"""
Etsy Product Conversion Service.

Convertit les produits Stoflow vers le format Etsy API v3:
- Mapping attributs Stoflow → Etsy
- Validation données requises
- Génération payload API Etsy
- Gestion des variations (tailles, couleurs)

Business Rules (2025-12-10):
- Etsy requiert: quantity, title, description, price, who_made, when_made, taxonomy_id
- Prix en USD (float, pas de centimes comme eBay)
- Tags max 13, max 20 caractères chacun
- Materials max 13 items
- Title max 140 caractères
- Description max 50 000 caractères

Author: Claude
Date: 2025-12-10
"""

from typing import Any, Dict, List, Optional

from models.user.product import Product
from shared.exceptions import ProductValidationError


class EtsyProductConversionService:
    """
    Service de conversion produits Stoflow → Etsy.

    Usage:
        >>> service = EtsyProductConversionService()
        >>> product = db.query(Product).first()
        >>>
        >>> # Convert to Etsy listing format
        >>> listing_data = service.convert_to_listing_data(
        ...     product,
        ...     taxonomy_id=1234,  # Category
        ...     shipping_profile_id=5678,
        ... )
        >>>
        >>> # Create listing on Etsy
        >>> client.create_draft_listing(listing_data)
    """

    # Mapping condition (Integer 0-10) → Etsy who_made
    # 10 = Neuf avec étiquettes, 9 = Neuf sans étiquettes, 8 = Très bon état
    # 7 = Bon état, 6 = Satisfaisant, 5 = À réparer
    CONDITION_TO_WHO_MADE = {
        10: "i_did",  # Neuf avec étiquettes = fait par moi
        9: "i_did",   # Neuf sans étiquettes = fait par moi
        8: "i_did",   # Très bon état = fait par moi
        7: "someone_else",  # Bon état = fait par quelqu'un d'autre
        6: "someone_else",  # Satisfaisant
        5: "someone_else",  # À réparer
    }

    # Mapping condition (Integer 0-10) → Etsy when_made
    CONDITION_TO_WHEN_MADE = {
        10: "made_to_order",  # Neuf avec étiquettes
        9: "made_to_order",   # Neuf sans étiquettes
        8: "2020_2023",       # Très bon état
        7: "2010_2019",       # Bon état
        6: "before_2010",     # Satisfaisant
        5: "before_2010",     # À réparer
    }

    def __init__(self):
        """Initialise le service de conversion."""
        pass

    def convert_to_listing_data(
        self,
        product: Product,
        taxonomy_id: int,
        shipping_profile_id: Optional[int] = None,
        return_policy_id: Optional[int] = None,
        shop_section_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Convertit un produit Stoflow en listing_data Etsy.

        Args:
            product: Produit Stoflow
            taxonomy_id: ID catégorie Etsy (requis)
            shipping_profile_id: ID shipping profile Etsy (optionnel)
            return_policy_id: ID return policy Etsy (optionnel)
            shop_section_id: ID shop section Etsy (optionnel)

        Returns:
            Dict prêt pour create_draft_listing()

        Raises:
            ProductValidationError: Si données invalides

        Examples:
            >>> service = EtsyProductConversionService()
            >>> listing_data = service.convert_to_listing_data(
            ...     product,
            ...     taxonomy_id=1234,
            ...     shipping_profile_id=5678,
            ... )
        """
        # Validation
        self._validate_product(product)

        # Basic required fields
        listing_data = {
            "quantity": int(product.stock_quantity or 1),
            "title": self._build_title(product),
            "description": self._build_description(product),
            "price": float(product.price or 0.0),
            "who_made": self._get_who_made(product),
            "when_made": self._get_when_made(product),
            "taxonomy_id": taxonomy_id,
        }

        # Optional fields
        if shipping_profile_id:
            listing_data["shipping_profile_id"] = shipping_profile_id

        if return_policy_id:
            listing_data["return_policy_id"] = return_policy_id

        if shop_section_id:
            listing_data["shop_section_id"] = shop_section_id

        # Tags (max 13, max 20 chars each)
        tags = self._build_tags(product)
        if tags:
            listing_data["tags"] = tags

        # Materials (max 13)
        materials = self._build_materials(product)
        if materials:
            listing_data["materials"] = materials

        # Dimensions (if available)
        if product.dim1 and product.dim2 and product.dim3:
            listing_data.update(
                {
                    "item_length": float(product.dim1),
                    "item_width": float(product.dim2),
                    "item_height": float(product.dim3),
                    "item_dimensions_unit": "cm",
                }
            )

        # Product type (physical by default)
        listing_data["type"] = "physical"

        # Auto-renew (default false)
        listing_data["should_auto_renew"] = False

        # Supply or finished product
        listing_data["is_supply"] = False  # Finished product, not craft supply

        return listing_data

    def _validate_product(self, product: Product) -> None:
        """
        Valide qu'un produit a les données requises pour Etsy.

        Args:
            product: Produit à valider

        Raises:
            ProductValidationError: Si validation échoue
        """
        errors = []

        # Title requis
        if not product.title or len(product.title.strip()) == 0:
            errors.append("Title est requis")

        # Title max 140 chars
        if product.title and len(product.title) > 140:
            errors.append("Title doit faire max 140 caractères (actuellement: {})".format(len(product.title)))

        # Description requise
        if not product.description or len(product.description.strip()) == 0:
            errors.append("Description est requise")

        # Price requis > 0
        if not product.price or product.price <= 0:
            errors.append("Price doit être > 0")

        # Stock quantity requis > 0
        if not product.stock_quantity or product.stock_quantity <= 0:
            errors.append("Stock quantity doit être > 0")

        # Images requises (au moins 1)
        image_urls = self._get_image_urls(product)
        if not image_urls or len(image_urls) == 0:
            errors.append("Au moins 1 image est requise pour publier sur Etsy")

        if errors:
            raise ProductValidationError(
                "Validation Etsy échouée:\n" + "\n".join(f"- {e}" for e in errors)
            )

    def _build_title(self, product: Product) -> str:
        """
        Construit le title Etsy (max 140 chars).

        Args:
            product: Produit Stoflow

        Returns:
            Title optimisé pour Etsy
        """
        title = product.title or ""

        # Truncate if too long
        if len(title) > 140:
            title = title[:137] + "..."

        return title

    def _build_description(self, product: Product) -> str:
        """
        Construit la description Etsy (max 50 000 chars).

        Args:
            product: Produit Stoflow

        Returns:
            Description enrichie
        """
        description_parts = []

        # Description principale
        if product.description:
            description_parts.append(product.description)

        # Ajouter attributs importants
        if product.brand:
            description_parts.append(f"\n**Brand:** {product.brand}")

        if product.material:
            description_parts.append(f"\n**Material:** {product.material}")

        if product.color:
            description_parts.append(f"\n**Color:** {product.color}")

        if product.size_original:
            description_parts.append(f"\n**Size:** {product.size_original}")

        if product.condition:
            description_parts.append(f"\n**Condition:** {product.condition}")

        description = "\n".join(description_parts)

        # Truncate if too long (max 50 000 chars)
        if len(description) > 50000:
            description = description[:49997] + "..."

        return description

    def _get_who_made(self, product: Product) -> str:
        """
        Détermine le who_made Etsy basé sur la condition.

        Args:
            product: Produit Stoflow

        Returns:
            who_made value (i_did, someone_else, collective)
        """
        condition = product.condition if product.condition is not None else 7  # 7 = Bon état (default)
        return self.CONDITION_TO_WHO_MADE.get(condition, "someone_else")

    def _get_when_made(self, product: Product) -> str:
        """
        Détermine le when_made Etsy basé sur la condition.

        Args:
            product: Produit Stoflow

        Returns:
            when_made value (made_to_order, 2020_2023, etc.)
        """
        condition = product.condition if product.condition is not None else 7  # 7 = Bon état (default)
        return self.CONDITION_TO_WHEN_MADE.get(condition, "2010_2019")

    def _build_tags(self, product: Product) -> List[str]:
        """
        Construit la liste de tags Etsy (max 13, max 20 chars each).

        Args:
            product: Produit Stoflow

        Returns:
            Liste de tags
        """
        tags = []

        # Add category as tag
        if product.category:
            tag = product.category.lower()[:20]
            if tag not in tags:
                tags.append(tag)

        # Add brand as tag
        if product.brand:
            tag = product.brand.lower()[:20]
            if tag not in tags:
                tags.append(tag)

        # Add color as tag
        if product.color:
            tag = product.color.lower()[:20]
            if tag not in tags:
                tags.append(tag)

        # Add material as tag
        if product.material:
            tag = product.material.lower()[:20]
            if tag not in tags:
                tags.append(tag)

        # Add condition as tag
        if product.condition:
            tag = product.condition.lower()[:20]
            if tag not in tags:
                tags.append(tag)

        # Add gender as tag
        if product.gender:
            tag = product.gender.lower()[:20]
            if tag not in tags:
                tags.append(tag)

        # Max 13 tags
        return tags[:13]

    def _build_materials(self, product: Product) -> List[str]:
        """
        Construit la liste de materials Etsy (max 13).

        Args:
            product: Produit Stoflow

        Returns:
            Liste de matériaux
        """
        materials = []

        # Add main material
        if product.material:
            materials.append(product.material)

        # Max 13 materials
        return materials[:13]

    def _get_image_urls(self, product: Product) -> List[str]:
        """
        Extrait les URLs d'images du produit.

        Args:
            product: Produit Stoflow

        Returns:
            Liste d'URLs
        """
        if not product.images:
            return []

        if isinstance(product.images, list):
            return product.images

        # If stored as JSON string
        import json

        try:
            return json.loads(product.images)
        except (json.JSONDecodeError, TypeError):
            return []

    def build_inventory_update(
        self,
        product: Product,
        sku: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Construit un payload d'update inventaire Etsy.

        Args:
            product: Produit Stoflow
            sku: SKU optionnel

        Returns:
            Dict pour update_listing_inventory()

        Examples:
            >>> inventory_data = service.build_inventory_update(
            ...     product,
            ...     sku="PROD-001"
            ... )
            >>> client.update_listing_inventory(listing_id, inventory_data)
        """
        return {
            "products": [
                {
                    "sku": sku or product.sku,
                    "offerings": [
                        {
                            "price": float(product.price or 0.0),
                            "quantity": int(product.stock_quantity or 1),
                            "is_enabled": True,
                        }
                    ],
                }
            ]
        }
