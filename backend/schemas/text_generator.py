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
        le=3,
        description="Title format (1=Ultra Complete, 2=Technical, 3=Style & Trend)"
    )
    description_style: Optional[int] = Field(
        None,
        ge=1,
        le=3,
        description="Description style (1=Professional, 2=Storytelling, 3=Minimalist)"
    )


class TextPreviewInput(BaseModel):
    """
    Input schema for preview from raw attributes.

    Used with the /products/text/preview endpoint to preview
    generated text before saving the product. All fields are optional
    to allow partial preview.
    """

    brand: Optional[str] = Field(None, description="Brand name (e.g., 'Levi\\'s')")
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

    model_config = ConfigDict(from_attributes=True)


class TextGeneratorOutput(BaseModel):
    """
    Output schema with all generated titles and descriptions.

    Contains dictionaries with generated text keyed by format/style name.
    """

    titles: dict[str, str] = Field(
        ...,
        description="Generated titles by format key (ultra_complete, technical, style_trend)"
    )
    descriptions: dict[str, str] = Field(
        ...,
        description="Generated descriptions by style key (professional, storytelling, minimalist)"
    )

    model_config = ConfigDict(from_attributes=True)
