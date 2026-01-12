"""
Pricing API Routes

REST API endpoint for price calculation using the pricing algorithm.

Architecture:
- Service layer pattern: route delegates to PricingService
- Dependency injection for DB session + authentication
- Proper error handling (ValueError → 400, ServiceError → 500)
- Multi-tenant isolation via get_user_db()

Created: 2026-01-12
Author: Claude
"""

import time

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.dependencies import get_current_user, get_user_db
from models.public.user import User
from repositories.brand_group_repository import BrandGroupRepository
from repositories.model_repository import ModelRepository
from schemas.pricing import PriceInput, PriceOutput
from services.pricing.pricing_generation_service import PricingGenerationService
from services.pricing_service import PricingService
from shared.exceptions import (
    BrandGroupGenerationError,
    GroupDeterminationError,
    ModelGenerationError,
    PricingCalculationError,
)
from shared.logging_setup import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/pricing", tags=["Pricing"])


@router.post(
    "/calculate",
    response_model=PriceOutput,
    status_code=status.HTTP_200_OK,
    summary="Calculate product price with 3 levels",
    description="Orchestrates all pricing calculators to generate quick/standard/premium prices with detailed breakdown"
)
async def calculate_price(
    input: PriceInput,
    db_user: tuple[Session, User] = Depends(get_user_db),
    current_user: User = Depends(get_current_user)
) -> PriceOutput:
    """
    Calculate product price using pricing algorithm.

    Fetches/generates BrandGroup and Model data, applies all 6 adjustment calculators,
    returns 3 price levels (quick/standard/premium) with detailed breakdown.

    Args:
        input: PriceInput with product attributes and adjustment parameters
        db_user: Database session with user schema set
        current_user: Authenticated user

    Returns:
        PriceOutput with 3 price levels and adjustment breakdown

    Raises:
        HTTPException 400: Invalid input data or group determination failure
        HTTPException 500: Service error (LLM failure, DB error)
        HTTPException 504: Timeout during LLM generation
    """
    db, user = db_user
    start_time = time.time()

    logger.info(
        "[API:pricing] Pricing calculation request",
        extra={
            "user_id": user.id,
            "brand": input.brand,
            "category": input.category,
            "model": input.model_name
        }
    )

    # Create pricing service
    # Note: Repositories and generation service use static methods
    pricing_service = PricingService(
        db=db,
        brand_group_repo=BrandGroupRepository,
        model_repo=ModelRepository,
        generation_service=PricingGenerationService
    )

    try:
        # Calculate price
        result = await pricing_service.calculate_price(input)

        # Log success with performance metrics
        elapsed_time = time.time() - start_time
        logger.info(
            "[API:pricing] Pricing calculation successful",
            extra={
                "user_id": user.id,
                "brand": input.brand,
                "elapsed_time_ms": round(elapsed_time * 1000, 2),
                "standard_price": str(result.standard_price)
            }
        )

        return result

    except GroupDeterminationError as e:
        # Invalid category/materials combination
        elapsed_time = time.time() - start_time
        logger.warning(
            f"[API:pricing] Group determination failed: {e}",
            extra={
                "user_id": user.id,
                "category": e.category,
                "materials": e.materials,
                "elapsed_time_ms": round(elapsed_time * 1000, 2)
            }
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot determine product group: {str(e)}"
        )

    except (BrandGroupGenerationError, ModelGenerationError) as e:
        # LLM generation failures
        elapsed_time = time.time() - start_time
        logger.error(
            f"[API:pricing] Generation failed: {e}",
            extra={
                "user_id": user.id,
                "elapsed_time_ms": round(elapsed_time * 1000, 2)
            }
        )

        # Check if timeout
        if "timeout" in str(e).lower() or elapsed_time > 10:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Price calculation timed out. Please try again."
            )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate pricing data: {str(e)}"
        )

    except PricingCalculationError as e:
        # Calculation errors (adjustment or price calculation)
        elapsed_time = time.time() - start_time
        logger.error(
            f"[API:pricing] Calculation failed: {e}",
            extra={
                "user_id": user.id,
                "elapsed_time_ms": round(elapsed_time * 1000, 2)
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Price calculation failed: {str(e)}"
        )

    except Exception as e:
        # Unexpected errors
        elapsed_time = time.time() - start_time
        logger.error(
            f"[API:pricing] Unexpected error in calculate_price: {e}",
            exc_info=True,
            extra={
                "user_id": user.id,
                "elapsed_time_ms": round(elapsed_time * 1000, 2)
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during price calculation"
        )
