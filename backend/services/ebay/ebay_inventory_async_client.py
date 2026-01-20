"""
eBay Inventory API Async Client.

Async version of EbayInventoryClient for use in the worker.

Author: Claude
Date: 2026-01-20
"""

from typing import Any, Optional

from services.ebay.ebay_async_client import EbayAsyncClient


class EbayInventoryAsyncClient(EbayAsyncClient):
    """
    Async client for eBay Inventory API.

    Usage:
        async with EbayInventoryAsyncClient(user_id=1, marketplace_id="EBAY_FR") as client:
            items = await client.get_inventory_items(limit=100)
            item = await client.get_inventory_item("SKU-123")
    """

    # API Endpoints
    INVENTORY_ITEMS_URL = "/sell/inventory/v1/inventory_item"
    INVENTORY_LOCATIONS_URL = "/sell/inventory/v1/location"
    BULK_CREATE_URL = "/sell/inventory/v1/bulk_create_or_replace_inventory_item"

    # ========== INVENTORY ITEM API ==========

    async def get_inventory_items(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """
        Get list of inventory items.

        Args:
            limit: Max items to return (max 100)
            offset: Pagination offset

        Returns:
            Dict with 'inventoryItems' (list) and 'total' (int)
        """
        params = {"offset": offset, "limit": min(limit, 100)}
        return await self.api_call("GET", self.INVENTORY_ITEMS_URL, params=params)

    async def get_inventory_item(self, sku: str) -> dict[str, Any]:
        """
        Get inventory item by SKU.

        Args:
            sku: Item SKU

        Returns:
            Inventory item details
        """
        return await self.api_call("GET", f"{self.INVENTORY_ITEMS_URL}/{sku}")

    async def create_or_replace_inventory_item(
        self,
        sku: str,
        item_data: dict[str, Any],
        content_language: Optional[str] = None,
    ) -> None:
        """
        Create or replace inventory item (PUT = upsert).

        Args:
            sku: Item SKU
            item_data: Inventory item data
            content_language: Content-Language header override
        """
        await self.api_call(
            "PUT",
            f"{self.INVENTORY_ITEMS_URL}/{sku}",
            json_data=item_data,
            content_language=content_language,
        )

    async def delete_inventory_item(self, sku: str) -> None:
        """
        Delete inventory item.

        Args:
            sku: SKU to delete
        """
        await self.api_call("DELETE", f"{self.INVENTORY_ITEMS_URL}/{sku}")

    # ========== BULK OPERATIONS API ==========

    async def bulk_create_or_replace_inventory_items(
        self,
        items: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Bulk create/replace inventory items.

        Args:
            items: List of items (max 25)

        Returns:
            Dict with 'responses' list
        """
        if len(items) > 25:
            raise ValueError("Bulk operations limited to 25 items")

        return await self.api_call(
            "POST",
            self.BULK_CREATE_URL,
            json_data={"requests": items},
        )

    # ========== INVENTORY LOCATION API ==========

    async def create_inventory_location(
        self,
        merchant_location_key: str,
        location_data: dict[str, Any],
    ) -> None:
        """
        Create inventory location.

        Args:
            merchant_location_key: Location identifier
            location_data: Location details
        """
        await self.api_call(
            "POST",
            f"{self.INVENTORY_LOCATIONS_URL}/{merchant_location_key}",
            json_data=location_data,
        )

    async def get_inventory_location(self, merchant_location_key: str) -> dict[str, Any]:
        """
        Get inventory location by key.

        Args:
            merchant_location_key: Location identifier

        Returns:
            Location details
        """
        return await self.api_call(
            "GET",
            f"{self.INVENTORY_LOCATIONS_URL}/{merchant_location_key}",
        )

    async def get_inventory_locations(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """
        Get list of inventory locations.

        Args:
            limit: Max locations (max 100)
            offset: Pagination offset

        Returns:
            Dict with 'locations' list and 'total'
        """
        params = {"offset": offset, "limit": min(limit, 100)}
        return await self.api_call(
            "GET",
            self.INVENTORY_LOCATIONS_URL,
            params=params,
        )
