"""
AIGenerationLog Model - Schema Tenant

Ce modèle trace toutes les générations de descriptions par l'IA (OpenAI).
Utilisé pour le monitoring des coûts, de la qualité et du cache.

Business Rules:
- Chaque appel à l'API OpenAI est enregistré
- model: modèle utilisé (ex: gpt-4o, gpt-4o-mini)
- prompt_tokens, completion_tokens: pour calcul des coûts
- cached: indique si la réponse venait du cache Redis
- total_cost: coût estimé en USD (calculé via tokens * prix du modèle)
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DECIMAL, Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.database import Base


class AIGenerationLog(Base):
    """
    Modèle AIGenerationLog - Logs des générations IA.

    Attributes:
        id: Identifiant unique
        product_id: ID du produit pour lequel la description a été générée
        model: Modèle OpenAI utilisé (ex: gpt-4o, gpt-4o-mini)
        prompt_tokens: Nombre de tokens dans le prompt
        completion_tokens: Nombre de tokens dans la réponse
        total_tokens: Total des tokens (prompt + completion)
        total_cost: Coût estimé en USD
        cached: True si réponse venant du cache Redis
        generation_time_ms: Temps de génération en millisecondes
        error_message: Message d'erreur si échec
        created_at: Date de génération
    """

    __tablename__ = "ai_generation_logs"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Foreign Keys
    product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # OpenAI Fields
    model: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    prompt_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    completion_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    total_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    total_cost: Mapped[Decimal] = mapped_column(DECIMAL(10, 6), nullable=False)

    # Cache et performance
    cached: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    generation_time_ms: Mapped[int] = mapped_column(Integer, nullable=False)

    # Error handling
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )

    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="ai_generation_logs")

    def __repr__(self) -> str:
        return (
            f"<AIGenerationLog(id={self.id}, product_id={self.product_id}, "
            f"model='{self.model}', cached={self.cached}, cost={self.total_cost})>"
        )
