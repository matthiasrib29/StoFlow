"""
eBay schema models.

All eBay-related tables are stored in the 'ebay' PostgreSQL schema.
"""

from models.ebay.aspect_value import (
    AspectColour,
    AspectSize,
    AspectMaterial,
    AspectFit,
    AspectClosure,
    AspectRise,
    AspectWaistSize,
    AspectInsideLeg,
    AspectDepartment,
    AspectType,
    AspectStyle,
    AspectPattern,
    AspectNeckline,
    AspectSleeveLength,
    AspectOccasion,
    AspectFeatures,
    ASPECT_VALUE_MODELS,
    get_aspect_translation,
)

__all__ = [
    'AspectColour',
    'AspectSize',
    'AspectMaterial',
    'AspectFit',
    'AspectClosure',
    'AspectRise',
    'AspectWaistSize',
    'AspectInsideLeg',
    'AspectDepartment',
    'AspectType',
    'AspectStyle',
    'AspectPattern',
    'AspectNeckline',
    'AspectSleeveLength',
    'AspectOccasion',
    'AspectFeatures',
    'ASPECT_VALUE_MODELS',
    'get_aspect_translation',
]
