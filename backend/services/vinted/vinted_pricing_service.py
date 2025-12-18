"""
Vinted Pricing Service

Service de calcul de prix pour Vinted avec règles spécifiques.

Business Rules (2024-12-10):
- Prix Vinted = prix_base × 1.10 (marge de négociation)
- Arrondi psychologique: x.90 (ex: 25.30€ → 25.90€, 27.83€ → 27.90€)
- Prix minimum: 1.00€ (requis par validation API Vinted)
- Si prix < 1.00€ → ValueError (produit non publiable)

Architecture:
- Utilise le PricingService global pour calculer le prix de base
- Applique ensuite les règles spécifiques Vinted
- Pas d'accès DB direct (via PricingService)

Created: 2024-12-10
Author: Claude
"""

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

from services.pricing_service import PricingService

if TYPE_CHECKING:
    from models.user.product import Product


class VintedPricingService:
    """
    Service de calcul de prix pour Vinted.
    
    Applique les règles spécifiques Vinted:
    - +10% pour marge de négociation
    - Arrondi psychologique x.90
    - Minimum 1.00€
    """

    # Coefficient Vinted: +10% pour marge de négociation
    VINTED_MARKUP = Decimal("1.10")

    # Prix minimum Vinted (requis par API)
    MIN_VINTED_PRICE = Decimal("1.00")

    @staticmethod
    def calculate_vinted_price(db: Session, product: "Product") -> Decimal:
        """
        Calcule le prix de vente Vinted pour un produit.

        Workflow:
        1. Calcul prix de base via PricingService global
        2. Application coefficient +10% (marge de négociation)
        3. Arrondi psychologique x.90
        4. Vérification minimum 1.00€

        Args:
            db: Session SQLAlchemy
            product: Instance de Product avec attributs requis

        Returns:
            Decimal: Prix Vinted arrondi

        Raises:
            ValueError: Si prix final < 1.00€ (non publiable sur Vinted)

        Examples:
            >>> product = Product(brand="Levi's", category="Jeans", condition="EXCELLENT")
            >>> price = VintedPricingService.calculate_vinted_price(db, product)
            >>> print(price)  # Ex: 45.00€ base → 49.50€ → 49.90€
            Decimal('49.90')

            >>> product = Product(brand="NoName", category="T-shirt", condition="FAIR", price=0.50)
            >>> VintedPricingService.calculate_vinted_price(db, product)
            ValueError: Prix calculé incohérent: 0.55€ < 1.00€ minimum Vinted
        """
        # 1. Calculer prix de base via PricingService global
        base_price = PricingService.calculate_price(
            db=db,
            brand=product.brand,
            category=product.category,
            condition=product.condition,
            rarity=getattr(product, 'rarity', None),
            quality=getattr(product, 'quality', None)
        )

        # 2. Appliquer coefficient Vinted (+10%)
        vinted_price = base_price * VintedPricingService.VINTED_MARKUP

        # 3. Arrondir à x.90 (prix psychologique)
        vinted_price = VintedPricingService._round_to_psychological(vinted_price)

        # 4. Vérifier minimum Vinted (1.00€)
        if vinted_price < VintedPricingService.MIN_VINTED_PRICE:
            raise ValueError(
                f"Prix calculé incohérent: {vinted_price}€ < 1.00€ minimum Vinted. "
                f"Produit non publiable (brand={product.brand}, category={product.category}, "
                f"condition={product.condition}, base_price={base_price}€)"
            )

        return vinted_price

    @staticmethod
    def _round_to_psychological(price: Decimal) -> Decimal:
        """
        Arrondit au prix psychologique x.90.

        Business Rule:
        - Arrondir à l'entier inférieur + 0.90
        - Ex: 27.83€ → 27.90€
        - Ex: 49.50€ → 49.90€
        - Ex: 20.00€ → 20.90€

        Args:
            price: Prix à arrondir

        Returns:
            Decimal: Prix arrondi à x.90

        Examples:
            >>> VintedPricingService._round_to_psychological(Decimal("27.83"))
            Decimal('27.90')

            >>> VintedPricingService._round_to_psychological(Decimal("49.50"))
            Decimal('49.90')

            >>> VintedPricingService._round_to_psychological(Decimal("20.00"))
            Decimal('20.90')
        """
        # Arrondir à l'entier inférieur
        integer_part = int(price)

        # Ajouter 0.90
        return Decimal(f"{integer_part}.90")

    @staticmethod
    def calculate_price_without_base(base_price: Decimal) -> Decimal:
        """
        Calcule le prix Vinted depuis un prix de base donné.

        Utile pour recalculer rapidement un prix sans repasser par PricingService.

        Args:
            base_price: Prix de base en euros

        Returns:
            Decimal: Prix Vinted (+10%, arrondi x.90)

        Examples:
            >>> VintedPricingService.calculate_price_without_base(Decimal("25.00"))
            Decimal('27.90')

            >>> VintedPricingService.calculate_price_without_base(Decimal("50.00"))
            Decimal('55.90')
        """
        vinted_price = base_price * VintedPricingService.VINTED_MARKUP
        return VintedPricingService._round_to_psychological(vinted_price)
