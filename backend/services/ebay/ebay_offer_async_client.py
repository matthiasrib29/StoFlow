"""
eBay Offer API Async Client.

Async version of EbayOfferClient for use in the worker.

Author: Claude
Date: 2026-01-20
"""

from typing import Any, Optional

from services.ebay.ebay_async_client import EbayAsyncClient


class EbayOfferAsyncClient(EbayAsyncClient):
    """
    Async client for eBay Offer API.

    Usage:
        async with EbayOfferAsyncClient(user_id=1, marketplace_id="EBAY_FR") as client:
            offers = await client.get_offers(sku="SKU-123")
            await client.publish_offer(offer_id)
    """

    # API Endpoints
    OFFERS_URL = "/sell/inventory/v1/offer"
    BULK_UPDATE_PRICE_QUANTITY_URL = "/sell/inventory/v1/bulk_update_price_quantity"
    BULK_CREATE_OFFER_URL = "/sell/inventory/v1/bulk_create_offer"
    BULK_PUBLISH_OFFER_URL = "/sell/inventory/v1/bulk_publish_offer"

    # ========== OFFER API ==========

    async def get_offers(
        self,
        sku: Optional[str] = None,
        marketplace_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """
        Get list of offers.

        Args:
            sku: Filter by SKU (optional)
            marketplace_id: Filter by marketplace (optional)
            limit: Max offers (max 100)
            offset: Pagination offset

        Returns:
            Dict with 'offers' list and 'total'
        """
        params: dict[str, Any] = {
            "offset": offset,
            "limit": min(limit, 100),
        }

        if marketplace_id:
            params["marketplaceId"] = marketplace_id
        elif self.marketplace_id:
            params["marketplaceId"] = self.marketplace_id

        if sku:
            params["sku"] = sku

        return await self.api_call("GET", self.OFFERS_URL, params=params)

    async def get_offer(self, offer_id: str) -> dict[str, Any]:
        """
        Get offer by ID.

        Args:
            offer_id: Offer ID

        Returns:
            Offer details
        """
        return await self.api_call("GET", f"{self.OFFERS_URL}/{offer_id}")

    async def create_offer(self, offer_data: dict[str, Any]) -> dict[str, Any]:
        """
        Create offer (unpublished).

        Args:
            offer_data: Offer details

        Returns:
            Dict with 'offerId'
        """
        return await self.api_call("POST", self.OFFERS_URL, json_data=offer_data)

    async def update_offer(
        self,
        offer_id: str,
        offer_data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Update existing offer.

        Args:
            offer_id: Offer ID
            offer_data: Updated offer data

        Returns:
            Updated offer details
        """
        return await self.api_call(
            "PUT",
            f"{self.OFFERS_URL}/{offer_id}",
            json_data=offer_data,
        )

    async def publish_offer(self, offer_id: str) -> dict[str, Any]:
        """
        Publish offer to eBay.

        Args:
            offer_id: Offer ID to publish

        Returns:
            Dict with 'listingId'
        """
        return await self.api_call("POST", f"{self.OFFERS_URL}/{offer_id}/publish")

    async def withdraw_offer(self, offer_id: str) -> None:
        """
        Withdraw published offer.

        Args:
            offer_id: Offer ID to withdraw
        """
        await self.api_call("POST", f"{self.OFFERS_URL}/{offer_id}/withdraw")

    async def delete_offer(self, offer_id: str) -> None:
        """
        Delete offer.

        Args:
            offer_id: Offer ID to delete
        """
        await self.api_call("DELETE", f"{self.OFFERS_URL}/{offer_id}")

    # ========== BULK OPERATIONS API ==========

    async def bulk_update_price_quantity(
        self,
        updates: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Bulk update price/quantity for multiple offers.

        Args:
            updates: List of updates (max 25)

        Returns:
            Dict with 'responses' list
        """
        if len(updates) > 25:
            raise ValueError("Bulk operations limited to 25 offers")

        return await self.api_call(
            "POST",
            self.BULK_UPDATE_PRICE_QUANTITY_URL,
            json_data={"requests": updates},
        )

    async def bulk_create_offer(
        self,
        offers: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Bulk create offers.

        Args:
            offers: List of offers (max 25)

        Returns:
            Dict with 'responses' list
        """
        if len(offers) > 25:
            raise ValueError("Bulk operations limited to 25 offers")

        return await self.api_call(
            "POST",
            self.BULK_CREATE_OFFER_URL,
            json_data={"requests": offers},
        )

    async def bulk_publish_offer(
        self,
        offer_ids: list[str],
    ) -> dict[str, Any]:
        """
        Bulk publish offers.

        Args:
            offer_ids: List of offer IDs (max 25)

        Returns:
            Dict with 'responses' list
        """
        if len(offer_ids) > 25:
            raise ValueError("Bulk operations limited to 25 offers")

        requests_data = [{"offerId": oid} for oid in offer_ids]
        return await self.api_call(
            "POST",
            self.BULK_PUBLISH_OFFER_URL,
            json_data={"requests": requests_data},
        )
