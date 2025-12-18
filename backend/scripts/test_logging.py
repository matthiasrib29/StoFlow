"""Test logging configuration."""
import sys
from pathlib import Path

# Ajouter le répertoire parent au PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.logging_setup import get_logger

logger = get_logger(__name__)


def test_logging():
    """Test différents niveaux de log."""
    print("\n" + "="*60)
    print("🔍 TESTING LOGGING SYSTEM")
    print("="*60 + "\n")

    logger.debug("🔍 This is a DEBUG message")
    logger.info("ℹ️  This is an INFO message")
    logger.warning("⚠️  This is a WARNING message")
    logger.error("❌ This is an ERROR message")

    try:
        1 / 0
    except ZeroDivisionError:
        logger.exception("💥 This is an EXCEPTION with traceback")

    print("\n" + "="*60)
    print("✅ Logging test completed")
    print("Check logs/ directory for log file")
    print("="*60 + "\n")


if __name__ == "__main__":
    test_logging()
