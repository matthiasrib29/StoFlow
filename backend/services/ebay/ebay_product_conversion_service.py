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
from models.public.ebay_marketplace_config import MarketplaceConfig
from models.public.platform_mapping import Platform, PlatformMapping
from models.user.product import Product
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
                        Si None, utilise une catégorie générique

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
        Updated: 2025-12-10 - Fix categoryId fallback dangereux
        """
        # Validation: category_id requis
        if not category_id:
            raise ProductValidationError(
                "category_id est requis pour créer une offer eBay. "
                "Veuillez spécifier l'ID de catégorie eBay appropriée. "
                "Exemple: '11450' pour T-shirts homme, '15687' pour Jeans femme. "
                "Utilisez eBay Taxonomy API pour trouver la bonne catégorie."
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
            "categoryId": category_id,  # Requis - pas de fallback
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

        # Ajouter condition supplémentaire si présente
        if product.condition_sup:
            description += f"<p><strong>Condition:</strong> {product.condition_sup}</p>"

        return description

    def _build_aspects(
        self, product: Product, marketplace_id: str
    ) -> Dict[str, List[str]]:
        """
        Construit les aspects eBay avec traduction multilingue.

        Utilise la table aspect_mappings pour traduire les noms d'aspects
        dans la langue du marketplace (ex: "Colour" → "Couleur" pour EBAY_FR).

        Args:
            product: Product Stoflow
            marketplace_id: Marketplace (ex: "EBAY_FR")

        Returns:
            Dict {aspect_name_localized: [values]}

        Author: Claude
        Date: 2025-12-10
        Updated: 2025-12-10 - Ajout traductions multilingues via aspect_mappings
        """
        # Charger les mappings d'aspects pour cette marketplace
        aspect_translations = AspectMapping.get_all_for_marketplace(
            self.db, marketplace_id
        )

        # Fallback si pas de mappings en DB (aspects en anglais)
        if not aspect_translations:
            aspect_translations = {
                "Brand": "Brand",
                "Colour": "Colour",
                "Size": "Size",
                "Material": "Material",
                "Department": "Department",
                "Style": "Style",
            }

        aspects = {}

        # Brand (toujours en anglais, universel)
        if product.brand:
            brand_name = aspect_translations.get("Brand", "Brand")
            aspects[brand_name] = [product.brand]

        # Colour
        if product.color:
            colour_name = aspect_translations.get("Colour", "Colour")
            aspects[colour_name] = [product.color]

        # Size
        if product.label_size:
            size_name = aspect_translations.get("Size", "Size")
            aspects[size_name] = [product.label_size]

        # Material
        if product.material:
            material_name = aspect_translations.get("Material", "Material")
            aspects[material_name] = [product.material]

        # Gender (Department)
        if product.gender:
            department_name = aspect_translations.get("Department", "Department")
            aspects[department_name] = [self._map_gender(product.gender)]

        # Style (si fit disponible)
        if product.fit:
            style_name = aspect_translations.get("Style", "Style")
            aspects[style_name] = [product.fit]

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
