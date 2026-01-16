"""
BetaSignup Model - Schema Public

Ce modèle stocke les inscriptions à la beta de StoFlow.
Les inscriptions sont dans le schema public car elles ne sont pas liées à un tenant.

Business Rules:
- Chaque inscription est unique par email
- Status: pending (en attente du lancement), converted (compte créé), cancelled
- Les données sont utilisées pour qualifier les prospects avant le lancement
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SQLEnum, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class BetaSignupStatus(str, Enum):
    """Statuts d'inscription beta."""
    PENDING = "pending"  # En attente du lancement
    CONVERTED = "converted"  # Compte créé
    CANCELLED = "cancelled"  # Annulé par l'utilisateur


class BetaSignup(Base):
    """
    Modèle BetaSignup - Inscriptions à la beta StoFlow.

    Attributes:
        id: Identifiant unique
        email: Adresse email du prospect
        name: Nom complet
        vendor_type: Type de vendeur (particulier/professionnel)
        monthly_volume: Volume mensuel de ventes
        status: Statut de l'inscription
        created_at: Date d'inscription
        updated_at: Date de dernière modification
    """

    __tablename__ = "beta_signups"
    __table_args__ = (
        UniqueConstraint("email", name="uq_beta_signups_email"),
        {"schema": "public"},
    )

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # User Data
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    vendor_type: Mapped[str] = mapped_column(String(50), nullable=False)  # particulier/professionnel
    monthly_volume: Mapped[str] = mapped_column(String(50), nullable=False)  # 0-10, 10-50, 50+

    # Status
    status: Mapped[BetaSignupStatus] = mapped_column(
        SQLEnum(BetaSignupStatus, native_enum=False, length=20),
        default=BetaSignupStatus.PENDING,
        nullable=False,
        index=True,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<BetaSignup(id={self.id}, email={self.email}, status={self.status})>"
