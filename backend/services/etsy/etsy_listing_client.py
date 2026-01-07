"""
Etsy Listing Client - Listings Management API.

Client pour gérer les listings (produits) sur Etsy:
- Create/Update/Delete listings
- Manage inventory & variations
- Upload images & files
- Get listings (active, draft, inactive)

Scopes requis: listings_r, listings_w, listings_d

Documentation officielle:
https://developer.etsy.com/documentation/tutorials/listings/

Author: Claude
Date: 2025-12-10
"""

from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from services.etsy.etsy_base_client import EtsyBaseClient


class EtsyListingClient(EtsyBaseClient):
    """
    Client Etsy Listings API.

    Usage:
        >>> client = EtsyListingClient(db_session, user_id=1)
        >>>
        >>> # Get active listings
        >>> listings = client.get_shop_listings_active(limit=25)
        >>>
        >>> # Create draft listing
        >>> listing = client.create_draft_listing({
        ...     "quantity": 1,
        ...     "title": "Handmade Necklace",
        ...     "description": "Beautiful vintage necklace",
        ...     "price": 29.99,
        ...     "who_made": "i_did",
        ...     "when_made": "2020_2023",
        ...     "taxonomy_id": 1234,
        ... })
    """

    def get_shop_listings_active(
        self,
        limit: int = 25,
        offset: int = 0,
        sort_on: str = "created",
        sort_order: str = "desc",
    ) -> Dict[str, Any]:
        """
        Récupère les listings actifs du shop.

        Args:
            limit: Nombre de résultats (max 100)
            offset: Pagination offset
            sort_on: Champ de tri (created, updated, price)
            sort_order: Ordre (asc, desc)

        Returns:
            Dict avec "count", "results" (list of listings)

        Examples:
            >>> listings = client.get_shop_listings_active(limit=50)
            >>> print(f"Total active: {listings['count']}")
            >>> for listing in listings['results']:
            ...     print(f"- {listing['title']}: ${listing['price']['amount']/100}")
        """
        return self.api_call(
            "GET",
            f"/application/shops/{self.shop_id}/listings/active",
            params={
                "limit": limit,
                "offset": offset,
                "sort_on": sort_on,
                "sort_order": sort_order,
            },
        )

    def get_shop_listings_draft(
        self,
        limit: int = 25,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Récupère les listings en draft (non publiés).

        Args:
            limit: Nombre de résultats
            offset: Pagination offset

        Returns:
            Dict avec listings en draft
        """
        return self.api_call(
            "GET",
            f"/application/shops/{self.shop_id}/listings/draft",
            params={"limit": limit, "offset": offset},
        )

    def get_shop_listings_inactive(
        self,
        limit: int = 25,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Récupère les listings inactifs.

        Args:
            limit: Nombre de résultats
            offset: Pagination offset

        Returns:
            Dict avec listings inactifs
        """
        return self.api_call(
            "GET",
            f"/application/shops/{self.shop_id}/listings/inactive",
            params={"limit": limit, "offset": offset},
        )

    def get_listing(self, listing_id: int) -> Dict[str, Any]:
        """
        Récupère un listing spécifique.

        Args:
            listing_id: ID du listing Etsy

        Returns:
            Détails du listing

        Examples:
            >>> listing = client.get_listing(123456789)
            >>> print(listing['title'])
            >>> print(listing['state'])  # active, draft, inactive
        """
        return self.api_call(
            "GET",
            f"/application/listings/{listing_id}",
        )

    def create_draft_listing(
        self,
        listing_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Crée un nouveau listing en draft.

        Args:
            listing_data: Données du listing avec structure:
                {
                    "quantity": int (required),
                    "title": str (required, max 140 chars),
                    "description": str (required),
                    "price": float (required, USD),
                    "who_made": str (required: i_did, someone_else, collective),
                    "when_made": str (required: made_to_order, 2020_2023, etc.),
                    "taxonomy_id": int (required),
                    "shipping_profile_id": int (optional),
                    "return_policy_id": int (optional),
                    "materials": List[str] (optional, max 13 items),
                    "shop_section_id": int (optional),
                    "processing_min": int (optional, days),
                    "processing_max": int (optional, days),
                    "tags": List[str] (optional, max 13, max 20 chars each),
                    "styles": List[str] (optional, max 2),
                    "item_weight": float (optional, kg),
                    "item_length": float (optional, cm),
                    "item_width": float (optional, cm),
                    "item_height": float (optional, cm),
                    "item_weight_unit": str (optional: oz, lb, g, kg),
                    "item_dimensions_unit": str (optional: in, ft, mm, cm, m),
                    "is_personalizable": bool (optional),
                    "personalization_is_required": bool (optional),
                    "personalization_char_count_max": int (optional),
                    "personalization_instructions": str (optional),
                    "production_partner_ids": List[int] (optional),
                    "image_ids": List[int] (optional),
                    "is_supply": bool (optional, default false),
                    "is_customizable": bool (optional),
                    "should_auto_renew": bool (optional, default false),
                    "is_taxable": bool (optional, default false),
                    "type": str (optional: physical or download),
                }

        Returns:
            Listing créé

        Examples:
            >>> listing = client.create_draft_listing({
            ...     "quantity": 1,
            ...     "title": "Vintage Handmade Necklace",
            ...     "description": "Beautiful vintage necklace handcrafted...",
            ...     "price": 49.99,
            ...     "who_made": "i_did",
            ...     "when_made": "2020_2023",
            ...     "taxonomy_id": 1234,
            ...     "tags": ["vintage", "handmade", "necklace"],
            ...     "materials": ["silver", "beads"],
            ... })
            >>> print(f"Draft created: {listing['listing_id']}")
        """
        return self.api_call(
            "POST",
            f"/application/shops/{self.shop_id}/listings",
            json_data=listing_data,
        )

    def update_listing(
        self,
        listing_id: int,
        listing_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Met à jour un listing existant.

        Args:
            listing_id: ID du listing
            listing_data: Données à mettre à jour (mêmes champs que create_draft_listing)

        Returns:
            Listing mis à jour

        Examples:
            >>> # Update price
            >>> listing = client.update_listing(123456789, {
            ...     "price": 39.99,
            ...     "quantity": 5,
            ... })
            >>>
            >>> # Move to shop section
            >>> listing = client.update_listing(123456789, {
            ...     "shop_section_id": 12345,
            ... })
        """
        return self.api_call(
            "PATCH",
            f"/application/shops/{self.shop_id}/listings/{listing_id}",
            json_data=listing_data,
        )

    def delete_listing(self, listing_id: int) -> None:
        """
        Supprime un listing définitivement.

        Scope requis: listings_d

        Args:
            listing_id: ID du listing à supprimer

        Examples:
            >>> client.delete_listing(123456789)
        """
        self.api_call(
            "DELETE",
            f"/application/shops/{self.shop_id}/listings/{listing_id}",
        )

    def get_listing_inventory(self, listing_id: int) -> Dict[str, Any]:
        """
        Récupère l'inventaire d'un listing (stock, prix, variations).

        Args:
            listing_id: ID du listing

        Returns:
            Inventory data avec "products" array

        Examples:
            >>> inventory = client.get_listing_inventory(123456789)
            >>> for product in inventory['products']:
            ...     print(f"SKU: {product['sku']}, Stock: {product['offerings'][0]['quantity']}")
        """
        return self.api_call(
            "GET",
            f"/application/listings/{listing_id}/inventory",
        )

    def update_listing_inventory(
        self,
        listing_id: int,
        inventory_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Met à jour l'inventaire d'un listing (stock, prix, variations).

        Args:
            listing_id: ID du listing
            inventory_data: Données inventaire avec structure:
                {
                    "products": [
                        {
                            "sku": str (optional),
                            "property_values": [...] (for variations),
                            "offerings": [
                                {
                                    "price": float,
                                    "quantity": int,
                                    "is_enabled": bool,
                                }
                            ]
                        }
                    ],
                    "price_on_property": List[int] (optional),
                    "quantity_on_property": List[int] (optional),
                    "sku_on_property": List[int] (optional),
                }

        Returns:
            Inventory mis à jour

        Examples:
            >>> # Update stock
            >>> inventory = client.update_listing_inventory(123456789, {
            ...     "products": [{
            ...         "sku": "PROD-001",
            ...         "offerings": [{
            ...             "price": 29.99,
            ...             "quantity": 10,
            ...             "is_enabled": True,
            ...         }]
            ...     }]
            ... })
        """
        return self.api_call(
            "PUT",
            f"/application/listings/{listing_id}/inventory",
            json_data=inventory_data,
        )

    def upload_listing_image(
        self,
        listing_id: int,
        image_url: str,
        rank: int = 1,
        overwrite: bool = False,
        alt_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Upload une image pour un listing Etsy via multipart/form-data.

        Note: Au moins 1 image requise pour publier un listing.
        Max 10 images par listing (rank 1-10).

        Args:
            listing_id: ID du listing Etsy
            image_url: URL de l'image (depuis Cloudflare R2)
            rank: Position de l'image (1-10)
            overwrite: Si True, remplace l'image au même rank
            alt_text: Texte alternatif pour accessibilité

        Returns:
            Image data with listing_image_id, url fields

        Raises:
            requests.exceptions.HTTPError: Si erreur upload

        Examples:
            >>> image = client.upload_listing_image(
            ...     listing_id=123456789,
            ...     image_url="https://r2.example.com/image.jpg",
            ...     rank=1
            ... )
            >>> print(image['listing_image_id'])

        Docs:
            https://developer.etsy.com/documentation/reference/#operation/uploadListingImage
        """
        import httpx

        # 1. Download image from R2 URL
        logger.info(f"Downloading image from {image_url}...")
        try:
            img_response = httpx.get(image_url, timeout=30.0)
            img_response.raise_for_status()
            image_bytes = img_response.content
            logger.info(f"Image downloaded: {len(image_bytes)} bytes")
        except Exception as e:
            logger.error(f"Failed to download image from {image_url}: {e}")
            raise

        # 2. Upload to Etsy (multipart/form-data)
        # Note: Ne pas utiliser self.api_call() car multipart nécessite requests direct
        import requests

        files = {"image": ("image.jpg", image_bytes, "image/jpeg")}

        data = {
            "rank": rank,
            "overwrite": str(overwrite).lower(),  # Etsy requires lowercase boolean
        }

        if alt_text:
            data["alt_text"] = alt_text

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "x-api-key": self.api_key,
        }

        url = f"{self.BASE_URL}/application/shops/{self.shop_id}/listings/{listing_id}/images"

        logger.info(f"Uploading image to Etsy listing {listing_id} (rank {rank})...")

        try:
            upload_response = requests.post(
                url, files=files, data=data, headers=headers, timeout=60.0
            )

            upload_response.raise_for_status()
            result = upload_response.json()

            logger.info(
                f"✅ Image uploaded successfully: image_id={result.get('listing_image_id')}"
            )

            return result

        except requests.exceptions.HTTPError as e:
            logger.error(f"Etsy image upload failed: {e.response.text}")
            raise

    def get_listing_images(self, listing_id: int) -> List[Dict[str, Any]]:
        """
        Récupère les images d'un listing.

        Args:
            listing_id: ID du listing

        Returns:
            Liste des images

        Examples:
            >>> images = client.get_listing_images(123456789)
            >>> for img in images:
            ...     print(f"Image {img['rank']}: {img['url_570xN']}")
        """
        result = self.api_call(
            "GET",
            f"/application/shops/{self.shop_id}/listings/{listing_id}/images",
        )
        return result.get("results", [])

    def find_all_listings_active(
        self,
        keywords: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        taxonomy_id: Optional[int] = None,
        limit: int = 25,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Recherche de listings actifs sur tout Etsy (marketplace).

        Args:
            keywords: Mots-clés de recherche
            min_price: Prix minimum (USD)
            max_price: Prix maximum (USD)
            taxonomy_id: Filtre par catégorie
            limit: Nombre de résultats
            offset: Pagination offset

        Returns:
            Dict avec "count", "results"

        Examples:
            >>> # Search vintage necklaces
            >>> results = client.find_all_listings_active(
            ...     keywords="vintage necklace",
            ...     min_price=10.0,
            ...     max_price=100.0,
            ...     limit=50
            ... )
        """
        params = {"limit": limit, "offset": offset}

        if keywords:
            params["keywords"] = keywords
        if min_price is not None:
            params["min_price"] = min_price
        if max_price is not None:
            params["max_price"] = max_price
        if taxonomy_id is not None:
            params["taxonomy_id"] = taxonomy_id

        return self.api_call(
            "GET",
            "/application/listings/active",
            params=params,
        )
