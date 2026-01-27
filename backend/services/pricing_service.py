"""
Pricing Service

Core pricing engine that orchestrates all calculators and generates price levels.
Handles data fetching/generation, applies adjustments, and returns detailed breakdown.

Architecture:
- Service layer orchestrating repositories, generation, and calculators
- Fetch-or-generate pattern for BrandGroup and Model data
- Clean separation: data fetching → calculation → output
- Error handling with graceful fallbacks

Updated 2026-01-22: All coefficients now loaded from database.
Formula: PRICE = BASE_PRICE × MODEL_COEFF × CONDITION_MULT × (1 + ADJUSTMENTS)

Created: 2026-01-12
Author: Claude
"""

from decimal import Decimal, InvalidOperation
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.public.brand_group import BrandGroup
from models.public.condition import Condition
from models.public.decade import Decade
from models.public.origin import Origin
from models.public.fit import Fit
from models.public.trend import Trend
from models.public.unique_feature import UniqueFeature
from models.product_attributes.model import Model
from repositories.brand_group_repository import BrandGroupRepository
from repositories.model_repository import ModelRepository
from schemas.pricing import (
    AdjustmentBreakdown,
    AdjustmentDetail,
    ConditionDetail,
    PriceInput,
    PriceOutput,
)
from services.pricing.adjustment_calculators import (
    calculateConditionMultiplier,
    calculateDecadeAdjustment,
    calculateFeatureAdjustment,
    calculateFitAdjustment,
    calculateModelCoefficient,
    calculateOriginAdjustment,
    calculateTrendAdjustment,
)
from services.pricing.group_determination import determine_group
from services.pricing.pricing_generation_service import PricingGenerationService
from shared.exceptions import (
    BrandGroupGenerationError,
    GroupDeterminationError,
    ModelGenerationError,
    PricingCalculationError,
    PricingError,
)
from shared.logging import get_logger

logger = get_logger(__name__)


