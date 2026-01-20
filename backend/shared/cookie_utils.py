"""
Cookie utilities for secure JWT token storage.

Security (2026-01-20):
- Access tokens stored in httpOnly cookies (XSS protection)
- Refresh tokens stored in httpOnly cookies with restricted path
- CSRF protection via double-submit cookie pattern
"""

import secrets
from typing import Optional

from fastapi import Response

from shared.config import settings
from shared.logging import get_logger

logger = get_logger(__name__)

# Cookie names (constants for consistency)
ACCESS_TOKEN_COOKIE = "access_token"
REFRESH_TOKEN_COOKIE = "refresh_token"
CSRF_TOKEN_COOKIE = "csrf_token"


def _get_cookie_secure() -> bool:
    """
    Determine if cookies should use Secure flag.

    In development mode, we allow non-HTTPS cookies for easier testing.
    In production, Secure flag is always True.
    """
    if settings.is_development:
        return False  # Allow HTTP in dev
    return settings.cookie_secure


def set_access_token_cookie(
    response: Response,
    token: str,
    max_age_seconds: Optional[int] = None
) -> None:
    """
    Set the access token cookie.

    Security:
    - httpOnly: True (prevents JS access, XSS protection)
    - secure: True in production (HTTPS only)
    - samesite: lax (CSRF protection)
    - path: "/" (available on all routes)

    Args:
        response: FastAPI Response object
        token: JWT access token
        max_age_seconds: Cookie expiration (default: access token lifetime)
    """
    if max_age_seconds is None:
        max_age_seconds = settings.jwt_access_token_expire_minutes * 60

    response.set_cookie(
        key=ACCESS_TOKEN_COOKIE,
        value=token,
        max_age=max_age_seconds,
        path="/",
        domain=settings.cookie_domain,
        secure=_get_cookie_secure(),
        httponly=True,
        samesite=settings.cookie_samesite,
    )
    logger.debug(f"Access token cookie set (max_age={max_age_seconds}s)")


def set_refresh_token_cookie(
    response: Response,
    token: str,
    max_age_seconds: Optional[int] = None
) -> None:
    """
    Set the refresh token cookie with restricted path.

    Security:
    - httpOnly: True (prevents JS access, XSS protection)
    - secure: True in production (HTTPS only)
    - samesite: strict (more restrictive for refresh tokens)
    - path: "/api/auth" (only sent to auth endpoints)

    Args:
        response: FastAPI Response object
        token: JWT refresh token
        max_age_seconds: Cookie expiration (default: refresh token lifetime)
    """
    if max_age_seconds is None:
        max_age_seconds = settings.jwt_refresh_token_expire_days * 24 * 60 * 60

    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE,
        value=token,
        max_age=max_age_seconds,
        path="/api/auth",  # Only sent to auth endpoints
        domain=settings.cookie_domain,
        secure=_get_cookie_secure(),
        httponly=True,
        samesite="strict",  # More restrictive for refresh tokens
    )
    logger.debug(f"Refresh token cookie set (max_age={max_age_seconds}s)")


def set_csrf_token_cookie(response: Response, token: Optional[str] = None) -> str:
    """
    Set the CSRF token cookie (readable by JavaScript for double-submit pattern).

    Security:
    - httpOnly: False (JS needs to read it for double-submit)
    - secure: True in production (HTTPS only)
    - samesite: lax (allows cross-site GET but blocks POST)

    The CSRF token must be sent back in the X-CSRF-Token header for
    POST/PUT/PATCH/DELETE requests.

    Args:
        response: FastAPI Response object
        token: Optional CSRF token (generated if not provided)

    Returns:
        The CSRF token (for inclusion in response body if needed)
    """
    if token is None:
        token = secrets.token_urlsafe(32)

    # CSRF cookie should live as long as the session
    max_age_seconds = settings.jwt_refresh_token_expire_days * 24 * 60 * 60

    response.set_cookie(
        key=CSRF_TOKEN_COOKIE,
        value=token,
        max_age=max_age_seconds,
        path="/",
        domain=settings.cookie_domain,
        secure=_get_cookie_secure(),
        httponly=False,  # JS must read this for double-submit
        samesite=settings.cookie_samesite,
    )
    logger.debug("CSRF token cookie set")
    return token


def clear_auth_cookies(response: Response) -> None:
    """
    Clear all authentication cookies on logout.

    Sets cookies with max_age=0 to delete them from the browser.

    Args:
        response: FastAPI Response object
    """
    # Clear access token
    response.delete_cookie(
        key=ACCESS_TOKEN_COOKIE,
        path="/",
        domain=settings.cookie_domain,
    )

    # Clear refresh token (must use same path as when set)
    response.delete_cookie(
        key=REFRESH_TOKEN_COOKIE,
        path="/api/auth",
        domain=settings.cookie_domain,
    )

    # Clear CSRF token
    response.delete_cookie(
        key=CSRF_TOKEN_COOKIE,
        path="/",
        domain=settings.cookie_domain,
    )

    logger.debug("Auth cookies cleared")


def set_auth_cookies(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: Optional[str] = None
) -> str:
    """
    Convenience function to set all auth cookies at once.

    Args:
        response: FastAPI Response object
        access_token: JWT access token
        refresh_token: JWT refresh token
        csrf_token: Optional CSRF token (generated if not provided)

    Returns:
        The CSRF token
    """
    set_access_token_cookie(response, access_token)
    set_refresh_token_cookie(response, refresh_token)
    return set_csrf_token_cookie(response, csrf_token)
