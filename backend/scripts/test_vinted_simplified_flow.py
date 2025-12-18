"""
Test du flux simplifié Vinted (userId + login uniquement).

Ce script teste:
1. POST /api/vinted/user/sync - Sync userId + login
2. GET /api/vinted/user/status - Récupération statut
"""
import sys
sys.path.append('/home/maribeiro/Stoflow/Stoflow_BackEnd')

import requests
import json

# Configuration
BASE_URL = "http://localhost:8000"
TEST_USER_EMAIL = "matthiasribeiro77@gmail.com"  # Remplace par un email test

# Données de test Vinted
TEST_VINTED_USER_ID = 29535217
TEST_VINTED_LOGIN = "shoptonoutfit"

def login():
    """Se connecter pour obtenir un token."""
    print("\n1️⃣ Connexion...")
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={
            "email": TEST_USER_EMAIL,
            "password": "Test1234"  # Remplace par le bon mot de passe
        }
    )

    if response.status_code == 200:
        data = response.json()
        token = data["access_token"]
        print(f"✅ Connecté avec succès")
        return token
    else:
        print(f"❌ Échec connexion: {response.status_code}")
        print(response.text)
        return None


def sync_vinted_user(token):
    """Synchroniser l'utilisateur Vinted."""
    print("\n2️⃣ Synchronisation utilisateur Vinted...")

    response = requests.post(
        f"{BASE_URL}/api/vinted/user/sync",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "vinted_user_id": TEST_VINTED_USER_ID,
            "login": TEST_VINTED_LOGIN
        }
    )

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Utilisateur Vinted synchronisé")
        print(f"   - User ID: {data['vinted_user_id']}")
        print(f"   - Login: {data['login']}")
        print(f"   - Last sync: {data['last_sync']}")
        return True
    else:
        print(f"❌ Échec sync: {response.status_code}")
        print(response.text)
        return False


def get_vinted_status(token):
    """Récupérer le statut de connexion Vinted."""
    print("\n3️⃣ Récupération statut Vinted...")

    response = requests.get(
        f"{BASE_URL}/api/vinted/user/status",
        headers={"Authorization": f"Bearer {token}"}
    )

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Statut récupéré")
        print(f"   - Connecté: {data['is_connected']}")
        if data['is_connected']:
            print(f"   - User ID: {data['vinted_user_id']}")
            print(f"   - Login: {data['login']}")
            print(f"   - Last sync: {data['last_sync']}")
        return True
    else:
        print(f"❌ Échec récupération statut: {response.status_code}")
        print(response.text)
        return False


def main():
    print("="*60)
    print("TEST - Flux Simplifié Vinted (userId + login)")
    print("="*60)

    # Étape 1: Login
    token = login()
    if not token:
        return

    # Étape 2: Sync utilisateur Vinted
    if not sync_vinted_user(token):
        return

    # Étape 3: Vérifier le statut
    if not get_vinted_status(token):
        return

    print("\n" + "="*60)
    print("✅ TOUS LES TESTS RÉUSSIS !")
    print("="*60)


if __name__ == "__main__":
    main()
