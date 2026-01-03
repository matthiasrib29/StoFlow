"""
Etsy Mapper

Mapping bidirectionnel entre modèle Etsy et modèle Stoflow.

Business Rules (2025-12-06):
- Etsy → Stoflow : Import produits actifs
- Stoflow → Etsy : Publication produits
- Etsy utilise OAuth2, pas de cookies

Author: Claude
Date: 2025-12-06
Updated: 2025-12-10 - Refactored to use BaseMarketplaceMapper
"""

from services.base_mapper import BaseMarketplaceMapper


class EtsyMapper(BaseMarketplaceMapper):
    """Mapper pour convertir données Etsy ↔ Stoflow."""

    PLATFORM_NAME = "etsy"

    # ===== MAPPING ETSY → STOFLOW =====

    # Etsy n'a pas de condition_id strict, utilise who_made + when_made
    # Mapping Etsy who_made → Stoflow condition (Integer 0-10)
    CONDITION_MAP = {
        "i_did": 8,       # I made it myself → Très bon état
        "collective": 8,  # Collective/studio → Très bon état
        "someone_else": 7,  # Someone else → Bon état
    }

    # Mapping Etsy when_made → Stoflow condition (Integer 0-10)
    WHEN_MADE_MAP = {
        "made_to_order": 10,  # → Neuf avec étiquettes
        "2020_2023": 8,       # → Très bon état
        "2010_2019": 7,       # → Bon état
        "before_2010": 6,     # → Satisfaisant
    }

    # Etsy supporte toutes catégories (orienté handmade/vintage)
    CATEGORY_MAP = {}
    REVERSE_CATEGORY_MAP = {}

    # Reverse condition mapping (Stoflow Integer 0-10 → Etsy who_made)
    REVERSE_CONDITION_MAP = {
        10: "made_to_order",  # Neuf avec étiquettes
        9: "made_to_order",   # Neuf sans étiquettes
        8: "i_did",           # Très bon état
        7: "someone_else",    # Bon état
        6: "someone_else",    # Satisfaisant
        5: "someone_else",    # À réparer
        # Legacy string support
        "NEW": "made_to_order",
        "EXCELLENT": "i_did",
        "GOOD": "someone_else",
        "FAIR": "someone_else",
        "POOR": "someone_else",
    }

    @staticmethod
    def platform_to_stoflow(etsy_listing: dict) -> dict:
        """
        Convertit un produit Etsy en format Stoflow.

        Args:
            etsy_listing: Objet listing Etsy de l'API

        Returns:
            dict: Données produit format Stoflow

        Example Etsy listing:
        {
            "listing_id": 123456789,
            "title": "Vintage Handmade Necklace",
            "description": "Beautiful vintage...",
            "price": {"amount": 4599, "divisor": 100, "currency_code": "USD"},
            "quantity": 1,
            "who_made": "i_did",
            "when_made": "2020_2023",
            "taxonomy_id": 1234,
            "images": [{"url_570xN": "https://..."}],
            "url": "https://etsy.com/listing/123456789"
        }
        """
        # Extract price (Etsy uses cents)
        price_obj = etsy_listing.get("price", {})
        amount = price_obj.get("amount", 0)
        divisor = price_obj.get("divisor", 100)
        price = float(amount) / divisor

        # Map condition based on who_made
        who_made = etsy_listing.get("who_made", "someone_else")
        condition = EtsyMapper.map_condition_to_stoflow(who_made)

        # Extract images
        images = []
        for img in etsy_listing.get("images", []):
            url = img.get("url_570xN") or img.get("url_fullxfull")
            if url:
                images.append(url)

        # Build integration metadata
        metadata = EtsyMapper.build_integration_metadata(
            platform_id=etsy_listing.get("listing_id"),
            platform_url=etsy_listing.get("url"),
            taxonomy_id=etsy_listing.get("taxonomy_id"),
            who_made=etsy_listing.get("who_made"),
            when_made=etsy_listing.get("when_made"),
        )

        return {
            # Basic info
            "title": etsy_listing.get("title", ""),
            "description": etsy_listing.get("description", ""),
            "price": price,

            # Attributes
            "brand": None,  # Etsy n'a pas de champ brand
            "category": "Handmade",  # Catégorie générique pour Etsy
            "condition": condition,
            "size_original": None,
            "color": None,

            # Images
            "images": images,

            # Stock
            "stock_quantity": int(etsy_listing.get("quantity", 1)),

            # Integration Metadata
            "integration_metadata": metadata
        }

    @staticmethod
    def stoflow_to_platform(stoflow_product: dict) -> dict:
        """
        Convertit un produit Stoflow en format Etsy pour publication.

        Args:
            stoflow_product: Données produit Stoflow

        Returns:
            dict: Payload pour API Etsy

        Note: Etsy requiert beaucoup de champs obligatoires
        """
        # Convert price to cents
        price = stoflow_product.get("price", 0)
        price_cents = int(price * 100)

        # Map condition to who_made
        condition = stoflow_product.get("condition", 7)  # 7 = Bon état (default)
        who_made = EtsyMapper.map_condition_to_platform(condition)

        return {
            "title": stoflow_product.get("title", ""),
            "description": stoflow_product.get("description", ""),
            "price": price_cents,
            "quantity": stoflow_product.get("stock_quantity", 1),
            "who_made": who_made or "someone_else",
            "when_made": "2010_2019",    # Default (vintage)
            "taxonomy_id": 1234,          # TODO: Mapper catégories
            "shipping_template_id": None, # À configurer
            "shop_section_id": None,      # À configurer
        }

    # ===== OVERRIDE: Etsy supporte toutes les catégories =====

    @classmethod
    def get_supported_categories(cls) -> list[str]:
        """Etsy supporte toutes catégories car orienté handmade/vintage."""
        return []

    @classmethod
    def is_category_supported(cls, category: str) -> bool:
        """Etsy supporte toutes les catégories."""
        return True

    # ===== ALIASES pour rétrocompatibilité =====

    @staticmethod
    def etsy_to_stoflow(etsy_listing: dict) -> dict:
        """Alias pour rétrocompatibilité."""
        return EtsyMapper.platform_to_stoflow(etsy_listing)

    @staticmethod
    def stoflow_to_etsy(stoflow_product: dict) -> dict:
        """Alias pour rétrocompatibilité."""
        return EtsyMapper.stoflow_to_platform(stoflow_product)
