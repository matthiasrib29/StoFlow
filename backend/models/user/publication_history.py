"""
PublicationHistory Model - Schema Tenant

Ce modèle trace l'historique de toutes les publications d'un produit sur les plateformes.
Un produit peut être publié plusieurs fois (republication, mise à jour, etc.).

Business Rules:
- Chaque tentative de publication est enregistrée
- Status: success, failed, pending
- error_message contient le détail en cas d'échec
- Utilisé pour le calcul des limites de publications/mois (Subscription.max_publications_per_month)
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.database import Base


class PublicationStatus(str, Enum):
    """Statuts de publication."""
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


class PublicationHistory(Base):
    """
    Modèle PublicationHistory - Historique des publications sur plateformes.

    Attributes:
        id: Identifiant unique
        product_id: ID du produit publié
        platform: Plateforme cible (vinted, ebay, etsy)
        status: Statut de la publication (success, failed, pending)
        platform_product_id: ID de l'annonce sur la plateforme (si success)
        platform_url: URL de l'annonce (si success)
        error_message: Message d'erreur (si failed)
        published_at: Date de publication (ou tentative)
        created_at: Date de création
    """

    __tablename__ = "publication_history"
    __table_args__ = {"schema": "tenant"}  # Placeholder for schema_translate_map

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Foreign Keys
    product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("tenant.products.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Business Fields
    platform: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    status: Mapped[PublicationStatus] = mapped_column(
        SQLEnum(PublicationStatus, name="publication_status", create_type=True),
        default=PublicationStatus.PENDING,
        nullable=False,
        index=True
    )

    # Données de publication
    platform_product_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    platform_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="publication_history")

    def __repr__(self) -> str:
        return (
            f"<PublicationHistory(id={self.id}, product_id={self.product_id}, "
            f"platform='{self.platform}', status={self.status})>"
        )