class PricingService:
    """
    Core pricing service that orchestrates the pricing algorithm.

    Responsibilities:
    - Fetch or generate BrandGroup and Model data
    - Calculate adjusted prices using all calculators
    - Generate 3 price levels (quick, standard, premium)
    - Return detailed breakdown for transparency
    """

    def __init__(
        self,
        db: Session,
        brand_group_repo: BrandGroupRepository,
        model_repo: ModelRepository,
        generation_service: PricingGenerationService,
    ):
        """
        Initialize PricingService with dependencies.

        Args:
            db: Database session
            brand_group_repo: BrandGroup repository
            model_repo: Model repository
            generation_service: LLM generation service
        """
        self.db = db
        self.brand_group_repo = brand_group_repo
        self.model_repo = model_repo
        self.generation_service = generation_service

    def _load_pricing_coefficients(self) -> dict[str, dict[str, Decimal]]:
        """
        Load pricing coefficients from database tables.

        Fetches coefficients from:
        - product_attributes.conditions (condition_coefficients by note)
        - product_attributes.origins (origin_coefficients)
        - product_attributes.decades (decade_coefficients)
        - product_attributes.trends (trend_coefficients)
        - product_attributes.unique_features (feature_coefficients)

        Returns:
            dict with keys:
            - condition_coefficients: Dict[int, Decimal] mapping note to coefficient
            - origin_coefficients: Dict[str, Decimal] mapping origin name to coefficient
            - decade_coefficients: Dict[str, Decimal] mapping decade name to coefficient
            - trend_coefficients: Dict[str, Decimal] mapping trend name to coefficient
            - feature_coefficients: Dict[str, Decimal] mapping feature name to coefficient
        """
        # Load condition coefficients (by note 0-10)
        conditions = self.db.execute(select(Condition)).scalars().all()
        condition_coefficients = {
            c.note: c.coefficient for c in conditions if c.coefficient is not None
        }

        # Load origin coefficients
        origins = self.db.execute(select(Origin)).scalars().all()
        origin_coefficients = {
            o.name_en: o.pricing_coefficient for o in origins
        }

        # Load decade coefficients
        decades = self.db.execute(select(Decade)).scalars().all()
        decade_coefficients = {
            d.name_en: d.pricing_coefficient for d in decades
        }

        # Load trend coefficients
        trends = self.db.execute(select(Trend)).scalars().all()
        trend_coefficients = {
            t.name_en: t.pricing_coefficient for t in trends
        }

        # Load feature coefficients
        features = self.db.execute(select(UniqueFeature)).scalars().all()
        feature_coefficients = {
            f.name_en: f.pricing_coefficient for f in features
        }

        # Load fit coefficients
        fits = self.db.execute(select(Fit)).scalars().all()
        fit_coefficients = {
            f.name_en: f.pricing_coefficient for f in fits
        }

        logger.debug(
            f"[PricingService] Loaded pricing coefficients: "
            f"{len(condition_coefficients)} conditions, "
            f"{len(origin_coefficients)} origins, "
            f"{len(decade_coefficients)} decades, "
            f"{len(trend_coefficients)} trends, "
            f"{len(feature_coefficients)} features, "
            f"{len(fit_coefficients)} fits"
        )

        return {
            "condition_coefficients": condition_coefficients,
            "origin_coefficients": origin_coefficients,
            "decade_coefficients": decade_coefficients,
            "trend_coefficients": trend_coefficients,
            "feature_coefficients": feature_coefficients,
            "fit_coefficients": fit_coefficients,
        }

    @staticmethod
    def _build_single_detail(
        actual_value: Optional[str],
        expected_values: list[str],
        coefficients: dict[str, Decimal],
    ) -> AdjustmentDetail:
        """Build detail for single-value adjustments (origin, decade, fit)."""
        actual_coef = Decimal("0.00")
        if actual_value and actual_value.strip():
            actual_coef = coefficients.get(actual_value, Decimal("0.00"))

        expected_coef = Decimal("0.00")
        expected_best = None
        if expected_values:
            best_coef = Decimal("-999")
            for val in expected_values:
                c = coefficients.get(val, Decimal("0.00"))
                if c > best_coef:
                    best_coef = c
                    expected_best = val
            expected_coef = best_coef if best_coef > Decimal("-999") else Decimal("0.00")

        return AdjustmentDetail(
            actual_value=actual_value if actual_value and actual_value.strip() else None,
            actual_coef=actual_coef,
            expected_values=expected_values,
            expected_best=expected_best,
            expected_coef=expected_coef,
        )

    @staticmethod
    def _build_list_detail(
        actual_values: list[str],
        expected_values: list[str],
        coefficients: dict[str, Decimal],
    ) -> AdjustmentDetail:
        """Build detail for list-value adjustments (trend, feature)."""
        actual_coef = Decimal("0.00")
        actual_best = None
        if actual_values:
            best_coef = Decimal("-999")
            for val in actual_values:
                if val in coefficients:
                    c = coefficients[val]
                    if c > best_coef:
                        best_coef = c
                        actual_best = val
            actual_coef = best_coef if best_coef > Decimal("-999") else Decimal("0.00")

        expected_coef = Decimal("0.00")
        expected_best = None
        if expected_values:
            best_coef = Decimal("-999")
            for val in expected_values:
                if val in coefficients:
                    c = coefficients[val]
                    if c > best_coef:
                        best_coef = c
                        expected_best = val
            expected_coef = best_coef if best_coef > Decimal("-999") else Decimal("0.00")

        return AdjustmentDetail(
            actual_value=actual_best,
            actual_coef=actual_coef,
            expected_values=expected_values,
            expected_best=expected_best,
            expected_coef=expected_coef,
        )

    async def fetch_or_generate_pricing_data(
        self,
        brand: str,
        category: str,
        materials: list[str],
        model_name: Optional[str] = None,
    ) -> dict:
        """
        Fetch or generate BrandGroup and Model data for pricing.

        This method implements the fetch-or-generate pattern:
        1. Determine group from category and materials
        2. Fetch BrandGroup from DB, generate if missing
        3. If model_name provided: fetch Model from DB, generate if missing
        4. Return pricing data with base_price and model_coeff

        Args:
            brand: Brand name
            category: Product category
            materials: List of product materials
            model_name: Optional model name

        Returns:
            dict with keys:
            - base_price: Decimal
            - model_coeff: Decimal
            - brand_group: BrandGroup
            - model: Optional[Model]
            - group: str

        Raises:
            GroupDeterminationError: If group cannot be determined
            BrandGroupGenerationError: If BrandGroup generation fails
            ModelGenerationError: If Model generation fails
        """
        # Step 1: Determine group
        try:
            group = determine_group(category, materials)
        except ValueError as e:
            logger.error(
                f"[PricingService] Group determination failed: {e}",
                extra={
                    "category": category,
                    "materials": materials
                }
            )
            raise GroupDeterminationError(category, materials) from e

        logger.info(
            f"[PricingService] Pricing data request: "
            f"brand={brand}, group={group}, model_name={model_name}"
        )

        # Step 2: Fetch or generate BrandGroup
        brand_group = self.brand_group_repo.get_by_brand_and_group(self.db, brand, group)

        if brand_group is None:
            logger.info(
                f"[PricingService] BrandGroup not found for {brand} + {group}, generating..."
            )
            try:
                result = await self.generation_service.generate_brand_group(
                    brand, group
                )
                # Save to DB (extract BrandGroup from GenerationResult)
                brand_group = self.brand_group_repo.create(self.db, result.brand_group)
                self.db.commit()
                logger.info(
                    f"[PricingService] BrandGroup generated and saved: "
                    f"{brand} + {group}, base_price={brand_group.base_price}"
                )
            except Exception as e:
                self.db.rollback()
                logger.error(
                    f"[PricingService] Failed to generate BrandGroup: {e}",
                    exc_info=True,
                    extra={
                        "brand": brand,
                        "group": group
                    }
                )
                raise BrandGroupGenerationError(brand, group, str(e)) from e

        # Extract base_price
        base_price = brand_group.base_price

        # Step 3: Fetch or generate Model (if model_name provided)
        model = None
        model_coeff = Decimal("1.0")  # Default coefficient if no model

        if model_name:
            model = self.model_repo.get_by_brand_group_and_name(
                self.db, brand, group, model_name
            )

            if model is None:
                logger.info(
                    f"[PricingService] Model not found for {brand} + {group} + {model_name}, generating..."
                )
                try:
                    model = await self.generation_service.generate_model(
                        brand, group, model_name, base_price
                    )
                    # Save to DB
                    model = self.model_repo.create(self.db, model)
                    self.db.commit()
                    logger.info(
                        f"[PricingService] Model generated and saved: "
                        f"{brand} + {group} + {model_name}, coefficient={model.coefficient}"
                    )
                except Exception as e:
                    self.db.rollback()
                    logger.error(
                        f"[PricingService] Failed to generate Model: {e}",
                        exc_info=True,
                        extra={
                            "brand": brand,
                            "group": group,
                            "model": model_name
                        }
                    )
                    raise ModelGenerationError(brand, group, model_name, str(e)) from e

            # Extract coefficient
            model_coeff = model.coefficient

        logger.info(
            f"[PricingService] Pricing data ready: "
            f"base_price={base_price}, model_coeff={model_coeff}"
        )

        return {
            "base_price": base_price,
            "model_coeff": model_coeff,
            "brand_group": brand_group,
            "model": model,
            "group": group,
        }

    async def calculate_price(self, input_data: PriceInput) -> PriceOutput:
        """
        Calculate adjusted price with all calculators and 3 price levels.

        Formula: PRICE = BASE_PRICE × MODEL_COEFF × CONDITION_MULT × (1 + ADJUSTMENTS)
        Where ADJUSTMENTS = origin + decade + trend + feature

        3 price levels:
        - Quick: PRICE × 0.75
        - Standard: PRICE × 1.0
        - Premium: PRICE × 1.30

        Args:
            input_data: PriceInput with all product attributes and adjustment parameters

        Returns:
            PriceOutput: Complete pricing data with 3 levels and detailed breakdown

        Raises:
            GroupDeterminationError: If group cannot be determined
            BrandGroupGenerationError: If BrandGroup generation fails
            ModelGenerationError: If Model generation fails
            PricingCalculationError: If calculation fails
        """
        try:
            logger.info(
                f"[PricingService] Calculate price request: "
                f"brand={input_data.brand}, category={input_data.category}, "
                f"model={input_data.model_name}"
            )

            # Step 1: Fetch or generate pricing data
            pricing_data = await self.fetch_or_generate_pricing_data(
                brand=input_data.brand,
                category=input_data.category,
                materials=input_data.materials,
                model_name=input_data.model_name,
            )

            base_price = pricing_data["base_price"]
            brand_group = pricing_data["brand_group"]
            model = pricing_data["model"]
            group = pricing_data["group"]

            # Step 2: Calculate model coefficient
            if model:
                model_coeff = calculateModelCoefficient(model)
            else:
                model_coeff = Decimal("1.0")

            # Step 3: Load pricing coefficients from database
            coefficients = self._load_pricing_coefficients()

            # Step 4: Calculate condition multiplier and all adjustments
            try:
                # Get condition coefficient from DB (based on condition_score as note)
                condition_coefficient = coefficients["condition_coefficients"].get(
                    input_data.condition_score, Decimal("1.0")
                )
                condition_mult = calculateConditionMultiplier(condition_coefficient)

                # Calculate other adjustments
                origin_adj = calculateOriginAdjustment(
                    input_data.actual_origin,
                    input_data.expected_origins or brand_group.expected_origins,
                    coefficients["origin_coefficients"],
                )

                decade_adj = calculateDecadeAdjustment(
                    input_data.actual_decade,
                    input_data.expected_decades or brand_group.expected_decades,
                    coefficients["decade_coefficients"],
                )

                trend_adj = calculateTrendAdjustment(
                    input_data.actual_trends,
                    input_data.expected_trends or brand_group.expected_trends,
                    coefficients["trend_coefficients"],
                )

                # For feature adjustment, use expected_features from Model if input is empty
                expected_features = input_data.expected_features
                if model and not expected_features:  # Empty list or None
                    expected_features = model.expected_features or []

                feature_adj = calculateFeatureAdjustment(
                    input_data.actual_features,
                    expected_features,
                    coefficients["feature_coefficients"],
                )

                # Calculate fit adjustment
                fit_adj = calculateFitAdjustment(
                    input_data.actual_fit,
                    input_data.expected_fits or [],
                    coefficients["fit_coefficients"],
                )
            except (ValueError, KeyError, InvalidOperation) as e:
                logger.error(
                    f"[PricingService] Adjustment calculation failed: {e}",
                    exc_info=True,
                    extra={
                        "brand": input_data.brand,
                        "category": input_data.category,
                        "model": input_data.model_name
                    }
                )
                raise PricingCalculationError(f"Failed to calculate adjustments: {str(e)}") from e

            # Step 5: Apply formula and calculate prices
            # PRICE = BASE_PRICE × MODEL_COEFF × CONDITION_MULT × (1 + ADJUSTMENTS)
            try:
                total_adjustment = origin_adj + decade_adj + trend_adj + feature_adj + fit_adj
                adjusted_price = base_price * model_coeff * condition_mult * (1 + total_adjustment)

                # Step 6: Calculate 3 price levels with quantization
                quick_price = (adjusted_price * Decimal("0.75")).quantize(Decimal("0.01"))
                standard_price = adjusted_price.quantize(Decimal("0.01"))
                premium_price = (adjusted_price * Decimal("1.30")).quantize(Decimal("0.01"))
            except (InvalidOperation, OverflowError) as e:
                logger.error(
                    f"[PricingService] Price calculation failed: {e}",
                    exc_info=True,
                    extra={
                        "base_price": str(base_price),
                        "model_coeff": str(model_coeff),
                        "condition_mult": str(condition_mult),
                        "total_adjustment": str(total_adjustment) if 'total_adjustment' in locals() else "N/A"
                    }
                )
                raise PricingCalculationError(f"Failed to calculate final prices: {str(e)}") from e

            logger.info(
                f"[PricingService] Price calculated: "
                f"quick={quick_price}, standard={standard_price}, premium={premium_price}, "
                f"base={base_price}, model_coeff={model_coeff}, condition_mult={condition_mult}, "
                f"total_adj={total_adjustment}"
            )

            # Step 7: Build detail objects for each adjustment
            condition_as_adjustment = condition_mult - Decimal("1.0")

            origin_detail = self._build_single_detail(
                input_data.actual_origin,
                input_data.expected_origins or brand_group.expected_origins,
                coefficients["origin_coefficients"],
            )
            decade_detail = self._build_single_detail(
                input_data.actual_decade,
                input_data.expected_decades or brand_group.expected_decades,
                coefficients["decade_coefficients"],
            )
            trend_detail = self._build_list_detail(
                input_data.actual_trends,
                input_data.expected_trends or brand_group.expected_trends,
                coefficients["trend_coefficients"],
            )
            feature_detail = self._build_list_detail(
                input_data.actual_features,
                expected_features,
                coefficients["feature_coefficients"],
            )
            fit_detail = self._build_single_detail(
                input_data.actual_fit,
                input_data.expected_fits or [],
                coefficients["fit_coefficients"],
            )

            # Step 8: Build output
            return PriceOutput(
                # Price levels
                quick_price=quick_price,
                standard_price=standard_price,
                premium_price=premium_price,
                # Breakdown
                base_price=base_price,
                model_coefficient=model_coeff,
                condition_multiplier=condition_mult,
                adjustments=AdjustmentBreakdown(
                    condition=condition_as_adjustment,
                    origin=origin_adj,
                    decade=decade_adj,
                    trend=trend_adj,
                    feature=feature_adj,
                    fit=fit_adj,
                    total=condition_as_adjustment + total_adjustment,
                    # Detailed calculation steps
                    condition_detail=ConditionDetail(
                        score=input_data.condition_score,
                        multiplier=condition_mult,
                    ),
                    origin_detail=origin_detail,
                    decade_detail=decade_detail,
                    trend_detail=trend_detail,
                    feature_detail=feature_detail,
                    fit_detail=fit_detail,
                ),
                # Metadata
                brand=input_data.brand,
                group=group,
                model_name=input_data.model_name,
            )

        except PricingError:
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            # Catch any unexpected errors
            logger.error(
                f"[PricingService] Unexpected error in calculate_price: {e}",
                exc_info=True,
                extra={
                    "brand": input_data.brand,
                    "category": input_data.category,
                    "model": input_data.model_name
                }
            )
            raise PricingCalculationError(f"Unexpected error during price calculation: {str(e)}") from e
