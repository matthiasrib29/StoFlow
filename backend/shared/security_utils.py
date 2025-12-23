"""
Security Utilities

Helper functions for security operations.

Created: 2025-12-05
Updated: 2025-12-23 - Added redact_email() for GDPR compliance
"""

from shared.config import settings


def redact_email(email: str | None) -> str:
    """
    Redact email pour logging RGPD-compliant.

    Business Rules (Security - 2025-12-23):
    - Production: Masque la partie locale et le domaine
    - Dev: Montre l'email complet pour faciliter le debugging
    - None/vide: '<empty>'

    Args:
        email: Adresse email à redact

    Returns:
        str: Version redacted de l'email

    Example:
        >>> redact_email("john.doe@example.com")  # Prod
        "j***@e***.com"
        >>> redact_email("john.doe@example.com")  # Dev
        "john.doe@example.com"
    """
    if not email:
        return "<empty>"

    if "@" not in email:
        return "<invalid>"

    # Development: garder l'email complet pour debugging
    if not settings.is_production:
        return email

    # Production: masquer pour RGPD compliance
    try:
        local, domain = email.split("@", 1)

        # Masquer la partie locale (garder première lettre)
        if len(local) > 1:
            local_redacted = local[0] + "***"
        else:
            local_redacted = "***"

        # Masquer le domaine (garder première lettre + TLD)
        domain_parts = domain.split(".")
        if len(domain_parts) >= 2:
            # e.g., "example.com" -> "e***.com"
            domain_redacted = domain_parts[0][0] + "***." + domain_parts[-1]
        else:
            domain_redacted = domain[0] + "***"

        return f"{local_redacted}@{domain_redacted}"
    except Exception:
        return "<redacted>"


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
    - email (RGPD compliance - 2025-12-23)

    Args:
        data: Dictionnaire à sanitize

    Returns:
        dict: Copie du dictionnaire avec valeurs redacted

    Example:
        >>> sanitize_for_log({"email": "test@test.com", "password": "secret"})
        {"email": "t***@t***.com", "password": "sec***"}  # In production
    """
    password_fields = {
        "password",
        "hashed_password",
        "secret_key",
        "api_key",
        "token",
        "access_token",
        "refresh_token",
        "jwt_secret_key",
    }

    email_fields = {
        "email",
        "user_email",
        "owner_email",
    }

    sanitized = data.copy()

    for key, value in sanitized.items():
        key_lower = key.lower()
        if key_lower in password_fields:
            sanitized[key] = redact_password(str(value) if value else None)
        elif key_lower in email_fields:
            sanitized[key] = redact_email(str(value) if value else None)

    return sanitized
