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

    Multi-tenant: une instance par user_id (chaque user a son propre
    compteur de requêtes et seuil de pause périodique).

    Usage:
        limiter = VintedRateLimiter.for_user(user_id)
        delay = await limiter.wait_before_request(path, http_method)
    """

    # Configuration des délais par méthode HTTP (min_delay, max_delay en secondes)
    # Protection renforcée contre détection bot (2026-01-22)
    METHOD_DELAYS = {
        "GET": (3.0, 8.0),       # Lecture
        "POST": (5.0, 12.0),     # Création
        "PUT": (5.0, 12.0),      # Modification
        "DELETE": (6.0, 15.0),   # Suppression
    }

    # Espacement minimum entre requêtes (en secondes)
    MIN_SPACING = 3.0

    # Pause périodique (simule pause humaine)
    PAUSE_INTERVAL_MIN = 10   # Pause après 10-15 requêtes (aléatoire)
    PAUSE_INTERVAL_MAX = 15
    PAUSE_DURATION_MIN = 15.0   # Durée de la pause: 15-30 secondes
    PAUSE_DURATION_MAX = 30.0

    # Registry: one instance per user_id
    _instances: dict[int, "VintedRateLimiter"] = {}

    def __init__(self, user_id: int):
        self.user_id = user_id
        self._last_request_time: float = 0
        self._request_count: int = 0
        self._next_pause_at: int = 0

    @classmethod
    def for_user(cls, user_id: int) -> "VintedRateLimiter":
        """Get or create a rate limiter instance for the given user."""
        if user_id not in cls._instances:
            cls._instances[user_id] = cls(user_id)
        return cls._instances[user_id]

    def _get_delay_for_method(self, http_method: str) -> tuple[float, float]:
        """Retourne (min_delay, max_delay) pour une méthode HTTP."""
        return self.METHOD_DELAYS.get(http_method.upper(), self.METHOD_DELAYS["GET"])

    async def wait_before_request(self, path: str, http_method: str = "GET") -> float:
        """
        Attend un délai aléatoire avant d'exécuter une requête.

        Args:
            path: URL de la requête (pour logs)
            http_method: GET, POST, PUT, DELETE

        Returns:
            float: Délai effectif appliqué en secondes
        """
        min_delay, max_delay = self._get_delay_for_method(http_method)

        # Calculer délai aléatoire
        delay = random.uniform(min_delay, max_delay)

        # Assurer espacement minimum depuis la dernière requête
        time_since_last = time.time() - self._last_request_time
        if time_since_last < self.MIN_SPACING:
            extra_wait = self.MIN_SPACING - time_since_last
            delay = max(delay, extra_wait)

        # Pause périodique aléatoire (simule une pause humaine)
        self._request_count += 1

        # Initialiser le prochain seuil de pause si nécessaire
        if self._next_pause_at == 0:
            self._next_pause_at = random.randint(
                self.PAUSE_INTERVAL_MIN, self.PAUSE_INTERVAL_MAX
            )

        # Déclencher la pause si on atteint le seuil
        if self._request_count >= self._next_pause_at:
            pause_duration = random.uniform(
                self.PAUSE_DURATION_MIN, self.PAUSE_DURATION_MAX
            )
            delay += pause_duration
            logger.info(
                f"[RateLimiter] user={self.user_id} Pause périodique de "
                f"{pause_duration:.1f}s (après {self._request_count} requêtes)"
            )
            # Réinitialiser le compteur et définir le prochain seuil
            self._request_count = 0
            self._next_pause_at = random.randint(
                self.PAUSE_INTERVAL_MIN, self.PAUSE_INTERVAL_MAX
            )

        if delay > 0:
            logger.debug(
                f"[RateLimiter] user={self.user_id} Attente {delay:.2f}s "
                f"avant {http_method} {path[:50]}..."
            )
            await asyncio.sleep(delay)

        self._last_request_time = time.time()
        return delay

    @classmethod
    def reset(cls, user_id: int | None = None):
        """Reset rate limiter state (useful for tests).

        Args:
            user_id: Reset a specific user's limiter. If None, reset all.
        """
        if user_id is not None:
            cls._instances.pop(user_id, None)
        else:
            cls._instances.clear()


__all__ = ["VintedRateLimiter"]
