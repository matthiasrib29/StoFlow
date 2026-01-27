"""
Marketplace-specific validation rules for prices, titles, and descriptions.

Each marketplace has different limits for product data. This module
provides validation functions to catch issues before publication.

Issues #4, #26 - Business Logic Audit.
"""

MARKETPLACE_LIMITS = {
    "vinted": {
        "min_price": 1.00,
        "max_price": 30000,
        "max_title": 150,
        "max_description": 2000,
    },
    "ebay": {
        "min_price": 0.99,
        "max_price": 99999,
        "max_title": 80,
        "max_description": 4000,
    },
    "etsy": {
        "min_price": 0.20,
        "max_price": 50000,
        "max_title": 140,
        "max_description": 13000,
    },
}


def validate_price_for_marketplace(price: float, marketplace: str) -> list[str]:
    """
    Validate price against marketplace limits.

    Args:
        price: Product price.
        marketplace: Marketplace name (vinted, ebay, etsy).

    Returns:
        List of validation errors (empty if valid).
    """
    limits = MARKETPLACE_LIMITS.get(marketplace)
    if not limits:
        return []

    errors = []
    if price < limits["min_price"]:
        errors.append(
            f"Price {price} is below {marketplace} minimum ({limits['min_price']})"
        )
    if price > limits["max_price"]:
        errors.append(
            f"Price {price} exceeds {marketplace} maximum ({limits['max_price']})"
        )
    return errors


def validate_title_for_marketplace(title: str, marketplace: str) -> list[str]:
    """
    Validate title length against marketplace limits.

    Args:
        title: Product title.
        marketplace: Marketplace name.

    Returns:
        List of validation errors.
    """
    limits = MARKETPLACE_LIMITS.get(marketplace)
    if not limits or not title:
        return []

    errors = []
    max_len = limits["max_title"]
    if len(title) > max_len:
        errors.append(
            f"Title length ({len(title)}) exceeds {marketplace} maximum ({max_len})"
        )
    return errors


def validate_description_for_marketplace(
    description: str, marketplace: str
) -> list[str]:
    """
    Validate description length against marketplace limits.

    Args:
        description: Product description.
        marketplace: Marketplace name.

    Returns:
        List of validation errors.
    """
    limits = MARKETPLACE_LIMITS.get(marketplace)
    if not limits or not description:
        return []

    errors = []
    max_len = limits["max_description"]
    if len(description) > max_len:
        errors.append(
            f"Description length ({len(description)}) exceeds "
            f"{marketplace} maximum ({max_len})"
        )
    return errors


def validate_product_for_marketplace(
    product, marketplace: str
) -> list[str]:
    """
    Validate all product fields against marketplace limits.

    Args:
        product: Product object (must have price, title, description attributes).
        marketplace: Marketplace name.

    Returns:
        List of all validation errors.
    """
    errors = []

    if product.price is not None:
        errors.extend(validate_price_for_marketplace(float(product.price), marketplace))

    if product.title:
        errors.extend(validate_title_for_marketplace(product.title, marketplace))

    if product.description:
        errors.extend(
            validate_description_for_marketplace(product.description, marketplace)
        )

    return errors
