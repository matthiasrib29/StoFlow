"""
Security Headers Middleware

Ajoute les headers de sécurité HTTP pour protéger contre diverses attaques.

Business Rules (Security - 2025-12-05):
- HSTS: Force HTTPS pour 1 an (production uniquement)
- X-Frame-Options: DENY (protection clickjacking)
- X-Content-Type-Options: nosniff (protection MIME-sniffing)
- Content-Security-Policy: Bloque inline scripts

Created: 2025-12-05
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from shared.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware pour ajouter les headers de sécurité HTTP.

    Headers ajoutés:
    - X-Frame-Options: DENY
    - X-Content-Type-Options: nosniff
    - Content-Security-Policy: default-src 'self'
    - Strict-Transport-Security: max-age=31536000 (production uniquement)
    """

    async def dispatch(self, request: Request, call_next):
        """Ajoute les security headers à toutes les réponses."""
        response: Response = await call_next(request)

        # ===== X-Frame-Options: Bloque iframe (clickjacking) =====
        response.headers["X-Frame-Options"] = "DENY"

        # ===== X-Content-Type-Options: Empêche MIME-sniffing =====
        response.headers["X-Content-Type-Options"] = "nosniff"

        # ===== Content-Security-Policy: Bloque inline scripts =====
        # Note: 'unsafe-inline' requis pour Swagger UI, à retirer en production
        if settings.is_production:
            csp = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'"
        else:
            # Dev: Autoriser Swagger UI avec CDN jsdelivr.net et fastapi.tiangolo.com
            csp = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "img-src 'self' data: https://fastapi.tiangolo.com; "
                "font-src 'self' https://cdn.jsdelivr.net; "
                "connect-src 'self'"
            )

        response.headers["Content-Security-Policy"] = csp

        # ===== HSTS: Force HTTPS (production uniquement) =====
        if settings.is_production:
            # max-age=31536000 = 1 an
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # ===== X-XSS-Protection: Legacy header (bonus) =====
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # ===== Referrer-Policy: Limite les infos envoyées (bonus) =====
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # ===== Permissions-Policy: Désactive features non utilisées (bonus) =====
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        return response
