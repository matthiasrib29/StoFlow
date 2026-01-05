"""
Vinted Mapper

Mapping bidirectionnel entre modèle Vinted et modèle Stoflow.

Business Rules (2025-12-18):
- Vinted → Stoflow : Import produits via vinted_mapping (lookup inverse)
- Stoflow → Vinted : Publication via get_vinted_category() function
- Mapping catégories intelligent avec attributs (fit, length, rise, etc.)
- Dimensions: dim1=width, dim2=length pour hauts uniquement

Author: Claude
Date: 2025-12-06
Updated: 2025-12-10 - Refactored to use BaseMarketplaceMapper
Updated: 2025-12-18 - Use vinted_mapping table and get_vinted_category function
"""

from typing import Optional

from sqlalchemy.orm import Session

from services.base_mapper import BaseMarketplaceMapper
from repositories.vinted_mapping_repository import VintedMappingRepository
from shared.logging_setup import get_logger

logger = get_logger(__name__)


class VintedMapper(BaseMarketplaceMapper):
    """
    Mapper pour convertir données Vinted ↔ Stoflow.

    Utilise la table vinted_mapping et la fonction get_vinted_category
    pour un mapping intelligent basé sur les attributs.

    Usage avec DB (recommandé):
        mapper = VintedMapper(db)
        vinted_id = mapper.get_vinted_category_id_from_db("jeans", "men", fit="slim")

    Usage statique (fallback hardcodé):
        category = VintedMapper.get_stoflow_category(1193)  # → "jeans"
    """

    PLATFORM_NAME = "vinted"

    def __init__(self, db: Optional[Session] = None):
        """
        Initialize mapper with optional database session.

        Args:
            db: SQLAlchemy session for database lookups (recommended)
        """
        self.db = db
        self._repo = VintedMappingRepository(db) if db else None

    # ===== MAPPING VINTED → STOFLOW (FALLBACK STATIQUE) =====

    # Mapping Vinted status_id → Stoflow condition (Integer 0-10)
    # Stoflow scale: 10=Neuf avec étiquettes, 9=Neuf sans étiquettes, 8=Très bon, 7=Bon, 6=Satisfaisant, 5=À réparer
    CONDITION_MAP = {
        1: 10,  # Neuf avec étiquette → 10
        2: 8,   # Très bon état → 8
        3: 7,   # Bon état → 7
        4: 6,   # Satisfaisant → 6
        5: 5    # Utilisé → 5
    }

    # Fallback statique - utilisé si pas de session DB
    # NOTE: Préférer get_stoflow_category_from_db() pour mapping dynamique
    CATEGORY_MAP_FALLBACK = {
        # Vêtements Homme
        1193: "jeans",
        1203: "t-shirt",
        1195: "pants",
        1201: "shirt",
        1199: "sweater",
        1197: "jacket",
        1205: "shorts",
        # Vêtements Femme
        16: "dress",
        18: "skirt",
        1211: "jeans",
        1213: "pants",
        1215: "sweater",
        1217: "jacket",
        1219: "coat",
    }

    # ===== MAPPING STOFLOW → VINTED (FALLBACK STATIQUE) =====

    # Reverse mapping: Stoflow condition → Vinted status_id
    REVERSE_CONDITION_MAP = {
        "new": 1,
        "excellent": 2,
        "good": 3,
        "fair": 4,
        "poor": 5,
        # Uppercase compatibility
        "NEW": 1,
        "EXCELLENT": 2,
        "GOOD": 3,
        "FAIR": 4,
        "POOR": 5,
        # Integer keys (new format: 0-10 scale)
        10: 1,  # Neuf avec étiquettes
        9: 1,   # Neuf sans étiquettes
        8: 2,   # Très bon état → Vinted status 2
        7: 3,   # Bon état → Vinted status 3
        6: 4,   # Satisfaisant → Vinted status 4
        5: 5,   # À réparer → Vinted status 5
    }

    # Fallback reverse mapping - DEPRECATED, use get_vinted_category_id_from_db()
    REVERSE_CATEGORY_MAP = {v: k for k, v in CATEGORY_MAP_FALLBACK.items()}

    # Alias for compatibility
    CATEGORY_MAP = CATEGORY_MAP_FALLBACK

    @staticmethod
    def platform_to_stoflow(vinted_item: dict) -> dict:
        """
        Convertit un produit Vinted en format Stoflow.

        Args:
            vinted_item: Objet item Vinted de l'API

        Returns:
            dict: Données produit format Stoflow

        Example Vinted item structure:
        {
            "id": 123456,
            "title": "Jean Levi's 501",
            "description": "Jean vintage...",
            "price": "45.00",
            "currency": "EUR",
            "brand_title": "Levi's",
            "size_title": "W32L34",
            "status_id": 2,
            "catalog_id": 1193,
            "color": "Bleu",
            "photos": [
                {"full_size_url": "https://..."},
                ...
            ],
            "user_id": 789,
            "url": "https://vinted.fr/items/123456",
            "created_at_ts": 1638360000
        }
        """
        # Extract images using helper
        images = BaseMarketplaceMapper.extract_images(
            vinted_item,
            image_field="photos",
            url_field="full_size_url"
        )

        # Map condition
        condition_id = vinted_item.get("status_id", 3)
        condition = VintedMapper.map_condition_to_stoflow(condition_id)

        # Map category
        catalog_id = vinted_item.get("catalog_id", 0)
        category = VintedMapper.get_stoflow_category(catalog_id)

        # Build integration metadata
        metadata = VintedMapper.build_integration_metadata(
            platform_id=vinted_item.get("id"),
            platform_url=vinted_item.get("url"),
            user_id=vinted_item.get("user_id"),
            catalog_id=vinted_item.get("catalog_id"),
            created_at=vinted_item.get("created_at_ts"),
        )

        return {
            # Basic info
            "title": vinted_item.get("title", ""),
            "description": vinted_item.get("description", ""),
            "price": float(vinted_item.get("price", 0)),

            # Attributes
            "brand": vinted_item.get("brand_title"),
            "category": category,
            "condition": condition,
            "size_original": vinted_item.get("size_title"),
            "color": vinted_item.get("color"),

            # Images
            "images": images,

            # Stock
            "stock_quantity": 1,  # Vinted = toujours 1 pièce unique

            # Integration Metadata
            "integration_metadata": metadata
        }

    @staticmethod
    def stoflow_to_platform(stoflow_product: dict) -> dict:
        """
        Convertit un produit Stoflow en format Vinted pour publication.

        Args:
            stoflow_product: Données produit Stoflow

        Returns:
            dict: Payload pour API Vinted create item

        Example Stoflow product:
        {
            "title": "Jean Levi's 501",
            "description": "Jean vintage...",
            "price": 45.99,
            "brand": "Levi's",
            "category": "Jeans",
            "condition": "EXCELLENT",
            "size_original": "W32L34",
            "color": "Blue",
            "images": ["url1", "url2", ...]
        }
        """
        # Map condition
        condition = stoflow_product.get("condition", 7)  # 7 = Bon état (default)
        status_id = VintedMapper.map_condition_to_platform(condition)

        # Map category
        category = stoflow_product.get("category", "Other")
        catalog_id = VintedMapper.get_platform_category_id(category)

        if not catalog_id:
            raise ValueError(
                f"Cannot map Stoflow category '{category}' to Vinted catalog_id. "
                f"Please use one of: {list(VintedMapper.REVERSE_CATEGORY_MAP.keys())}"
            )

        return {
            "title": stoflow_product.get("title", ""),
            "description": stoflow_product.get("description", ""),
            "price": stoflow_product.get("price", 0),
            "currency": "EUR",  # Fixe pour France
            "catalog_id": catalog_id,
            "status_id": status_id,

            # Optionnel mais recommandé
            "brand_title": stoflow_product.get("brand"),
            "size_title": stoflow_product.get("size_original"),
            "color": stoflow_product.get("color"),

            # Flags
            "is_for_sell": True,
            "is_visible": 1,  # Publié immédiatement
        }

    # ===== ALIASES pour rétrocompatibilité =====

    @staticmethod
    def vinted_to_stoflow(vinted_item: dict) -> dict:
        """Alias pour rétrocompatibilité."""
        return VintedMapper.platform_to_stoflow(vinted_item)

    @staticmethod
    def stoflow_to_vinted(stoflow_product: dict) -> dict:
        """Alias pour rétrocompatibilité."""
        return VintedMapper.stoflow_to_platform(stoflow_product)

    @staticmethod
    def get_vinted_catalog_id(stoflow_category: str) -> Optional[int]:
        """Alias pour rétrocompatibilité."""
        return VintedMapper.get_platform_category_id(stoflow_category)

    # =========================================================================
    # DATABASE-BACKED METHODS (using vinted_mapping table)
    # =========================================================================

    def get_vinted_category_id_from_db(
        self,
        category: str,
        gender: str,
        fit: Optional[str] = None,
        length: Optional[str] = None,
        rise: Optional[str] = None,
        material: Optional[str] = None,
        pattern: Optional[str] = None,
        neckline: Optional[str] = None,
        sleeve_length: Optional[str] = None
    ) -> Optional[int]:
        """
        Get Vinted category ID using vinted_mapping table and get_vinted_category function.

        This is the PREFERRED method for Stoflow → Vinted mapping.
        Uses intelligent matching with attributes.

        Args:
            category: Stoflow category name (e.g. "jeans", "t-shirt")
            gender: Gender (e.g. "men", "women")
            fit: Optional fit (e.g. "slim", "regular")
            length: Optional length
            rise: Optional rise (for pants)
            material: Optional material
            pattern: Optional pattern
            neckline: Optional neckline
            sleeve_length: Optional sleeve length

        Returns:
            Vinted catalog_id or None

        Example:
            >>> mapper = VintedMapper(db)
            >>> vinted_id = mapper.get_vinted_category_id_from_db("jeans", "men", fit="slim")
            >>> print(vinted_id)  # e.g. 1193
        """
        if not self._repo:
            logger.warning("No DB session, falling back to static mapping")
            return self.REVERSE_CATEGORY_MAP.get(category.lower())

        return self._repo.get_vinted_category_id(
            category=category,
            gender=gender,
            fit=fit,
            length=length,
            rise=rise,
            material=material,
            pattern=pattern,
            neckline=neckline,
            sleeve_length=sleeve_length
        )

    def get_stoflow_category_from_db(
        self,
        vinted_id: int
    ) -> tuple[Optional[str], Optional[str]]:
        """
        Get Stoflow category from Vinted category ID using vinted_mapping table.

        This is the PREFERRED method for Vinted → Stoflow mapping.
        Performs reverse lookup in vinted_mapping.

        Args:
            vinted_id: Vinted catalog_id

        Returns:
            Tuple (category, gender) or (None, None) if not found

        Example:
            >>> mapper = VintedMapper(db)
            >>> category, gender = mapper.get_stoflow_category_from_db(1193)
            >>> print(category, gender)  # "jeans", "men"
        """
        if not self._repo:
            logger.warning("No DB session, falling back to static mapping")
            category = self.CATEGORY_MAP_FALLBACK.get(vinted_id)
            return (category, None) if category else (None, None)

        return self._repo.reverse_map_category(vinted_id)

    def vinted_to_stoflow_with_db(self, vinted_item: dict) -> dict:
        """
        Convert Vinted item to Stoflow format using database mapping.

        Enhanced version of platform_to_stoflow that uses vinted_mapping
        for accurate category conversion.

        Args:
            vinted_item: Vinted item dict from API

        Returns:
            dict: Stoflow product data with mapped category
        """
        # Start with static conversion
        stoflow_data = VintedMapper.platform_to_stoflow(vinted_item)

        # Override category with DB lookup if available
        catalog_id = vinted_item.get("catalog_id")
        if catalog_id and self._repo:
            category, gender = self._repo.reverse_map_category(catalog_id)
            if category:
                stoflow_data["category"] = category
            if gender:
                stoflow_data["gender"] = gender

        # Extract dimensions from Vinted measurements
        measurement_width = vinted_item.get("measurement_width")
        measurement_length = vinted_item.get("measurement_length")

        if measurement_width:
            stoflow_data["dim1"] = int(measurement_width)
        if measurement_length:
            stoflow_data["dim2"] = int(measurement_length)

        return stoflow_data

    def stoflow_to_vinted_with_db(
        self,
        stoflow_product: dict,
        include_dimensions: bool = True
    ) -> dict:
        """
        Convert Stoflow product to Vinted format using database mapping.

        Enhanced version of stoflow_to_platform that uses get_vinted_category
        for intelligent category matching with attributes.

        Args:
            stoflow_product: Stoflow product dict
            include_dimensions: Include dim1/dim2 as measurement_width/length

        Returns:
            dict: Vinted API payload

        Raises:
            ValueError: If category cannot be mapped
        """
        # Get category using intelligent matching
        category = stoflow_product.get("category", "")
        gender = stoflow_product.get("gender", "men")
        fit = stoflow_product.get("fit")
        length = stoflow_product.get("length")
        rise = stoflow_product.get("rise")
        material = stoflow_product.get("material")
        pattern = stoflow_product.get("pattern")
        neckline = stoflow_product.get("neckline")
        sleeve_length = stoflow_product.get("sleeve_length")

        catalog_id = self.get_vinted_category_id_from_db(
            category=category,
            gender=gender,
            fit=fit,
            length=length,
            rise=rise,
            material=material,
            pattern=pattern,
            neckline=neckline,
            sleeve_length=sleeve_length
        )

        if not catalog_id:
            raise ValueError(
                f"Cannot map category '{category}' (gender={gender}, fit={fit}) to Vinted. "
                "Check vinted_mapping table."
            )

        # Map condition (Integer 0-10 → Vinted status_id)
        condition = stoflow_product.get("condition", 7)  # 7 = Bon état (default)
        # Support both int and legacy str conditions
        if isinstance(condition, str):
            status_id = self.REVERSE_CONDITION_MAP.get(condition.lower(), 3)
        else:
            status_id = self.REVERSE_CONDITION_MAP.get(condition, 3)

        result = {
            "title": stoflow_product.get("title", ""),
            "description": stoflow_product.get("description", ""),
            "price": stoflow_product.get("price", 0),
            "currency": "EUR",
            "catalog_id": catalog_id,
            "status_id": status_id,
            "brand_title": stoflow_product.get("brand"),
            "size_title": stoflow_product.get("size_original"),
            "color": stoflow_product.get("color"),
            "is_for_sell": True,
            "is_visible": 1,
        }

        # Add dimensions for tops only (hauts)
        if include_dimensions and self._is_top_category(category):
            dim1 = stoflow_product.get("dim1")
            dim2 = stoflow_product.get("dim2")
            if dim1:
                result["measurement_width"] = int(dim1)
            if dim2:
                result["measurement_length"] = int(dim2)

        return result

    @staticmethod
    def _is_top_category(category: str) -> bool:
        """
        Check if category is a top (haut) for dimension eligibility.

        Dimensions (width/length) are only shown on Vinted for tops.

        Args:
            category: Category name

        Returns:
            True if category is a top
        """
        top_categories = [
            "t-shirt", "tshirt", "t-shirts",
            "sweater", "sweat-shirt", "sweatshirt", "pull",
            "hoodie", "hoodies",
            "shirt", "chemise",
            "blouse",
            "top", "tops",
            "polo",
            "cardigan",
            "vest", "gilet",
        ]
        return category.lower() in top_categories

    # =========================================================================
    # CLASS METHODS (for use without instance)
    # =========================================================================

    @classmethod
    def with_db(cls, db: Session) -> "VintedMapper":
        """
        Create a VintedMapper instance with database session.

        Convenience method for one-off usage.

        Args:
            db: SQLAlchemy session

        Returns:
            VintedMapper instance with DB support

        Example:
            >>> mapper = VintedMapper.with_db(db)
            >>> vinted_id = mapper.get_vinted_category_id_from_db("jeans", "men")
        """
        return cls(db=db)
