"""
AI Schemas

Schemas Pydantic pour les endpoints IA.
"""

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


# =============================================================================
# GEMINI VISION - Analyse d'images
# =============================================================================


class GeminiVisionSchema(BaseModel):
    """
    Schema for Gemini Vision API response.

    NOTE: No default values allowed - Gemini API doesn't support them.
    All fields are nullable (Optional) but without defaults.
    """

    # === ATTRIBUTS PRINCIPAUX ===
    category: Optional[str]
    brand: Optional[str]
    condition: Optional[int]
    label_size: Optional[str]
    color: Optional[str]
    material: Optional[str]
    fit: Optional[str]
    gender: Optional[str]
    season: Optional[str]
    sport: Optional[str]
    neckline: Optional[str]
    length: Optional[str]
    pattern: Optional[str]

    # === ATTRIBUTS SUPPLÉMENTAIRES ===
    condition_sup: Optional[str]
    rise: Optional[str]
    closure: Optional[str]
    sleeve_length: Optional[str]
    stretch: Optional[str]
    lining: Optional[str]
    origin: Optional[str]
    decade: Optional[str]
    trend: Optional[str]
    model: Optional[str]

    # === FEATURES DESCRIPTIFS ===
    unique_feature: Optional[str]
    marking: Optional[str]

    # === META ===
    confidence: Optional[float]


class VisionExtractedAttributes(BaseModel):
    """Attributs extraits des images par Gemini Vision (mapping complet vers Product)."""

    # === ATTRIBUTS PRINCIPAUX ===
    category: Optional[str] = Field(None, description="Catégorie produit")
    brand: Optional[str] = Field(None, description="Marque détectée")
    condition: Optional[int] = Field(None, ge=0, le=10, description="État 0-10")
    label_size: Optional[str] = Field(None, description="Taille étiquette")
    color: Optional[list[str]] = Field(None, description="Couleurs détectées")
    material: Optional[list[str]] = Field(None, description="Matières détectées")
    fit: Optional[str] = Field(None, description="Coupe")
    gender: Optional[str] = Field(None, description="Genre: Homme/Femme/Mixte")
    season: Optional[str] = Field(None, description="Saison")
    sport: Optional[str] = Field(None, description="Sport associé")
    neckline: Optional[str] = Field(None, description="Encolure")
    length: Optional[str] = Field(None, description="Longueur")
    pattern: Optional[str] = Field(None, description="Motif")

    # === ATTRIBUTS SUPPLÉMENTAIRES ===
    condition_sup: Optional[list[str]] = Field(None, description="Détails état")
    rise: Optional[str] = Field(None, description="Hauteur taille (pantalons)")
    closure: Optional[str] = Field(None, description="Type fermeture")
    sleeve_length: Optional[str] = Field(None, description="Longueur manches")
    stretch: Optional[str] = Field(None, description="Élasticité")
    lining: Optional[str] = Field(None, description="Type de doublure")
    origin: Optional[str] = Field(None, description="Origine")
    decade: Optional[str] = Field(None, description="Décennie/époque")
    trend: Optional[str] = Field(None, description="Tendance")
    model: Optional[str] = Field(None, description="Référence modèle")

    # === FEATURES DESCRIPTIFS ===
    unique_feature: Optional[list[str]] = Field(None, description="Features uniques")
    marking: Optional[list[str]] = Field(None, description="Marquages visibles")

    # === META ===
    confidence: float = Field(0.0, ge=0, le=1, description="Confiance globale")

    model_config = {
        "json_schema_extra": {
            "example": {
                "category": "T-shirts",
                "brand": "Nike",
                "condition": 8,
                "color": ["Black", "White"],
                "material": ["Cotton", "Polyester"],
                "gender": "Men",
                "label_size": "M",
                "confidence": 0.85,
            }
        }
    }


class AIVisionAnalysisResponse(BaseModel):
    """Réponse de l'analyse d'images via Gemini Vision."""

    attributes: VisionExtractedAttributes = Field(
        ..., description="Attributs extraits des images"
    )
    model: str = Field(..., description="Modèle Gemini utilisé")
    images_analyzed: int = Field(..., description="Nombre d'images analysées")
    tokens_used: int = Field(..., description="Nombre de tokens utilisés")
    cost: Decimal = Field(..., description="Coût en USD")
    processing_time_ms: int = Field(..., description="Temps de traitement en ms")

    model_config = {
        "json_schema_extra": {
            "example": {
                "attributes": {
                    "brand": "Nike",
                    "category": "T-shirts",
                    "color": "Noir",
                    "condition": 8,
                    "confidence": 0.85,
                },
                "model": "gemini-2.5-flash",
                "images_analyzed": 3,
                "tokens_used": 1500,
                "cost": 0.002,
                "processing_time_ms": 2500,
            }
        }
    }
