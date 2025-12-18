"""
Security Utilities

Helper functions for security operations.

Created: 2025-12-05
"""

from shared.config import settings


def redact_password(password: str | None) -> str:
    """
    Redact password pour logging sécurisé.

    Business Rules (Security - 2025-12-05):
    - Dev: Montrer 3 premiers caractères + '***'
    - Prod: Toujours '******'
    - None/vide: '<empty>'

    Args:
        password: Mot de passe à redact

    Returns:
        str: Version redacted du password

    Example:
        >>> redact_password("MySecret123")  # Dev
        "MyS***"
        >>> redact_password("MySecret123")  # Prod
        "******"
    """
    if not password:
        return "<empty>"

    # Production: toujours redact complètement
    if settings.is_production:
        return "******"

    # Development: montrer 3 premiers chars
    if len(password) <= 3:
        return "***"

    return f"{password[:3]}***"


def sanitize_for_log(data: dict) -> dict:
    """
    Sanitize un dictionnaire pour logging sécurisé.

    Redact automatiquement les champs sensibles:
    - password, hashed_password
    - secret_key, api_key
    - token, access_token, refresh_token

    Args:
        data: Dictionnaire à sanitize

    Returns:
        dict: Copie du dictionnaire avec valeurs redacted

    Example:
        >>> sanitize_for_log({"email": "test@test.com", "password": "secret"})
        {"email": "test@test.com", "password": "sec***"}
    """
    sensitive_fields = {
        "password",
        "hashed_password",
        "secret_key",
        "api_key",
        "token",
        "access_token",
        "refresh_token",
        "jwt_secret_key",
    }

    sanitized = data.copy()

    for key, value in sanitized.items():
        if key.lower() in sensitive_fields:
            sanitized[key] = redact_password(str(value) if value else None)

    return sanitized
