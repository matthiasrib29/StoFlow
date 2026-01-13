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
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.database import Base


class AIGenerationLog(Base):
    """
    Modèle AIGenerationLog - Logs des générations IA.

    Attributes:
        id: Identifiant unique
        product_id: ID du produit pour lequel la description a été générée
        model: Modèle IA utilisé (ex: gpt-4o, gemini-2.5-flash)
        prompt_tokens: Nombre de tokens dans le prompt
        completion_tokens: Nombre de tokens dans la réponse
        total_tokens: Total des tokens (prompt + completion)
        total_cost: Coût estimé en USD
        cached: True si réponse venant du cache Redis
        generation_time_ms: Temps de génération en millisecondes
        error_message: Message d'erreur si échec
        response_data: Réponse brute JSON de l'IA (debugging, audit, re-parsing)
        created_at: Date de génération
    """

    __tablename__ = "ai_generation_logs"
    __table_args__ = {"schema": "tenant"}  # Placeholder for schema_translate_map

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Foreign Keys
    product_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("tenant.products.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Product ID (nullable for direct image analysis without product)"
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

    # Raw AI Response (for debugging and re-parsing)
    response_data: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Raw AI response JSON for debugging, audit, and re-parsing"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )

    # Relationships
    product: Mapped["Product | None"] = relationship("Product", back_populates="ai_generation_logs")

    def __repr__(self) -> str:
        return (
            f"<AIGenerationLog(id={self.id}, product_id={self.product_id}, "
            f"model='{self.model}', cached={self.cached}, cost={self.total_cost})>"
        )
