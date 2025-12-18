"""
Vinted Description Package

Package pour la génération de descriptions SEO optimisées pour Vinted.

Modules:
- hashtag_config: Configuration des hashtags
- translation_helper: Traductions FR/EN
- measurement_extractor: Extraction des mesures par catégorie
- section_builder: Construction des sections de description

Author: Claude
Date: 2025-12-11
"""

from .hashtag_config import HashtagConfig
from .translation_helper import TranslationHelper
from .measurement_extractor import MeasurementExtractor
from .section_builder import SectionBuilder

__all__ = [
    "HashtagConfig",
    "TranslationHelper",
    "MeasurementExtractor",
    "SectionBuilder",
]
