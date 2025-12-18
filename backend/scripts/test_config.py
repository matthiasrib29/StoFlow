"""Test configuration loading."""
import sys
from pathlib import Path

# Ajouter le répertoire parent au PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.config import settings


def test_config():
    """Test que la configuration se charge correctement."""
    print("=== STOFLOW CONFIGURATION ===")
    print(f"App Name: {settings.app_name}")
    print(f"Environment: {settings.app_env}")
    print(f"Debug: {settings.debug}")
    print(f"\nDatabase URL: {settings.database_url}")
    print(f"Redis URL: {settings.redis_url}")
    print(f"\nJWT Secret (first 10 chars): {settings.jwt_secret_key[:10]}...")
    print(f"OpenAI API Key (first 10 chars): {settings.openai_api_key[:10]}...")
    print(f"\nVinted Rate Limit: {settings.vinted_rate_limit_max} req / {settings.vinted_rate_limit_window_hours}h")
    print(f"CORS Origins: {settings.cors_origins}")
    print("\n✅ Configuration loaded successfully!")


if __name__ == "__main__":
    test_config()
