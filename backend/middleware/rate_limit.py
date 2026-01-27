"""
Rate Limiting Middleware (Pure ASGI).

Protection contre bruteforce attacks sur endpoints sensibles.
Converted from function middleware to pure ASGI to avoid Content-Length mismatch
when stacked with other middleware (known Starlette BaseHTTPMiddleware issue).

Business Rules (Security - 2025-12-18):
- /auth/login:
  - 10 tentatives / 5 minutes par IP
  - 5 tentatives / 5 minutes par EMAIL (plus strict, anti credential stuffing)
- Stockage en mémoire (simple dict avec cleanup)
- Retourne 429 Too Many Requests si dépassé
- DÉSACTIVÉ en mode TESTING (os.getenv("TESTING") == "1")

Created: 2025-12-05
Updated: 2025-12-18 - Ajout rate limiting par email
Updated: 2026-01-27 - Converted to pure ASGI middleware
"""

import json
import os
import time
from collections import defaultdict
from typing import Optional

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from shared.logging import get_logger

logger = get_logger(__name__)


class RateLimitStore:
    """
    Simple in-memory store pour rate limiting.

    Structure: {
        'ip_address:endpoint': {
            'attempts': int,
            'reset_at': float (timestamp)
        }
    }
    """

    def __init__(self):
        self.store: dict[str, dict] = defaultdict(dict)

    def get_attempts(self, key: str) -> int:
        """Retourne le nombre de tentatives pour une clé."""
        if key not in self.store:
            return 0

        # Check si fenêtre expirée
        if time.time() > self.store[key].get('reset_at', 0):
            del self.store[key]
            return 0

        return self.store[key].get('attempts', 0)

    def increment(self, key: str, window_seconds: int) -> int:
        """
        Incrémente le compteur de tentatives.

        Args:
            key: Clé unique (IP:endpoint ou email:endpoint)
            window_seconds: Durée de la fenêtre en secondes

        Returns:
            Nouveau nombre de tentatives
        """
        if key not in self.store or time.time() > self.store[key].get('reset_at', 0):
            # Nouvelle fenêtre
            self.store[key] = {
                'attempts': 1,
                'reset_at': time.time() + window_seconds
            }
            return 1

        self.store[key]['attempts'] += 1
        return self.store[key]['attempts']

    def get_reset_time(self, key: str) -> float:
        """Retourne le timestamp de reset pour une clé."""
        if key not in self.store:
            return time.time()

        return self.store[key].get('reset_at', time.time())

    def cleanup_expired(self):
        """Supprime les entrées expirées (pour éviter memory leak)."""
        now = time.time()
        expired_keys = [
            key for key, data in self.store.items()
            if now > data.get('reset_at', 0)
        ]

        for key in expired_keys:
            del self.store[key]


# Instance globale
rate_limit_store = RateLimitStore()


async def _read_body_from_receive(receive: Receive) -> bytes:
    """Read the full request body from ASGI receive channel."""
    body = b""
    while True:
        message = await receive()
        body += message.get("body", b"")
        if not message.get("more_body", False):
            break
    return body


def _make_body_replay(body: bytes, original_receive: Receive) -> Receive:
    """Create a receive callable that replays buffered body then delegates to original."""
    body_sent = False

    async def replay_receive():
        nonlocal body_sent
        if not body_sent:
            body_sent = True
            return {"type": "http.request", "body": body, "more_body": False}
        return await original_receive()

    return replay_receive


def _extract_email_from_body_bytes(body: bytes) -> Optional[str]:
    """Extract email from JSON body bytes."""
    try:
        if not body:
            return None
        data = json.loads(body)
        email = data.get("email")
        return email.lower() if email else None
    except (json.JSONDecodeError, AttributeError):
        return None


# Configuration par endpoint (Security 2025-12-23: Extended rate limiting)
RATE_LIMITS = {
    # Authentication endpoints
    '/api/auth/login': {
        'max_attempts_ip': 10,       # Par IP (général)
        'max_attempts_email': 5,     # Par email (plus strict, anti credential stuffing)
        'window_seconds': 300        # 5 minutes
    },
    '/api/auth/register': {
        'max_attempts_ip': 5,        # Anti-spam registration
        'window_seconds': 3600       # 1 heure
    },
    '/api/auth/resend-verification': {
        'max_attempts_ip': 3,
        'max_attempts_email': 1,     # 1 seul renvoi par email/heure (anti-spam)
        'window_seconds': 3600       # 1 heure
    },
    '/api/auth/verify-email': {
        'max_attempts_ip': 10,       # Anti brute force token
        'window_seconds': 300        # 5 minutes
    },
    '/api/auth/forgot-password': {
        'max_attempts_ip': 5,
        'window_seconds': 3600       # 1 heure
    },
    # Stripe payment endpoints
    '/api/stripe/create-checkout-session': {
        'max_attempts_ip': 10,
        'window_seconds': 3600       # 1 heure
    },
    '/api/stripe/create-portal-session': {
        'max_attempts_ip': 10,
        'window_seconds': 3600       # 1 heure
    },
    # Marketplace expensive operations (2026-01-08)
    '/api/vinted/products/sync': {
        'max_attempts_ip': 10,       # Limite sync Vinted (expensive DB/API operation)
        'window_seconds': 3600       # 1 heure
    },
    '/api/ebay/products/import': {
        'max_attempts_ip': 5,        # Limite import eBay (very expensive operation)
        'window_seconds': 3600       # 1 heure
    },
}


