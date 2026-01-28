"""
Error Classification for marketplace API calls.

Classifies errors as retryable or non-retryable to avoid wasting retries
on permanent failures (e.g., validation errors, auth errors).

Issue #21 - Business Logic Audit.
"""
from shared.exceptions import (
    MarketplaceAuthError,
    MarketplaceRateLimitError,
    MarketplaceConnectionError,
    ValidationError,
    ProductValidationError,
    CategoryMappingError,
)

# HTTP status codes that indicate transient failures (worth retrying)
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}

# Exceptions that are always retryable (transient)
RETRYABLE_EXCEPTIONS = (
    ConnectionError,
    TimeoutError,
    OSError,
    MarketplaceRateLimitError,
    MarketplaceConnectionError,
)

# Exceptions that are never retryable (permanent)
NON_RETRYABLE_EXCEPTIONS = (
    ValueError,
    TypeError,
    MarketplaceAuthError,
    ValidationError,
    ProductValidationError,
    CategoryMappingError,
)


def classify_error(error: Exception) -> str:
    """
    Classify an error as retryable or non-retryable.

    Args:
        error: The exception to classify.

    Returns:
        "retryable" or "non_retryable"
    """
    if isinstance(error, NON_RETRYABLE_EXCEPTIONS):
        return "non_retryable"

    if isinstance(error, RETRYABLE_EXCEPTIONS):
        return "retryable"

    # Check for HTTP status codes on marketplace errors
    status_code = getattr(error, "status_code", None)
    if status_code is not None:
        if status_code in RETRYABLE_STATUS_CODES:
            return "retryable"
        if 400 <= status_code < 500:
            return "non_retryable"

    # Default: retryable (safer for unknown errors)
    return "retryable"


def is_retryable(error: Exception) -> bool:
    """
    Check if an error is retryable.

    Args:
        error: The exception to check.

    Returns:
        True if the error is retryable.
    """
    return classify_error(error) == "retryable"
