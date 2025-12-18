"""
Datetime Utilities

Fonctions utilitaires pour gérer les timestamps de manière cohérente
dans toute l'application.

Business Rules (2025-12-05):
- Tous les timestamps en UTC
- Format ISO 8601 pour JSON
- Timezone-aware datetime objects
"""

from datetime import datetime, timezone
from typing import Optional


def utc_now() -> datetime:
    """
    Retourne l'heure UTC actuelle (timezone-aware).

    Cette fonction est la source unique de vérité pour tous les timestamps
    dans l'application. Elle garantit:
    - Timezone UTC explicite
    - Cohérence entre tous les services
    - Facilité de mock dans les tests

    Returns:
        datetime: Heure actuelle en UTC avec timezone info

    Example:
        >>> now = utc_now()
        >>> print(now)
        2025-12-05 15:30:45.123456+00:00
        >>> now.tzinfo
        datetime.timezone.utc
    """
    return datetime.now(timezone.utc)


def format_iso(dt: Optional[datetime]) -> Optional[str]:
    """
    Formate une datetime en ISO 8601 pour JSON.

    Args:
        dt: Datetime à formater (peut être None)

    Returns:
        str | None: Format ISO ou None

    Example:
        >>> dt = utc_now()
        >>> format_iso(dt)
        '2025-12-05T15:30:45.123456+00:00'
    """
    return dt.isoformat() if dt else None


def parse_iso(iso_string: str) -> datetime:
    """
    Parse une string ISO 8601 en datetime.

    Args:
        iso_string: String au format ISO 8601

    Returns:
        datetime: Datetime parsée (timezone-aware)

    Raises:
        ValueError: Si format invalide

    Example:
        >>> parse_iso('2025-12-05T15:30:45.123456+00:00')
        datetime.datetime(2025, 12, 5, 15, 30, 45, 123456, tzinfo=timezone.utc)
    """
    return datetime.fromisoformat(iso_string)
