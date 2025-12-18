"""
Configuration centralisée du système de logging.
"""
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from shared.config import settings


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
