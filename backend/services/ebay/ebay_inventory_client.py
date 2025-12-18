"""
eBay Inventory API Client.

Gère les opérations sur les inventory items et inventory locations.

API Reference:
- https://developer.ebay.com/api-docs/sell/inventory/resources/methods

Responsabilités:
- Inventory Items: create, read, update, delete
- Inventory Locations: create, read, list
- Bulk operations: batch create/update jusqu'à 25 items

Author: Claude (porté depuis pythonApiWOO)
Date: 2025-12-10
"""

from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from services.ebay.ebay_base_client import EbayBaseClient


class EbayInventoryClient(EbayBaseClient):
    """
    Client pour eBay Inventory API.

    Usage:
        >>> client = EbayInventoryClient(db, user_id=1, marketplace_id="EBAY_FR")
        >>> # Créer un inventory item
        >>> item_data = {
        ...     "product": {"title": "Nike Air Max", ...},
        ...     "condition": "NEW",
        ...     "availability": {"shipToLocationAvailability": {"quantity": 1}}
        ... }
        >>> client.create_or_replace_inventory_item("SKU-123-FR", item_data)
        
        >>> # Récupérer un inventory item
        >>> item = client.get_inventory_item("SKU-123-FR")
    """

    # API Endpoints
    INVENTORY_ITEMS_URL = "/sell/inventory/v1/inventory_item"
    INVENTORY_LOCATIONS_URL = "/sell/inventory/v1/location"
    BULK_CREATE_URL = "/sell/inventory/v1/bulk_create_or_replace_inventory_item"

    # ========== INVENTORY ITEM API ==========

    def get_inventory_items(
        self, limit: int = 100, offset: int = 0
    ) -> Dict[str, Any]:
        """
        Récupère la liste des inventory items du user.

        Args:
            limit: Nombre max d'items à retourner (max 100)
            offset: Offset pour pagination

        Returns:
            Dict avec 'inventoryItems' (liste) et 'total' (int)

        Examples:
            >>> result = client.get_inventory_items(limit=50)
            >>> print(f"Total: {result['total']}, Items: {len(result['inventoryItems'])}")
        """
        params = {"offset": offset, "limit": min(limit, 100)}
        return self.api_call(
            "GET", self.INVENTORY_ITEMS_URL, params=params, scopes=["sell.inventory"]
        )

    def get_inventory_item(self, sku: str) -> Dict[str, Any]:
        """
        Récupère un inventory item par SKU.

        Args:
            sku: SKU de l'item (ex: "SKU-123-FR")

        Returns:
            Dict avec les détails de l'inventory item

        Raises:
            RuntimeError: Si l'item n'existe pas (404)

        Examples:
            >>> item = client.get_inventory_item("SKU-123-FR")
            >>> print(item['product']['title'])
        """
        return self.api_call(
            "GET", f"{self.INVENTORY_ITEMS_URL}/{sku}", scopes=["sell.inventory"]
        )

    def create_or_replace_inventory_item(
        self,
        sku: str,
        item_data: Dict[str, Any],
        content_language: Optional[str] = None,
    ) -> None:
        """
        Crée ou remplace un inventory item (PUT = upsert).

        Args:
            sku: SKU de l'item (ex: "SKU-123-FR")
            item_data: Données de l'inventory item (product, condition, availability, etc.)
            content_language: Content-Language header (ex: "fr-FR")
                             Si None, auto-détecté depuis marketplace_id

        Returns:
            None (status 204 = success)

        Raises:
            RuntimeError: Si la création échoue

        Examples:
            >>> item_data = {
            ...     "product": {
            ...         "title": "Nike Air Max 90",
            ...         "description": "Sneakers iconiques",
            ...         "imageUrls": ["https://example.com/image1.jpg"],
            ...         "aspects": {
            ...             "Brand": ["Nike"],
            ...             "US Shoe Size": ["10"],
            ...             "Color": ["White"]
            ...         }
            ...     },
            ...     "condition": "NEW",
            ...     "availability": {
            ...         "shipToLocationAvailability": {
            ...             "quantity": 1
            ...         }
            ...     }
            ... }
            >>> client.create_or_replace_inventory_item("SKU-123-FR", item_data)
        """
        self.api_call(
            "PUT",
            f"{self.INVENTORY_ITEMS_URL}/{sku}",
            json_data=item_data,
            scopes=["sell.inventory"],
            content_language=content_language,
        )

    def create_or_update_inventory_item(
        self,
        sku: str,
        item_data: Dict[str, Any],
        content_language: Optional[str] = None,
    ) -> None:
        """
        Alias de create_or_replace_inventory_item pour compatibilité.

        Args:
            sku: SKU de l'item
            item_data: Données de l'inventory item
            content_language: Content-Language header (optionnel)

        Returns:
            None
        """
        self.create_or_replace_inventory_item(sku, item_data, content_language)

    def delete_inventory_item(self, sku: str) -> None:
        """
        Supprime un inventory item.

        ATTENTION: Cette action est irréversible.
        Si l'item a des offers publiées, elles doivent être withdrawées d'abord.

        Args:
            sku: SKU de l'item à supprimer

        Returns:
            None (status 204 = success)

        Raises:
            RuntimeError: Si la suppression échoue

        Examples:
            >>> client.delete_inventory_item("SKU-123-FR")
        """
        self.api_call(
            "DELETE", f"{self.INVENTORY_ITEMS_URL}/{sku}", scopes=["sell.inventory"]
        )

    # ========== BULK OPERATIONS API ==========

    def bulk_create_or_replace_inventory_items(
        self, items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Crée ou remplace plusieurs inventory items en une seule requête.

        Limite: 25 items maximum par batch.

        Args:
            items: Liste de dicts avec 'sku' et les données de l'item

        Returns:
            Dict avec 'responses' (liste des résultats par SKU)

        Examples:
            >>> items = [
            ...     {
            ...         "sku": "SKU-123-FR",
            ...         "product": {"title": "Product 1", ...},
            ...         "condition": "NEW",
            ...         "availability": {"shipToLocationAvailability": {"quantity": 1}}
            ...     },
            ...     {
            ...         "sku": "SKU-124-FR",
            ...         "product": {"title": "Product 2", ...},
            ...         "condition": "USED_EXCELLENT",
            ...         "availability": {"shipToLocationAvailability": {"quantity": 1}}
            ...     }
            ... ]
            >>> result = client.bulk_create_or_replace_inventory_items(items)
            >>> for resp in result['responses']:
            ...     print(f"SKU {resp['sku']}: {resp['statusCode']}")
        """
        if len(items) > 25:
            raise ValueError("Bulk operations limitées à 25 items maximum")

        return self.api_call(
            "POST",
            self.BULK_CREATE_URL,
            json_data={"requests": items},
            scopes=["sell.inventory"],
        )

    # ========== INVENTORY LOCATION API ==========

    def create_inventory_location(
        self, merchant_location_key: str, location_data: Dict[str, Any]
    ) -> None:
        """
        Crée un inventory location (warehouse/store).

        Required AVANT de pouvoir publier des offers.
        Chaque user doit avoir au moins 1 location configurée.

        Args:
            merchant_location_key: Identifiant unique (ex: "warehouse_paris_fr")
            location_data: Données de la location (name, merchantLocationTypes, location, etc.)

        Returns:
            None (status 204 = success)

        Examples:
            >>> location_data = {
            ...     "name": "Paris Warehouse",
            ...     "merchantLocationTypes": ["WAREHOUSE"],
            ...     "location": {
            ...         "address": {
            ...             "addressLine1": "123 Rue de Rivoli",
            ...             "city": "Paris",
            ...             "stateOrProvince": "Île-de-France",
            ...             "postalCode": "75001",
            ...             "country": "FR"
            ...         }
            ...     },
            ...     "locationInstructions": "Warehouse principal",
            ...     "locationWebUrl": "https://example.com"
            ... }
            >>> client.create_inventory_location("warehouse_paris_fr", location_data)
        """
        self.api_call(
            "POST",
            f"{self.INVENTORY_LOCATIONS_URL}/{merchant_location_key}",
            json_data=location_data,
            scopes=["sell.inventory"],
        )

    def get_inventory_location(self, merchant_location_key: str) -> Dict[str, Any]:
        """
        Récupère un inventory location par sa clé.

        Args:
            merchant_location_key: Identifiant de la location

        Returns:
            Dict avec les détails de la location

        Examples:
            >>> location = client.get_inventory_location("warehouse_paris_fr")
            >>> print(location['name'])
        """
        return self.api_call(
            "GET",
            f"{self.INVENTORY_LOCATIONS_URL}/{merchant_location_key}",
            scopes=["sell.inventory"],
        )

    def get_inventory_locations(
        self, limit: int = 100, offset: int = 0
    ) -> Dict[str, Any]:
        """
        Récupère la liste des inventory locations du user.

        Args:
            limit: Nombre max de locations (max 100)
            offset: Offset pour pagination

        Returns:
            Dict avec 'locations' (liste) et 'total' (int)

        Examples:
            >>> result = client.get_inventory_locations()
            >>> for loc in result['locations']:
            ...     print(f"{loc['merchantLocationKey']}: {loc['name']}")
        """
        params = {"offset": offset, "limit": min(limit, 100)}
        return self.api_call(
            "GET",
            self.INVENTORY_LOCATIONS_URL,
            params=params,
            scopes=["sell.inventory"],
        )
