"""
Script de test de l'API Stoflow

Ce script teste le workflow complet:
1. Créer un tenant
2. Créer un utilisateur pour ce tenant
3. Login avec cet utilisateur
4. Refresh du token
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


def test_create_tenant():
    """Test de création d'un tenant."""
    print_step("2. Création d'un tenant")
    data = {
        "name": "Test Company",
        "email": "test@company.com",
        "is_active": True
    }
    response = requests.post(f"{API_URL}/tenants", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 201, "Tenant creation failed"
    tenant = response.json()
    print(f"✅ Tenant créé: ID={tenant['id']}, Name={tenant['name']}")
    return tenant


def test_create_user(tenant_id: int):
    """Test de création d'un utilisateur."""
    print_step("3. Création d'un utilisateur")
    data = {
        "email": "admin@company.com",
        "password": "securepassword123",
        "full_name": "Admin User",
        "role": "admin",
        "is_active": True
    }
    response = requests.post(f"{API_URL}/tenants/{tenant_id}/users", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 201, "User creation failed"
    user = response.json()
    print(f"✅ Utilisateur créé: ID={user['id']}, Email={user['email']}, Role={user['role']}")
    return user


def test_login(email: str, password: str):
    """Test de login."""
    print_step("4. Login de l'utilisateur")
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
    print(f"   Tenant ID: {tokens['tenant_id']} (automatiquement déduit de l'email)")
    return tokens


def test_refresh_token(refresh_token: str):
    """Test de refresh du token."""
    print_step("5. Refresh du token")
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

        # Test 2: Créer un tenant
        tenant = test_create_tenant()

        # Test 3: Créer un utilisateur
        user = test_create_user(tenant['id'])

        # Test 4: Login (sans tenant_id, automatiquement déduit de l'email)
        tokens = test_login(
            email=user['email'],
            password="securepassword123"
        )

        # Test 5: Refresh token
        test_refresh_token(tokens['refresh_token'])

        # Résumé
        print_step("🎉 TOUS LES TESTS SONT PASSÉS ! 🎉")
        print(f"\n📊 Résumé:")
        print(f"   - Tenant ID: {tenant['id']}")
        print(f"   - User ID: {user['id']}")
        print(f"   - Email: {user['email']}")
        print(f"   - Role: {user['role']}")
        print("\n✅ L'authentification et le multi-tenant fonctionnent correctement !")
        print("✅ L'email est maintenant globalement unique (pas besoin de tenant_id au login) !")

    except AssertionError as e:
        print(f"\n❌ ÉCHEC: {e}")
        sys.exit(1)
    except requests.exceptions.ConnectionError:
        print(f"\n❌ ERREUR: Impossible de se connecter à {BASE_URL}")
        print("Assurez-vous que l'application FastAPI est démarrée.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERREUR INATTENDUE: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
