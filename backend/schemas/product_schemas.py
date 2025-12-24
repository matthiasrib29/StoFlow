"""
Product Schemas

Schemas Pydantic pour la validation des requêtes/réponses API Product.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


# ===== PRODUCT IMAGE SCHEMAS =====


class ProductImageCreate(BaseModel):
    """Schema pour créer une image de produit (utilisé lors de l'upload)."""

    display_order: int = Field(default=0, ge=0, description="Ordre d'affichage (0 = première image)")

    model_config = {
        "json_schema_extra": {
            "example": {"display_order": 0}
        }
    }


class ProductImageResponse(BaseModel):
    """Schema pour la réponse contenant une image de produit."""

    id: int
    product_id: int
    image_path: str
    display_order: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ===== PRODUCT SCHEMAS =====


class ProductCreate(BaseModel):
    """
    Schema pour créer un produit.

    Business Rules (Updated 2025-12-12):
    - ID auto-incrémenté comme identifiant unique (PostgreSQL SERIAL)
    - Category, condition OBLIGATOIRES
    - Brand, label_size, color OPTIONNELS (alignés avec DB nullable=True)
    - Prix peut être NULL (calculé automatiquement si absent)
    - Stock défaut: 1 (pièce unique)
    """

    title: str = Field(..., min_length=1, max_length=500, description="Titre du produit")
    description: str = Field(..., min_length=1, description="Description complète du produit")
    price: Decimal | None = Field(None, gt=0, description="Prix de vente (calculé automatiquement si absent)")

    # Attributs obligatoires (category, condition)
    category: str = Field(..., max_length=255, description="Catégorie (OBLIGATOIRE, FK public.categories)")
    condition: int = Field(..., ge=0, le=10, description="État 0-10 (OBLIGATOIRE, FK product_attributes.conditions)")

    # Attributs optionnels mais recommandés (alignés avec DB nullable=True)
    brand: str | None = Field(None, max_length=100, description="Marque (FK product_attributes.brands)")
    size: str | None = Field(None, max_length=100, description="Taille standardisée (FK product_attributes.sizes)")
    label_size: str | None = Field(None, max_length=100, description="Taille étiquette (texte libre)")
    color: str | None = Field(None, max_length=100, description="Couleur (FK product_attributes.colors)")

    # Attributs optionnels avec FK
    material: str | None = Field(None, max_length=100, description="Matière (FK public.materials)")
    fit: str | None = Field(None, max_length=100, description="Coupe (FK public.fits)")
    gender: str | None = Field(None, max_length=100, description="Genre (FK public.genders)")
    season: str | None = Field(None, max_length=100, description="Saison (FK public.seasons)")
    sport: str | None = Field(None, max_length=100, description="Sport (FK product_attributes.sports)")
    neckline: str | None = Field(None, max_length=100, description="Encolure (FK product_attributes.necklines)")
    length: str | None = Field(None, max_length=100, description="Longueur (FK product_attributes.lengths)")
    pattern: str | None = Field(None, max_length=100, description="Motif (FK product_attributes.patterns)")

    # Attributs supplémentaires (sans FK)
    condition_sup: str | None = Field(None, max_length=255, description="État supplémentaire/détails")
    rise: str | None = Field(None, max_length=100, description="Hauteur de taille (pantalons)")
    closure: str | None = Field(None, max_length=100, description="Type de fermeture")
    sleeve_length: str | None = Field(None, max_length=100, description="Longueur de manches")
    origin: str | None = Field(None, max_length=100, description="Origine/provenance")
    decade: str | None = Field(None, max_length=100, description="Décennie")
    trend: str | None = Field(None, max_length=100, description="Tendance")
    name_sup: str | None = Field(None, max_length=100, description="Titre supplémentaire")
    location: str | None = Field(None, max_length=100, description="Emplacement physique")
    model: str | None = Field(None, max_length=100, description="Référence modèle")

    # Dimensions (measurements en cm)
    dim1: int | None = Field(None, ge=0, description="Tour de poitrine/Épaules (cm)")
    dim2: int | None = Field(None, ge=0, description="Longueur totale (cm)")
    dim3: int | None = Field(None, ge=0, description="Longueur manche (cm)")
    dim4: int | None = Field(None, ge=0, description="Tour de taille (cm)")
    dim5: int | None = Field(None, ge=0, description="Tour de hanches (cm)")
    dim6: int | None = Field(None, ge=0, description="Entrejambe (cm)")

    # Stock (Updated 2025-12-08: default 1 pour pièces uniques)
    stock_quantity: int = Field(default=1, ge=0, description="Quantité en stock (défaut: 1)")

    # ===== SECURITY VALIDATION (2025-12-05): XSS Protection =====
    @field_validator('description', 'title', 'condition_sup', 'name_sup')
    @classmethod
    def validate_no_html(cls, value: str | None) -> str | None:
        """
        Valide qu'un champ texte ne contient pas de HTML (XSS protection).

        Business Rules (Security - 2025-12-05):
        - Bloquer si contient < ou >
        - Empêche injection de <script>, <iframe>, etc.
        - User doit entrer du texte brut uniquement

        Raises:
            ValueError: Si HTML détecté
        """
        if value and ('<' in value or '>' in value):
            raise ValueError(
                "HTML tags are not allowed. Please use plain text only. "
                "Found forbidden characters: < or >"
            )
        return value

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "title": "Levi's 501 Vintage",
                    "description": "Jean vintage en excellent état, coupe regular, W32L34",
                    "category": "Jeans",
                    "brand": "Levi's",
                    "condition": 8,
                    "size": "W32/L34",
                    "label_size": "32 x 34",
                    "color": "Blue",
                    "material": "Denim",
                    "fit": "Regular",
                    "gender": "Men",
                    "dim1": 32,
                    "dim6": 34,
                    "stock_quantity": 1
                },
                {
                    "title": "Nike Air Max 90",
                    "description": "Baskets neuves avec étiquettes, couleur blanche",
                    "price": 120.00,
                    "category": "Shoes",
                    "brand": "Nike",
                    "condition": 10,
                    "size": "L",
                    "label_size": "42 EU",
                    "color": "White",
                    "gender": "Men",
                    "stock_quantity": 1
                }
            ]
        }
    }


