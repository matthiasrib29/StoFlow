"""
Product Schemas

Schemas Pydantic pour la validation des requêtes/réponses API Product.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


# ===== PRODUCT IMAGE SCHEMAS =====


class ProductImageItem(BaseModel):
    """
    Schema pour une image de produit stockée en JSONB.

    Structure: {url, order, created_at}
    """

    url: str = Field(..., description="URL de l'image (CDN R2)")
    order: int = Field(..., ge=0, description="Ordre d'affichage (0 = première image)")
    created_at: datetime = Field(..., description="Date de création")

    model_config = {
        "json_schema_extra": {
            "example": {
                "url": "https://cdn.stoflow.io/1/products/5/abc123.jpg",
                "order": 0,
                "created_at": "2026-01-03T10:00:00Z"
            }
        }
    }


# ===== PRODUCT SCHEMAS =====


class MaterialDetail(BaseModel):
    """
    Schema for material with optional percentage.

    Used when specifying material composition with percentages.
    Example: [{"material": "Cotton", "percentage": 80}, {"material": "Polyester", "percentage": 20}]
    """

    material: str = Field(..., max_length=100, description="Material name (FK product_attributes.materials)")
    percentage: int | None = Field(None, ge=0, le=100, description="Percentage of this material in composition (0-100)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "material": "Cotton",
                "percentage": 80
            }
        }
    }


class ProductCreate(BaseModel):
    """
    Schema pour créer un produit.

    Business Rules (Updated 2025-12-12):
    - ID auto-incrémenté comme identifiant unique (PostgreSQL SERIAL)
    - Category, condition OBLIGATOIRES
    - Brand, size_original, color OPTIONNELS (alignés avec DB nullable=True)
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
    size_normalized: str | None = Field(None, max_length=100, description="Taille standardisée (FK product_attributes.sizes_normalized)")
    size_original: str | None = Field(None, max_length=100, description="Taille originale (FK product_attributes.sizes_original, auto-créée)")

    # DEPRECATED: Use colors (list) instead - Kept for backward compatibility during migration
    color: str | None = Field(None, max_length=100, description="Couleur (FK product_attributes.colors) - DEPRECATED, use colors")
    # NEW M2M: Multiple colors support (max 5 colors)
    colors: list[str] | None = Field(None, max_items=5, description="Liste des couleurs (max 5) - First color = primary")

    # DEPRECATED: Use materials (list) instead - Kept for backward compatibility during migration
    material: str | None = Field(None, max_length=100, description="Matière (FK public.materials) - DEPRECATED, use materials")
    # NEW M2M: Multiple materials support (max 3 materials)
    materials: list[str] | None = Field(None, max_items=3, description="Liste des matériaux (max 3)")
    # OPTIONAL: Material details with percentages
    material_details: list[MaterialDetail] | None = Field(None, max_items=3, description="Détails matériaux avec pourcentages optionnels")
    fit: str | None = Field(None, max_length=100, description="Coupe (FK public.fits)")
    gender: str | None = Field(None, max_length=100, description="Genre (FK public.genders)")
    season: str | None = Field(None, max_length=100, description="Saison (FK public.seasons)")
    sport: str | None = Field(None, max_length=100, description="Sport (FK product_attributes.sports)")
    neckline: str | None = Field(None, max_length=100, description="Encolure (FK product_attributes.necklines)")
    length: str | None = Field(None, max_length=100, description="Longueur (FK product_attributes.lengths)")
    pattern: str | None = Field(None, max_length=100, description="Motif (FK product_attributes.patterns)")

    # Attributs supplémentaires M2M
    # DEPRECATED: Use condition_sups instead - Kept for backward compatibility
    condition_sup: list[str] | None = Field(None, description="Détails état supplémentaires - DEPRECATED, use condition_sups")
    # NEW M2M: Multiple condition supplements (max 10)
    condition_sups: list[str] | None = Field(None, max_items=10, description="Détails état supplémentaires (ex: ['Tache légère', 'Bouton manquant']) - max 10")
    rise: str | None = Field(None, max_length=100, description="Hauteur de taille (pantalons)")
    closure: str | None = Field(None, max_length=100, description="Type de fermeture")
    sleeve_length: str | None = Field(None, max_length=100, description="Longueur de manches")
    origin: str | None = Field(None, max_length=100, description="Origine/provenance")
    decade: str | None = Field(None, max_length=100, description="Décennie")
    trend: str | None = Field(None, max_length=100, description="Tendance")
    location: str | None = Field(None, max_length=100, description="Emplacement physique")
    model: str | None = Field(None, max_length=100, description="Référence modèle")

    # Features descriptifs (JSONB arrays)
    unique_feature: list[str] | None = Field(None, description="Features uniques (JSONB array ex: ['Vintage', 'Logo brodé'])")
    marking: str | None = Field(None, max_length=500, description="Marquages/écritures visibles (dates, codes, textes)")

    # Pricing attributes
    pricing_edit: str | None = Field(None, max_length=100, description="Prix édité manuellement (indicateur)")
    pricing_rarity: str | None = Field(None, max_length=100, description="Rareté pour calcul prix")
    pricing_quality: str | None = Field(None, max_length=100, description="Qualité pour calcul prix")
    pricing_details: str | None = Field(None, max_length=100, description="Détails spécifiques pour calcul prix")
    pricing_style: str | None = Field(None, max_length=100, description="Style pour tarification")

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
    @field_validator('description', 'title')
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

    @field_validator('condition_sup', 'condition_sups', 'unique_feature', 'colors', 'materials')
    @classmethod
    def validate_no_html_in_list(cls, value: list[str] | None) -> list[str] | None:
        """Valide que les éléments d'une liste ne contiennent pas de HTML."""
        if value:
            for item in value:
                if '<' in item or '>' in item:
                    raise ValueError(
                        "HTML tags are not allowed in list items. Please use plain text only."
                    )
        return value

    @field_validator('colors')
    @classmethod
    def validate_colors_no_duplicates(cls, value: list[str] | None) -> list[str] | None:
        """Validate that colors list has no duplicates."""
        if value and len(value) != len(set(value)):
            raise ValueError("Duplicate colors are not allowed")
        return value

    @field_validator('materials')
    @classmethod
    def validate_materials_no_duplicates(cls, value: list[str] | None) -> list[str] | None:
        """Validate that materials list has no duplicates."""
        if value and len(value) != len(set(value)):
            raise ValueError("Duplicate materials are not allowed")
        return value

    @field_validator('condition_sups')
    @classmethod
    def validate_condition_sups_no_duplicates(cls, value: list[str] | None) -> list[str] | None:
        """Validate that condition_sups list has no duplicates."""
        if value and len(value) != len(set(value)):
            raise ValueError("Duplicate condition supplements are not allowed")
        return value

    @field_validator('material_details')
    @classmethod
    def validate_material_details_sum(cls, value: list[MaterialDetail] | None) -> list[MaterialDetail] | None:
        """Validate material percentages sum to 100 if provided (warning only)."""
        if value:
            # Check for duplicates
            materials = [md.material for md in value]
            if len(materials) != len(set(materials)):
                raise ValueError("Duplicate materials in material_details are not allowed")

            # Check percentages sum (warning only, not enforced)
            percentages = [md.percentage for md in value if md.percentage is not None]
            if percentages and sum(percentages) != 100:
                # Note: This is just for info, not blocking
                # In production, log a warning instead of raising
                pass
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
                    "size_normalized": "W32/L34",
                    "size_original": "32 x 34",
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
                    "size_normalized": "L",
                    "size_original": "42 EU",
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
    size_normalized: str | None = Field(None, max_length=100)
    size_original: str | None = Field(None, max_length=100)

    # DEPRECATED: Use colors (list) instead - Kept for backward compatibility
    color: str | None = Field(None, max_length=100, description="DEPRECATED, use colors")
    # NEW M2M: Multiple colors support
    colors: list[str] | None = Field(None, max_items=5, description="Liste des couleurs (max 5)")

    # DEPRECATED: Use materials (list) instead - Kept for backward compatibility
    material: str | None = Field(None, max_length=100, description="DEPRECATED, use materials")
    # NEW M2M: Multiple materials support
    materials: list[str] | None = Field(None, max_items=3, description="Liste des matériaux (max 3)")
    material_details: list[MaterialDetail] | None = Field(None, max_items=3)

    fit: str | None = Field(None, max_length=100)
    gender: str | None = Field(None, max_length=100)
    season: str | None = Field(None, max_length=100)
    sport: str | None = Field(None, max_length=100)
    neckline: str | None = Field(None, max_length=100)
    length: str | None = Field(None, max_length=100)
    pattern: str | None = Field(None, max_length=100)

    # DEPRECATED: Use condition_sups instead - Kept for backward compatibility
    condition_sup: list[str] | None = Field(None, description="DEPRECATED, use condition_sups")
    # NEW M2M: Multiple condition supplements
    condition_sups: list[str] | None = Field(None, max_items=10)

    rise: str | None = Field(None, max_length=100)
    closure: str | None = Field(None, max_length=100)
    sleeve_length: str | None = Field(None, max_length=100)
    origin: str | None = Field(None, max_length=100)
    decade: str | None = Field(None, max_length=100)
    trend: str | None = Field(None, max_length=100)
    location: str | None = Field(None, max_length=100)
    model: str | None = Field(None, max_length=100)

    unique_feature: list[str] | None = Field(None)
    marking: str | None = Field(None, max_length=500)

    # Pricing attributes
    pricing_edit: str | None = Field(None, max_length=100)
    pricing_rarity: str | None = Field(None, max_length=100)
    pricing_quality: str | None = Field(None, max_length=100)
    pricing_details: str | None = Field(None, max_length=100)
    pricing_style: str | None = Field(None, max_length=100)

    dim1: int | None = Field(None, ge=0)
    dim2: int | None = Field(None, ge=0)
    dim3: int | None = Field(None, ge=0)
    dim4: int | None = Field(None, ge=0)
    dim5: int | None = Field(None, ge=0)
    dim6: int | None = Field(None, ge=0)

    stock_quantity: int | None = Field(None, ge=0)

    # ===== SECURITY VALIDATION (2025-12-05): XSS Protection =====
    @field_validator('description', 'title')
    @classmethod
    def validate_no_html(cls, value: str | None) -> str | None:
        """Valide qu'un champ texte ne contient pas de HTML (XSS protection)."""
        if value and ('<' in value or '>' in value):
            raise ValueError(
                "HTML tags are not allowed. Please use plain text only. "
                "Found forbidden characters: < or >"
            )
        return value

    @field_validator('condition_sup', 'condition_sups', 'unique_feature', 'colors', 'materials')
    @classmethod
    def validate_no_html_in_list(cls, value: list[str] | None) -> list[str] | None:
        """Valide que les éléments d'une liste ne contiennent pas de HTML."""
        if value:
            for item in value:
                if '<' in item or '>' in item:
                    raise ValueError(
                        "HTML tags are not allowed in list items. Please use plain text only."
                    )
        return value

    @field_validator('colors')
    @classmethod
    def validate_colors_no_duplicates(cls, value: list[str] | None) -> list[str] | None:
        """Validate that colors list has no duplicates."""
        if value and len(value) != len(set(value)):
            raise ValueError("Duplicate colors are not allowed")
        return value

    @field_validator('materials')
    @classmethod
    def validate_materials_no_duplicates(cls, value: list[str] | None) -> list[str] | None:
        """Validate that materials list has no duplicates."""
        if value and len(value) != len(set(value)):
            raise ValueError("Duplicate materials are not allowed")
        return value

    @field_validator('condition_sups')
    @classmethod
    def validate_condition_sups_no_duplicates(cls, value: list[str] | None) -> list[str] | None:
        """Validate that condition_sups list has no duplicates."""
        if value and len(value) != len(set(value)):
            raise ValueError("Duplicate condition supplements are not allowed")
        return value

    @field_validator('material_details')
    @classmethod
    def validate_material_details_sum(cls, value: list[MaterialDetail] | None) -> list[MaterialDetail] | None:
        """Validate material percentages sum to 100 if provided (warning only)."""
        if value:
            # Check for duplicates
            materials = [md.material for md in value]
            if len(materials) != len(set(materials)):
                raise ValueError("Duplicate materials in material_details are not allowed")

            # Check percentages sum (warning only, not enforced)
            percentages = [md.percentage for md in value if md.percentage is not None]
            if percentages and sum(percentages) != 100:
                # Note: This is just for info, not blocking
                # In production, log a warning instead of raising
                pass
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
    size_normalized: str | None
    size_original: str | None

    # DEPRECATED: Use colors/primary_color instead - Kept for backward compatibility
    color: str | None
    # NEW M2M: Multiple colors support
    colors: list[str] = Field(default_factory=list, description="List of all colors")
    primary_color: str | None = Field(None, description="Primary/dominant color (helper for frontend)")

    # DEPRECATED: Use materials instead - Kept for backward compatibility
    material: str | None
    # NEW M2M: Multiple materials support
    materials: list[str] = Field(default_factory=list, description="List of all materials")

    fit: str | None
    gender: str | None
    season: str | None
    sport: str | None
    neckline: str | None
    length: str | None
    pattern: str | None

    # DEPRECATED: Use condition_sups instead - Kept for backward compatibility
    condition_sup: list[str] | None
    # NEW M2M: Multiple condition supplements
    condition_sups: list[str] = Field(default_factory=list, description="List of condition supplements")

    rise: str | None
    closure: str | None
    sleeve_length: str | None
    origin: str | None
    decade: str | None
    trend: str | None
    location: str | None
    model: str | None

    unique_feature: list[str] | None
    marking: str | None

    # Pricing attributes
    pricing_edit: str | None
    pricing_rarity: str | None
    pricing_quality: str | None
    pricing_details: str | None
    pricing_style: str | None

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
    sold_at: datetime | None
    deleted_at: datetime | None
    created_at: datetime
    updated_at: datetime

    # Images (JSONB)
    images: list[ProductImageItem] = []

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
