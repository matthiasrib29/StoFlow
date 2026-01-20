"""
Auth Dependencies

Helpers and factories for authentication routes.
"""

from fastapi import Request

from middleware.auth_rate_limit import get_auth_rate_limiter


async def apply_rate_limit(request: Request, action: str) -> None:
    """
    Apply rate limiting for auth actions.

    Args:
        request: FastAPI Request object
        action: Rate limit action (login, refresh, register, verify_email, resend_verification)
    """
    rate_limiter = get_auth_rate_limiter()
    await rate_limiter.check_rate_limit(request, action)
