"""
Group determination service for pricing algorithm.

Determines which pricing group a product belongs to based on its category and materials.
Uses material priority logic to resolve conflicts when multiple materials are present.
"""

from typing import Optional
from .constants import (
    MATERIAL_TYPE_MAPPING,
    MATERIAL_PRIORITY,
    CATEGORY_GROUP_MAPPING,
    VALID_GROUPS,
)


def determine_group(category: str, materials: list[str]) -> str:
    """
    Determine pricing group from category and materials.

    Business Rules:
    1. Normalize category to base group (e.g., "blazer" → "jacket")
    2. If jeans → always return "jeans" (no material suffix)
    3. Determine dominant material type using priority order
    4. Combine category + material type → group
    5. Validate group exists in VALID_GROUPS
    6. Fallback to generic group if no material match

    Material Priority (highest to lowest):
    LEATHER > DENIM > WOOL_LUXURY > NATURAL > TECHNICAL > SYNTHETIC

    Args:
        category: Product category (e.g., "jacket", "jeans", "shirt")
        materials: List of material names (e.g., ["cotton", "elastane"])

    Returns:
        str: Pricing group (e.g., "jacket_leather", "jeans", "shirt_natural")

    Raises:
        ValueError: If category is unknown or invalid

    Examples:
        >>> determine_group("jacket", ["leather", "cotton"])
        "jacket_leather"  # Leather wins priority

        >>> determine_group("jeans", ["denim", "elastane"])
        "jeans"  # Jeans always return "jeans"

        >>> determine_group("shirt", ["silk"])
        "shirt_luxury"  # Silk is luxury material

        >>> determine_group("t-shirt", [])
        "tshirt_natural"  # Default fallback for empty materials

        >>> determine_group("unknown_category", ["cotton"])
        ValueError: Unknown category 'unknown_category'
    """
    # 1. Normalize category
    category_lower = category.lower().strip()
    base_group = CATEGORY_GROUP_MAPPING.get(category_lower)

    if not base_group:
        raise ValueError(
            f"Unknown category '{category}'. Valid categories: "
            f"{', '.join(sorted(set(CATEGORY_GROUP_MAPPING.keys()))[:10])}..."
        )

    # 2. Special case: jeans always return "jeans"
    if base_group == "jeans":
        return "jeans"

    # 3. Determine dominant material type
    material_type = _get_dominant_material_type(materials)

    # 4. Build group name
    if material_type:
        group = f"{base_group}_{material_type}"
    else:
        # Fallback: use default material for category
        group = _get_default_group(base_group)

    # 5. Validate group exists
    if group not in VALID_GROUPS:
        # Fallback to most common variant
        group = _get_default_group(base_group)

    return group


def _get_dominant_material_type(materials: list[str]) -> Optional[str]:
    """
    Find dominant material type using priority order.

    When a product has multiple materials, the highest priority material
    determines the group. For example, a jacket with "cotton" and "leather"
    will be classified as leather because LEATHER has higher priority.

    Args:
        materials: List of material names (case-insensitive)

    Returns:
        Material type (e.g., "leather", "natural") or None if no match

    Examples:
        >>> _get_dominant_material_type(["cotton", "leather"])
        "leather"  # Leather wins

        >>> _get_dominant_material_type(["polyester", "wool"])
        "wool_luxury"  # Wool wins over polyester

        >>> _get_dominant_material_type(["cotton", "elastane"])
        "natural"  # Cotton wins (both map to different types, natural is higher)

        >>> _get_dominant_material_type([])
        None  # No materials

        >>> _get_dominant_material_type(["unknown_material"])
        None  # Unknown material ignored
    """
    if not materials:
        return None

    # Normalize materials to lowercase
    materials_lower = [m.lower().strip() for m in materials if m]

    # Map materials to types
    material_types = []
    for material in materials_lower:
        material_type = MATERIAL_TYPE_MAPPING.get(material)
        if material_type:
            material_types.append(material_type)

    if not material_types:
        return None

    # Return highest priority material
    for priority_type in MATERIAL_PRIORITY:
        if priority_type in material_types:
            return priority_type

    return None


def _get_default_group(base_group: str) -> str:
    """
    Get default group when material is unknown or group is invalid.

    Defaults are chosen based on the most common material for each category:
    - Jackets: natural (cotton/linen jackets most common)
    - Pants: natural (chinos, cotton pants)
    - Shirts: natural (cotton shirts most common)
    - T-shirts: natural (cotton is standard)
    - Sweaters: natural (cotton sweaters common)
    - Dresses: natural (cotton dresses common)
    - Skirts: natural (cotton skirts common)
    - Shoes: synthetic (most affordable shoes are synthetic)
    - Bags: synthetic (most bags are synthetic/nylon)
    - Accessories: natural (cotton/linen accessories common)

    Args:
        base_group: Base category group (e.g., "jacket", "pants")

    Returns:
        Default group with material suffix (e.g., "jacket_natural")

    Examples:
        >>> _get_default_group("jacket")
        "jacket_natural"

        >>> _get_default_group("shoes")
        "shoes_synthetic"

        >>> _get_default_group("unknown_category")
        "unknown_category_natural"  # Safe fallback
    """
    defaults = {
        "jacket": "jacket_natural",
        "pants": "pants_natural",
        "shorts": "shorts_natural",
        "shirt": "shirt_natural",
        "tshirt": "tshirt_natural",
        "sweater": "sweater_natural",
        "dress": "dress_natural",
        "skirt": "skirt_natural",
        "shoes": "shoes_synthetic",
        "bag": "bag_synthetic",
        "accessory": "accessory_natural",
    }
    return defaults.get(base_group, f"{base_group}_natural")
