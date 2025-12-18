"""
eBay Inventory Item Groups Client (Multi-Variations).

Client pour gérer les listings avec variations (tailles, couleurs, etc.).

Permet de créer un seul listing avec plusieurs variations:
- T-shirt disponible en S/M/L/XL
- Chaussures disponibles en pointures 38-45
- Produit disponible en plusieurs couleurs

Endpoints implémentés:
- POST /sell/inventory/v1/inventory_item_group - Créer groupe
- PUT /sell/inventory/v1/inventory_item_group/{group_id} - Modifier groupe
- GET /sell/inventory/v1/inventory_item_group/{group_id} - Récupérer groupe
- DELETE /sell/inventory/v1/inventory_item_group/{group_id} - Supprimer groupe

Documentation officielle:
https://developer.ebay.com/api-docs/sell/inventory/resources/inventory_item_group/methods/createOrReplaceInventoryItemGroup

Author: Claude
Date: 2025-12-10
"""

from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from services.ebay.ebay_base_client import EbayBaseClient


class EbayInventoryGroupClient(EbayBaseClient):
    """
    Client eBay Inventory Item Groups (Multi-Variations).

    Usage:
        >>> client = EbayInventoryGroupClient(db_session, user_id=1)
        >>>
        >>> # Créer groupe pour T-shirt avec variations taille
        >>> group_data = {
        ...     "aspects": {
        ...         "Brand": ["Nike"],
        ...         "Color": ["Black"],
        ...         "Size": ["S", "M", "L", "XL"]  # Variations
        ...     },
        ...     "title": "T-shirt Nike Black",
        ...     "description": "T-shirt Nike en coton",
        ...     "imageUrls": ["https://..."],
        ...     "variantSKUs": ["SKU-123-S", "SKU-123-M", "SKU-123-L", "SKU-123-XL"],
        ...     "variesBy": {
        ...         "specifications": [
        ...             {"name": "Size", "values": ["S", "M", "L", "XL"]}
        ...         ]
        ...     }
        ... }
        >>> result = client.create_or_replace_inventory_item_group(
        ...     "GROUP-TSHIRT-NIKE-123",
        ...     group_data
        ... )
    """

    def create_or_replace_inventory_item_group(
        self,
        inventory_item_group_key: str,
        group_data: Dict[str, Any],
    ) -> None:
        """
        Crée ou remplace un groupe d'inventory items (multi-variations).

        Args:
            inventory_item_group_key: Clé unique du groupe (ex: "GROUP-TSHIRT-123")
            group_data: Données du groupe avec structure:
                {
                    "aspects": {
                        "Brand": ["Nike"],
                        "Color": ["Black"],
                        "Size": ["S", "M", "L", "XL"]  # Variations
                    },
                    "title": "T-shirt Nike Black",
                    "description": "Description produit",
                    "imageUrls": ["https://..."],
                    "variantSKUs": ["SKU-S", "SKU-M", "SKU-L", "SKU-XL"],
                    "variesBy": {
                        "specifications": [
                            {
                                "name": "Size",
                                "values": ["S", "M", "L", "XL"]
                            }
                        ]
                    }
                }

        Examples:
            >>> # T-shirt avec variations taille
            >>> group_data = {
            ...     "aspects": {
            ...         "Brand": ["Nike"],
            ...         "Size": ["S", "M", "L"]
            ...     },
            ...     "title": "T-shirt Nike",
            ...     "description": "T-shirt Nike en coton",
            ...     "imageUrls": ["https://example.com/image.jpg"],
            ...     "variantSKUs": ["SKU-123-S", "SKU-123-M", "SKU-123-L"],
            ...     "variesBy": {
            ...         "specifications": [
            ...             {"name": "Size", "values": ["S", "M", "L"]}
            ...         ]
            ...     }
            ... }
            >>> client.create_or_replace_inventory_item_group(
            ...     "GROUP-NIKE-TSHIRT-123",
            ...     group_data
            ... )
        """
        scopes = ["sell.inventory"]

        self.api_call(
            "PUT",
            f"/sell/inventory/v1/inventory_item_group/{inventory_item_group_key}",
            json_data=group_data,
            scopes=scopes,
        )

    def get_inventory_item_group(
        self,
        inventory_item_group_key: str,
    ) -> Dict[str, Any]:
        """
        Récupère un groupe d'inventory items.

        Args:
            inventory_item_group_key: Clé du groupe

        Returns:
            Détails du groupe

        Examples:
            >>> group = client.get_inventory_item_group("GROUP-NIKE-TSHIRT-123")
            >>> print(f"Titre: {group['title']}")
            >>> print(f"Variations: {group['variantSKUs']}")
        """
        scopes = ["sell.inventory", "sell.inventory.readonly"]

        result = self.api_call(
            "GET",
            f"/sell/inventory/v1/inventory_item_group/{inventory_item_group_key}",
            scopes=scopes,
        )

        return result

    def delete_inventory_item_group(
        self,
        inventory_item_group_key: str,
    ) -> None:
        """
        Supprime un groupe d'inventory items.

        Args:
            inventory_item_group_key: Clé du groupe

        Examples:
            >>> client.delete_inventory_item_group("GROUP-NIKE-TSHIRT-123")
        """
        scopes = ["sell.inventory"]

        self.api_call(
            "DELETE",
            f"/sell/inventory/v1/inventory_item_group/{inventory_item_group_key}",
            scopes=scopes,
        )


