"""
Group determination service for pricing algorithm.

Determines which pricing group a product belongs to based on its category and materials.
Handles both variable groups (with material variants) and fixed groups (single group).
"""

from typing import Optional
from .constants import (
    MATERIAL_TYPE_MAPPING,
    MATERIAL_PRIORITY,
    VARIABLE_GROUPS,
    FIXED_GROUPS,
    VARIABLE_CATEGORY_ALIASES,
    VALID_GROUPS,
    MATERIAL_WOOL_LUXURY,
    MATERIAL_SILK_LUXURY,
)


def determine_group(category: str, materials: list[str]) -> str:
    """
    Determine pricing group from category and materials.

    Business Rules:
    1. Normalize category (lowercase, strip whitespace)
    2. If fixed group → return group name directly (ignores materials)
    3. If variable group:
       - Apply category aliases (e.g., chinos → pants)
       - Determine dominant material type using priority
       - Map material type to suffix (wool_luxury → wool, silk_luxury → luxury)
       - Build group name: category_suffix
       - Validate against VALID_GROUPS
       - Fallback if invalid

    Material Priority (highest to lowest):
    LEATHER > SILK_LUXURY > DENIM > WOOL_LUXURY > NATURAL > TECHNICAL > SYNTHETIC

    Args:
        category: Product category (e.g., "jacket", "jeans", "t-shirt")
        materials: List of material names (e.g., ["cotton", "elastane"])

    Returns:
        str: Pricing group (e.g., "jacket_leather", "jeans", "shirt_luxury")

    Raises:
        ValueError: If category is unknown

    Examples:
        >>> determine_group("jacket", ["leather", "cotton"])
        "jacket_leather"  # Leather wins priority

        >>> determine_group("jeans", ["denim", "elastane"])
        "jeans"  # Fixed group, ignores materials

        >>> determine_group("shirt", ["silk"])
        "shirt_luxury"  # Silk maps to luxury for shirts

        >>> determine_group("t-shirt", ["cotton"])
        "tshirt"  # Fixed group

        >>> determine_group("unknown_category", ["cotton"])
        ValueError: Unknown category 'unknown_category'
    """
    # 1. Normalize category
    category_lower = category.lower().strip()

    # 2. Check if fixed group
    if category_lower in FIXED_GROUPS:
        return FIXED_GROUPS[category_lower]

    # 3. Check if variable group
    if category_lower in VARIABLE_GROUPS or category_lower in VARIABLE_CATEGORY_ALIASES:
        # Apply alias if needed
        base_category = VARIABLE_CATEGORY_ALIASES.get(category_lower, category_lower)

        # Determine dominant material type
        material_type = _get_dominant_material_type(materials)

        if material_type:
            # Map material type to group suffix
            suffix = _material_type_to_suffix(material_type, base_category)
            group = f"{base_category}_{suffix}"
        else:
            # Fallback to most common material for category
            group = _get_default_group(base_category)

        # Validate group exists
        if group not in VALID_GROUPS:
            group = _get_default_group(base_category)

        return group

    # 4. Unknown category
    raise ValueError(
        f"Unknown category '{category}'. "
        f"Valid categories: variable groups ({', '.join(list(VARIABLE_GROUPS.keys())[:5])}...) "
        f"or fixed groups ({', '.join(list(FIXED_GROUPS.keys())[:5])}...)"
    )


def _get_dominant_material_type(materials: list[str]) -> Optional[str]:
    """
    Find dominant material type using priority order.

    Args:
        materials: List of material names (case-insensitive)

    Returns:
        Material type constant or None if no match

    Examples:
        >>> _get_dominant_material_type(["cotton", "leather"])
        "leather"  # LEATHER wins

        >>> _get_dominant_material_type(["silk", "polyester"])
        "silk_luxury"  # SILK_LUXURY wins

        >>> _get_dominant_material_type(["wool", "cotton"])
        "wool_luxury"  # WOOL_LUXURY wins over NATURAL
    """
    if not materials:
        return None

    # Normalize and map materials to types
    materials_lower = [m.lower().strip() for m in materials if m]
    material_types = []

    for material in materials_lower:
        material_type = MATERIAL_TYPE_MAPPING.get(material)
        if material_type:
            material_types.append(material_type)

    if not material_types:
        return None

    # Return highest priority material type
    for priority_type in MATERIAL_PRIORITY:
        if priority_type in material_types:
            return priority_type

    return None


def _material_type_to_suffix(material_type: str, category: str) -> str:
    """
    Convert material type constant to group suffix.

    Different categories use different suffixes for luxury materials:
    - shirt, blouse, dress: silk_luxury → "luxury"
    - jacket, coat, pants, etc.: wool_luxury → "wool"

    Args:
        material_type: Material type constant (e.g., "wool_luxury", "silk_luxury")
        category: Base category (e.g., "jacket", "shirt")

    Returns:
        Group suffix (e.g., "wool", "luxury", "natural")

    Examples:
        >>> _material_type_to_suffix("wool_luxury", "jacket")
        "wool"

        >>> _material_type_to_suffix("silk_luxury", "shirt")
        "luxury"

        >>> _material_type_to_suffix("natural", "pants")
        "natural"
    """
    # Silk luxury materials → "luxury" suffix
    if material_type == MATERIAL_SILK_LUXURY:
        return "luxury"

    # Wool luxury materials → "wool" suffix
    if material_type == MATERIAL_WOOL_LUXURY:
        return "wool"

    # All other types use their type name as suffix
    return material_type


def _get_default_group(category: str) -> str:
    """
    Get default group when material is unknown or invalid.

    Defaults chosen based on most common/affordable material per category:
    - Jacket/coat/blazer/pants/skirt: natural (cotton is most common)
    - Shirt/blouse/dress: natural (cotton is most common)

    Args:
        category: Base category (e.g., "jacket", "pants")

    Returns:
        Default group with material suffix

    Examples:
        >>> _get_default_group("jacket")
        "jacket_natural"

        >>> _get_default_group("shirt")
        "shirt_natural"
    """
    # All variable categories default to natural (most common/affordable)
    return f"{category}_natural"
