"""
Global exception handlers for sanitizing errors before sending to clients.

This middleware prevents information disclosure (OWASP A05:2021) by:
- Masking stack traces from clients
- Logging full error details server-side only
- Returning generic error messages for unexpected exceptions
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from shared.logging import get_logger
from shared.exceptions import (
    StoflowError,
    ValidationError,
    MarketplaceError,
    ServiceError,
    DatabaseError,
)

logger = get_logger(__name__)


async def stoflow_error_handler(request: Request, exc: StoflowError) -> JSONResponse:
    """
    Handle custom StoflowError exceptions.

    These are expected business logic errors that should be shown to users.
    """
    logger.warning(
        f"[ErrorHandler] StoflowError: {exc.__class__.__name__} - {str(exc)}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "error_type": exc.__class__.__name__,
        }
    )

    # Determine status code based on exception type
    status_code = status.HTTP_400_BAD_REQUEST
    if isinstance(exc, ValidationError):
        status_code = status.HTTP_400_BAD_REQUEST
    elif isinstance(exc, DatabaseError):
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    elif isinstance(exc, ServiceError):
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    elif isinstance(exc, MarketplaceError):
        status_code = status.HTTP_502_BAD_GATEWAY

    return JSONResponse(
        status_code=status_code,
        content={
            "detail": str(exc),
            "error_type": exc.__class__.__name__,
        }
    )


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handle Pydantic validation errors.

    Formats validation errors in a user-friendly way.
    """
    logger.info(
        f"[ErrorHandler] ValidationError on {request.url.path}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "errors": exc.errors(),
        }
    )

    # Format validation errors
    formatted_errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        formatted_errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"],
        })

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": formatted_errors,
        }
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    Handle standard HTTPException.

    These are intentional exceptions raised by routes (e.g., 401, 403, 404).
    Pass them through as-is.
    """
    logger.info(
        f"[ErrorHandler] HTTPException {exc.status_code} on {request.url.path}: {exc.detail}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "status_code": exc.status_code,
        }
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers,
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all handler for unexpected exceptions.

    SECURITY CRITICAL:
    - Logs full stack trace server-side
    - Returns generic message to client (no sensitive info)
    - Prevents information disclosure
    """
    logger.error(
        f"[ErrorHandler] Unhandled exception on {request.url.path}: {exc.__class__.__name__}: {str(exc)}",
        exc_info=True,  # Include full stack trace in logs
        extra={
            "path": request.url.path,
            "method": request.method,
            "error_type": exc.__class__.__name__,
        }
    )

    # Return generic error message (no stack trace, no internal details)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal server error occurred. Please try again later."
        }
    )
