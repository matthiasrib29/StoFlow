"""
eBay Offer API Client.

Gère la création et publication des offres (listings) sur eBay.

API Reference:
- https://developer.ebay.com/api-docs/sell/inventory/resources/offer/methods

Responsabilités:
- Offers: create, read, update, delete
- Publish/Withdraw: publier ou retirer des listings
- Bulk operations: batch create/publish jusqu'à 25 offers

Workflow typique:
1. Créer inventory item (via EbayInventoryClient)
2. Créer offer (ce client) → récupérer offer_id
3. Publier offer (ce client) → récupérer listing_id

Author: Claude (porté depuis pythonApiWOO)
Date: 2025-12-10
"""

from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from services.ebay.ebay_base_client import EbayBaseClient


class EbayOfferClient(EbayBaseClient):
    """
    Client pour eBay Offer API.

    Usage:
        >>> client = EbayOfferClient(db, user_id=1, marketplace_id="EBAY_FR")
        >>> 
        >>> # Créer une offer
        >>> offer_data = {
        ...     "sku": "SKU-123-FR",
        ...     "marketplaceId": "EBAY_FR",
        ...     "format": "FIXED_PRICE",
        ...     "pricingSummary": {"price": {"value": "49.90", "currency": "EUR"}},
        ...     "listingPolicies": {
        ...         "paymentPolicyId": "123456",
        ...         "fulfillmentPolicyId": "789012",
        ...         "returnPolicyId": "345678"
        ...     },
        ...     "categoryId": "11450",
        ...     "merchantLocationKey": "warehouse_paris_fr"
        ... }
        >>> result = client.create_offer(offer_data)
        >>> offer_id = result['offerId']
        >>> 
        >>> # Publier l'offer
        >>> listing = client.publish_offer(offer_id)
        >>> listing_id = listing['listingId']
    """

    # API Endpoints
    OFFERS_URL = "/sell/inventory/v1/offer"
    BULK_UPDATE_PRICE_QUANTITY_URL = "/sell/inventory/v1/bulk_update_price_quantity"
    BULK_CREATE_OFFER_URL = "/sell/inventory/v1/bulk_create_offer"
    BULK_PUBLISH_OFFER_URL = "/sell/inventory/v1/bulk_publish_offer"

    # ========== OFFER API ==========

    def get_offers(
        self,
        sku: Optional[str] = None,
        marketplace_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Récupère la liste des offers du user.

        Args:
            sku: Filtrer par SKU spécifique (optionnel)
            marketplace_id: Filtrer par marketplace (ex: "EBAY_FR")
                           Si None, utilise self.marketplace_id ou toutes les marketplaces
            limit: Nombre max d'offers (max 100)
            offset: Offset pour pagination

        Returns:
            Dict avec 'offers' (liste) et 'total' (int)

        Examples:
            >>> # Toutes les offers
            >>> result = client.get_offers()
            >>> 
            >>> # Offers pour un SKU spécifique
            >>> result = client.get_offers(sku="SKU-123-FR")
            >>> 
            >>> # Offers pour EBAY_FR uniquement
            >>> result = client.get_offers(marketplace_id="EBAY_FR")
        """
        params: Dict[str, Any] = {
            "offset": offset,
            "limit": min(limit, 100),
        }

        # Marketplace filter
        if marketplace_id:
            params["marketplaceId"] = marketplace_id
        elif self.marketplace_id:
            params["marketplaceId"] = self.marketplace_id

        # SKU filter
        if sku:
            params["sku"] = sku

        return self.api_call(
            "GET", self.OFFERS_URL, params=params, scopes=["sell.inventory"]
        )

    def get_offer(self, offer_id: str) -> Dict[str, Any]:
        """
        Récupère une offer par ID.

        Args:
            offer_id: ID de l'offer eBay

        Returns:
            Dict avec les détails de l'offer

        Examples:
            >>> offer = client.get_offer("123456789")
            >>> print(f"SKU: {offer['sku']}, Price: {offer['pricingSummary']['price']['value']}")
        """
        return self.api_call(
            "GET", f"{self.OFFERS_URL}/{offer_id}", scopes=["sell.inventory"]
        )

    def create_offer(self, offer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée une offer (non publiée).

        Args:
            offer_data: Données de l'offer (sku, marketplaceId, format, pricingSummary, etc.)

        Returns:
            Dict avec 'offerId'

        Raises:
            RuntimeError: Si la création échoue

        Examples:
            >>> offer_data = {
            ...     "sku": "SKU-123-FR",
            ...     "marketplaceId": "EBAY_FR",
            ...     "format": "FIXED_PRICE",
            ...     "pricingSummary": {
            ...         "price": {"value": "49.90", "currency": "EUR"}
            ...     },
            ...     "listingPolicies": {
            ...         "paymentPolicyId": "123456",
            ...         "fulfillmentPolicyId": "789012",
            ...         "returnPolicyId": "345678"
            ...     },
            ...     "categoryId": "11450",
            ...     "merchantLocationKey": "warehouse_paris_fr",
            ...     "availableQuantity": 1
            ... }
            >>> result = client.create_offer(offer_data)
            >>> offer_id = result['offerId']
        """
        return self.api_call(
            "POST", self.OFFERS_URL, json_data=offer_data, scopes=["sell.inventory"]
        )

    def update_offer(self, offer_id: str, offer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Met à jour une offer existante (published ou unpublished).

        Args:
            offer_id: ID de l'offer
            offer_data: Données à mettre à jour (même format que create_offer)

        Returns:
            Dict avec les détails de l'offer mise à jour

        Examples:
            >>> # Mettre à jour le prix
            >>> offer_data = {
            ...     "sku": "SKU-123-FR",
            ...     "marketplaceId": "EBAY_FR",
            ...     "format": "FIXED_PRICE",
            ...     "pricingSummary": {
            ...         "price": {"value": "39.90", "currency": "EUR"}
            ...     },
            ...     # ... autres champs requis
            ... }
            >>> client.update_offer("123456789", offer_data)
        """
        return self.api_call(
            "PUT",
            f"{self.OFFERS_URL}/{offer_id}",
            json_data=offer_data,
            scopes=["sell.inventory"],
        )

    def publish_offer(self, offer_id: str) -> Dict[str, Any]:
        """
        Publie une offer sur eBay (crée le listing public).

        Args:
            offer_id: ID de l'offer à publier

        Returns:
            Dict avec 'listingId' (ID du listing publié)

        Raises:
            RuntimeError: Si la publication échoue

        Examples:
            >>> result = client.publish_offer("123456789")
            >>> listing_id = result['listingId']
            >>> print(f"Listing publié: {listing_id}")
        """
        return self.api_call(
            "POST",
            f"{self.OFFERS_URL}/{offer_id}/publish",
            scopes=["sell.inventory"],
        )

    def withdraw_offer(self, offer_id: str) -> None:
        """
        Retire une offer publiée (dé-liste le produit).

        Le produit ne sera plus visible sur eBay mais l'offer reste en base.
        Pour supprimer complètement, utiliser delete_offer() après withdraw.

        Args:
            offer_id: ID de l'offer à retirer

        Returns:
            None (status 204 = success)

        Examples:
            >>> client.withdraw_offer("123456789")
        """
        self.api_call(
            "POST",
            f"{self.OFFERS_URL}/{offer_id}/withdraw",
            scopes=["sell.inventory"],
        )

    def delete_offer(self, offer_id: str) -> None:
        """
        Supprime une offer.

        ATTENTION: L'offer doit être withdrawée d'abord si publiée.

        Args:
            offer_id: ID de l'offer à supprimer

        Returns:
            None (status 204 = success)

        Examples:
            >>> # Supprimer une offer publiée
            >>> client.withdraw_offer("123456789")
            >>> client.delete_offer("123456789")
        """
        self.api_call(
            "DELETE", f"{self.OFFERS_URL}/{offer_id}", scopes=["sell.inventory"]
        )

    # ========== BULK OPERATIONS API ==========

    def bulk_update_price_quantity(
        self, updates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Met à jour prix et/ou quantité en masse pour plusieurs offers.

        Limite: 25 offers maximum par batch.

        Args:
            updates: Liste de dicts avec 'offerId' et 'pricingSummary' et/ou 'availableQuantity'

        Returns:
            Dict avec 'responses' (liste des résultats par offer)

        Examples:
            >>> updates = [
            ...     {
            ...         "offerId": "123456789",
            ...         "pricingSummary": {"price": {"value": "39.90", "currency": "EUR"}}
            ...     },
            ...     {
            ...         "offerId": "987654321",
            ...         "availableQuantity": 5
            ...     }
            ... ]
            >>> result = client.bulk_update_price_quantity(updates)
            >>> for resp in result['responses']:
            ...     print(f"Offer {resp['offerId']}: {resp['statusCode']}")
        """
        if len(updates) > 25:
            raise ValueError("Bulk operations limitées à 25 offers maximum")

        return self.api_call(
            "POST",
            self.BULK_UPDATE_PRICE_QUANTITY_URL,
            json_data={"requests": updates},
            scopes=["sell.inventory"],
        )

    def bulk_create_offer(self, offers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Crée plusieurs offers en une seule requête.

        Limite: 25 offers maximum par batch.

        Args:
            offers: Liste de dicts (même format que create_offer)

        Returns:
            Dict avec 'responses' (liste des résultats avec offerId)

        Examples:
            >>> offers = [
            ...     {
            ...         "sku": "SKU-123-FR",
            ...         "marketplaceId": "EBAY_FR",
            ...         "format": "FIXED_PRICE",
            ...         "pricingSummary": {"price": {"value": "49.90", "currency": "EUR"}},
            ...         # ... autres champs
            ...     },
            ...     {
            ...         "sku": "SKU-124-FR",
            ...         "marketplaceId": "EBAY_FR",
            ...         # ...
            ...     }
            ... ]
            >>> result = client.bulk_create_offer(offers)
        """
        if len(offers) > 25:
            raise ValueError("Bulk operations limitées à 25 offers maximum")

        return self.api_call(
            "POST",
            self.BULK_CREATE_OFFER_URL,
            json_data={"requests": offers},
            scopes=["sell.inventory"],
        )

    def bulk_publish_offer(self, offer_ids: List[str]) -> Dict[str, Any]:
        """
        Publie plusieurs offers en une seule requête.

        Limite: 25 offers maximum par batch.

        Args:
            offer_ids: Liste d'IDs d'offers à publier

        Returns:
            Dict avec 'responses' (liste des résultats avec listingId)

        Examples:
            >>> offer_ids = ["123456789", "987654321", "555666777"]
            >>> result = client.bulk_publish_offer(offer_ids)
            >>> for resp in result['responses']:
            ...     if resp['statusCode'] == 200:
            ...         print(f"Publié: {resp['listingId']}")
        """
        if len(offer_ids) > 25:
            raise ValueError("Bulk operations limitées à 25 offers maximum")

        requests_data = [{"offerId": oid} for oid in offer_ids]
        return self.api_call(
            "POST",
            self.BULK_PUBLISH_OFFER_URL,
            json_data={"requests": requests_data},
            scopes=["sell.inventory"],
        )
