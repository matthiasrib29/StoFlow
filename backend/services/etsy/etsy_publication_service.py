"""
Etsy Publication Service.

Service orchestrateur pour publier des produits sur Etsy:
- Convert produit Stoflow → Etsy format
- Create draft listing
- Upload images
- Publish listing (set to active)
- Handle errors

Author: Claude
Date: 2025-12-10
"""

from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from models.user.product import Product
from services.etsy.etsy_listing_client import EtsyListingClient
from services.etsy.etsy_product_conversion_service import (
    EtsyProductConversionService,
    ProductValidationError,
)
from shared.logging_setup import get_logger

logger = get_logger(__name__)


class EtsyPublicationError(Exception):
    """Erreur lors de la publication sur Etsy."""

    pass


class EtsyPublicationService:
    """
    Service orchestrateur pour publier sur Etsy.

    Usage:
        >>> service = EtsyPublicationService(db_session, user_id=1)
        >>> product = db.query(Product).first()
        >>>
        >>> result = service.publish_product(
        ...     product=product,
        ...     taxonomy_id=1234,
        ...     shipping_profile_id=5678,
        ... )
        >>>
        >>> if result["success"]:
        ...     print(f"✅ Published: {result['listing_url']}")
    """

    def __init__(self, db: Session, user_id: int):
        """
        Initialise le service de publication.

        Args:
            db: Session SQLAlchemy
            user_id: ID utilisateur Stoflow
        """
        self.db = db
        self.user_id = user_id
        self.client = EtsyListingClient(db, user_id)
        self.converter = EtsyProductConversionService()

    def publish_product(
        self,
        product: Product,
        taxonomy_id: int,
        shipping_profile_id: Optional[int] = None,
        return_policy_id: Optional[int] = None,
        shop_section_id: Optional[int] = None,
        state: str = "draft",
    ) -> Dict[str, Any]:
        """
        Publie un produit Stoflow sur Etsy.

        Flow:
        1. Validate product data
        2. Convert to Etsy format
        3. Create draft listing
        4. Upload images (TODO)
        5. Set state (active/draft)

        Args:
            product: Produit Stoflow à publier
            taxonomy_id: ID catégorie Etsy (requis)
            shipping_profile_id: ID shipping profile Etsy
            return_policy_id: ID return policy Etsy
            shop_section_id: ID shop section Etsy
            state: État du listing (draft ou active)

        Returns:
            Dict {
                "success": bool,
                "listing_id": int | None,
                "listing_url": str | None,
                "state": str | None,
                "error": str | None,
            }

        Examples:
            >>> result = service.publish_product(
            ...     product=product,
            ...     taxonomy_id=1234,
            ...     shipping_profile_id=5678,
            ...     state="active"
            ... )
        """
        try:
            logger.info(
                f"Publishing product {product.id} ({product.title}) to Etsy..."
            )

            # Step 1: Convert to Etsy format
            listing_data = self.converter.convert_to_listing_data(
                product=product,
                taxonomy_id=taxonomy_id,
                shipping_profile_id=shipping_profile_id,
                return_policy_id=return_policy_id,
                shop_section_id=shop_section_id,
            )

            # Step 2: Create draft listing
            listing = self.client.create_draft_listing(listing_data)
            listing_id = listing["listing_id"]

            logger.info(f"✅ Draft listing created: {listing_id}")

            # Step 3: Upload images (TODO: requires multipart/form-data)
            # image_urls = self.converter._get_image_urls(product)
            # for i, image_url in enumerate(image_urls[:10]):  # Max 10 images
            #     # TODO: Download image from URL and upload to Etsy
            #     pass

            # Step 4: Set state (active or draft)
            if state == "active":
                # Publish listing by setting state to active
                updated_listing = self.client.update_listing(
                    listing_id=listing_id,
                    listing_data={"state": "active"},
                )
                logger.info(f"✅ Listing published (active): {listing_id}")
            else:
                updated_listing = listing

            # Build listing URL
            listing_url = updated_listing.get("url") or f"https://www.etsy.com/listing/{listing_id}"

            return {
                "success": True,
                "listing_id": listing_id,
                "listing_url": listing_url,
                "state": updated_listing.get("state", "draft"),
                "error": None,
            }

        except ProductValidationError as e:
            logger.error(f"Validation error: {e}")
            return {
                "success": False,
                "listing_id": None,
                "listing_url": None,
                "state": None,
                "error": str(e),
            }

        except Exception as e:
            logger.error(f"Publication error: {e}")
            return {
                "success": False,
                "listing_id": None,
                "listing_url": None,
                "state": None,
                "error": f"Etsy publication failed: {str(e)}",
            }

    def update_product(
        self,
        product: Product,
        listing_id: int,
    ) -> Dict[str, Any]:
        """
        Met à jour un listing Etsy existant avec données Stoflow.

        Args:
            product: Produit Stoflow mis à jour
            listing_id: ID du listing Etsy à mettre à jour

        Returns:
            Dict {
                "success": bool,
                "listing_id": int | None,
                "error": str | None,
            }
        """
        try:
            logger.info(f"Updating Etsy listing {listing_id}...")

            # Build update data
            listing_data = {
                "title": self.converter._build_title(product),
                "description": self.converter._build_description(product),
                "price": float(product.price or 0.0),
                "quantity": int(product.stock_quantity or 1),
            }

            # Update listing
            self.client.update_listing(listing_id, listing_data)

            # Update inventory
            inventory_data = self.converter.build_inventory_update(product)
            self.client.update_listing_inventory(listing_id, inventory_data)

            logger.info(f"✅ Listing {listing_id} updated")

            return {
                "success": True,
                "listing_id": listing_id,
                "error": None,
            }

        except Exception as e:
            logger.error(f"Update error: {e}")
            return {
                "success": False,
                "listing_id": None,
                "error": f"Etsy update failed: {str(e)}",
            }

    def delete_product(self, listing_id: int) -> Dict[str, Any]:
        """
        Supprime un listing Etsy.

        Args:
            listing_id: ID du listing à supprimer

        Returns:
            Dict {"success": bool, "error": str | None}
        """
        try:
            logger.info(f"Deleting Etsy listing {listing_id}...")

            self.client.delete_listing(listing_id)

            logger.info(f"✅ Listing {listing_id} deleted")

            return {
                "success": True,
                "error": None,
            }

        except Exception as e:
            logger.error(f"Delete error: {e}")
            return {
                "success": False,
                "error": f"Etsy delete failed: {str(e)}",
            }
