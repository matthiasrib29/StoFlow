"""
Custom Exceptions for Stoflow

Exceptions personnalisées pour une meilleure gestion des erreurs.

Includes:
- Exception hierarchy for all domains
- HTTP error helpers (not_found, bad_request, etc.)

Author: Claude
Date: 2025-12-11
Updated: 2026-01-20 - Added HTTP error helpers from error_handling.py
"""

from functools import wraps
from typing import Callable

from fastapi import HTTPException, status


class StoflowError(Exception):
    """Exception de base pour toutes les erreurs Stoflow."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


# ===== DATABASE EXCEPTIONS =====

class DatabaseError(StoflowError):
    """Erreur liée à la base de données."""
    pass


class SchemaCreationError(DatabaseError):
    """Erreur lors de la création d'un schema."""
    pass


class SchemaNotFoundError(DatabaseError):
    """Schema utilisateur non trouvé."""
    pass


class NotFoundError(DatabaseError):
    """Resource not found in database."""
    pass


# ===== API EXCEPTIONS =====

class APIError(StoflowError):
    """Erreur liée aux appels API externes."""
    pass


class APIConnectionError(APIError):
    """Erreur de connexion à une API externe."""
    pass


class APIAuthenticationError(APIError):
    """Erreur d'authentification API."""
    pass


class APIRateLimitError(APIError):
    """Rate limit atteint sur une API."""
    pass


class APIValidationError(APIError):
    """Données invalides retournées par l'API."""
    pass


# ===== MARKETPLACE EXCEPTIONS =====

class MarketplaceError(StoflowError):
    """
    Erreur liée aux marketplaces (Vinted, eBay, Etsy).

    Attributes:
        platform: Nom de la plateforme (vinted, ebay, etsy)
        operation: Type d'opération (publish, update, delete, connect, import)
        status_code: Code HTTP de la réponse (optionnel)
        response_body: Corps de la réponse d'erreur (optionnel)
    """

    def __init__(
        self,
        message: str,
        platform: str = None,
        operation: str = None,
        status_code: int = None,
        response_body: dict = None,
        details: dict = None,
    ):
        super().__init__(message, details=details or {})
        self.platform = platform
        self.operation = operation
        self.status_code = status_code
        self.response_body = response_body

        # Enrichir details
        self.details.update({
            "platform": platform,
            "operation": operation,
            "status_code": status_code,
        })

    def to_dict(self) -> dict:
        """Convertit l'erreur en dictionnaire pour les réponses API."""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "platform": self.platform,
            "operation": self.operation,
            "status_code": self.status_code,
            "details": self.details,
        }


class MarketplaceConnectionError(MarketplaceError):
    """Erreur de connexion à une marketplace."""

    def __init__(self, platform: str, message: str = None, **kwargs):
        super().__init__(
            message=message or f"Impossible de se connecter à {platform}",
            platform=platform,
            operation="connect",
            **kwargs
        )


class MarketplacePublishError(MarketplaceError):
    """Erreur lors de la publication sur une marketplace."""

    def __init__(self, platform: str, message: str = None, **kwargs):
        super().__init__(
            message=message or f"Échec de publication sur {platform}",
            platform=platform,
            operation="publish",
            **kwargs
        )


class MarketplaceUpdateError(MarketplaceError):
    """Erreur lors de la mise à jour sur une marketplace."""

    def __init__(self, platform: str, message: str = None, **kwargs):
        super().__init__(
            message=message or f"Échec de mise à jour sur {platform}",
            platform=platform,
            operation="update",
            **kwargs
        )


class MarketplaceDeleteError(MarketplaceError):
    """Erreur lors de la suppression sur une marketplace."""

    def __init__(self, platform: str, message: str = None, **kwargs):
        super().__init__(
            message=message or f"Échec de suppression sur {platform}",
            platform=platform,
            operation="delete",
            **kwargs
        )


