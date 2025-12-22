"""
Pricing Service

Service pour calcul automatique de prix selon brand, category, condition, rarity, quality.

Business Rules (2025-12-08):
- Formule: prix_final = base_price × coeff_condition × coeff_rarity × coeff_quality
- Prix minimum: 5€, arrondi: 0.50€
- Compatible avec PostEditFlet logic (adjust_price)

Author: Claude
Date: 2025-12-08
"""

from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from models.public.clothing_price import ClothingPrice
from models.public.condition import Condition
from shared.logging_setup import get_logger

logger = get_logger(__name__)


class PricingService:
    """Service pour calcul automatique de prix."""

    # Coefficients de rareté
    RARITY_COEFFICIENTS = {
        "Rare": 1.3,
        "Vintage": 1.2,
        "Common": 1.0,
        "Standard": 1.0,
    }

    # Coefficients de qualité
    QUALITY_COEFFICIENTS = {
        "Premium": 1.2,
        "Good": 1.0,
        "Average": 0.8,
        "Standard": 1.0,
    }

    # Prix par défaut si non trouvé
    DEFAULT_BASE_PRICE = Decimal("30.00")

    # Prix minimum (Business Rule)
    MIN_PRICE = Decimal("5.00")

    # Arrondi (Business Rule: 0.50€)
    ROUND_TO = Decimal("0.50")

    @staticmethod
    def calculate_price(
        db: Session,
        brand: Optional[str],
        category: str,
        condition: str,
        rarity: Optional[str] = None,
        quality: Optional[str] = None,
    ) -> Decimal:
        """
        Calcule le prix automatiquement selon les attributs produit.

        Business Rules (2025-12-08):
        - Prix = base_price × coeff_condition × coeff_rarity × coeff_quality
        - Prix minimum: 5€
        - Arrondi: 0.50€ (ex: 24.30€ → 24.50€)
        - Si base_price non trouvé → DEFAULT_BASE_PRICE (30€)

        Args:
            db: Session SQLAlchemy
            brand: Marque (ex: "Levi's")
            category: Catégorie (ex: "Jeans")
            condition: État (ex: "EXCELLENT", "GOOD", etc.)
            rarity: Rareté (ex: "Rare", "Vintage", "Common")
            quality: Qualité (ex: "Premium", "Good", "Average")

        Returns:
            Decimal: Prix final calculé et arrondi

        Examples:
            >>> price = PricingService.calculate_price(db, "Levi's", "Jeans", "EXCELLENT")
            >>> print(price)
            Decimal('45.00')

            >>> price = PricingService.calculate_price(
            ...     db, "Diesel", "Jeans", "GOOD", rarity="Vintage", quality="Premium"
            ... )
            >>> print(price)  # 80 * 0.9 * 1.2 * 1.2 = 103.68 → 104.00
            Decimal('104.00')
        """
        logger.debug(
            f"[PricingService] Calculating price: brand={brand}, category={category}, "
            f"condition={condition}, rarity={rarity}, quality={quality}"
        )

        # 1. Récupérer prix de base depuis DB
        base_price = PricingService._get_base_price(db, brand, category)

        # 2. Récupérer coefficient condition depuis DB
        coeff_condition = PricingService._get_condition_coefficient(db, condition)

        # 3. Récupérer coefficient rareté
        coeff_rarity = PricingService.RARITY_COEFFICIENTS.get(rarity or "Standard", 1.0)

        # 4. Récupérer coefficient qualité
        coeff_quality = PricingService.QUALITY_COEFFICIENTS.get(quality or "Standard", 1.0)

        # 5. Calcul prix final
        price = base_price * Decimal(str(coeff_condition)) * Decimal(str(coeff_rarity)) * Decimal(str(coeff_quality))

        # 6. Appliquer minimum
        if price < PricingService.MIN_PRICE:
            price = PricingService.MIN_PRICE

        # 7. Arrondir à 0.50€
        price = PricingService._round_to_nearest(price, PricingService.ROUND_TO)

        logger.debug(
            f"[PricingService] Price calculated: {price} EUR "
            f"(base={base_price}, cond={coeff_condition}, "
            f"rarity={coeff_rarity}, qual={coeff_quality})"
        )

        return price

    @staticmethod
    def _get_base_price(db: Session, brand: Optional[str], category: str) -> Decimal:
        """
        Récupère le prix de base depuis la table clothing_prices.

        Args:
            db: Session SQLAlchemy
            brand: Marque
            category: Catégorie

        Returns:
            Decimal: Prix de base (ou DEFAULT_BASE_PRICE si non trouvé)
        """
        if not brand:
            return PricingService.DEFAULT_BASE_PRICE

        # Query la table clothing_prices
        clothing_price = (
            db.query(ClothingPrice)
            .filter(ClothingPrice.brand == brand, ClothingPrice.category == category)
            .first()
        )

        if clothing_price:
            return clothing_price.base_price

        # Si non trouvé, retourner prix par défaut
        return PricingService.DEFAULT_BASE_PRICE

    @staticmethod
    def _get_condition_coefficient(db: Session, condition: str) -> float:
        """
        Récupère le coefficient de condition depuis la table conditions.

        Args:
            db: Session SQLAlchemy
            condition: Note condition (0-10, ex: 0=neuf, 5=bon état)

        Returns:
            float: Coefficient (ex: 1.0 pour neuf, 0.9 pour bon état)
        """
        condition_obj = db.query(Condition).filter(Condition.note == condition).first()

        if condition_obj and condition_obj.coefficient:
            return float(condition_obj.coefficient)

        # Fallback si non trouvé
        return 1.0

    @staticmethod
    def _round_to_nearest(value: Decimal, round_to: Decimal) -> Decimal:
        """
        Arrondit à la valeur la plus proche.

        Business Rule: Arrondir à 0.50€ (ex: 24.30€ → 24.50€, 24.70€ → 25.00€)

        Args:
            value: Valeur à arrondir
            round_to: Increment d'arrondi (ex: 0.50)

        Returns:
            Decimal: Valeur arrondie

        Examples:
            >>> PricingService._round_to_nearest(Decimal("24.30"), Decimal("0.50"))
            Decimal('24.50')

            >>> PricingService._round_to_nearest(Decimal("24.70"), Decimal("0.50"))
            Decimal('25.00')
        """
        return (value / round_to).quantize(Decimal("1")) * round_to
