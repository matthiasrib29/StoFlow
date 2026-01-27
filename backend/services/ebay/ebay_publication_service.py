"""
eBay Publication Service - Orchestrateur.

Service de haut niveau qui coordonne la publication d'un produit sur eBay.

Workflow complet:
1. Convertir Product → Inventory Item (via EbayProductConversionService)
2. Créer/Update Inventory Item sur eBay
3. Créer Offer
4. Publier Offer → récupérer listing_id
5. Enregistrer dans ebay_products_marketplace

Author: Claude
Date: 2025-12-10
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from models.user.ebay_marketplace_settings import EbayMarketplaceSettings
from models.user.ebay_product import EbayProduct
from models.user.product import Product
from services.ebay.ebay_account_client import EbayAccountClient
from services.ebay.ebay_inventory_client import EbayInventoryClient
from services.ebay.ebay_offer_client import EbayOfferClient
from services.ebay.ebay_product_conversion_service import (
    EbayProductConversionService,
    ProductValidationError,
)


class EbayPublicationError(Exception):
    """Exception levée lors d'une erreur de publication eBay."""
    pass


class EbayPublicationService:
    """
    Service orchestrateur pour publication eBay.

    Usage:
        >>> service = EbayPublicationService(db, user_id=1)
        >>> 
        >>> # Publier un produit sur EBAY_FR
        >>> result = service.publish_product(
        ...     product_id=12345,
        ...     marketplace_id="EBAY_FR"
        ... )
        >>> 
        >>> print(f"Listing ID: {result['listing_id']}")
        >>> print(f"Offer ID: {result['offer_id']}")
        >>> print(f"SKU: {result['sku_derived']}")
    """

    def __init__(self, db: Session, user_id: int):
        """
        Initialise le service de publication.

        Args:
            db: Session SQLAlchemy
            user_id: ID du user
        """
        self.db = db
        self.user_id = user_id

        # Initialiser conversion service
        self.conversion_service = EbayProductConversionService(db, user_id)

    def publish_product(
        self,
        product_id: int,
        marketplace_id: str,
        category_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Publie un produit sur une marketplace eBay.

        Workflow:
        1. Load Product depuis DB
        2. Générer SKU dérivé (product_id-marketplace_code)
        3. Convertir → Inventory Item
        4. Create/Update Inventory Item sur eBay
        5. Créer Offer
        6. Publier Offer
        7. Enregistrer dans ebay_products_marketplace

        Args:
            product_id: ID du Product Stoflow
            marketplace_id: Marketplace (ex: "EBAY_FR")
            category_id: eBay category ID (optionnel, utilise fallback si None)

        Returns:
            Dict avec:
                - sku_derived: SKU dérivé
                - offer_id: eBay Offer ID
                - listing_id: eBay Listing ID
                - marketplace_id: Marketplace

        Raises:
            EbayPublicationError: Si publication échoue
            ProductValidationError: Si produit invalide

        Examples:
            >>> result = service.publish_product(12345, "EBAY_FR", category_id="11450")
            >>> print(f"Publié sur eBay: {result['listing_id']}")
        """
        # 1. Load Product
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise EbayPublicationError(f"Product {product_id} introuvable")

        # 2. Générer SKU dérivé
        marketplace_code = marketplace_id.split("_")[1]  # EBAY_FR → FR
        sku_derived = f"{product.id}-{marketplace_code}"

        try:
            # 3. Initialiser clients eBay
            inventory_client = EbayInventoryClient(
                self.db, self.user_id, marketplace_id=marketplace_id
            )
            offer_client = EbayOfferClient(
                self.db, self.user_id, marketplace_id=marketplace_id
            )
            account_client = EbayAccountClient(
                self.db, self.user_id, marketplace_id=marketplace_id
            )

            # 4. Récupérer business policies + inventory location
            policies = self._get_user_policies(account_client, marketplace_id)

            # 5. Convertir → Inventory Item
            inventory_item = self.conversion_service.convert_to_inventory_item(
                product, sku_derived, marketplace_id
            )

            # 6. Create/Update Inventory Item
            inventory_client.create_or_replace_inventory_item(
                sku_derived, inventory_item
            )

            # 7. Créer Offer
            offer_data = self.conversion_service.create_offer_data(
                product,
                sku_derived,
                marketplace_id,
                payment_policy_id=policies["payment_policy_id"],
                fulfillment_policy_id=policies["fulfillment_policy_id"],
                return_policy_id=policies["return_policy_id"],
                inventory_location=policies["inventory_location"],
                category_id=category_id,
            )

            offer_result = offer_client.create_offer(offer_data)
            offer_id = offer_result["offerId"]

            # 8. Publier Offer
            publish_result = offer_client.publish_offer(offer_id)
            listing_id = publish_result["listingId"]

            # 9. Enregistrer dans DB (ebay_products_marketplace)
            self._save_product_marketplace(
                product_id=product.id,
                sku_derived=sku_derived,
                marketplace_id=marketplace_id,
                ebay_offer_id=int(offer_id),
                ebay_listing_id=int(listing_id),
            )

            return {
                "sku_derived": sku_derived,
                "offer_id": offer_id,
                "listing_id": listing_id,
                "marketplace_id": marketplace_id,
            }

        except ProductValidationError as e:
            raise EbayPublicationError(f"Validation produit échouée: {e}") from e
        except Exception as e:
            # Enregistrer l'erreur dans DB
            self._save_product_marketplace(
                product_id=product.id,
                sku_derived=sku_derived,
                marketplace_id=marketplace_id,
                status="error",
                error_message=str(e),
            )
            raise EbayPublicationError(f"Publication échouée: {e}") from e

    def unpublish_product(
        self, product_id: int, marketplace_id: str
    ) -> Dict[str, Any]:
        """
        Dé-publie un produit d'une marketplace eBay (withdraw).

        Args:
            product_id: ID du Product
            marketplace_id: Marketplace (ex: "EBAY_FR")

        Returns:
            Dict avec status

        Examples:
            >>> service.unpublish_product(12345, "EBAY_FR")
        """
        # Generate sku_derived from product_id and marketplace
        marketplace_code = marketplace_id.split("_")[1]
        sku_derived = f"{product_id}-{marketplace_code}"

        # Find the EbayProduct by sku_derived
        ebay_product = (
            self.db.query(EbayProduct)
            .filter(EbayProduct.sku_derived == sku_derived)
            .first()
        )

        if not ebay_product:
            raise EbayPublicationError(
                f"Produit {product_id} non publié sur {marketplace_id}"
            )

        if not ebay_product.ebay_offer_id:
            raise EbayPublicationError(
                f"Pas d'offer_id pour {sku_derived}"
            )

        # Withdraw offer
        offer_client = EbayOfferClient(
            self.db, self.user_id, marketplace_id=marketplace_id
        )
        offer_client.withdraw_offer(str(ebay_product.ebay_offer_id))

        # Update status
        ebay_product.status = "withdrawn"
        self.db.flush()

        return {"status": "withdrawn", "sku_derived": sku_derived}

    # ========== PRIVATE METHODS ==========

    def _get_user_policies(
        self, account_client: EbayAccountClient, marketplace_id: str
    ) -> Dict[str, str]:
        """
        Retrieve business policies and inventory location from ebay_marketplace_settings.

        Raises EbayPublicationError when required fields are missing.

        Returns:
            Dict with payment_policy_id, fulfillment_policy_id, return_policy_id, inventory_location
        """
        settings = (
            self.db.query(EbayMarketplaceSettings)
            .filter(EbayMarketplaceSettings.marketplace_id == marketplace_id)
            .first()
        )

        if not settings:
            raise EbayPublicationError(
                f"No eBay settings configured for {marketplace_id}. "
                "Please configure via PUT /api/ebay/settings/{marketplace_id}"
            )

        if not settings.payment_policy_id:
            raise EbayPublicationError(
                "Payment Policy non configurée. "
                f"Veuillez configurer via PUT /api/ebay/settings/{marketplace_id}"
            )

        if not settings.fulfillment_policy_id:
            raise EbayPublicationError(
                "Fulfillment Policy non configurée. "
                f"Veuillez configurer via PUT /api/ebay/settings/{marketplace_id}"
            )

        if not settings.return_policy_id:
            raise EbayPublicationError(
                "Return Policy non configurée. "
                f"Veuillez configurer via PUT /api/ebay/settings/{marketplace_id}"
            )

        if not settings.inventory_location_key:
            raise EbayPublicationError(
                "Inventory Location non configurée. "
                f"Veuillez configurer via PUT /api/ebay/settings/{marketplace_id}"
            )

        return {
            "payment_policy_id": settings.payment_policy_id,
            "fulfillment_policy_id": settings.fulfillment_policy_id,
            "return_policy_id": settings.return_policy_id,
            "inventory_location": settings.inventory_location_key,
        }

    def _save_product_marketplace(
        self,
        product_id: int,
        sku_derived: str,
        marketplace_id: str,
        ebay_offer_id: Optional[int] = None,
        ebay_listing_id: Optional[int] = None,
        status: str = "published",
        error_message: Optional[str] = None,
    ) -> None:
        """
        Update ebay_products with publication data.

        Args:
            product_id: ID du Product
            sku_derived: SKU dérivé
            marketplace_id: Marketplace
            ebay_offer_id: Offer ID (optionnel)
            ebay_listing_id: Listing ID (optionnel)
            status: Status (draft, published, error, withdrawn)
            error_message: Message d'erreur si status=error
        """
        # Find the EbayProduct linked to this Product
        ebay_product = (
            self.db.query(EbayProduct)
            .filter(EbayProduct.product_id == product_id)
            .first()
        )

        if not ebay_product:
            raise EbayPublicationError(
                f"EbayProduct not found for product_id={product_id}"
            )

        # Update ebay_product with publication data
        ebay_product.sku_derived = sku_derived
        ebay_product.marketplace_id = marketplace_id
        if ebay_offer_id:
            ebay_product.ebay_offer_id = ebay_offer_id
        if ebay_listing_id:
            ebay_product.ebay_listing_id = ebay_listing_id
        ebay_product.status = status
        ebay_product.error_message = error_message

        if status == "published":
            ebay_product.published_at = datetime.now(timezone.utc)

        self.db.flush()
