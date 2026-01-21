"""
BetaSignup Model - Schema Public

Ce modèle stocke les inscriptions à la beta de StoFlow.
Les inscriptions sont dans le schema public car elles ne sont pas liées à un tenant.

Business Rules:
- Chaque inscription est unique par email
- Status: pending (en attente du lancement), converted (compte créé), cancelled, revoked
- Les données sont utilisées pour qualifier les prospects avant le lancement
- Les beta testers éligibles reçoivent -50% à vie sur leur abonnement
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.database import Base


class BetaSignupStatus(str, Enum):
    """Statuts d'inscription beta."""
    PENDING = "pending"  # En attente du lancement
    CONVERTED = "converted"  # Compte créé et réduction appliquée
    CANCELLED = "cancelled"  # Annulé par l'utilisateur
    REVOKED = "revoked"  # Réduction révoquée par admin


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
        user_id: Lien vers l'utilisateur converti (si applicable)
        discount_applied_at: Date d'application du coupon -50%
        discount_revoked_at: Date de révocation de la réduction
        discount_revoked_by: Admin qui a révoqué la réduction
        revocation_reason: Raison de la révocation
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
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    vendor_type: Mapped[str | None] = mapped_column(String(50), nullable=True)  # particulier/professionnel
    monthly_volume: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 0-10, 10-50, 50+

    # Status
    status: Mapped[BetaSignupStatus] = mapped_column(
        SQLEnum(BetaSignupStatus, native_enum=False, length=20),
        default=BetaSignupStatus.PENDING,
        nullable=False,
        index=True,
    )

    # Conversion tracking
    user_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("public.users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Discount tracking
    discount_applied_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    discount_revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    discount_revoked_by: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("public.users.id", ondelete="SET NULL"),
        nullable=True,
    )
    revocation_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=True,
    )

    # Relationships (for admin display)
    user = relationship(
        "User",
        foreign_keys=[user_id],
        lazy="selectin",
    )
    revoked_by_user = relationship(
        "User",
        foreign_keys=[discount_revoked_by],
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<BetaSignup(id={self.id}, email={self.email}, status={self.status})>"

    def is_eligible_for_discount(self) -> bool:
        """
        Check if this beta signup is eligible for the -50% discount.

        Returns:
            True if eligible, False if revoked or cancelled.
        """
        return (
            self.status != BetaSignupStatus.REVOKED
            and self.status != BetaSignupStatus.CANCELLED
            and self.discount_revoked_at is None
        )
