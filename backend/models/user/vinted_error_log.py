"""
VintedErrorLog Model - Schema user_{id}

Enregistre toutes les erreurs de publication/modification de produits Vinted.
Permet le debugging et la traçabilité des échecs.

Business Rules (Created: 2024-12-10):
- Enregistre les erreurs techniques uniquement (pas les validations simples)
- Types d'erreurs: mapping_error, api_error, image_error
- Operations: publish, update, delete
- Auto-nettoyage après publish/update réussi
- Index sur product_id, error_type, created_at pour performances

Architecture:
- Stocké dans schema user_{id} pour isolation multi-tenant
- Relation CASCADE avec products (suppression automatique)
- Index optimisés pour queries fréquentes
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional

from shared.database import Base


class VintedErrorLog(Base):
    """
    Modèle VintedErrorLog - Logs d'erreurs Vinted.

    Attributes:
        id: Identifiant unique (PK)
        product_id: ID du produit concerné (FK)
        operation: Type d'opération (publish, update, delete)
        error_type: Type d'erreur (mapping_error, api_error, image_error)
        error_message: Message d'erreur principal
        error_details: Détails contextuels (ex: "brand='Levi\'s', brand_id=None")
        created_at: Timestamp de création
    """

    __tablename__ = "vinted_error_logs"
    __table_args__ = (
        Index('idx_vinted_error_logs_product_id', 'product_id'),
        Index('idx_vinted_error_logs_error_type', 'error_type'),
        Index('idx_vinted_error_logs_created_at', 'created_at'),
    )

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Foreign Keys
    product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="ID du produit concerné"
    )

    # Error Fields
    operation: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Type d'opération: publish, update, delete"
    )

    error_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Type d'erreur: mapping_error, api_error, image_error"
    )

    error_message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Message d'erreur principal"
    )

    error_details: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Détails contextuels (ex: brand='Levi\'s', brand_id=None)"
    )

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    product: Mapped["Product"] = relationship("Product", foreign_keys=[product_id])

    def __repr__(self) -> str:
        return (
            f"<VintedErrorLog(id={self.id}, product_id={self.product_id}, "
            f"operation='{self.operation}', error_type='{self.error_type}')>"
        )