class RateLimitMiddleware:
    """
    Pure ASGI rate limiting middleware.

    Business Rules (Security - 2025-12-18):
    - /auth/login:
      - 10 tentatives / 5 minutes par IP
      - 5 tentatives / 5 minutes par EMAIL (plus strict, anti credential stuffing)
    - Autres endpoints: pas de limite (pour l'instant)
    - DÉSACTIVÉ en mode TESTING pour permettre les tests

    Returns 429 Too Many Requests si limite dépassée.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope)

        # BYPASS RULES (Security 2026-01-12)
        app_env = os.getenv("APP_ENV", "development")
        disable_rate_limit = os.getenv("DISABLE_RATE_LIMIT") == "1"

        if disable_rate_limit:
            if app_env == "production":
                logger.critical(
                    "🚨 SECURITY: DISABLE_RATE_LIMIT=1 detected in production environment. "
                    "This flag is IGNORED for security. Rate limiting is ACTIVE."
                )
                # Continue to rate limiting (do NOT bypass)
            elif app_env == "test":
                logger.debug("[RateLimit] Bypass active (test environment)")
                await self.app(scope, receive, send)
                return
            else:
                logger.warning(
                    "[RateLimit] Bypass active (development environment). "
                    "Do NOT use in production."
                )
                await self.app(scope, receive, send)
                return

        # Check si endpoint rate-limité
        path = request.url.path
        if path not in RATE_LIMITS:
            await self.app(scope, receive, send)
            return

        config = RATE_LIMITS[path]

        # Récupérer IP du client
        client_ip = request.client.host if request.client else "unknown"
        key_ip = f"ip:{client_ip}:{path}"

        # Vérifier limite par IP
        attempts_ip = rate_limit_store.get_attempts(key_ip)
        if attempts_ip >= config['max_attempts_ip']:
            reset_at = rate_limit_store.get_reset_time(key_ip)
            retry_after = max(1, int(reset_at - time.time()))

            logger.warning(f"Rate limit exceeded (IP): ip={client_ip}, attempts={attempts_ip}")

            response = JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": f"Too many login attempts from this IP. Please try again in {retry_after} seconds.",
                    "retry_after": retry_after,
                    "limit_type": "ip"
                },
                headers={"Retry-After": str(retry_after)}
            )
            await response(scope, receive, send)
            return

        # Extraire email pour rate limiting par email
        email = None
        body_bytes = None
        if path == '/api/auth/login' and request.method == "POST":
            body_bytes = await _read_body_from_receive(receive)
            email = _extract_email_from_body_bytes(body_bytes)
        elif path == '/api/auth/resend-verification' and request.method == "POST":
            email = request.query_params.get('email')
            if email:
                email = email.lower()

        # Vérifier limite par email (si configurée et email disponible)
        if email and 'max_attempts_email' in config:
            key_email = f"email:{email}:{path}"
            attempts_email = rate_limit_store.get_attempts(key_email)

            if attempts_email >= config['max_attempts_email']:
                reset_at = rate_limit_store.get_reset_time(key_email)
                retry_after = max(1, int(reset_at - time.time()))

                logger.warning(f"Rate limit exceeded (email): email={email[:3]}***, path={path}, attempts={attempts_email}")

                response = JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "detail": f"Trop de tentatives pour cette adresse email. Réessayez dans {retry_after} secondes.",
                        "retry_after": retry_after,
                        "limit_type": "email"
                    },
                    headers={"Retry-After": str(retry_after)}
                )
                await response(scope, receive, send)
                return

        # Incrémenter les compteurs (seulement si pas dépassé)
        rate_limit_store.increment(key_ip, config['window_seconds'])
        if email and 'max_attempts_email' in config:
            key_email = f"email:{email}:{path}"
            rate_limit_store.increment(key_email, config['window_seconds'])

        # Cleanup périodique (1 fois sur 100 requêtes)
        import random
        if random.randint(1, 100) == 1:
            rate_limit_store.cleanup_expired()

        # If body was consumed for email extraction, replay it for downstream
        if body_bytes is not None:
            await self.app(scope, _make_body_replay(body_bytes, receive), send)
        else:
            await self.app(scope, receive, send)
