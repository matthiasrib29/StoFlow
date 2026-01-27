"""
CSRF Protection Middleware using Double-Submit Cookie Pattern.

Security (2026-01-20):
- Validates X-CSRF-Token header against csrf_token cookie for state-changing requests
- Exempt paths: login, register, webhooks (no session to protect)
- Only applies to POST, PUT, PATCH, DELETE methods

How it works:
1. On login, server sets csrf_token cookie (readable by JS)
2. Frontend reads the cookie and includes value in X-CSRF-Token header
3. This middleware compares header value with cookie value
4. If they match, request is allowed; if not, 403 Forbidden
"""

from typing import Set

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse

from shared.config import settings
from shared.cookie_utils import CSRF_TOKEN_COOKIE
from shared.logging import get_logger

logger = get_logger(__name__)

# HTTP methods that require CSRF protection (state-changing)
CSRF_PROTECTED_METHODS: Set[str] = {"POST", "PUT", "PATCH", "DELETE"}

# Paths exempt from CSRF protection (no session to protect or external webhooks)
CSRF_EXEMPT_PATHS: Set[str] = {
    "/api/auth/login",
    "/api/auth/register",
    "/api/auth/refresh",    # Protected by httpOnly samesite=strict cookie
    "/api/auth/logout",     # Logout should always work (clears cookies)
    "/api/auth/verify-email",
    "/api/auth/resend-verification",
    "/api/auth/forgot-password",
    "/api/auth/reset-password",
    "/api/stripe/webhook",  # Stripe webhook (has its own signature verification)
    "/api/ebay/webhook",    # eBay webhook (has its own verification)
}

# Path prefixes exempt from CSRF (for flexibility)
CSRF_EXEMPT_PREFIXES: tuple = (
    "/api/stripe/",  # All Stripe webhooks
    "/api/ebay/webhook/",  # All eBay webhooks
)


def _is_csrf_exempt(path: str) -> bool:
    """Check if a path is exempt from CSRF protection."""
    # Exact path match
    if path in CSRF_EXEMPT_PATHS:
        return True

    # Prefix match
    if path.startswith(CSRF_EXEMPT_PREFIXES):
        return True

    return False


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    Double-Submit Cookie CSRF Protection Middleware.

    For protected methods (POST, PUT, PATCH, DELETE), validates that the
    X-CSRF-Token header matches the csrf_token cookie value.

    Security considerations:
    - Cookie is SameSite=Lax, preventing cross-site form submissions
    - JS-readable cookie + header requirement prevents CSRF attacks
    - Works with both same-origin and CORS-enabled requests (with credentials)
    """

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint
    ) -> Response:
        # Skip CSRF check for safe methods (GET, HEAD, OPTIONS)
        if request.method not in CSRF_PROTECTED_METHODS:
            return await call_next(request)

        # Skip CSRF check for exempt paths
        if _is_csrf_exempt(request.url.path):
            return await call_next(request)

        # Skip CSRF check if no auth cookie present (not logged in)
        # This allows public POST endpoints to work
        csrf_cookie = request.cookies.get(CSRF_TOKEN_COOKIE)
        if not csrf_cookie:
            # No CSRF cookie = no session to protect
            # Let the auth dependency handle authentication
            return await call_next(request)

        # Get CSRF token from header
        csrf_header = request.headers.get("X-CSRF-Token")

        # Validate: header must match cookie
        if not csrf_header or csrf_header != csrf_cookie:
            logger.warning(
                f"CSRF validation failed: path={request.url.path}, "
                f"method={request.method}, "
                f"has_cookie={bool(csrf_cookie)}, "
                f"has_header={bool(csrf_header)}, "
                f"match={csrf_header == csrf_cookie if csrf_header else False}"
            )
            return JSONResponse(
                status_code=403,
                content={
                    "detail": "CSRF validation failed. Please refresh the page and try again."
                }
            )

        return await call_next(request)
