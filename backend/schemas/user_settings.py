"""
User Settings Schemas

Pydantic schemas for user preferences (text generator settings).
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TextGeneratorSettings(BaseModel):
    """User preferences for text generation."""

    default_title_format: Optional[int] = Field(
        None,
        ge=1,
        le=3,
        description="Default title format: 1=Ultra Complete, 2=Technical, 3=Style & Trend"
    )
    default_description_style: Optional[int] = Field(
        None,
        ge=1,
        le=3,
        description="Default description style: 1=Professional, 2=Storytelling, 3=Minimalist"
    )

    model_config = ConfigDict(from_attributes=True)


class TextGeneratorSettingsUpdate(BaseModel):
    """Update schema for text generator settings."""

    default_title_format: Optional[int] = Field(
        None,
        ge=1,
        le=3,
        description="Default title format: 1=Ultra Complete, 2=Technical, 3=Style & Trend"
    )
    default_description_style: Optional[int] = Field(
        None,
        ge=1,
        le=3,
        description="Default description style: 1=Professional, 2=Storytelling, 3=Minimalist"
    )