class MarketplaceImportError(MarketplaceError):
    """Erreur lors de l'import depuis une marketplace."""

    def __init__(self, platform: str, message: str = None, **kwargs):
        super().__init__(
            message=message or f"Échec d'import depuis {platform}",
            platform=platform,
            operation="import",
            **kwargs
        )


class MarketplaceRateLimitError(MarketplaceError):
    """Rate limit atteint sur une marketplace."""

    def __init__(self, platform: str, retry_after: int = None, **kwargs):
        super().__init__(
            message=f"Rate limit atteint sur {platform}. Réessayez dans {retry_after}s" if retry_after else f"Rate limit atteint sur {platform}",
            platform=platform,
            operation=kwargs.pop("operation", None),
            details={"retry_after": retry_after},
            **kwargs
        )
        self.retry_after = retry_after


class MarketplaceAuthError(MarketplaceError):
    """Erreur d'authentification avec une marketplace."""

    def __init__(self, platform: str, message: str = None, **kwargs):
        super().__init__(
            message=message or f"Authentification échouée avec {platform}. Veuillez vous reconnecter.",
            platform=platform,
            operation="auth",
            **kwargs
        )


class VintedError(MarketplaceError):
    """Erreur spécifique à Vinted."""

    def __init__(self, message: str, operation: str = None, **kwargs):
        super().__init__(message, platform="vinted", operation=operation, **kwargs)


class VintedConnectionError(VintedError):
    """Erreur de connexion à Vinted."""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(
            message=message or "Impossible de se connecter à Vinted",
            operation="connect",
            **kwargs
        )


class VintedPublishError(VintedError):
    """Erreur lors de la publication sur Vinted."""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(
            message=message or "Échec de publication sur Vinted",
            operation="publish",
            **kwargs
        )


class VintedImportError(VintedError):
    """Erreur lors de l'import depuis Vinted."""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(
            message=message or "Échec d'import depuis Vinted",
            operation="import",
            **kwargs
        )


class VintedAPIError(VintedError):
    """Erreur retournée par l'API Vinted (non-200)."""

    def __init__(self, message: str, status_code: int = None, response_body: dict = None, **kwargs):
        super().__init__(
            message=message,
            status_code=status_code,
            response_body=response_body,
            **kwargs
        )


class AllStepsCompleted(Exception):
    """Exception signal indiquant que tous les steps d'une queue sont terminés."""
    pass


class TaskCancelledError(StoflowError):
    """Erreur indiquant qu'une tâche a été annulée."""
    pass


class EbayError(MarketplaceError):
    """Erreur spécifique à eBay."""

    def __init__(self, message: str, operation: str = None, **kwargs):
        super().__init__(message, platform="ebay", operation=operation, **kwargs)


class EbayOAuthError(EbayError):
    """Erreur OAuth avec eBay."""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(
            message=message or "Authentification eBay échouée",
            operation="auth",
            **kwargs
        )


class EbayPublishError(EbayError):
    """Erreur lors de la publication sur eBay."""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(
            message=message or "Échec de publication sur eBay",
            operation="publish",
            **kwargs
        )


class EbayAPIError(EbayError):
    """Erreur retournée par l'API eBay."""

    def __init__(self, message: str, status_code: int = None, response_body: dict = None, **kwargs):
        super().__init__(
            message=message,
            status_code=status_code,
            response_body=response_body,
            **kwargs
        )


class EtsyError(MarketplaceError):
    """Erreur spécifique à Etsy."""

    def __init__(self, message: str, operation: str = None, **kwargs):
        super().__init__(message, platform="etsy", operation=operation, **kwargs)


class EtsyOAuthError(EtsyError):
    """Erreur OAuth avec Etsy."""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(
            message=message or "Authentification Etsy échouée",
            operation="auth",
            **kwargs
        )


class EtsyPublishError(EtsyError):
    """Erreur lors de la publication sur Etsy."""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(
            message=message or "Échec de publication sur Etsy",
            operation="publish",
            **kwargs
        )


