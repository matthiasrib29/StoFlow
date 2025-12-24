"""
Public API Endpoints

Endpoints that don't require authentication.
Used for landing page data like pricing plans.

Author: Claude
Date: 2024-12-24
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from shared.database import get_db
from models.public.subscription_quota import SubscriptionQuota
from schemas.pricing import PricingPlanResponse, PricingFeatureResponse

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/pricing", response_model=list[PricingPlanResponse])
async def get_pricing_plans(db: Session = Depends(get_db)):
    """
    Get all subscription plans for pricing page display.

    This endpoint is public and doesn't require authentication.
    Returns plans ordered by display_order with their features.
    """
    plans = (
        db.query(SubscriptionQuota)
        .options(joinedload(SubscriptionQuota.features))
        .order_by(SubscriptionQuota.display_order)
        .all()
    )

    return [
        PricingPlanResponse(
            tier=plan.tier.value,
            display_name=plan.display_name,
            description=plan.description,
            price=int(plan.price) if plan.price else 0,
            annual_discount_percent=plan.annual_discount_percent,
            is_popular=plan.is_popular,
            cta_text=plan.cta_text,
            display_order=plan.display_order,
            max_products=plan.max_products,
            max_platforms=plan.max_platforms,
            ai_credits_monthly=plan.ai_credits_monthly,
            features=[
                PricingFeatureResponse(
                    feature_text=f.feature_text,
                    display_order=f.display_order
                )
                for f in sorted(plan.features, key=lambda x: x.display_order)
            ]
        )
        for plan in plans
    ]
