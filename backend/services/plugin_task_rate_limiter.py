"""
Plugin Task Rate Limiter - Anti-bot detection for Vinted API calls.

Rate limiter with random delays to avoid bot detection on Vinted.

Configuration:
- Different delays based on operation type
- Randomization to simulate human behavior
- Tracking of last call for minimum spacing

Author: Claude
Date: 2025-12-12
Refactored: 2026-01-05
"""

import asyncio
import random
import re
import time

from shared.logging_setup import get_logger

logger = get_logger(__name__)


class VintedRateLimiter:
    """
    Rate limiter avec délais aléatoires pour éviter la détection bot.

    Configuration:
    - Délais différents selon le type d'opération
    - Randomisation pour simuler comportement humain
    - Tracking du dernier appel pour espacement minimum
    """

    # Configuration des délais par pattern d'URL (min_delay, max_delay en secondes)
    DELAY_CONFIG = {
        # Opérations sensibles - délais longs
        "item_upload": (3.0, 6.0),  # Création de produit
        "items/.*/delete": (2.5, 5.0),  # Suppression
        "photos": (2.0, 4.0),  # Upload d'images
        # Opérations de lecture - délais courts
        "wardrobe": (0.5, 1.5),  # Liste produits
        "my_orders": (0.5, 1.5),  # Commandes
        "users": (0.3, 1.0),  # Info utilisateur
        # Par défaut
        "default": (0.3, 1.0),
    }

    # Multiplicateur pour les opérations d'écriture (PUT/DELETE)
    WRITE_MULTIPLIER = 1.8

    # Espacement minimum entre requêtes (en secondes)
    MIN_SPACING = 0.5

    _last_request_time: float = 0
    _request_count: int = 0

    @classmethod
    def _get_delay_config(cls, path: str) -> tuple[float, float]:
        """Retourne (min_delay, max_delay) pour une URL donnée."""
        for pattern, delays in cls.DELAY_CONFIG.items():
            if pattern == "default":
                continue
            if re.search(pattern, path, re.IGNORECASE):
                return delays
        return cls.DELAY_CONFIG["default"]

    @classmethod
    async def wait_before_request(cls, path: str, http_method: str = "GET") -> float:
        """
        Attend un délai aléatoire avant d'exécuter une requête.

        Args:
            path: URL de la requête
            http_method: GET, POST, PUT, DELETE

        Returns:
            float: Délai effectif appliqué en secondes
        """
        min_delay, max_delay = cls._get_delay_config(path)

        # Augmenter le délai pour les opérations d'écriture
        if http_method in ("POST", "PUT", "DELETE"):
            min_delay *= cls.WRITE_MULTIPLIER
            max_delay *= cls.WRITE_MULTIPLIER

        # Calculer délai aléatoire
        delay = random.uniform(min_delay, max_delay)

        # Assurer espacement minimum depuis la dernière requête
        time_since_last = time.time() - cls._last_request_time
        if time_since_last < cls.MIN_SPACING:
            extra_wait = cls.MIN_SPACING - time_since_last
            delay = max(delay, extra_wait)

        # Ajouter une variation supplémentaire tous les 10 appels
        cls._request_count += 1
        if cls._request_count % 10 == 0:
            # Pause plus longue périodiquement (simule une pause humaine)
            delay += random.uniform(1.0, 3.0)
            logger.debug(
                f"[RateLimiter] Pause périodique ajoutée (requête #{cls._request_count})"
            )

        if delay > 0:
            logger.debug(
                f"[RateLimiter] Attente {delay:.2f}s avant {http_method} {path[:50]}..."
            )
            await asyncio.sleep(delay)

        cls._last_request_time = time.time()
        return delay

    @classmethod
    def reset(cls):
        """Reset le compteur (utile pour les tests)."""
        cls._last_request_time = 0
        cls._request_count = 0


__all__ = ["VintedRateLimiter"]
