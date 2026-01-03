"""
eBay Product Conversion Service (MVP).

Convertit un Product Stoflow vers le format eBay (Inventory Item + Offer).

Cette version MVP fournit les fonctionnalités essentielles:
- Conversion Product → eBay Inventory Item
- Création Offer avec pricing basique
- Aspects eBay basiques (Brand, Colour, Size, Condition)
- Support multi-marketplace (pricing coefficient par marketplace)

TODO (prochaines versions):
- SEO multilingue (titres optimisés par marketplace)
- Aspects avancés (Type, Style, Department, etc.)
- Best Offer automatique
- Promoted Listings

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
from models.public.platform_mapping import Platform, PlatformMapping
from models.user.product import Product
from services.ebay.ebay_aspect_value_service import (
    EbayAspectValueService,
    get_aspect_value_service,
)
from services.ebay.ebay_mapper import EbayMapper
from shared.exceptions import ProductValidationError
from shared.logging_setup import get_logger

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

        # Charger platform_mapping pour pricing
        self.platform_mapping = (
            db.query(PlatformMapping)
            .filter(
                PlatformMapping.user_id == user_id,
                PlatformMapping.platform == Platform.EBAY,
            )
            .first()
        )

        if not self.platform_mapping:
            raise ValueError(f"User {user_id} n'a pas de configuration eBay")

        # Load condition mapping from DB (condition_name → ebay_condition)
        self._condition_map = self._load_condition_mapping()

        # Initialize aspect value service for multilingual translations
        self._aspect_value_service = get_aspect_value_service(db)

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

        # Construire title (simple pour MVP)
        title = self._build_title(product)

        # Construire description (simple pour MVP)
        description = self._build_description(product)

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

        if not product.condition:
            raise ProductValidationError("Product.condition est requis")

        # Validation images (eBay exige au moins 1 image)
        image_urls = self._get_image_urls(product)
        if not image_urls or len(image_urls) == 0:
            raise ProductValidationError(
                "Au moins 1 image est requise pour publier sur eBay. "
                "Veuillez ajouter des images à votre produit."
            )

    def _build_title(self, product: Product) -> str:
        """
        Construit le titre eBay (80 caractères max).

        MVP: Simple concatenation Brand + Title.
        TODO: SEO multilingue via EbaySeoService.
        """
        parts = []

        if product.brand:
            parts.append(product.brand)

        if product.title:
            parts.append(product.title)

        title = " ".join(parts)

        # Limiter à 80 caractères
        if len(title) > 80:
            title = title[:77] + "..."

        return title

    def _build_description(self, product: Product) -> str:
        """
        Construit la description eBay (HTML).

        MVP: Description simple en texte.
        TODO: HTML formaté multilingue via generate_ebay_description_multilang.
        """
        description = f"<p>{product.description or 'No description'}</p>"

        # Ajouter condition supplémentaire si présente (JSONB array)
        if product.condition_sup:
            condition_details = ", ".join(product.condition_sup) if isinstance(product.condition_sup, list) else str(product.condition_sup)
            description += f"<p><strong>Condition:</strong> {condition_details}</p>"

        return description

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

        # Colour - translate both name AND value
        if product.color:
            colour_name = aspect_name_translations.get("Colour", "Colour")
            translated_color = self._aspect_value_service.get_aspect_value(
                product.color, "color", marketplace_id
            )
            aspects[colour_name] = [translated_color or product.color]

        # Size - translate both name AND value
        if product.size_original:
            size_name = aspect_name_translations.get("Size", "Size")
            translated_size = self._aspect_value_service.get_aspect_value(
                product.size_original, "size", marketplace_id
            )
            aspects[size_name] = [translated_size or product.size_original]

        # Material - translate both name AND value
        if product.material:
            material_name = aspect_name_translations.get("Material", "Material")
            translated_material = self._aspect_value_service.get_aspect_value(
                product.material, "material", marketplace_id
            )
            aspects[material_name] = [translated_material or product.material]

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

    def _load_condition_mapping(self) -> dict[str, str]:
        """
        Charge le mapping conditions depuis la table product_attributes.conditions.

        Returns:
            dict: {condition_name.lower(): ebay_condition}

        Examples:
            >>> mapping = service._load_condition_mapping()
            >>> mapping.get('new')
            'NEW'
            >>> mapping.get('excellent')
            'PRE_OWNED_EXCELLENT'
        """
        conditions = self.db.query(Condition).all()
        mapping = {}

        for c in conditions:
            if c.name and c.ebay_condition:
                # Store with lowercase key for case-insensitive lookup
                mapping[c.name.lower()] = c.ebay_condition

                # Also add description variants for multi-language support
                for lang in ['en', 'fr', 'de', 'it', 'es', 'nl', 'pl']:
                    desc = getattr(c, f'description_{lang}', None)
                    if desc:
                        mapping[desc.lower()] = c.ebay_condition

        logger.debug(f"Loaded {len(mapping)} condition mappings from DB")
        return mapping

    def _map_condition(self, condition: str) -> str:
        """
        Mappe condition Stoflow → condition eBay via la table DB.

        Uses the product_attributes.conditions table for mapping.

        Args:
            condition: Condition name from Product (e.g., "Excellent", "New")

        Returns:
            str: eBay condition code (e.g., "PRE_OWNED_EXCELLENT", "NEW")

        eBay conditions:
        - NEW, NEW_WITH_TAGS, NEW_WITHOUT_TAGS, NEW_WITH_DEFECTS
        - PRE_OWNED_EXCELLENT, PRE_OWNED_GOOD, PRE_OWNED_FAIR
        - USED_EXCELLENT, USED_VERY_GOOD, USED_GOOD, USED_ACCEPTABLE
        """
        if not condition:
            return "PRE_OWNED_EXCELLENT"  # Safe default

        condition_lower = condition.lower().strip()

        # Lookup in DB mapping
        ebay_condition = self._condition_map.get(condition_lower)
        if ebay_condition:
            return ebay_condition

        # Fallback: log warning and return safe default
        logger.warning(
            f"Unknown condition '{condition}' - not found in DB. "
            f"Using PRE_OWNED_EXCELLENT as fallback."
        )
        return "PRE_OWNED_EXCELLENT"

    def _get_image_urls(self, product: Product) -> List[str]:
        """
        Récupère les URLs des images du produit.

        Returns:
            Liste de URLs publiques (12 max pour eBay)
        """
        # TODO: Récupérer depuis product_images table
        # Pour MVP, parser le champ product.images si JSON
        import json

        if product.images:
            try:
                images = json.loads(product.images)
                if isinstance(images, list):
                    return images[:12]  # eBay limite à 12 images
            except Exception:
                pass

        return []

    def _calculate_price(self, product: Product, marketplace_id: str) -> Decimal:
        """
        Calcule le prix final avec coefficient + fees marketplace.

        Formula: (base_price × coefficient) + fees

        Args:
            product: Product Stoflow
            marketplace_id: Marketplace (ex: "EBAY_FR")

        Returns:
            Decimal: Prix final arrondi à 0.90 (pricing psychologique)
        """
        base_price = Decimal(str(product.price))

        # Récupérer coefficient + fees selon marketplace
        coef_attr = f"ebay_price_coefficient_{marketplace_id.split('_')[1].lower()}"
        fee_attr = f"ebay_price_fee_{marketplace_id.split('_')[1].lower()}"

        coefficient = getattr(self.platform_mapping, coef_attr, Decimal("1.00"))
        fee = getattr(self.platform_mapping, fee_attr, Decimal("0.00"))

        # Calculer prix
        price = (base_price * coefficient) + fee

        # Arrondir à x.90 (pricing psychologique)
        price_rounded = int(price) + Decimal("0.90")

        return price_rounded
