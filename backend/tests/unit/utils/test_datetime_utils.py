"""
Tests pour datetime_utils

Vérifie que les fonctions utilitaires datetime fonctionnent correctement.
"""

from datetime import datetime, timezone
from shared.datetime_utils import utc_now, format_iso, parse_iso


def test_utc_now_returns_timezone_aware():
    """Test que utc_now() retourne bien une datetime timezone-aware."""
    now = utc_now()

    assert isinstance(now, datetime)
    assert now.tzinfo is not None
    assert now.tzinfo == timezone.utc


def test_utc_now_returns_current_time():
    """Test que utc_now() retourne l'heure actuelle (à quelques secondes près)."""
    before = datetime.now(timezone.utc)
    now = utc_now()
    after = datetime.now(timezone.utc)

    assert before <= now <= after


def test_format_iso_with_datetime():
    """Test format_iso() avec une datetime valide."""
    dt = datetime(2025, 12, 5, 15, 30, 45, 123456, tzinfo=timezone.utc)
    result = format_iso(dt)

    assert result == "2025-12-05T15:30:45.123456+00:00"


def test_format_iso_with_none():
    """Test format_iso() avec None."""
    assert format_iso(None) is None


def test_parse_iso():
    """Test parse_iso() avec une string ISO valide."""
    iso_str = "2025-12-05T15:30:45.123456+00:00"
    result = parse_iso(iso_str)

    assert isinstance(result, datetime)
    assert result.year == 2025
    assert result.month == 12
    assert result.day == 5
    assert result.hour == 15
    assert result.minute == 30
    assert result.second == 45
    assert result.microsecond == 123456
    assert result.tzinfo is not None


def test_roundtrip_iso_conversion():
    """Test que format_iso() et parse_iso() sont symétriques."""
    original = utc_now()
    iso_str = format_iso(original)
    parsed = parse_iso(iso_str)

    # Compare timestamps (microsecond precision)
    assert parsed == original
