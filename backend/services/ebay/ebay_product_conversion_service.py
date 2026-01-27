"""
eBay Product Conversion Service (MVP).

Convertit un Product Stoflow vers le format eBay (Inventory Item + Offer).

Fonctionnalites:
- Conversion Product → eBay Inventory Item
- Creation Offer avec pricing basique
- Aspects eBay multilingues (Brand, Colour, Size, Condition, etc.)
- Support multi-marketplace (pricing coefficient par marketplace)
- SEO multilingue (titres optimises par marketplace via EbaySeoTitleService)

Author: Claude
Date: 2025-12-10
"""

from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from models.public.condition import Condition
from models.public.ebay_aspect_mapping import AspectMapping
from models.public.ebay_category_mapping import EbayCategoryMapping
from models.public.ebay_marketplace_config import MarketplaceConfig
from models.user.ebay_marketplace_settings import EbayMarketplaceSettings
from models.user.product import Product
from services.ebay.ebay_aspect_value_service import (
    EbayAspectValueService,
    get_aspect_value_service,
)
from services.ebay.ebay_description_service import EbayDescriptionService
from services.ebay.ebay_mapper import EbayMapper
from services.ebay.ebay_seo_title_service import EbaySeoTitleService
from shared.exceptions import ProductValidationError
from shared.logging import get_logger

logger = get_logger(__name__)


