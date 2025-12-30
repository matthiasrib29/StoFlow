"""
AI Schemas

Schemas Pydantic pour les endpoints IA.
"""

from decimal import Decimal

from pydantic import BaseModel, Field


class AIDescriptionResponse(BaseModel):
    """Schema pour la réponse de génération de description."""

    description: str = Field(..., description="Description générée par l'IA")
    model: str = Field(..., description="Modèle IA utilisé")
    tokens_used: int = Field(..., description="Nombre de tokens utilisés")
    cost: Decimal = Field(..., description="Coût en USD")
    cached: bool = Field(False, description="True si la réponse venait du cache")

    model_config = {
        "json_schema_extra": {
            "example": {
                "description": "Ce superbe jean Levi's 501 vintage...",
                "model": "claude-sonnet-4-20250514",
                "tokens_used": 250,
                "cost": 0.000750,
                "cached": False,
            }
        }
    }
