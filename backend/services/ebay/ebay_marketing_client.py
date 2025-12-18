"""
eBay Marketing API Client.

Client pour gérer les campagnes publicitaires Promoted Listings.

Promoted Listings permet de booster la visibilité des annonces moyennant
une commission sur vente (CPS - Cost Per Sale) ou coût par clic (CPC).

Endpoints implémentés:
- GET /sell/marketing/v1/ad_campaign - Liste des campagnes
- POST /sell/marketing/v1/ad_campaign - Créer campagne
- GET /sell/marketing/v1/ad_campaign/{campaign_id} - Détails campagne
- PUT /sell/marketing/v1/ad_campaign/{campaign_id} - Modifier campagne
- DELETE /sell/marketing/v1/ad_campaign/{campaign_id} - Supprimer campagne
- POST /sell/marketing/v1/ad_campaign/{campaign_id}/bulk_create_ads_by_inventory_reference - Ajouter produits

Documentation officielle:
https://developer.ebay.com/api-docs/sell/marketing/overview.html

Author: Claude
Date: 2025-12-10
"""

from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from services.ebay.ebay_base_client import EbayBaseClient


class EbayMarketingClient(EbayBaseClient):
    """
    Client eBay Marketing API (Promoted Listings).

    Usage:
        >>> client = EbayMarketingClient(db_session, user_id=1, marketplace_id="EBAY_FR")
        >>>
        >>> # Créer campagne
        >>> campaign = client.create_campaign(
        ...     name="Promo Hiver 2024",
        ...     funding_strategy="COST_PER_SALE",
        ...     marketplace_id="EBAY_FR"
        ... )
        >>>
        >>> # Ajouter produits à la campagne
        >>> result = client.add_products_to_campaign(
        ...     campaign_id=campaign["campaignId"],
        ...     skus=["SKU-123-FR", "SKU-456-FR"],
        ...     bid_percentage=5.0
        ... )
    """

    def get_campaigns(
        self,
        campaign_name: Optional[str] = None,
        campaign_status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Récupère la liste des campagnes publicitaires.

        Args:
            campaign_name: Filtre par nom (optionnel)
            campaign_status: Filtre par statut (RUNNING, PAUSED, ENDED)

        Returns:
            Liste de campagnes

        Examples:
            >>> client = EbayMarketingClient(db, user_id=1)
            >>> campaigns = client.get_campaigns(campaign_status="RUNNING")
            >>> for campaign in campaigns:
            ...     print(f"Campaign: {campaign['campaignName']} - Status: {campaign['campaignStatus']}")
        """
        params = {}
        if campaign_name:
            params["campaign_name"] = campaign_name
        if campaign_status:
            params["campaign_status"] = campaign_status

        scopes = ["sell.marketing", "sell.marketing.readonly"]

        result = self.api_call(
            "GET",
            "/sell/marketing/v1/ad_campaign",
            params=params,
            scopes=scopes,
        )

        return result.get("campaigns", []) if result else []

    def create_campaign(
        self,
        name: str,
        marketplace_id: str,
        funding_strategy: str = "COST_PER_SALE",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Crée une nouvelle campagne Promoted Listings.

        Args:
            name: Nom de la campagne
            marketplace_id: Marketplace (EBAY_FR, EBAY_GB, etc.)
            funding_strategy: Stratégie de coût
                - "COST_PER_SALE" (CPS): Commission sur vente (défaut)
                - "COST_PER_CLICK" (CPC): Coût par clic
            start_date: Date début (ISO 8601, ex: "2024-12-10T00:00:00.000Z")
            end_date: Date fin (optionnel)

        Returns:
            Dict avec détails de la campagne créée:
            {
                "campaignId": "12345678",
                "campaignName": "Promo Hiver 2024",
                "campaignStatus": "RUNNING",
                "fundingStrategy": "COST_PER_SALE",
                "marketplaceId": "EBAY_FR"
            }

        Examples:
            >>> # Campagne CPS (commission 5% sur vente)
            >>> campaign = client.create_campaign(
            ...     name="Promo Hiver 2024",
            ...     marketplace_id="EBAY_FR",
            ...     funding_strategy="COST_PER_SALE"
            ... )
            >>> print(f"Campaign créée: {campaign['campaignId']}")
            >>>
            >>> # Campagne CPC (paiement par clic)
            >>> campaign_cpc = client.create_campaign(
            ...     name="Black Friday",
            ...     marketplace_id="EBAY_GB",
            ...     funding_strategy="COST_PER_CLICK"
            ... )
        """
        from datetime import datetime, timezone

        # Date début par défaut = maintenant
        if not start_date:
            start_date = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

        campaign_data = {
            "campaignName": name,
            "marketplaceId": marketplace_id,
            "fundingStrategy": funding_strategy,
            "startDate": start_date,
        }

        if end_date:
            campaign_data["endDate"] = end_date

        scopes = ["sell.marketing"]

        result = self.api_call(
            "POST",
            "/sell/marketing/v1/ad_campaign",
            json_data=campaign_data,
            scopes=scopes,
        )

        return result

    def get_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """
        Récupère les détails d'une campagne.

        Args:
            campaign_id: ID de la campagne

        Returns:
            Détails complets de la campagne

        Examples:
            >>> campaign = client.get_campaign("12345678")
            >>> print(f"Budget dépensé: {campaign.get('budget', {}).get('spentBudget')}")
        """
        scopes = ["sell.marketing", "sell.marketing.readonly"]

        result = self.api_call(
            "GET",
            f"/sell/marketing/v1/ad_campaign/{campaign_id}",
            scopes=scopes,
        )

        return result

    def update_campaign(
        self,
        campaign_id: str,
        name: Optional[str] = None,
        status: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Met à jour une campagne existante.

        Args:
            campaign_id: ID de la campagne
            name: Nouveau nom (optionnel)
            status: Nouveau statut (RUNNING, PAUSED, ENDED)
            end_date: Nouvelle date fin (optionnel)

        Returns:
            Campagne mise à jour

        Examples:
            >>> # Mettre en pause une campagne
            >>> client.update_campaign(campaign_id="12345678", status="PAUSED")
            >>>
            >>> # Renommer une campagne
            >>> client.update_campaign(campaign_id="12345678", name="Nouvelle promo")
        """
        campaign_data = {}
        if name:
            campaign_data["campaignName"] = name
        if status:
            campaign_data["campaignStatus"] = status
        if end_date:
            campaign_data["endDate"] = end_date

        scopes = ["sell.marketing"]

        result = self.api_call(
            "PUT",
            f"/sell/marketing/v1/ad_campaign/{campaign_id}",
            json_data=campaign_data,
            scopes=scopes,
        )

        return result

    def delete_campaign(self, campaign_id: str) -> None:
        """
        Supprime une campagne.

        Args:
            campaign_id: ID de la campagne

        Examples:
            >>> client.delete_campaign("12345678")
        """
        scopes = ["sell.marketing"]

        self.api_call(
            "DELETE",
            f"/sell/marketing/v1/ad_campaign/{campaign_id}",
            scopes=scopes,
        )

    def add_products_to_campaign(
        self,
        campaign_id: str,
        skus: List[str],
        bid_percentage: float,
    ) -> Dict[str, Any]:
        """
        Ajoute des produits à une campagne Promoted Listings.

        Args:
            campaign_id: ID de la campagne
            skus: Liste de SKUs à promouvoir (ex: ["SKU-123-FR", "SKU-456-FR"])
            bid_percentage: Pourcentage de commission (CPS) ou enchère (CPC)
                - CPS: 2-20% de commission sur vente
                - CPC: Montant par clic (varie selon catégorie)

        Returns:
            Résultat de l'ajout avec statut par SKU

        Examples:
            >>> # Ajouter produits avec commission 5%
            >>> result = client.add_products_to_campaign(
            ...     campaign_id="12345678",
            ...     skus=["SKU-123-FR", "SKU-456-FR", "SKU-789-FR"],
            ...     bid_percentage=5.0
            ... )
            >>> print(f"Ajoutés: {result.get('ads', [])}")
        """
        # Construire requests pour chaque SKU
        inventory_references = []
        for sku in skus:
            inventory_references.append({
                "inventoryReferenceId": sku,
                "inventoryReferenceType": "INVENTORY_ITEM",
            })

        request_data = {
            "requests": [
                {
                    "bidPercentage": str(bid_percentage),
                    "inventoryReferences": inventory_references,
                }
            ]
        }

        scopes = ["sell.marketing"]

        result = self.api_call(
            "POST",
            f"/sell/marketing/v1/ad_campaign/{campaign_id}/bulk_create_ads_by_inventory_reference",
            json_data=request_data,
            scopes=scopes,
        )

        return result

    def remove_products_from_campaign(
        self,
        campaign_id: str,
        ad_ids: List[str],
    ) -> Dict[str, Any]:
        """
        Retire des produits d'une campagne.

        Args:
            campaign_id: ID de la campagne
            ad_ids: Liste d'IDs d'annonces à retirer

        Returns:
            Résultat de la suppression

        Examples:
            >>> result = client.remove_products_from_campaign(
            ...     campaign_id="12345678",
            ...     ad_ids=["ad-001", "ad-002"]
            ... )
        """
        request_data = {
            "adIds": ad_ids
        }

        scopes = ["sell.marketing"]

        result = self.api_call(
            "POST",
            f"/sell/marketing/v1/ad_campaign/{campaign_id}/bulk_delete_ads_by_inventory_reference",
            json_data=request_data,
            scopes=scopes,
        )

        return result

    def get_campaign_ads(
        self,
        campaign_id: str,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Récupère les annonces (ads) d'une campagne.

        Args:
            campaign_id: ID de la campagne
            limit: Nombre max de résultats

        Returns:
            Liste des annonces dans la campagne

        Examples:
            >>> ads = client.get_campaign_ads(campaign_id="12345678")
            >>> for ad in ads:
            ...     print(f"SKU: {ad['inventoryReferenceId']} - Bid: {ad['bidPercentage']}%")
        """
        params = {
            "campaign_id": campaign_id,
            "limit": min(limit, 500),  # eBay max = 500
        }

        scopes = ["sell.marketing", "sell.marketing.readonly"]

        result = self.api_call(
            "GET",
            "/sell/marketing/v1/ad",
            params=params,
            scopes=scopes,
        )

        return result.get("ads", []) if result else []
