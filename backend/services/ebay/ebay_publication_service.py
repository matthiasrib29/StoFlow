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

from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from models.user.ebay_product_marketplace import EbayProductMarketplace
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
        # Récupérer ebay_products_marketplace
        marketplace_code = marketplace_id.split("_")[1]
        sku_derived = f"{product_id}-{marketplace_code}"

        pm = (
            self.db.query(EbayProductMarketplace)
            .filter(EbayProductMarketplace.sku_derived == sku_derived)
            .first()
        )

        if not pm:
            raise EbayPublicationError(
                f"Produit {product_id} non publié sur {marketplace_id}"
            )

        if not pm.ebay_offer_id:
            raise EbayPublicationError(
                f"Pas d'offer_id pour {sku_derived}"
            )

        # Withdraw offer
        offer_client = EbayOfferClient(
            self.db, self.user_id, marketplace_id=marketplace_id
        )
        offer_client.withdraw_offer(str(pm.ebay_offer_id))

        # Mettre à jour status
        pm.status = "withdrawn"
        self.db.commit()

        return {"status": "withdrawn", "sku_derived": sku_derived}

    # ========== PRIVATE METHODS ==========

    def _get_user_policies(
        self, account_client: EbayAccountClient, marketplace_id: str
    ) -> Dict[str, str]:
        """
        Récupère les business policies du user depuis platform_mappings.

        Si non configurées, lève une erreur avec instructions.

        Returns:
            Dict avec payment_policy_id, fulfillment_policy_id, return_policy_id, inventory_location
        """
        # Récupérer depuis platform_mapping (configuré dans migration)
        pm = self.conversion_service.platform_mapping

        if not pm.ebay_payment_policy_id:
            raise EbayPublicationError(
                "Payment Policy non configurée. "
                "Veuillez configurer les business policies via /api/ebay/policies"
            )

        if not pm.ebay_fulfillment_policy_id:
            raise EbayPublicationError(
                "Fulfillment Policy non configurée. "
                "Veuillez configurer les business policies via /api/ebay/policies"
            )

        if not pm.ebay_return_policy_id:
            raise EbayPublicationError(
                "Return Policy non configurée. "
                "Veuillez configurer les business policies via /api/ebay/policies"
            )

        if not pm.ebay_inventory_location:
            raise EbayPublicationError(
                "Inventory Location non configurée. "
                "Veuillez configurer via /api/ebay/location"
            )

        return {
            "payment_policy_id": str(pm.ebay_payment_policy_id),
            "fulfillment_policy_id": str(pm.ebay_fulfillment_policy_id),
            "return_policy_id": str(pm.ebay_return_policy_id),
            "inventory_location": pm.ebay_inventory_location,
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
        Enregistre ou met à jour ebay_products_marketplace.

        Args:
            product_id: ID du Product
            sku_derived: SKU dérivé
            marketplace_id: Marketplace
            ebay_offer_id: Offer ID (optionnel)
            ebay_listing_id: Listing ID (optionnel)
            status: Status (draft, published, error, withdrawn)
            error_message: Message d'erreur si status=error
        """
        # Chercher existant
        existing = (
            self.db.query(EbayProductMarketplace)
            .filter(EbayProductMarketplace.sku_derived == sku_derived)
            .first()
        )

        if existing:
            # Mettre à jour
            existing.ebay_offer_id = ebay_offer_id or existing.ebay_offer_id
            existing.ebay_listing_id = ebay_listing_id or existing.ebay_listing_id
            existing.status = status
            existing.error_message = error_message
            if status == "published":
                from datetime import datetime, timezone
                existing.published_at = datetime.now(timezone.utc)
        else:
            # Créer nouveau
            pm = EbayProductMarketplace(
                sku_derived=sku_derived,
                product_id=product_id,
                marketplace_id=marketplace_id,
                ebay_offer_id=ebay_offer_id,
                ebay_listing_id=ebay_listing_id,
                status=status,
                error_message=error_message,
            )
            if status == "published":
                from datetime import datetime, timezone
                pm.published_at = datetime.now(timezone.utc)
            self.db.add(pm)

        self.db.commit()
