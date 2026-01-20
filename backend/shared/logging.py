"""
Logging Module

Centralized logging configuration and utilities.

Combines:
- Logging setup and configuration
- Structured logging helpers
- Security redaction for GDPR compliance

Created: 2025-12-05
Updated: 2026-01-20 - Consolidated from logging_setup.py, logging_helpers.py, security_utils.py
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Optional

from shared.config import settings


# =============================================================================
# LOGGING SETUP
# =============================================================================


def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
) -> logging.Logger:
    """
    Configure le système de logging.

    Args:
        log_level: Niveau de log (DEBUG, INFO, WARNING, ERROR)
        log_file: Chemin du fichier log (optionnel)

    Returns:
        Logger configuré
    """
    level = log_level or settings.log_level

    # Format des logs
    if settings.log_format == "detailed":
        log_format = (
            "[%(asctime)s] %(levelname)-8s "
            "%(name)s:%(funcName)s:%(lineno)d - %(message)s"
        )
    else:
        log_format = "[%(asctime)s] %(levelname)-8s - %(message)s"

    date_format = "%Y-%m-%d %H:%M:%S"

    # Configurer le logger racine
    logger = logging.getLogger("stoflow")
    logger.setLevel(getattr(logging, level.upper()))

    # Supprimer handlers existants
    logger.handlers.clear()

    # Handler console (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    console_handler.setFormatter(
        logging.Formatter(log_format, datefmt=date_format)
    )
    logger.addHandler(console_handler)

    # Handler fichier (si activé)
    if settings.log_file_enabled:
        file_path = Path(log_file or settings.log_file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            file_path,
            maxBytes=settings.log_file_max_bytes,
            backupCount=settings.log_file_backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(getattr(logging, level.upper()))
        file_handler.setFormatter(
            logging.Formatter(log_format, datefmt=date_format)
        )
        logger.addHandler(file_handler)

    # Ne pas propager aux loggers parents
    logger.propagate = False

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Récupère un logger avec le nom spécifié.

    Args:
        name: Nom du logger (généralement __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(f"stoflow.{name}")


# Logger principal de l'application
logger = setup_logging()


# =============================================================================
# SECURITY REDACTION (GDPR Compliance)
# =============================================================================


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
    except (ValueError, IndexError):
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


# =============================================================================
# STRUCTURED LOGGING
# =============================================================================


class StructuredLogger:
    """
    Structured logger with consistent formatting.

    Usage:
        log = StructuredLogger("vinted_sync")
        log.info("sync_started", user_id=123, product_count=45)
        # Output: [vinted_sync] sync_started: user_id=123, product_count=45

        log.error("sync_failed", user_id=123, error=str(e), exc_info=True)
        # Output: [vinted_sync] sync_failed: user_id=123, error=Connection timeout
    """

    def __init__(self, module_name: str):
        """
        Initialize structured logger.

        Args:
            module_name: Module/component name (e.g., "vinted_sync", "ebay_import")
        """
        self.module_name = module_name
        self.logger = get_logger(module_name)

    def _format_message(self, action: str, **context) -> str:
        """
        Format log message with structured context.

        Args:
            action: Action being performed (e.g., "sync_started", "product_created")
            **context: Key-value pairs for context

        Returns:
            Formatted message: "[module] action: key1=value1, key2=value2"
        """
        if not context:
            return f"[{self.module_name}] {action}"

        context_str = ", ".join(f"{k}={v}" for k, v in context.items())
        return f"[{self.module_name}] {action}: {context_str}"

    def debug(self, action: str, **context):
        """Log debug message with structured context."""
        self.logger.debug(self._format_message(action, **context))

    def info(self, action: str, **context):
        """Log info message with structured context."""
        self.logger.info(self._format_message(action, **context))

    def warning(self, action: str, **context):
        """Log warning message with structured context."""
        self.logger.warning(self._format_message(action, **context))

    def error(self, action: str, exc_info: bool = False, **context):
        """
        Log error message with structured context.

        Args:
            action: Action that failed
            exc_info: Include exception traceback (default False)
            **context: Key-value pairs for context
        """
        self.logger.error(self._format_message(action, **context), exc_info=exc_info)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def log_operation_start(module: str, operation: str, **context):
    """
    Log operation start with timing capability.

    Usage:
        log_operation_start("vinted_sync", "sync_products", user_id=123)
    """
    log = StructuredLogger(module)
    log.info(f"{operation}_started", **context)


def log_operation_success(module: str, operation: str, duration_ms: Optional[float] = None, **context):
    """
    Log successful operation completion.

    Args:
        module: Module name
        operation: Operation name
        duration_ms: Optional duration in milliseconds
        **context: Additional context
    """
    log = StructuredLogger(module)
    if duration_ms:
        context["duration_ms"] = round(duration_ms, 2)
    log.info(f"{operation}_completed", **context)


def log_operation_failure(module: str, operation: str, error: Exception, **context):
    """
    Log failed operation with error details.

    Args:
        module: Module name
        operation: Operation name
        error: Exception that occurred
        **context: Additional context
    """
    log = StructuredLogger(module)
    context["error"] = str(error)
    context["error_type"] = error.__class__.__name__
    log.error(f"{operation}_failed", exc_info=True, **context)