class ProductUpdate(BaseModel):
    """
    Schema pour mettre à jour un produit.

    Tous les champs sont optionnels (permet update partiel).
    """

    title: str | None = Field(None, min_length=1, max_length=500)
    description: str | None = Field(None, min_length=1)
    price: Decimal | None = Field(None, gt=0)

    category: str | None = Field(None, max_length=255)
    condition: int | None = Field(None, ge=0, le=10)
    brand: str | None = Field(None, max_length=100)
    size: str | None = Field(None, max_length=100)
    label_size: str | None = Field(None, max_length=100)
    color: str | None = Field(None, max_length=100)
    material: str | None = Field(None, max_length=100)
    fit: str | None = Field(None, max_length=100)
    gender: str | None = Field(None, max_length=100)
    season: str | None = Field(None, max_length=100)
    sport: str | None = Field(None, max_length=100)
    neckline: str | None = Field(None, max_length=100)
    length: str | None = Field(None, max_length=100)
    pattern: str | None = Field(None, max_length=100)

    condition_sup: str | None = Field(None, max_length=255)
    rise: str | None = Field(None, max_length=100)
    closure: str | None = Field(None, max_length=100)
    sleeve_length: str | None = Field(None, max_length=100)
    origin: str | None = Field(None, max_length=100)
    decade: str | None = Field(None, max_length=100)
    trend: str | None = Field(None, max_length=100)
    name_sup: str | None = Field(None, max_length=100)
    location: str | None = Field(None, max_length=100)
    model: str | None = Field(None, max_length=100)

    dim1: int | None = Field(None, ge=0)
    dim2: int | None = Field(None, ge=0)
    dim3: int | None = Field(None, ge=0)
    dim4: int | None = Field(None, ge=0)
    dim5: int | None = Field(None, ge=0)
    dim6: int | None = Field(None, ge=0)

    stock_quantity: int | None = Field(None, ge=0)

    # ===== SECURITY VALIDATION (2025-12-05): XSS Protection =====
    @field_validator('description', 'title', 'condition_sup', 'name_sup')
    @classmethod
    def validate_no_html(cls, value: str | None) -> str | None:
        """Valide qu'un champ texte ne contient pas de HTML (XSS protection)."""
        if value and ('<' in value or '>' in value):
            raise ValueError(
                "HTML tags are not allowed. Please use plain text only. "
                "Found forbidden characters: < or >"
            )
        return value


class ProductResponse(BaseModel):
    """
    Schema pour la réponse contenant un produit complet.

    Inclut toutes les informations du produit + images.
    """

    id: int
    title: str
    description: str
    price: Decimal

    # Attributs
    category: str
    brand: str | None
    condition: int | None  # Optional for DRAFT products (validated on publish)
    size: str | None
    label_size: str | None
    color: str | None
    material: str | None
    fit: str | None
    gender: str | None
    season: str | None
    sport: str | None
    neckline: str | None
    length: str | None
    pattern: str | None

    condition_sup: str | None
    rise: str | None
    closure: str | None
    sleeve_length: str | None
    origin: str | None
    decade: str | None
    trend: str | None
    name_sup: str | None
    location: str | None
    model: str | None

    # Dimensions
    dim1: int | None
    dim2: int | None
    dim3: int | None
    dim4: int | None
    dim5: int | None
    dim6: int | None

    # Stock
    stock_quantity: int

    # Status
    status: str

    # Dates
    scheduled_publish_at: datetime | None
    published_at: datetime | None
    sold_at: datetime | None
    deleted_at: datetime | None
    created_at: datetime
    updated_at: datetime

    # Metadata
    integration_metadata: dict | None

    # Images
    product_images: list[ProductImageResponse] = []

    model_config = {"from_attributes": True}


class ProductListResponse(BaseModel):
    """
    Schema pour la réponse contenant une liste paginée de produits.

    Business Rules:
    - Skip/limit pour pagination
    - Total count pour calculer les pages
    """

    products: list[ProductResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

    model_config = {
        "json_schema_extra": {
            "example": {
                "products": [],
                "total": 42,
                "page": 1,
                "page_size": 20,
                "total_pages": 3
            }
        }
    }
