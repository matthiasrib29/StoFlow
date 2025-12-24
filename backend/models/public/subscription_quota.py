"""
Subscription Quota Model

Table pour définir les quotas associés à chaque tier d'abonnement.

Business Rules (2025-12-09):
- 4 tiers: FREE, STARTER, PRO, ENTERPRISE
- Quotas définis: max_products, max_platforms, ai_credits_monthly
- Valeurs stockées en base (facile à modifier sans redéploiement)
- ENTERPRISE = quotas illimités (999999)

Updated (2024-12-24):
- Added display fields for landing page pricing section
- display_name, description, annual_discount_percent, is_popular, cta_text, display_order
- Added features relationship to SubscriptionFeature

Author: Claude
Date: 2025-12-09
"""

import os
from sqlalchemy import Column, Integer, String, Boolean, Enum, DECIMAL
from sqlalchemy.orm import relationship
from decimal import Decimal
from typing import TYPE_CHECKING

from shared.database import Base
from models.public.user import SubscriptionTier

if TYPE_CHECKING:
    from models.public.subscription_feature import SubscriptionFeature


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

    # Display fields for landing page pricing (added 2024-12-24)
    display_name = Column(
        String(50),
        nullable=False,
        default="",
        comment="Display name on pricing page (e.g., 'Gratuit', 'Pro')"
    )
    description = Column(
        String(200),
        nullable=True,
        comment="Short description (e.g., 'Pour découvrir Stoflow')"
    )
    annual_discount_percent = Column(
        Integer,
        nullable=False,
        default=20,
        comment="Annual discount percentage (e.g., 20 for -20%)"
    )
    is_popular = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="Show 'Populaire' badge"
    )
    cta_text = Column(
        String(100),
        nullable=True,
        comment="Call-to-action button text (e.g., 'Essai gratuit 14 jours')"
    )
    display_order = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Order of display on pricing page (lower = first)"
    )

    # Relations
    users = relationship("User", back_populates="subscription_quota")
    features = relationship(
        "SubscriptionFeature",
        back_populates="subscription_quota",
        cascade="all, delete-orphan",
        order_by="SubscriptionFeature.display_order"
    )

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

    def to_pricing_dict(self):
        """Convert to pricing page dictionary (includes display fields and features)."""
        return {
            "tier": self.tier.value,
            "display_name": self.display_name,
            "description": self.description,
            "price": int(self.price) if self.price else 0,  # Integer for display
            "annual_discount_percent": self.annual_discount_percent,
            "is_popular": self.is_popular,
            "cta_text": self.cta_text,
            "display_order": self.display_order,
            "max_products": self.max_products,
            "max_platforms": self.max_platforms,
            "ai_credits_monthly": self.ai_credits_monthly,
            "features": [f.to_dict() for f in self.features] if self.features else [],
        }


# Quotas par défaut (utilisés pour seed)
DEFAULT_QUOTAS = {
    SubscriptionTier.FREE: {
        "max_products": 50,
        "max_platforms": 1,
        "ai_credits_monthly": 100,
        "price": Decimal("0"),
        "display_name": "Gratuit",
        "description": "Pour découvrir Stoflow",
        "annual_discount_percent": 0,
        "is_popular": False,
        "cta_text": "Commencer",
        "display_order": 0,
    },
    SubscriptionTier.STARTER: {
        "max_products": 500,
        "max_platforms": 2,
        "ai_credits_monthly": 1000,
        "price": Decimal("19"),
        "display_name": "Pro",
        "description": "Pour les vendeurs actifs",
        "annual_discount_percent": 20,
        "is_popular": True,
        "cta_text": "Essai gratuit 14 jours",
        "display_order": 1,
    },
    SubscriptionTier.PRO: {
        "max_products": 2000,
        "max_platforms": 5,
        "ai_credits_monthly": 5000,
        "price": Decimal("49"),
        "display_name": "Business",
        "description": "Pour les professionnels",
        "annual_discount_percent": 20,
        "is_popular": False,
        "cta_text": "Essai gratuit 14 jours",
        "display_order": 2,
    },
    SubscriptionTier.ENTERPRISE: {
        "max_products": 999999,  # Illimité
        "max_platforms": 999,  # Illimité
        "ai_credits_monthly": 50000,  # Illimité
        "price": Decimal("199"),
        "display_name": "Enterprise",
        "description": "Pour les grandes équipes",
        "annual_discount_percent": 20,
        "is_popular": False,
        "cta_text": "Nous contacter",
        "display_order": 3,
    },
}

# Features par défaut pour chaque tier (utilisés pour seed)
DEFAULT_FEATURES = {
    SubscriptionTier.FREE: [
        "Jusqu'à 50 produits",
        "1 marketplace",
        "Support email",
    ],
    SubscriptionTier.STARTER: [
        "Produits illimités",
        "Toutes les marketplaces",
        "Génération IA (100/mois)",
        "Support prioritaire",
    ],
    SubscriptionTier.PRO: [
        "Tout le plan Pro",
        "Génération IA illimitée",
        "API access",
        "Support dédié",
    ],
    SubscriptionTier.ENTERPRISE: [
        "Tout illimité",
        "Multi-utilisateurs",
        "Intégration sur mesure",
        "Account manager dédié",
    ],
}
