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
Updated: 2025-12-22 - Added database-backed category mapping with gender support
"""

from typing import Optional

from sqlalchemy.orm import Session

from models.public.ebay_category_mapping import EbayCategoryMapping
from services.base_mapper import BaseMarketplaceMapper


class EbayMapper(BaseMarketplaceMapper):
    """Mapper pour convertir données eBay ↔ Stoflow."""

    PLATFORM_NAME = "ebay"

    # ===== MAPPING EBAY → STOFLOW =====

    # Mapping Condition IDs eBay → Stoflow (Integer 0-10)
    # Stoflow scale: 10=Neuf avec étiquettes, 9=Neuf sans étiquettes, 8=Très bon, 7=Bon, 6=Satisfaisant, 5=À réparer
    CONDITION_MAP = {
        1000: 10,           # New → Neuf avec étiquettes
        1500: 9,            # New other → Neuf sans étiquettes
        1750: 8,            # New with defects → Très bon état
        2000: 8,            # Manufacturer refurbished → Très bon état
        2500: 8,            # Seller refurbished → Très bon état
        3000: 8,            # Used - Excellent → Très bon état
        4000: 7,            # Used - Good → Bon état
        5000: 6,            # Used - Fair → Satisfaisant
        6000: 5,            # Used - Poor → À réparer
        7000: 5,            # For parts or not working → À réparer
    }

    # Mapping Category IDs eBay → Catégories Stoflow (FALLBACK - use DB mapping)
    # NOTE: This is a legacy fallback. Prefer using get_ebay_category_id_from_db()
    CATEGORY_MAP = {
        # Vêtements Homme
        15687: "t-shirt",    # T-Shirts (men)
        11483: "jeans",      # Jeans (men)
        57989: "pants",      # Trousers (men)
        57990: "shirt",      # Casual Shirts & Tops (men)

        # Vêtements Femme
        53159: "top",        # Tops & Shirts (women)
        63861: "dress",      # Dresses (women)
        11554: "jeans",      # Jeans (women)
        63864: "skirt",      # Skirts (women)

        # Outerwear
        57988: "jacket",     # Coats, Jackets & Waistcoats (men)
        63862: "jacket",     # Coats, Jackets & Waistcoats (women)
    }

    # ===== MAPPING STOFLOW → EBAY =====

    # Reverse mapping (FALLBACK - without gender distinction)
    # Stoflow condition (Integer 0-10) → eBay condition ID
    REVERSE_CONDITION_MAP = {
        10: 1000,  # Neuf avec étiquettes → New
        9: 1500,   # Neuf sans étiquettes → New other
        8: 3000,   # Très bon état → Used - Excellent
        7: 4000,   # Bon état → Used - Good
        6: 5000,   # Satisfaisant → Used - Fair
        5: 6000,   # À réparer → Used - Poor
        # Legacy string support
        "NEW": 1000,
        "EXCELLENT": 3000,
        "GOOD": 4000,
        "FAIR": 5000,
        "POOR": 6000,
    }

    # NOTE: This is imprecise without gender. Use get_ebay_category_id_from_db() instead.
    REVERSE_CATEGORY_MAP = {v: k for k, v in CATEGORY_MAP.items()}

    # ===== DATABASE-BACKED CATEGORY MAPPING (PREFERRED) =====

    @staticmethod
    def get_ebay_category_id_from_db(
        session: Session,
        category: str,
        gender: str
    ) -> Optional[int]:
        """
        Get eBay category ID from database mapping.

        This is the preferred method as it considers both category and gender
        for accurate mapping (e.g., "jeans" + "men" → 11483, "jeans" + "women" → 11554).

        Args:
            session: SQLAlchemy session
            category: StoFlow category name (e.g., 'jeans', 't-shirt', 'jacket')
            gender: Gender ('men' or 'women')

        Returns:
            int | None: eBay category ID or None if not found

        Example:
            >>> category_id = EbayMapper.get_ebay_category_id_from_db(session, "jeans", "men")
            >>> category_id
            11483
        """
        return EbayCategoryMapping.get_ebay_category_id(session, category, gender)

    @staticmethod
    def get_ebay_category_from_db(
        session: Session,
        category: str,
        gender: str
    ) -> Optional[EbayCategoryMapping]:
        """
        Get full eBay category mapping from database.

        Args:
            session: SQLAlchemy session
            category: StoFlow category name
            gender: Gender ('men' or 'women')

        Returns:
            EbayCategoryMapping | None: Full mapping object or None
        """
        return EbayCategoryMapping.get_ebay_category(session, category, gender)

    @staticmethod
    def resolve_ebay_category_id(
        session: Optional[Session],
        category: str,
        gender: Optional[str] = None
    ) -> Optional[int]:
        """
        Resolve eBay category ID with fallback strategy.

        Strategy:
        1. If session and gender provided: lookup in database
        2. If not found or no session: use static REVERSE_CATEGORY_MAP fallback

        Args:
            session: SQLAlchemy session (optional)
            category: StoFlow category name
            gender: Gender ('men' or 'women', optional)

        Returns:
            int | None: eBay category ID or None if not found
        """
        # Normalize category name
        category_lower = category.lower().strip() if category else ""

        # Try database lookup first
        if session and gender:
            gender_lower = gender.lower().strip()
            db_category_id = EbayMapper.get_ebay_category_id_from_db(
                session, category_lower, gender_lower
            )
            if db_category_id:
                return db_category_id

        # Fallback to static mapping (without gender distinction)
        return EbayMapper.REVERSE_CATEGORY_MAP.get(category_lower)

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
            "size_original": ebay_item.get("size"),
            "color": ebay_item.get("color"),

            # Images
            "images": images,

            # Stock
            "stock_quantity": int(ebay_item.get("quantity", 1)),

            # Integration Metadata
            "integration_metadata": metadata
        }

    @staticmethod
    def stoflow_to_platform(
        stoflow_product: dict,
        session: Optional[Session] = None
    ) -> dict:
        """
        Convertit un produit Stoflow en format eBay pour publication.

        Args:
            stoflow_product: Données produit Stoflow
            session: SQLAlchemy session (optional, for DB-backed category lookup)

        Returns:
            dict: Payload pour API eBay

        Example Stoflow product:
        {
            "title": "Vintage Levi's 501 Jeans",
            "description": "Classic vintage...",
            "price": 45.99,
            "brand": "Levi's",
            "category": "jeans",
            "gender": "men",
            "condition": "EXCELLENT",
            "images": ["url1", "url2"]
        }
        """
        # Map condition
        condition = stoflow_product.get("condition", 7)  # 7 = Bon état (default)
        condition_id = EbayMapper.map_condition_to_platform(condition)

        # Map category (with gender for accurate mapping)
        category = stoflow_product.get("category", "")
        gender = stoflow_product.get("gender", "")

        # Use database-backed mapping if session provided
        category_id = EbayMapper.resolve_ebay_category_id(session, category, gender)

        if not category_id:
            raise ValueError(
                f"Cannot map Stoflow category '{category}' (gender: {gender}) to eBay category_id. "
                f"Please add mapping to ebay_category_mapping table or use fallback categories: "
                f"{list(EbayMapper.REVERSE_CATEGORY_MAP.keys())}"
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
            "size": stoflow_product.get("size_original"),
            "color": stoflow_product.get("color"),
        }

    # ===== ALIASES pour rétrocompatibilité =====

    @staticmethod
    def ebay_to_stoflow(ebay_item: dict) -> dict:
        """Alias pour rétrocompatibilité."""
        return EbayMapper.platform_to_stoflow(ebay_item)

    @staticmethod
    def stoflow_to_ebay(
        stoflow_product: dict,
        session: Optional[Session] = None
    ) -> dict:
        """Alias pour rétrocompatibilité."""
        return EbayMapper.stoflow_to_platform(stoflow_product, session)
