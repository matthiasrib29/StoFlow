"""
BetaSignup Model - Schema Public

Ce modele stocke les inscriptions a la beta de StoFlow.
Les inscriptions sont dans le schema public car elles ne sont pas liees a un tenant.

Business Rules:
- Chaque inscription est unique par email
- Status: pending (en attente du lancement), converted (compte cree), cancelled
- Les donnees sont utilisees pour qualifier les prospects avant le lancement
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class BetaSignupStatus(str, Enum):
    """Statuts d'inscription beta."""
    PENDING = "pending"  # En attente du lancement
    CONVERTED = "converted"  # Compte cree
    CANCELLED = "cancelled"  # Annule par l'utilisateur


class BetaSignup(Base):
    """
    Modele BetaSignup - Inscriptions a la beta StoFlow.

    Attributes:
        id: Identifiant unique
        email: Adresse email du prospect
        name: Nom complet
        vendor_type: Type de vendeur (particulier/professionnel)
        monthly_volume: Nombre de produits (stocke product_count)
        status: Statut de l'inscription
        created_at: Date d'inscription
    """

    __tablename__ = "beta_signups"
    __table_args__ = {"schema": "public"}

    # Primary Key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # User Data
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    vendor_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    monthly_volume: Mapped[str | None] = mapped_column(String(50), nullable=True)  # Stores product_count

    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False,
        index=True,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<BetaSignup(id={self.id}, email={self.email}, status={self.status})>"
