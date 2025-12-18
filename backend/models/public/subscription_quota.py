"""
Subscription Quota Model

Table pour définir les quotas associés à chaque tier d'abonnement.

Business Rules (2025-12-09):
- 4 tiers: FREE, STARTER, PRO, ENTERPRISE
- Quotas définis: max_products, max_platforms, ai_credits_monthly
- Valeurs stockées en base (facile à modifier sans redéploiement)
- ENTERPRISE = quotas illimités (999999)

Author: Claude
Date: 2025-12-09
"""

import os
from sqlalchemy import Column, Integer, String, Enum, DECIMAL
from sqlalchemy.orm import relationship
from decimal import Decimal

from shared.database import Base
from models.public.user import SubscriptionTier


class SubscriptionQuota(Base):
    """
    Modèle pour les quotas d'abonnement.

    Définit les limites pour chaque tier (FREE, STARTER, PRO, ENTERPRISE).
    """
    __tablename__ = "subscription_quotas"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True, index=True)
    tier = Column(
        Enum(SubscriptionTier, name="subscriptiontier", schema=None if os.getenv("TESTING") else "public"),
        unique=True,
        nullable=False,
        index=True,
        comment="Tier d'abonnement (FREE, STARTER, PRO, ENTERPRISE)"
    )

    # Quotas
    max_products = Column(
        Integer,
        nullable=False,
        default=30,
        comment="Nombre maximum de produits actifs"
    )
    max_platforms = Column(
        Integer,
        nullable=False,
        default=2,
        comment="Nombre maximum de plateformes connectées"
    )
    ai_credits_monthly = Column(
        Integer,
        nullable=False,
        default=15,
        comment="Crédits IA mensuels"
    )
    price = Column(
        DECIMAL(10, 2),
        nullable=False,
        default=0.00,
        comment="Prix mensuel de l'abonnement en euros"
    )

    # Relations
    users = relationship("User", back_populates="subscription_quota")

    def __repr__(self):
        return (
            f"<SubscriptionQuota(tier={self.tier.value}, "
            f"max_products={self.max_products}, "
            f"max_platforms={self.max_platforms}, "
            f"ai_credits_monthly={self.ai_credits_monthly})>"
        )

    def to_dict(self):
        """Convertit le quota en dictionnaire."""
        return {
            "tier": self.tier.value,
            "max_products": self.max_products,
            "max_platforms": self.max_platforms,
            "ai_credits_monthly": self.ai_credits_monthly,
            "price": float(self.price) if self.price else 0.0,
        }


# Quotas par défaut (utilisés pour seed)
DEFAULT_QUOTAS = {
    SubscriptionTier.FREE: {
        "max_products": 50,
        "max_platforms": 1,
        "ai_credits_monthly": 100,
        "price": Decimal("0.00"),
    },
    SubscriptionTier.STARTER: {
        "max_products": 500,
        "max_platforms": 2,
        "ai_credits_monthly": 1000,
        "price": Decimal("19.99"),
    },
    SubscriptionTier.PRO: {
        "max_products": 2000,
        "max_platforms": 5,
        "ai_credits_monthly": 5000,
        "price": Decimal("49.99"),
    },
    SubscriptionTier.ENTERPRISE: {
        "max_products": 999999,  # Illimité
        "max_platforms": 999,  # Illimité
        "ai_credits_monthly": 50000,  # Illimité
        "price": Decimal("199.99"),
    },
}
