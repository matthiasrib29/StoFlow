"""
Script to update subscription prices in the database.

Run this script once after the migration to set the correct prices.

Usage:
    python scripts/update_subscription_prices.py
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from decimal import Decimal
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from shared.config import settings
from models.public.subscription_quota import SubscriptionQuota, SubscriptionTier, DEFAULT_QUOTAS


def update_prices():
    """Update prices in subscription_quotas table."""
    engine = create_engine(str(settings.database_url))

    with Session(engine) as session:
        print("🔄 Updating subscription prices...")

        for tier, quotas in DEFAULT_QUOTAS.items():
            price = quotas["price"]

            # Update the price for this tier (tier values are uppercase in DB)
            tier_upper = tier.value.upper()
            result = session.execute(
                text("UPDATE public.subscription_quotas SET price = :price WHERE UPPER(tier::text) = :tier"),
                {"price": str(price), "tier": tier_upper}
            )

            print(f"✅ Updated {tier.value}: price = {price}€")

        session.commit()
        print("\n✅ All prices updated successfully!")


if __name__ == "__main__":
    update_prices()
