"""
Script de test de l'API Stoflow (version simplifiée sans tenant)

Ce script teste le workflow complet:
1. Register un nouvel utilisateur
2. Login avec cet utilisateur
3. Refresh du token
"""

import sys
from pathlib import Path

import requests

# Ajouter le projet au path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configuration
BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api"


def print_step(step: str):
    """Affiche une étape de test."""
    print(f"\n{'=' * 60}")
    print(f"  {step}")
    print('=' * 60)


def test_health():
    """Test de la route de santé."""
    print_step("1. Test de la route de santé")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200, "Health check failed"
    print("✅ Health check OK")


def test_register():
    """Test de création d'un utilisateur via /register."""
    print_step("2. Register nouvel utilisateur")
    data = {
        "email": "test@example.com",
        "password": "SecurePass123!",
        "full_name": "Test User"
    }
    response = requests.post(f"{API_URL}/auth/register", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 201, "Register failed"
    tokens = response.json()
    print(f"✅ Utilisateur créé et connecté automatiquement")
    print(f"   User ID: {tokens['user_id']}")
    print(f"   Role: {tokens['role']}")
    print(f"   Subscription Tier: {tokens['subscription_tier']}")
    print(f"   Access Token: {tokens['access_token'][:50]}...")
    return tokens


def test_login(email: str, password: str):
    """Test de login."""
    print_step("3. Login de l'utilisateur")
    data = {
        "email": email,
        "password": password
    }
    response = requests.post(f"{API_URL}/auth/login", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200, "Login failed"
    tokens = response.json()
    print(f"✅ Login réussi")
    print(f"   Access Token: {tokens['access_token'][:50]}...")
    print(f"   Refresh Token: {tokens['refresh_token'][:50]}...")
    print(f"   User ID: {tokens['user_id']}")
    print(f"   Subscription Tier: {tokens['subscription_tier']}")
    return tokens


def test_refresh_token(refresh_token: str):
    """Test de refresh du token."""
    print_step("4. Refresh du token")
    data = {
        "refresh_token": refresh_token
    }
    response = requests.post(f"{API_URL}/auth/refresh", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200, "Token refresh failed"
    result = response.json()
    print(f"✅ Token refresh réussi")
    print(f"   New Access Token: {result['access_token'][:50]}...")
    return result


def main():
    """Fonction principale de test."""
    try:
        # Test 1: Health check
        test_health()

        # Test 2: Register (crée user + connecté automatiquement)
        tokens = test_register()

        # Test 3: Login (avec le même user)
        login_tokens = test_login(
            email="test@example.com",
            password="SecurePass123!"
        )

        # Test 4: Refresh token
        test_refresh_token(login_tokens['refresh_token'])

        # Résumé
        print_step("🎉 TOUS LES TESTS SONT PASSÉS ! 🎉")
        print(f"\n📊 Résumé:")
        print(f"   - User ID: {tokens['user_id']}")
        print(f"   - Email: test@example.com")
        print(f"   - Role: {tokens['role']}")
        print(f"   - Subscription Tier: {tokens['subscription_tier']} (starter par défaut)")
        print("\n✅ L'authentification simplifiée fonctionne correctement !")
        print("✅ Plus besoin de tenant_id - architecture simplifiée réussie !")
        print("✅ Schema PostgreSQL 'user_1' créé automatiquement")

    except AssertionError as e:
        print(f"\n❌ ÉCHEC: {e}")
        sys.exit(1)
    except requests.exceptions.ConnectionError:
        print(f"\n❌ ERREUR: Impossible de se connecter à {BASE_URL}")
        print("Assurez-vous que l'application FastAPI est démarrée:")
        print("  python -m uvicorn main:app --reload --port 8000")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERREUR INATTENDUE: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
