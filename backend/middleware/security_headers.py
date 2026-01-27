"""
Security Headers Middleware (Pure ASGI).

Ajoute les headers de sécurité HTTP pour protéger contre diverses attaques.
Converted from BaseHTTPMiddleware to pure ASGI to avoid Content-Length mismatch
when stacked with other middleware (known Starlette issue).

Business Rules (Security - 2025-12-05):
- HSTS: Force HTTPS pour 1 an (production uniquement)
- X-Frame-Options: DENY (protection clickjacking)
- X-Content-Type-Options: nosniff (protection MIME-sniffing)
- Content-Security-Policy: Bloque inline scripts

Created: 2025-12-05
Updated: 2026-01-27 - Converted to pure ASGI middleware
"""

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from shared.config import settings


class SecurityHeadersMiddleware:
    """
    Pure ASGI middleware pour ajouter les headers de sécurité HTTP.

    Headers ajoutés:
    - X-Frame-Options: DENY
    - X-Content-Type-Options: nosniff
    - Content-Security-Policy: default-src 'self'
    - Strict-Transport-Security: max-age=31536000 (production uniquement)
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_security_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)

                headers.append("X-Frame-Options", "DENY")
                headers.append("X-Content-Type-Options", "nosniff")

                if settings.is_production:
                    csp = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'"
                else:
                    csp = (
                        "default-src 'self'; "
                        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                        "img-src 'self' data: https://fastapi.tiangolo.com; "
                        "font-src 'self' https://cdn.jsdelivr.net; "
                        "connect-src 'self'"
                    )
                headers.append("Content-Security-Policy", csp)

                if settings.is_production:
                    headers.append("Strict-Transport-Security", "max-age=31536000; includeSubDomains")

                headers.append("X-XSS-Protection", "1; mode=block")
                headers.append("Referrer-Policy", "strict-origin-when-cross-origin")
                headers.append("Permissions-Policy", "geolocation=(), microphone=(), camera=()")

            await send(message)

        await self.app(scope, receive, send_with_security_headers)