def build_variation_group(
    base_sku: str,
    title: str,
    description: str,
    image_urls: List[str],
    aspects: Dict[str, List[str]],
    variations: List[Dict[str, str]],
    variation_attribute: str = "Size",
) -> Dict[str, Any]:
    """
    Helper function pour construire un groupe de variations.

    Args:
        base_sku: SKU de base (ex: "SKU-123")
        title: Titre du produit
        description: Description
        image_urls: URLs des images
        aspects: Aspects communs (Brand, Color, etc.)
        variations: Liste des variations avec format:
            [
                {"value": "S", "sku": "SKU-123-S"},
                {"value": "M", "sku": "SKU-123-M"},
            ]
        variation_attribute: Attribut de variation (Size, Color, etc.)

    Returns:
        Dict prêt pour create_or_replace_inventory_item_group()

    Examples:
        >>> # Créer groupe pour T-shirt avec tailles
        >>> group_data = build_variation_group(
        ...     base_sku="SKU-TSHIRT-123",
        ...     title="T-shirt Nike Black",
        ...     description="T-shirt Nike en coton",
        ...     image_urls=["https://example.com/image.jpg"],
        ...     aspects={
        ...         "Brand": ["Nike"],
        ...         "Color": ["Black"],
        ...     },
        ...     variations=[
        ...         {"value": "S", "sku": "SKU-TSHIRT-123-S"},
        ...         {"value": "M", "sku": "SKU-TSHIRT-123-M"},
        ...         {"value": "L", "sku": "SKU-TSHIRT-123-L"},
        ...         {"value": "XL", "sku": "SKU-TSHIRT-123-XL"},
        ...     ],
        ...     variation_attribute="Size"
        ... )
        >>>
        >>> client.create_or_replace_inventory_item_group(
        ...     f"GROUP-{base_sku}",
        ...     group_data
        ... )
    """
    # Extraire valeurs et SKUs des variations
    variation_values = [v["value"] for v in variations]
    variant_skus = [v["sku"] for v in variations]

    # Ajouter attribut de variation aux aspects
    full_aspects = {**aspects, variation_attribute: variation_values}

    # Construire groupe
    return {
        "aspects": full_aspects,
        "title": title,
        "description": description,
        "imageUrls": image_urls,
        "variantSKUs": variant_skus,
        "variesBy": {
            "specifications": [
                {
                    "name": variation_attribute,
                    "values": variation_values,
                }
            ]
        },
    }
