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
import time

from shared.logging import get_logger

logger = get_logger(__name__)


class VintedRateLimiter:
    """
    Rate limiter avec délais aléatoires pour éviter la détection bot.

    Configuration simplifiée:
    - Délais uniformes par type de requête HTTP (GET, POST, PUT, DELETE)
    - Minimum 1 seconde pour toutes les requêtes
    - Randomisation pour simuler comportement humain
    """

    # Configuration des délais par méthode HTTP (min_delay, max_delay en secondes)
    # Minimum 1 seconde pour tout
    METHOD_DELAYS = {
        "GET": (1.0, 2.5),      # Lecture
        "POST": (2.0, 4.0),     # Création
        "PUT": (2.0, 4.0),      # Modification
        "DELETE": (3.0, 5.0),   # Suppression
    }

    # Espacement minimum entre requêtes (en secondes)
    MIN_SPACING = 1.0

    # Pause périodique (simule pause humaine)
    PAUSE_INTERVAL_MIN = 8   # Pause après 8-14 requêtes (aléatoire)
    PAUSE_INTERVAL_MAX = 14
    PAUSE_DURATION_MIN = 5.0   # Durée de la pause: 5-15 secondes
    PAUSE_DURATION_MAX = 15.0

    _last_request_time: float = 0
    _request_count: int = 0
    _next_pause_at: int = 0  # Prochain seuil pour pause (0 = non initialisé)

    @classmethod
    def _get_delay_for_method(cls, http_method: str) -> tuple[float, float]:
        """Retourne (min_delay, max_delay) pour une méthode HTTP."""
        return cls.METHOD_DELAYS.get(http_method.upper(), cls.METHOD_DELAYS["GET"])

    @classmethod
    async def wait_before_request(cls, path: str, http_method: str = "GET") -> float:
        """
        Attend un délai aléatoire avant d'exécuter une requête.

        Args:
            path: URL de la requête (unused, kept for compatibility)
            http_method: GET, POST, PUT, DELETE

        Returns:
            float: Délai effectif appliqué en secondes
        """
        min_delay, max_delay = cls._get_delay_for_method(http_method)

        # Calculer délai aléatoire
        delay = random.uniform(min_delay, max_delay)

        # Assurer espacement minimum depuis la dernière requête
        time_since_last = time.time() - cls._last_request_time
        if time_since_last < cls.MIN_SPACING:
            extra_wait = cls.MIN_SPACING - time_since_last
            delay = max(delay, extra_wait)

        # Pause périodique aléatoire (simule une pause humaine)
        cls._request_count += 1

        # Initialiser le prochain seuil de pause si nécessaire
        if cls._next_pause_at == 0:
            cls._next_pause_at = random.randint(
                cls.PAUSE_INTERVAL_MIN, cls.PAUSE_INTERVAL_MAX
            )

        # Déclencher la pause si on atteint le seuil
        if cls._request_count >= cls._next_pause_at:
            pause_duration = random.uniform(
                cls.PAUSE_DURATION_MIN, cls.PAUSE_DURATION_MAX
            )
            delay += pause_duration
            logger.info(
                f"[RateLimiter] Pause périodique de {pause_duration:.1f}s "
                f"(après {cls._request_count} requêtes)"
            )
            # Réinitialiser le compteur et définir le prochain seuil
            cls._request_count = 0
            cls._next_pause_at = random.randint(
                cls.PAUSE_INTERVAL_MIN, cls.PAUSE_INTERVAL_MAX
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
        cls._next_pause_at = 0


__all__ = ["VintedRateLimiter"]