class EtsyAPIError(EtsyError):
    """Erreur retournée par l'API Etsy."""

    def __init__(self, message: str, status_code: int = None, response_body: dict = None, **kwargs):
        super().__init__(
            message=message,
            status_code=status_code,
            response_body=response_body,
            **kwargs
        )


# ===== FILE EXCEPTIONS =====

class FileError(StoflowError):
    """Erreur liée aux fichiers."""
    pass


class StoflowFileNotFoundError(FileError):
    """Fichier non trouvé."""
    pass


class FileUploadError(FileError):
    """Erreur lors de l'upload d'un fichier."""
    pass


class ImageProcessingError(FileError):
    """Erreur lors du traitement d'une image."""
    pass


# ===== VALIDATION EXCEPTIONS =====

class ValidationError(StoflowError):
    """Erreur de validation des données."""
    pass


class ProductValidationError(ValidationError):
    """Erreur de validation d'un produit."""
    pass


class CategoryMappingError(ValidationError):
    """Erreur de mapping de catégorie."""
    pass


# ===== SERVICE EXCEPTIONS =====

class ServiceError(StoflowError):
    """Erreur dans un service métier."""
    pass


class SKUGenerationError(ServiceError):
    """Erreur lors de la génération d'un SKU."""
    pass


class TaskExecutionError(ServiceError):
    """Erreur lors de l'exécution d'une tâche."""
    pass


class ConcurrentModificationError(ServiceError):
    """
    Erreur de modification concurrente détectée (optimistic locking).

    Raised when a version_number mismatch indicates another transaction
    modified the same resource between read and update.

    Client should:
    1. Fetch latest version
    2. Re-apply changes
    3. Retry operation
    """
    pass


class ConflictError(ServiceError):
    """
    Conflict error when a resource is locked by another worker.

    Used with SELECT FOR UPDATE to prevent concurrent modifications.
    Different from ConcurrentModificationError which is for optimistic locking.

    Client should:
    1. Retry after a short delay
    2. Or give up and report to user
    """
    pass


class OutOfStockError(ServiceError):
    """
    Erreur de stock insuffisant pour l'opération demandée.

    Raised when:
    - Trying to mark as SOLD a product already out of stock
    - Atomic stock decrement fails due to concurrent sale
    """
    pass


# ===== AI EXCEPTIONS =====

class AIError(StoflowError):
    """Erreur liée aux services IA."""
    pass


class AIQuotaExceededError(AIError):
    """Crédits IA insuffisants."""
    pass


class AIGenerationError(AIError):
    """Erreur lors de la génération IA."""
    pass


# ===== PRICING EXCEPTIONS =====

class PricingError(ServiceError):
    """Base exception for pricing-related errors."""
    pass


class GroupDeterminationError(PricingError):
    """Raised when group cannot be determined from category/materials."""
    def __init__(self, category: str, materials: list[str]):
        self.category = category
        self.materials = materials
        super().__init__(f"Cannot determine group for category '{category}' with materials {materials}")


class BrandGroupGenerationError(PricingError):
    """Raised when BrandGroup generation fails after retries."""
    def __init__(self, brand: str, group: str, reason: str):
        self.brand = brand
        self.group = group
        super().__init__(f"Failed to generate BrandGroup for {brand}/{group}: {reason}")


class ModelGenerationError(PricingError):
    """Raised when Model generation fails after retries."""
    def __init__(self, brand: str, group: str, model: str, reason: str):
        self.brand = brand
        self.group = group
        self.model = model
        super().__init__(f"Failed to generate Model for {brand}/{group}/{model}: {reason}")


class PricingCalculationError(PricingError):
    """Raised when price calculation fails."""
    pass


# =============================================================================
# HTTP ERROR HELPERS
# =============================================================================


def with_rollback(db):
    """
    Decorator to automatically rollback database on exceptions.

    Usage:
        @with_rollback(db)
        def some_operation():
            db.add(item)
            # If exception occurs, db will be rolled back

    Note: For routes, prefer letting exceptions bubble up.
          This is mainly for service layer methods.
    """
    from shared.logging import get_logger
    logger = get_logger(__name__)

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                db.rollback()
                logger.error(f"[{func.__name__}] Exception occurred, rolled back: {e}", exc_info=True)
                raise
        return wrapper
    return decorator


