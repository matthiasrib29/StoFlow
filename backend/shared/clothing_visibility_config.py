"""
Clothing Attributes Visibility Configuration

Defines which clothing attributes are visible based on the parent category group.
Used by the frontend to conditionally show/hide attribute fields in the product form.
Also used by the AI pipeline to filter attributes sent to the Expert step.
"""

# All 11 clothing attributes
ALL_CLOTHING_ATTRIBUTES = [
    "fit", "season", "sport", "neckline", "length",
    "pattern", "rise", "closure", "sleeve_length", "stretch", "lining"
]

# Tier 1: DB table keys always sent to the AI Expert step
ALWAYS_INCLUDED_DB_KEYS = [
    "categories", "colors", "materials", "conditions",
    "condition_sups", "genders",
]

# Mapping: clothing visibility config key -> DB table key
CLOTHING_ATTR_TO_DB_KEY = {
    "fit": "fits",
    "season": "seasons",
    "sport": "sports",
    "neckline": "necklines",
    "length": "lengths",
    "pattern": "patterns",
    "rise": "rises",
    "closure": "closures",
    "sleeve_length": "sleeve_lengths",
    "stretch": "stretches",
    "lining": "linings",
}

# Mapping: parent category group -> visible clothing attributes
CLOTHING_VISIBILITY_CONFIG = {
    "tops": [
        "fit", "season", "neckline", "length", "pattern",
        "closure", "sleeve_length", "stretch", "lining"
    ],
    "bottoms": [
        "fit", "season", "length", "pattern",
        "rise", "closure", "stretch", "lining"
    ],
    "outerwear": [
        "fit", "season", "length", "pattern",
        "closure", "sleeve_length", "stretch", "lining"
    ],
    "dresses-jumpsuits": [
        "fit", "season", "neckline", "length", "pattern",
        "closure", "sleeve_length", "stretch", "lining"
    ],
    "formalwear": [
        "fit", "season", "length", "pattern",
        "closure", "sleeve_length", "lining"
    ],
    "sportswear": [
        "fit", "season", "sport", "length", "pattern",
        "closure", "sleeve_length", "stretch", "lining"
    ],
}
