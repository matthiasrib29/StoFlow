"""
eBay Mapper

Mapping bidirectionnel entre modèle eBay et modèle Stoflow.

Business Rules (2025-12-06):
- eBay → Stoflow : Import produits actifs
- Stoflow → eBay : Publication produits
- Mapping catégories, conditions selon API eBay

Author: Claude
Date: 2025-12-06
Updated: 2025-12-10 - Refactored to use BaseMarketplaceMapper
"""

from services.base_mapper import BaseMarketplaceMapper


class EbayMapper(BaseMarketplaceMapper):
    """Mapper pour convertir données eBay ↔ Stoflow."""

    PLATFORM_NAME = "ebay"

    # ===== MAPPING EBAY → STOFLOW =====

    # Mapping Condition IDs eBay → Stoflow
    CONDITION_MAP = {
        1000: "NEW",           # New
        1500: "NEW",           # New other
        1750: "NEW",           # New with defects
        2000: "EXCELLENT",     # Manufacturer refurbished
        2500: "EXCELLENT",     # Seller refurbished
        3000: "EXCELLENT",     # Used - Excellent
        4000: "GOOD",          # Used - Good
        5000: "FAIR",          # Used - Fair
        6000: "POOR",          # Used - Poor
        7000: "POOR",          # For parts or not working
    }

    # Mapping Category IDs eBay → Catégories Stoflow (exemples)
    CATEGORY_MAP = {
        # Vêtements Homme
        1059: "T-Shirts",
        57989: "Jeans",
        57990: "Pantalons",
        57991: "Chemises",

        # Vêtements Femme
        53159: "Robes",
        63861: "Jupes",
        15724: "Hauts",
        11554: "Jeans",

        # Chaussures
        93427: "Baskets",
        95672: "Chaussures",

        # Accessoires
        169291: "Sacs",
        281: "Bijoux",
        260324: "Montres",
    }

    # ===== MAPPING STOFLOW → EBAY =====

    # Reverse mapping
    REVERSE_CONDITION_MAP = {
        "NEW": 1000,
        "EXCELLENT": 3000,
        "GOOD": 4000,
        "FAIR": 5000,
        "POOR": 6000,
    }

    REVERSE_CATEGORY_MAP = {v: k for k, v in CATEGORY_MAP.items()}

    @staticmethod
    def platform_to_stoflow(ebay_item: dict) -> dict:
        """
        Convertit un produit eBay en format Stoflow.

        Args:
            ebay_item: Objet item eBay de l'API

        Returns:
            dict: Données produit format Stoflow

        Example eBay item structure:
        {
            "itemId": "123456789",
            "title": "Vintage Levi's 501 Jeans",
            "description": "Classic vintage jeans...",
            "price": {"value": "45.00", "currency": "USD"},
            "condition": "USED_EXCELLENT",
            "conditionId": "3000",
            "categoryId": "57989",
            "image": {"imageUrl": "https://..."},
            "listingUrl": "https://ebay.com/itm/123456789"
        }
        """
        # Extract price
        price_obj = ebay_item.get("price", {})
        price = float(price_obj.get("value", 0))

        # Map condition
        condition_id = int(ebay_item.get("conditionId", 3000))
        condition = EbayMapper.map_condition_to_stoflow(condition_id)

        # Map category
        category_id = int(ebay_item.get("categoryId", 0))
        category = EbayMapper.get_stoflow_category(category_id)

        # Extract images (eBay has different image structure)
        images = []
        if "image" in ebay_item:
            images.append(ebay_item["image"]["imageUrl"])
        if "additionalImages" in ebay_item:
            for img in ebay_item["additionalImages"]:
                images.append(img["imageUrl"])

        # Build integration metadata
        metadata = EbayMapper.build_integration_metadata(
            platform_id=ebay_item.get("itemId"),
            platform_url=ebay_item.get("listingUrl"),
            category_id=ebay_item.get("categoryId"),
            condition_id=ebay_item.get("conditionId"),
        )

        return {
            # Basic info
            "title": ebay_item.get("title", ""),
            "description": ebay_item.get("description", ""),
            "price": price,

            # Attributes
            "brand": ebay_item.get("brand"),
            "category": category,
            "condition": condition,
            "label_size": ebay_item.get("size"),
            "color": ebay_item.get("color"),

            # Images
            "images": images,

            # Stock
            "stock_quantity": int(ebay_item.get("quantity", 1)),

            # Integration Metadata
            "integration_metadata": metadata
        }

    @staticmethod
    def stoflow_to_platform(stoflow_product: dict) -> dict:
        """
        Convertit un produit Stoflow en format eBay pour publication.

        Args:
            stoflow_product: Données produit Stoflow

        Returns:
            dict: Payload pour API eBay

        Example Stoflow product:
        {
            "title": "Vintage Levi's 501 Jeans",
            "description": "Classic vintage...",
            "price": 45.99,
            "brand": "Levi's",
            "category": "Jeans",
            "condition": "EXCELLENT",
            "images": ["url1", "url2"]
        }
        """
        # Map condition
        condition = stoflow_product.get("condition", "GOOD")
        condition_id = EbayMapper.map_condition_to_platform(condition)

        # Map category
        category = stoflow_product.get("category", "Other")
        category_id = EbayMapper.get_platform_category_id(category)

        if not category_id:
            raise ValueError(
                f"Cannot map Stoflow category '{category}' to eBay category_id. "
                f"Supported: {list(EbayMapper.REVERSE_CATEGORY_MAP.keys())}"
            )

        return {
            "title": stoflow_product.get("title", ""),
            "description": stoflow_product.get("description", ""),
            "price": {
                "value": str(stoflow_product.get("price", 0)),
                "currency": "EUR"
            },
            "categoryId": str(category_id),
            "conditionId": str(condition_id),
            "quantity": stoflow_product.get("stock_quantity", 1),

            # Optionnel
            "brand": stoflow_product.get("brand"),
            "size": stoflow_product.get("label_size"),
            "color": stoflow_product.get("color"),
        }

    # ===== ALIASES pour rétrocompatibilité =====

    @staticmethod
    def ebay_to_stoflow(ebay_item: dict) -> dict:
        """Alias pour rétrocompatibilité."""
        return EbayMapper.platform_to_stoflow(ebay_item)

    @staticmethod
    def stoflow_to_ebay(stoflow_product: dict) -> dict:
        """Alias pour rétrocompatibilité."""
        return EbayMapper.stoflow_to_platform(stoflow_product)
