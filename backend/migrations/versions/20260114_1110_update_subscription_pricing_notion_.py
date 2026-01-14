"""update_subscription_pricing_notion_strategy

Update subscription pricing to match Notion pricing strategy (2026-01-14).

Changes:
- FREE: 50 -> 30 products, 100 -> 10 AI credits
- STARTER: 500 -> 200 products, 1000 -> 40 AI credits, 19€ -> 9.99€, 20% -> 34% discount
- PRO: 2000 -> 500 products, 5000 -> 100 AI credits, 49€ -> 19.99€, 20% -> 34% discount
- ENTERPRISE: 50000 -> 300 AI credits, 199€ -> 39.99€, display_name "Business", 20% -> 34% discount

Revision ID: 85be05b7612e
Revises: 20260114_1300
Create Date: 2026-01-14 11:10:45.563130+01:00

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '85be05b7612e'
down_revision: Union[str, None] = '20260114_1300'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# New pricing from Notion strategy
NEW_PRICING = {
    "FREE": {
        "max_products": 30,
        "ai_credits_monthly": 10,
        "price": 0.00,
        "display_name": "Gratuit",
        "description": "Pour découvrir Stoflow",
        "annual_discount_percent": 0,
    },
    "STARTER": {
        "max_products": 200,
        "ai_credits_monthly": 40,
        "price": 9.99,
        "display_name": "Starter",
        "description": "Pour les vendeurs actifs",
        "annual_discount_percent": 34,
    },
    "PRO": {
        "max_products": 500,
        "ai_credits_monthly": 100,
        "price": 19.99,
        "display_name": "Pro",
        "description": "Pour les professionnels",
        "annual_discount_percent": 34,
    },
    "ENTERPRISE": {
        "max_products": 999999,
        "ai_credits_monthly": 300,
        "price": 39.99,
        "display_name": "Business",
        "description": "Pour les grandes équipes",
        "annual_discount_percent": 34,
    },
}

# Old pricing for downgrade
OLD_PRICING = {
    "FREE": {
        "max_products": 50,
        "ai_credits_monthly": 100,
        "price": 0.00,
        "display_name": "Gratuit",
        "description": "Pour découvrir Stoflow",
        "annual_discount_percent": 0,
    },
    "STARTER": {
        "max_products": 500,
        "ai_credits_monthly": 1000,
        "price": 19.00,
        "display_name": "Pro",
        "description": "Pour les vendeurs actifs",
        "annual_discount_percent": 20,
    },
    "PRO": {
        "max_products": 2000,
        "ai_credits_monthly": 5000,
        "price": 49.00,
        "display_name": "Business",
        "description": "Pour les professionnels",
        "annual_discount_percent": 20,
    },
    "ENTERPRISE": {
        "max_products": 999999,
        "ai_credits_monthly": 50000,
        "price": 199.00,
        "display_name": "Enterprise",
        "description": "Pour les grandes équipes",
        "annual_discount_percent": 20,
    },
}


def upgrade() -> None:
    """Update subscription_quotas with new Notion pricing strategy."""
    conn = op.get_bind()

    for tier, values in NEW_PRICING.items():
        conn.execute(
            text("""
                UPDATE public.subscription_quotas
                SET
                    max_products = :max_products,
                    ai_credits_monthly = :ai_credits_monthly,
                    price = :price,
                    display_name = :display_name,
                    description = :description,
                    annual_discount_percent = :annual_discount_percent
                WHERE tier = :tier
            """),
            {
                "tier": tier,
                "max_products": values["max_products"],
                "ai_credits_monthly": values["ai_credits_monthly"],
                "price": values["price"],
                "display_name": values["display_name"],
                "description": values["description"],
                "annual_discount_percent": values["annual_discount_percent"],
            }
        )


def downgrade() -> None:
    """Restore previous pricing values."""
    conn = op.get_bind()

    for tier, values in OLD_PRICING.items():
        conn.execute(
            text("""
                UPDATE public.subscription_quotas
                SET
                    max_products = :max_products,
                    ai_credits_monthly = :ai_credits_monthly,
                    price = :price,
                    display_name = :display_name,
                    description = :description,
                    annual_discount_percent = :annual_discount_percent
                WHERE tier = :tier
            """),
            {
                "tier": tier,
                "max_products": values["max_products"],
                "ai_credits_monthly": values["ai_credits_monthly"],
                "price": values["price"],
                "display_name": values["display_name"],
                "description": values["description"],
                "annual_discount_percent": values["annual_discount_percent"],
            }
        )
