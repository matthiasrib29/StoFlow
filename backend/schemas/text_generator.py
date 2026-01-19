"""
Text Generator Schemas

Pydantic schemas for the text generation API.
Input/output validation for SEO title and description generation.

Architecture:
- TextGenerateInput: Request schema for generating text from existing product
- TextPreviewInput: Request schema for preview from raw attributes (before save)
- TextGeneratorOutput: Response schema with all generated titles and descriptions

Created: 2026-01-13
Author: Claude
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TextGenerateInput(BaseModel):
    """
    Input schema for generating text from an existing product.

    Used with the /products/text/generate endpoint to generate
    SEO titles and descriptions for a product already in the database.
    """

    product_id: int = Field(..., description="Product ID to generate text for")
    title_format: Optional[int] = Field(
        None,
        ge=1,
        le=5,
        description="Title format (1=Minimaliste, 2=Standard Vinted, 3=SEO & Mots-clés, 4=Vintage & Collectionneur, 5=Technique & Professionnel)"
    )
    description_style: Optional[int] = Field(
        None,
        ge=1,
        le=5,
        description="Description style (1=Catalogue Structuré, 2=Descriptif Rédigé, 3=Fiche Technique, 4=Vendeur Pro, 5=Visuel Emoji)"
    )


class TextPreviewInput(BaseModel):
    """
    Input schema for preview from raw attributes.

    Used with the /products/text/preview endpoint to preview
    generated text before saving the product. All fields are optional
    to allow partial preview.
    """

    brand: Optional[str] = Field(None, description="Brand name (e.g., 'Levi\\'s')")
    model: Optional[str] = Field(None, description="Model name (e.g., '501')")
    category: Optional[str] = Field(None, description="Product category (e.g., 'jeans')")
    gender: Optional[str] = Field(None, description="Target gender (e.g., 'Men', 'Women')")
    size_normalized: Optional[str] = Field(None, description="Normalized size (e.g., 'W32/L34')")
    colors: Optional[list[str]] = Field(None, description="List of colors")
    material: Optional[str] = Field(None, description="Main material (e.g., 'Denim')")
    fit: Optional[str] = Field(None, description="Fit type (e.g., 'Slim', 'Regular')")
    condition: Optional[int] = Field(
        None,
        ge=0,
        le=10,
        description="Condition score (0-10, where 10 is new)"
    )
    decade: Optional[str] = Field(None, description="Era/decade (e.g., '90s')")
    rise: Optional[str] = Field(None, description="Rise type (e.g., 'Mid-rise')")
    closure: Optional[str] = Field(None, description="Closure type (e.g., 'Button fly')")
    unique_feature: Optional[list[str]] = Field(
        None,
        description="Unique features (e.g., ['Selvedge', 'Raw denim'])"
    )
    pattern: Optional[str] = Field(None, description="Pattern (e.g., 'Solid', 'Striped')")
    trend: Optional[str] = Field(None, description="Trend style (e.g., 'Vintage')")
    season: Optional[str] = Field(None, description="Season (e.g., 'All seasons')")
    origin: Optional[str] = Field(None, description="Country of origin (e.g., 'USA')")
    condition_sup: Optional[list[str]] = Field(
        None,
        description="Condition supplements (e.g., ['Original tags', 'No defects'])"
    )
    neckline: Optional[str] = Field(None, description="Neckline type (e.g., 'V-neck', 'Round')")
    sleeve_length: Optional[str] = Field(None, description="Sleeve length (e.g., 'Long', 'Short')")
    lining: Optional[str] = Field(None, description="Lining material (e.g., 'Polyester', 'Silk')")
    stretch: Optional[str] = Field(None, description="Stretch level (e.g., 'No stretch', 'Slight stretch')")
    sport: Optional[str] = Field(None, description="Sport type if applicable (e.g., 'Running', 'Tennis')")
    length: Optional[str] = Field(None, description="Garment length (e.g., 'Regular', 'Long', 'Cropped')")
    marking: Optional[str] = Field(None, description="Marking/label type (e.g., 'Made in France')")
    location: Optional[str] = Field(None, description="Item location (e.g., 'Paris', 'Lyon')")
    dim1: Optional[float] = Field(None, description="Pit-to-pit measurement in cm")
    dim2: Optional[float] = Field(None, description="Length measurement in cm")
    dim3: Optional[float] = Field(None, description="Shoulder measurement in cm")
    dim4: Optional[float] = Field(None, description="Sleeve measurement in cm")
    dim5: Optional[float] = Field(None, description="Waist measurement in cm")
    dim6: Optional[float] = Field(None, description="Inseam measurement in cm")

    model_config = ConfigDict(from_attributes=True)


class TextGeneratorOutput(BaseModel):
    """
    Output schema with all generated titles and descriptions.

    Contains dictionaries with generated text keyed by format/style name.
    """

    titles: dict[str, str] = Field(
        ...,
        description="Generated titles by format key (minimaliste, standard_vinted, seo_mots_cles, vintage_collectionneur, technique_professionnel)"
    )
    descriptions: dict[str, str] = Field(
        ...,
        description="Generated descriptions by style key (catalogue_structure, descriptif_redige, fiche_technique, vendeur_pro, visuel_emoji)"
    )

    model_config = ConfigDict(from_attributes=True)