def business_error(message: str, status_code: int = status.HTTP_400_BAD_REQUEST) -> HTTPException:
    """
    Create HTTPException for business logic errors.

    Args:
        message: User-facing error message
        status_code: HTTP status code (default 400 Bad Request)

    Returns:
        HTTPException ready to be raised

    Usage:
        if not item:
            raise business_error("Item not found", status.HTTP_404_NOT_FOUND)
    """
    return HTTPException(status_code=status_code, detail=message)


def not_found(resource: str, identifier: int | str) -> HTTPException:
    """
    Create 404 Not Found exception with consistent message format.

    Args:
        resource: Type of resource (e.g., "Product", "User", "Order")
        identifier: ID or identifier of the resource

    Returns:
        HTTPException with 404 status

    Usage:
        if not product:
            raise not_found("Product", product_id)
    """
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"{resource} #{identifier} not found"
    )


def forbidden(message: str = "Access forbidden") -> HTTPException:
    """
    Create 403 Forbidden exception.

    Args:
        message: Reason for forbidden access

    Returns:
        HTTPException with 403 status
    """
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=message
    )


def bad_request(message: str) -> HTTPException:
    """
    Create 400 Bad Request exception.

    Args:
        message: Validation or business rule error

    Returns:
        HTTPException with 400 status
    """
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=message
    )


def unauthorized(message: str = "Authentication required") -> HTTPException:
    """
    Create 401 Unauthorized exception.

    Args:
        message: Reason for unauthorized access

    Returns:
        HTTPException with 401 status
    """
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=message
    )


def internal_error(message: str = "Internal server error occurred") -> HTTPException:
    """
    Create 500 Internal Server Error exception.

    Note: Prefer letting exceptions bubble up to global handler.
          Only use when you need to catch and transform specific errors.

    Args:
        message: Error description (will be logged)

    Returns:
        HTTPException with 500 status
    """
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=message
    )


__all__ = [
    # Base
    "StoflowError",

    # Database
    "DatabaseError",
    "SchemaCreationError",
    "SchemaNotFoundError",

    # API
    "APIError",
    "APIConnectionError",
    "APIAuthenticationError",
    "APIRateLimitError",
    "APIValidationError",

    # Marketplace - Base
    "MarketplaceError",
    "MarketplaceConnectionError",
    "MarketplacePublishError",
    "MarketplaceUpdateError",
    "MarketplaceDeleteError",
    "MarketplaceImportError",
    "MarketplaceRateLimitError",
    "MarketplaceAuthError",

    # Marketplace - Vinted
    "VintedError",
    "VintedConnectionError",
    "VintedPublishError",
    "VintedImportError",
    "VintedAPIError",

    # Marketplace - eBay
    "EbayError",
    "EbayOAuthError",
    "EbayPublishError",
    "EbayAPIError",

    # Marketplace - Etsy
    "EtsyError",
    "EtsyOAuthError",
    "EtsyPublishError",
    "EtsyAPIError",

    # Task
    "AllStepsCompleted",
    "TaskCancelledError",

    # File
    "FileError",
    "StoflowFileNotFoundError",
    "FileUploadError",
    "ImageProcessingError",

    # Validation
    "ValidationError",
    "ProductValidationError",
    "CategoryMappingError",

    # Service
    "ServiceError",
    "SKUGenerationError",
    "TaskExecutionError",
    "ConcurrentModificationError",
    "OutOfStockError",

    # AI
    "AIError",
    "AIQuotaExceededError",
    "AIGenerationError",

    # Pricing
    "PricingError",
    "GroupDeterminationError",
    "BrandGroupGenerationError",
    "ModelGenerationError",
    "PricingCalculationError",

    # HTTP Error Helpers
    "with_rollback",
    "business_error",
    "not_found",
    "forbidden",
    "bad_request",
    "unauthorized",
    "internal_error",
]
