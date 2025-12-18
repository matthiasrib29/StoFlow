"""
Rate Limiting Middleware

Protection contre bruteforce attacks sur endpoints sensibles.

Business Rules (Security - 2025-12-18):
- /auth/login:
  - 10 tentatives / 5 minutes par IP
  - 5 tentatives / 5 minutes par EMAIL (plus strict, anti credential stuffing)
- Stockage en mémoire (simple dict avec cleanup)
- Retourne 429 Too Many Requests si dépassé
- DÉSACTIVÉ en mode TESTING (os.getenv("TESTING") == "1")

Created: 2025-12-05
Updated: 2025-12-18 - Ajout rate limiting par email
"""

import json
import os
import time
from collections import defaultdict
from typing import Callable, Optional

from fastapi import Request, status
from fastapi.responses import JSONResponse

from shared.logging_setup import get_logger

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


async def _extract_email_from_body(request: Request) -> Optional[str]:
    """
    Extrait l'email du body JSON de la requête.

    Note: Cette fonction consomme le body, donc on doit le re-stocker
    pour que le handler puisse le lire ensuite.
    """
    try:
        # Lire le body
        body = await request.body()
        if not body:
            return None

        # Parser le JSON
        data = json.loads(body)
        email = data.get("email")

        # Re-stocker le body pour le handler (important!)
        # FastAPI/Starlette permet de relire le body si on le stocke dans _body
        request._body = body

        return email.lower() if email else None
    except (json.JSONDecodeError, AttributeError):
        return None


async def rate_limit_middleware(request: Request, call_next: Callable):
    """
    Middleware de rate limiting.

    Business Rules (Security - 2025-12-18):
    - /auth/login:
      - 10 tentatives / 5 minutes par IP
      - 5 tentatives / 5 minutes par EMAIL (plus strict, anti credential stuffing)
    - Autres endpoints: pas de limite (pour l'instant)
    - DÉSACTIVÉ en mode TESTING pour permettre les tests

    Returns:
        429 Too Many Requests si limite dépassée
    """
    # BYPASS en mode TESTING (2025-12-09)
    if os.getenv("TESTING") == "1":
        return await call_next(request)

    # Configuration par endpoint
    rate_limits = {
        '/api/auth/login': {
            'max_attempts_ip': 10,       # Par IP (général)
            'max_attempts_email': 5,     # Par email (plus strict, anti credential stuffing)
            'window_seconds': 300        # 5 minutes
        }
    }

    # Check si endpoint rate-limité
    path = request.url.path
    if path not in rate_limits:
        # Pas de limite sur cet endpoint
        return await call_next(request)

    config = rate_limits[path]

    # Récupérer IP du client
    client_ip = request.client.host if request.client else "unknown"
    key_ip = f"ip:{client_ip}:{path}"

    # Vérifier limite par IP
    attempts_ip = rate_limit_store.get_attempts(key_ip)
    if attempts_ip >= config['max_attempts_ip']:
        reset_at = rate_limit_store.get_reset_time(key_ip)
        retry_after = max(1, int(reset_at - time.time()))

        logger.warning(f"Rate limit exceeded (IP): ip={client_ip}, attempts={attempts_ip}")

        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "detail": f"Too many login attempts from this IP. Please try again in {retry_after} seconds.",
                "retry_after": retry_after,
                "limit_type": "ip"
            },
            headers={"Retry-After": str(retry_after)}
        )

    # Extraire email du body pour rate limiting par email (uniquement pour login)
    email = None
    if path == '/api/auth/login' and request.method == "POST":
        email = await _extract_email_from_body(request)

    # Vérifier limite par email (si email disponible)
    if email:
        key_email = f"email:{email}:{path}"
        attempts_email = rate_limit_store.get_attempts(key_email)

        if attempts_email >= config['max_attempts_email']:
            reset_at = rate_limit_store.get_reset_time(key_email)
            retry_after = max(1, int(reset_at - time.time()))

            logger.warning(f"Rate limit exceeded (email): email={email}, attempts={attempts_email}")

            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": f"Too many login attempts for this account. Please try again in {retry_after} seconds.",
                    "retry_after": retry_after,
                    "limit_type": "email"
                },
                headers={"Retry-After": str(retry_after)}
            )

    # Incrémenter les compteurs (seulement si pas dépassé)
    rate_limit_store.increment(key_ip, config['window_seconds'])
    if email:
        key_email = f"email:{email}:{path}"
        rate_limit_store.increment(key_email, config['window_seconds'])

    # Continuer la requête
    response = await call_next(request)

    # Cleanup périodique (1 fois sur 100 requêtes)
    import random
    if random.randint(1, 100) == 1:
        rate_limit_store.cleanup_expired()

    return response