class EbayProductConversionService:
    """
    Service de conversion Product → eBay.

    Usage:
        >>> service = EbayProductConversionService(db, user_id=1)
        >>> 
        >>> # Convertir en inventory item
        >>> sku_derived = "12345-FR"
        >>> product = db.query(Product).filter(Product.id == 12345).first()
        >>> inventory_item = service.convert_to_inventory_item(
        ...     product, sku_derived, marketplace_id="EBAY_FR"
        ... )
        >>> 
        >>> # Créer une offer
        >>> offer_data = service.create_offer_data(
        ...     product, sku_derived, marketplace_id="EBAY_FR",
        ...     payment_policy_id="123", fulfillment_policy_id="456", return_policy_id="789",
        ...     inventory_location="warehouse_fr"
        ... )
    """

    def __init__(self, db: Session, user_id: int):
        """
        Initialise le service de conversion.

        Args:
            db: Session SQLAlchemy
            user_id: ID du user (pour récupérer pricing coefficients)
        """
        self.db = db
        self.user_id = user_id

        # Load condition mapping from DB (condition_note → ebay_condition)
        self._condition_map = self._load_condition_mapping()

        # Initialize aspect value service for multilingual translations
        self._aspect_value_service = get_aspect_value_service(db)

        # Initialize SEO title service for multilingual titles
        self._seo_title_service = EbaySeoTitleService(db)

        # Initialize description service for multilingual HTML descriptions
        self._description_service = EbayDescriptionService(db)

    def convert_to_inventory_item(
        self,
        product: Product,
        sku_derived: str,
        marketplace_id: str,
    ) -> Dict[str, Any]:
        """
        Convertit un Product en Inventory Item eBay.

        Args:
            product: Product Stoflow
            sku_derived: SKU dérivé (ex: "12345-FR")
            marketplace_id: Marketplace (ex: "EBAY_FR")

        Returns:
            Dict formaté pour PUT /sell/inventory/v1/inventory_item/{sku}

        Raises:
            ProductValidationError: Si validation échoue

        Examples:
            >>> inventory_item = service.convert_to_inventory_item(
            ...     product, "12345-FR", "EBAY_FR"
            ... )
            >>> # Utiliser avec EbayInventoryClient
            >>> client.create_or_replace_inventory_item("12345-FR", inventory_item)
        """
        # Validations
        self._validate_product(product)

        # Récupérer marketplace config
        marketplace = (
            self.db.query(MarketplaceConfig)
            .filter(MarketplaceConfig.marketplace_id == marketplace_id)
            .first()
        )
        if not marketplace:
            raise ValueError(f"Marketplace inconnue: {marketplace_id}")

        # Construire title SEO multilingue
        title = self._build_title(product, marketplace_id)

        # Construire description HTML multilingue
        description = self._build_description(product, marketplace_id)

        # Construire aspects eBay
        aspects = self._build_aspects(product, marketplace_id)

        # Images
        image_urls = self._get_image_urls(product)

        # Construire inventory item
        inventory_item = {
            "product": {
                "title": title,
                "description": description,
                "aspects": aspects,
                "imageUrls": image_urls,
            },
            "condition": self._map_condition(product.condition),
            "availability": {
                "shipToLocationAvailability": {
                    "quantity": product.stock_quantity or 1
                }
            },
        }

        return inventory_item

    def create_offer_data(
        self,
        product: Product,
        sku_derived: str,
        marketplace_id: str,
        payment_policy_id: str,
        fulfillment_policy_id: str,
        return_policy_id: str,
        inventory_location: str,
        category_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Crée les données d'une Offer eBay.

        Args:
            product: Product Stoflow
            sku_derived: SKU dérivé (ex: "12345-FR")
            marketplace_id: Marketplace (ex: "EBAY_FR")
            payment_policy_id: ID payment policy
            fulfillment_policy_id: ID fulfillment policy
            return_policy_id: ID return policy
            inventory_location: Inventory location key
            category_id: eBay category ID (ex: "11450" pour T-shirts homme)
                        Si None, auto-résolu depuis product.category + product.gender
                        via la table ebay_category_mapping

        Returns:
            Dict formaté pour POST /sell/inventory/v1/offer

        Examples:
            >>> offer_data = service.create_offer_data(
            ...     product, "12345-FR", "EBAY_FR",
            ...     payment_policy_id="123",
            ...     fulfillment_policy_id="456",
            ...     return_policy_id="789",
            ...     inventory_location="warehouse_fr",
            ...     category_id="11450"
            ... )
            >>> # Utiliser avec EbayOfferClient
            >>> result = client.create_offer(offer_data)
            >>> offer_id = result['offerId']

        Author: Claude
        Date: 2025-12-10
        Updated: 2025-12-22 - Auto-resolve category_id via ebay_category_mapping table
        """
        # Auto-resolve category_id if not provided
        resolved_category_id = category_id
        if not resolved_category_id:
            # Try to resolve from product.category + product.gender
            if product.category and product.gender:
                resolved_category_id = EbayMapper.resolve_ebay_category_id(
                    self.db, product.category, product.gender
                )
                if resolved_category_id:
                    resolved_category_id = str(resolved_category_id)
                    logger.info(
                        f"Auto-resolved eBay category_id={resolved_category_id} "
                        f"for category='{product.category}', gender='{product.gender}'"
                    )

        # Validation: category_id requis (either provided or resolved)
        if not resolved_category_id:
            raise ProductValidationError(
                "category_id est requis pour créer une offer eBay. "
                f"Impossible de résoudre automatiquement pour category='{product.category}', "
                f"gender='{product.gender}'. "
                "Veuillez spécifier l'ID de catégorie eBay manuellement ou ajouter "
                "le mapping dans la table ebay_category_mapping."
            )

        # Calculer prix avec coefficient marketplace
        price = self._calculate_price(product, marketplace_id)

        # Récupérer marketplace config pour currency
        marketplace = (
            self.db.query(MarketplaceConfig)
            .filter(MarketplaceConfig.marketplace_id == marketplace_id)
            .first()
        )

        # Construire offer data
        offer_data = {
            "sku": sku_derived,
            "marketplaceId": marketplace_id,
            "format": "FIXED_PRICE",
            "availableQuantity": product.stock_quantity or 1,
            "categoryId": resolved_category_id,  # Auto-resolved or provided
            "listingPolicies": {
                "paymentPolicyId": payment_policy_id,
                "fulfillmentPolicyId": fulfillment_policy_id,
                "returnPolicyId": return_policy_id,
            },
            "merchantLocationKey": inventory_location,
            "pricingSummary": {
                "price": {
                    "value": str(price),
                    "currency": marketplace.currency,
                }
            },
        }

        return offer_data

    # ========== PRIVATE METHODS ==========

    def _validate_product(self, product: Product) -> None:
        """
        Valide qu'un produit peut être publié sur eBay.

        Raises:
            ProductValidationError: Si validation échoue

        Author: Claude
        Date: 2025-12-10
        Updated: 2025-12-10 - Ajout validation images (minimum 1 image requise)
        """
        if not product.title:
            raise ProductValidationError("Product.title est requis")

        if not product.price or float(product.price) <= 0:
            raise ProductValidationError(f"Prix invalide: {product.price}")

        if product.condition is None:
            raise ProductValidationError("Product.condition est requis")

        # Validation images (eBay exige au moins 1 image)
        image_urls = self._get_image_urls(product)
        if not image_urls or len(image_urls) == 0:
            raise ProductValidationError(
                "Au moins 1 image est requise pour publier sur eBay. "
                "Veuillez ajouter des images à votre produit."
            )

    def _build_title(self, product: Product, marketplace_id: str) -> str:
        """Build SEO-optimized title translated per marketplace."""
        return self._seo_title_service.generate_seo_title(product, marketplace_id)

    def _build_description(self, product: Product, marketplace_id: str) -> str:
        """Build multilingual HTML description for eBay."""
        return self._description_service.generate_description(product, marketplace_id)

    def _build_aspects(
        self, product: Product, marketplace_id: str
    ) -> Dict[str, List[str]]:
        """
        Construit les aspects eBay avec traduction multilingue.

        Two-level translation:
        1. Aspect NAMES: via ebay.aspect_name_mapping (ex: "Colour" → "Couleur")
        2. Aspect VALUES: via ebay.aspect_* tables (ex: "Blue" → "Bleu")

        Args:
            product: Product Stoflow
            marketplace_id: Marketplace (ex: "EBAY_FR")

        Returns:
            Dict {aspect_name_localized: [values_localized]}

        Author: Claude
        Date: 2025-12-10
        Updated: 2025-12-22 - Ajout traduction des VALEURS via EbayAspectValueService
        """
        # Load aspect NAME translations for this marketplace
        aspect_name_translations = AspectMapping.get_all_for_marketplace(
            self.db, marketplace_id
        )

        # Fallback if no mappings in DB (English aspect names)
        if not aspect_name_translations:
            aspect_name_translations = {
                "Brand": "Brand",
                "Colour": "Colour",
                "Size": "Size",
                "Material": "Material",
                "Department": "Department",
                "Style": "Style",
                "Fit": "Fit",
                "Pattern": "Pattern",
                "Neckline": "Neckline",
                "Sleeve Length": "Sleeve Length",
                "Occasion": "Occasion",
                "Type": "Type",
            }

        aspects = {}

        # Brand (universal, no translation needed)
        if product.brand:
            brand_name = aspect_name_translations.get("Brand", "Brand")
            aspects[brand_name] = [product.brand]

        # Colour - translate both name AND value (M2M, multi-value)
        if product.colors:
            colour_name = aspect_name_translations.get("Colour", "Colour")
            translated_colors = []
            for color_name_en in product.colors:
                translated = self._aspect_value_service.get_aspect_value(
                    color_name_en, "color", marketplace_id
                )
                translated_colors.append(translated or color_name_en)
            aspects[colour_name] = translated_colors

        # Size - translate both name AND value
        if product.size_original:
            size_name = aspect_name_translations.get("Size", "Size")
            translated_size = self._aspect_value_service.get_aspect_value(
                product.size_original, "size", marketplace_id
            )
            aspects[size_name] = [translated_size or product.size_original]

        # Material - translate both name AND value (M2M, multi-value)
        if product.materials:
            material_name = aspect_name_translations.get("Material", "Material")
            translated_materials = []
            for material_name_en in product.materials:
                translated = self._aspect_value_service.get_aspect_value(
                    material_name_en, "material", marketplace_id
                )
                translated_materials.append(translated or material_name_en)
            aspects[material_name] = translated_materials

        # Department - translate via gender mapping then translate value
        if product.gender:
            department_name = aspect_name_translations.get("Department", "Department")
            gb_department = self._map_gender(product.gender)  # men → Men
            translated_dept = self._aspect_value_service.translate_direct(
                gb_department, "department", marketplace_id
            )
            aspects[department_name] = [translated_dept]

        # Fit - translate both name AND value
        if product.fit:
            fit_name = aspect_name_translations.get("Fit", "Fit")
            translated_fit = self._aspect_value_service.get_aspect_value(
                product.fit, "fit", marketplace_id
            )
            aspects[fit_name] = [translated_fit or product.fit]

        # Pattern (if available on product)
        pattern = getattr(product, 'pattern', None)
        if pattern:
            pattern_name = aspect_name_translations.get("Pattern", "Pattern")
            translated_pattern = self._aspect_value_service.get_aspect_value(
                pattern, "pattern", marketplace_id
            )
            aspects[pattern_name] = [translated_pattern or pattern]

        return aspects

    def _map_gender(self, gender: str) -> str:
        """Mappe gender Stoflow → Department eBay."""
        mapping = {
            "men": "Men",
            "women": "Women",
            "unisex": "Unisex Adults",
        }
        return mapping.get(gender.lower(), "Unisex Adults")

    def _load_condition_mapping(self) -> dict[int, str]:
        """
        Load condition mapping from product_attributes.conditions table.

        Returns:
            dict: {condition_note (int): ebay_condition (str)}
        """
        conditions = self.db.query(Condition).all()
        mapping = {}

        for c in conditions:
            if c.ebay_condition:
                mapping[c.note] = c.ebay_condition

        logger.debug(f"Loaded {len(mapping)} condition mappings from DB")
        return mapping

    def _map_condition(self, condition: int | None) -> str:
        """
        Map Stoflow condition note (0-10) to eBay condition code.

        Args:
            condition: Condition note (0-10 integer scale)

        Returns:
            str: eBay condition code (e.g., "PRE_OWNED_EXCELLENT")
        """
        if condition is None:
            return "PRE_OWNED_EXCELLENT"

        ebay_condition = self._condition_map.get(condition)
        if ebay_condition:
            return ebay_condition

        logger.warning(
            f"Unknown condition note={condition} - not found in DB. "
            f"Using PRE_OWNED_EXCELLENT as fallback."
        )
        return "PRE_OWNED_EXCELLENT"

    def _get_image_urls(self, product: Product) -> List[str]:
        """
        Retrieve product image URLs for eBay listing.

        Filters out label images (internal price labels) and limits to 12
        (eBay maximum). Images ordered by 'order' field via relationship.
        """
        if not product.product_images:
            return []

        urls = [
            img.url
            for img in product.product_images
            if not img.is_label and img.url
        ]

        return urls[:12]

    def _calculate_price(self, product: Product, marketplace_id: str) -> Decimal:
        """
        Calculate final price using per-marketplace coefficient and fee.

        Formula: (base_price * coefficient) + fee

        Loads coefficient/fee from ebay_marketplace_settings.
        Falls back to 1.00 / 0.00 when no settings exist.

        Args:
            product: Product Stoflow
            marketplace_id: Marketplace (e.g. "EBAY_FR")

        Returns:
            Decimal: Final price rounded to x.90 (psychological pricing)
        """
        base_price = Decimal(str(product.price))

        # Load pricing from marketplace settings
        settings = (
            self.db.query(EbayMarketplaceSettings)
            .filter(EbayMarketplaceSettings.marketplace_id == marketplace_id)
            .first()
        )

        coefficient = Decimal(str(settings.price_coefficient)) if settings else Decimal("1.00")
        fee = Decimal(str(settings.price_fee)) if settings else Decimal("0.00")

        # Calculate price
        price = (base_price * coefficient) + fee

        # Round to x.90 (psychological pricing)
        price_rounded = int(price) + Decimal("0.90")

        return price_rounded
