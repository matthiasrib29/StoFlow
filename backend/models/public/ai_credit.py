"""
AI Credit Model

Table pour tracker les crédits IA pour chaque utilisateur.

Business Rules (2025-12-10):
- Chaque user a des crédits mensuels (viaabonnement) + crédits achetés
- ai_credits_purchased: Cr édits achetés en plus de l'abonnement (ne s'épuisent jamais)
- ai_credits_used_this_month: Consommés ce mois-ci (reset chaque 1er du mois)
- last_reset_date: Date du dernier reset mensuel

Author: Claude
Date: 2025-12-10
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DECIMAL, Boolean, DateTime, Integer, String, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.database import Base


class AICredit(Base):
    """
    Modèle pour les crédits IA de chaque utilisateur.

    Business Rules (2025-12-10):
    - Un enregistrement unique par user (user_id = FK unique)
    - ai_credits_purchased: Crédits achetés (cumulables, ne s'épuisent pas)
    - ai_credits_used_this_month: Consommation du mois en cours
    - Calcul total = (abonnement.ai_credits_monthly + ai_credits_purchased) - ai_credits_used_this_month
    """

    __tablename__ = "ai_credits"
    __table_args__ = {"schema": "public"}

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Foreign Key vers User (unique = 1 enregistrement par user)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("public.users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
        comment="Utilisateur propriétaire"
    )

    # Crédits achetés (permanents)
    ai_credits_purchased: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Crédits IA achetés (cumulables, ne s'épuisent pas)"
    )

    # Utilisation mensuelle (reset chaque mois)
    ai_credits_used_this_month: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Crédits IA utilisés ce mois-ci"
    )

    # Date du dernier reset
    last_reset_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Date du dernier reset mensuel"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relations
    user: Mapped["User"] = relationship("User", back_populates="ai_credit")

    def __repr__(self) -> str:
        return (
            f"<AICredit(user_id={self.user_id}, "
            f"purchased={self.ai_credits_purchased}, "
            f"used_this_month={self.ai_credits_used_this_month})>"
        )

    def get_remaining_credits(self, monthly_credits: int) -> int:
        """
        Calcule les crédits restants pour l'utilisateur.

        Args:
            monthly_credits: Crédits mensuels de l'abonnement

        Returns:
            int: Crédits restants
        """
        total_available = monthly_credits + self.ai_credits_purchased
        remaining = total_available - self.ai_credits_used_this_month
        return max(0, remaining)
