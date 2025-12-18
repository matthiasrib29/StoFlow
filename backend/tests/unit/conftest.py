"""
Pytest Configuration pour les tests unitaires.

Ces tests n'ont pas besoin de base de données - ils utilisent des mocks.
Ce conftest.py override les fixtures du conftest.py parent qui nécessitent une DB.
"""

import os
import sys

# S'assurer que le répertoire racine est dans le path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest

# Configuration pytest-asyncio pour les tests async
pytest_plugins = ('pytest_asyncio',)


# Override la fixture session-scoped du parent pour éviter la connexion DB
@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """
    Override de la fixture parent - pas besoin de DB pour les tests unitaires.
    """
    print("\n Running unit tests (no database required)")
    yield
    print("\n Unit tests complete")


# Override la fixture de cleanup
@pytest.fixture(scope="function", autouse=True)
def cleanup_data(request):
    """
    Override de la fixture parent - pas de cleanup nécessaire.
    """
    yield


@pytest.fixture(autouse=True)
def reset_rate_limit_store():
    """
    Reset le rate limit store entre chaque test pour isolation.
    """
    try:
        from middleware.rate_limit import rate_limit_store
        rate_limit_store.store.clear()
    except ImportError:
        pass  # Module not available, skip
    yield
    try:
        from middleware.rate_limit import rate_limit_store
        rate_limit_store.store.clear()
    except ImportError:
        pass
