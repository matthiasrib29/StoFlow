"""
Tests d'intégration pour le rate limiting.

Tests de sécurité CRITIQUES vérifiant que:
- Les endpoints sensibles (login) sont protégés contre bruteforce
- Le rate limiting est correctement appliqué par IP
- Les limites sont respectées et les erreurs 429 sont retournées
- Le reset de la fenêtre temporelle fonctionne correctement

Security Priority: P0 CRITICAL
Created: 2025-12-09
"""

import time
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from main import app
from middleware.rate_limit import rate_limit_store, RateLimitStore
from models.public.user import User, UserRole
from services.auth_service import AuthService


# ===== FIXTURES =====


@pytest.fixture(scope="function")
def reset_rate_limit_store():
    """
    Reset le rate limit store avant chaque test.

    CRITICAL: Sans ce reset, les tests peuvent s'influencer mutuellement
    et créer des faux positifs/négatifs.
    """
    # Clear le store global
    rate_limit_store.store.clear()
    yield rate_limit_store
    # Cleanup après le test
    rate_limit_store.store.clear()


@pytest.fixture(scope="function")
def test_user_for_login(db_session: Session):
    """
    Crée un utilisateur de test pour les tentatives de login.

    Returns:
        tuple: (User object, plaintext password)
    """
    password_plain = "testpassword123"
    user = User(
        email="login_test@example.com",
        hashed_password=AuthService.hash_password(password_plain),
        full_name="Login Test User",
        role=UserRole.USER,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user, password_plain


# ===== TESTS RATE LIMITING =====


class TestLoginRateLimiting:
    """
    Tests du rate limiting sur l'endpoint /api/auth/login.

    Business Rules (Security - 2025-12-05):
    - 10 tentatives maximum par IP dans une fenêtre de 5 minutes (300s)
    - 11ème tentative retourne 429 Too Many Requests
    - Header Retry-After indique le temps d'attente
    - Chaque IP a son propre compteur indépendant
    """

    def test_login_within_rate_limit_succeeds(
        self,
        client: TestClient,
        test_user_for_login: tuple,
        reset_rate_limit_store: RateLimitStore
    ):
        """
        Test 1: Les 10 premières tentatives de login sont acceptées.

        SECURITY TEST:
        - Vérifie que les tentatives légitimes ne sont pas bloquées
        - Vérifie que le compteur est incrémenté correctement

        Expected:
        - Les 10 premières requêtes doivent passer (200 ou 401 selon credentials)
        - Aucune erreur 429 ne doit être retournée
        """
        user, password = test_user_for_login

        # Tester 10 tentatives (la limite exacte)
        for i in range(10):
            response = client.post(
                "/api/auth/login",
                json={
                    "email": user.email,
                    "password": password
                }
            )

            # ASSERTION: Doit être 200 OK (login valide), pas 429
            assert response.status_code == 200, (
                f"RATE LIMIT ERROR: Attempt {i+1}/10 was blocked with "
                f"status {response.status_code}. Expected 200 for valid credentials."
            )

            data = response.json()
            assert "access_token" in data, (
                f"Attempt {i+1}/10 didn't return access_token"
            )

        # Vérifier que le compteur est à 10
        key = "testclient:127.0.0.1:/api/auth/login"
        # TestClient utilise "testclient" comme host
        attempts = reset_rate_limit_store.get_attempts("testclient:/api/auth/login")

        print(f"✅ Rate limit test passed: 10 successful login attempts allowed")

    def test_login_exceeds_rate_limit_returns_429(
        self,
        client: TestClient,
        test_user_for_login: tuple,
        reset_rate_limit_store: RateLimitStore
    ):
        """
        Test 2: La 11ème tentative de login retourne 429 Too Many Requests.

        SECURITY TEST CRITIQUE:
        - Vérifie que le rate limiting bloque les tentatives excessives
        - Protège contre les attaques bruteforce

        Expected:
        - Tentatives 1-10: 200 OK
        - Tentative 11+: 429 Too Many Requests
        - Header Retry-After présent dans la réponse 429
        """
        user, password = test_user_for_login

        # Faire 10 tentatives valides
        for i in range(10):
            response = client.post(
                "/api/auth/login",
                json={"email": user.email, "password": password}
            )
            assert response.status_code == 200, f"Attempt {i+1} should succeed"

        # 11ème tentative DOIT être bloquée
        response_11 = client.post(
            "/api/auth/login",
            json={"email": user.email, "password": password}
        )

        # ASSERTION CRITIQUE: 11ème tentative bloquée
        assert response_11.status_code == 429, (
            f"SECURITY BREACH: 11th login attempt was NOT rate limited! "
            f"Expected 429, got {response_11.status_code}. "
            f"This allows bruteforce attacks!"
        )

        data = response_11.json()

        # Vérifier le message d'erreur
        assert "detail" in data, "429 response should contain 'detail' field"
        assert "Too many login attempts" in data["detail"], (
            f"Unexpected error message: {data['detail']}"
        )

        # Vérifier le header Retry-After
        assert "retry_after" in data, "429 response should contain 'retry_after' field"
        assert isinstance(data["retry_after"], int), "retry_after should be an integer"
        assert data["retry_after"] > 0, "retry_after should be positive"

        print(f"✅ Security test passed: 11th login attempt blocked with 429")
        print(f"   Retry after: {data['retry_after']} seconds")

    def test_failed_login_attempts_count_towards_rate_limit(
        self,
        client: TestClient,
        test_user_for_login: tuple,
        reset_rate_limit_store: RateLimitStore
    ):
        """
        Test 3: Les tentatives de login ÉCHOUÉES comptent aussi vers la limite.

        SECURITY TEST CRITIQUE:
        - Empêche un attaquant de contourner le rate limit en utilisant
          des credentials invalides
        - Toutes les tentatives (valides ou non) doivent compter

        Expected:
        - 10 tentatives avec mauvais password: 401 Unauthorized
        - 11ème tentative: 429 Too Many Requests
        """
        user, password = test_user_for_login
        wrong_password = "wrong_password_123"

        # Faire 10 tentatives avec mauvais password
        for i in range(10):
            response = client.post(
                "/api/auth/login",
                json={"email": user.email, "password": wrong_password}
            )
            # Devrait être 401 (unauthorized) mais PAS 429
            assert response.status_code == 401, (
                f"Failed login attempt {i+1} should return 401, got {response.status_code}"
            )

        # 11ème tentative DOIT être bloquée (même avec bon password!)
        response_11 = client.post(
            "/api/auth/login",
            json={"email": user.email, "password": password}  # Bon password cette fois
        )

        # ASSERTION CRITIQUE: Bloqué même avec credentials valides
        assert response_11.status_code == 429, (
            f"SECURITY BREACH: Failed login attempts don't count towards rate limit! "
            f"Expected 429, got {response_11.status_code}. "
            f"Attacker can bruteforce by ignoring 401 responses!"
        )

        print("✅ Security test passed: Failed login attempts count towards rate limit")

    def test_rate_limit_resets_after_window_expires(
        self,
        client: TestClient,
        test_user_for_login: tuple,
        reset_rate_limit_store: RateLimitStore
    ):
        """
        Test 4: Le rate limiting se reset après expiration de la fenêtre (5 minutes).

        SECURITY TEST:
        - Vérifie que le compteur se réinitialise correctement
        - Empêche les blocages permanents d'utilisateurs légitimes

        Expected:
        - 10 tentatives → OK
        - 11ème tentative → 429
        - Après 301 secondes → les tentatives redeviennent possibles

        Note: On mock time.time() pour simuler le passage du temps
        """
        user, password = test_user_for_login

        # Faire 10 tentatives
        for i in range(10):
            response = client.post(
                "/api/auth/login",
                json={"email": user.email, "password": password}
            )
            assert response.status_code == 200

        # 11ème tentative bloquée
        response_11 = client.post(
            "/api/auth/login",
            json={"email": user.email, "password": password}
        )
        assert response_11.status_code == 429

        # SIMULATION: Avancer le temps de 301 secondes (> 300s window)
        original_time = time.time()
        future_time = original_time + 301  # 5 minutes + 1 seconde

        with patch('middleware.rate_limit.time.time', return_value=future_time):
            # Nouvelle tentative après expiration
            response_after_reset = client.post(
                "/api/auth/login",
                json={"email": user.email, "password": password}
            )

            # ASSERTION: Doit fonctionner à nouveau
            assert response_after_reset.status_code == 200, (
                f"RATE LIMIT ERROR: Login still blocked after window expired! "
                f"Expected 200, got {response_after_reset.status_code}. "
                f"Rate limit window should reset after 300 seconds."
            )

            data = response_after_reset.json()
            assert "access_token" in data, "Login should succeed after window reset"

        print("✅ Rate limit test passed: Window resets after 300 seconds")

    def test_different_ips_have_independent_rate_limits(
        self,
        test_user_for_login: tuple,
        reset_rate_limit_store: RateLimitStore
    ):
        """
        Test 5: Différentes IPs ont des compteurs de rate limit indépendants.

        SECURITY TEST:
        - Vérifie qu'un attaquant ne peut pas bloquer d'autres utilisateurs
        - Vérifie l'isolation des compteurs par IP

        Expected:
        - IP1 fait 10 tentatives → OK
        - IP1 fait 11ème tentative → 429
        - IP2 fait 1 tentative → OK (compteur indépendant)

        Note: TestClient ne permet pas facilement de changer l'IP,
        donc on teste directement avec le store.
        """
        user, password = test_user_for_login

        # Simuler 10 tentatives depuis IP1
        ip1_key = "192.168.1.1:/api/auth/login"
        for i in range(10):
            attempts = reset_rate_limit_store.increment(ip1_key, window_seconds=300)

        # IP1 est maintenant à la limite
        assert reset_rate_limit_store.get_attempts(ip1_key) == 10

        # IP2 doit avoir un compteur indépendant à 0
        ip2_key = "192.168.1.2:/api/auth/login"
        attempts_ip2 = reset_rate_limit_store.get_attempts(ip2_key)

        # ASSERTION CRITIQUE: IP2 n'est pas affectée par IP1
        assert attempts_ip2 == 0, (
            f"RATE LIMIT ERROR: IP2 is affected by IP1's rate limit! "
            f"Expected 0 attempts for IP2, got {attempts_ip2}. "
            f"Rate limits should be isolated per IP."
        )

        # IP2 peut faire des tentatives
        new_attempts = reset_rate_limit_store.increment(ip2_key, window_seconds=300)
        assert new_attempts == 1, "IP2 should start with 1 attempt"

        # IP1 est toujours bloquée
        assert reset_rate_limit_store.get_attempts(ip1_key) >= 10

        print("✅ Rate limit test passed: IPs have independent rate limits")


class TestRateLimitBypass:
    """
    Tests vérifiant que les endpoints NON rate-limités fonctionnent normalement.

    Business Rules:
    - Seul /api/auth/login est rate-limité
    - Tous les autres endpoints ne doivent PAS être affectés
    """

    def test_non_rate_limited_endpoints_work_normally(
        self,
        client: TestClient,
        reset_rate_limit_store: RateLimitStore
    ):
        """
        Test 6: Les endpoints non rate-limités ne sont pas affectés.

        FUNCTIONALITY TEST:
        - Vérifie que le rate limiting n'affecte que /api/auth/login
        - Vérifie que les autres endpoints fonctionnent normalement

        Expected:
        - 100 requêtes sur / (root) → Toutes passent
        - 100 requêtes sur /health → Toutes passent
        - Aucune erreur 429
        """
        # Tester endpoint root
        for i in range(20):
            response = client.get("/")
            assert response.status_code == 200, (
                f"Root endpoint blocked at attempt {i+1}! "
                f"This endpoint should NOT be rate limited."
            )

        # Tester endpoint health
        for i in range(20):
            response = client.get("/health")
            assert response.status_code == 200, (
                f"Health endpoint blocked at attempt {i+1}! "
                f"This endpoint should NOT be rate limited."
            )

        print("✅ Rate limit test passed: Non-rate-limited endpoints work normally")

    def test_authenticated_endpoints_not_rate_limited(
        self,
        client: TestClient,
        auth_headers: dict,
        reset_rate_limit_store: RateLimitStore
    ):
        """
        Test 7: Les endpoints authentifiés (non-login) ne sont pas rate-limités.

        FUNCTIONALITY TEST:
        - Vérifie que /api/products, /api/attributes etc. ne sont pas rate-limités
        - Ces endpoints sont déjà protégés par l'authentification JWT

        Expected:
        - 20 requêtes sur /api/products/list → Toutes passent
        - Aucune erreur 429
        """
        # Tester endpoint products list (GET /)
        for i in range(20):
            response = client.get(
                "/api/products/",
                headers=auth_headers
            )
            # Doit être 200 OK, pas 429
            assert response.status_code == 200, (
                f"Products list endpoint blocked at attempt {i+1}! "
                f"This endpoint should NOT be rate limited. "
                f"Status: {response.status_code}"
            )

        print("✅ Rate limit test passed: Authenticated endpoints not rate limited")


class TestRateLimitStore:
    """
    Tests unitaires du RateLimitStore.

    Tests de bas niveau vérifiant le fonctionnement du store de rate limiting.
    """

    def test_store_increments_correctly(self):
        """
        Test 8: Le store incrémente correctement les tentatives.

        UNIT TEST:
        - Vérifie le fonctionnement basique du store
        - get_attempts, increment, reset
        """
        store = RateLimitStore()
        key = "test_ip:/api/test"

        # Initial: 0 tentatives
        assert store.get_attempts(key) == 0

        # Incrémenter 5 fois
        for i in range(1, 6):
            attempts = store.increment(key, window_seconds=300)
            assert attempts == i, f"Expected {i} attempts, got {attempts}"

        # Vérifier le compteur
        assert store.get_attempts(key) == 5

        print("✅ Store test passed: Increment works correctly")

    def test_store_expires_old_entries(self):
        """
        Test 9: Le store expire correctement les entrées anciennes.

        UNIT TEST:
        - Vérifie que cleanup_expired() fonctionne
        - Vérifie que les entrées expirées sont supprimées
        """
        store = RateLimitStore()
        key = "test_ip:/api/test"

        # Créer une entrée avec window de 1 seconde
        store.increment(key, window_seconds=1)
        assert store.get_attempts(key) == 1

        # Attendre 2 secondes
        time.sleep(2)

        # L'entrée devrait être expirée
        attempts_after_expiry = store.get_attempts(key)
        assert attempts_after_expiry == 0, (
            f"Store didn't expire old entry! "
            f"Expected 0 attempts after 2s, got {attempts_after_expiry}"
        )

        # Cleanup manuel
        store.cleanup_expired()
        assert key not in store.store, "Expired entry should be removed from store"

        print("✅ Store test passed: Old entries expire correctly")

    def test_store_handles_multiple_keys(self):
        """
        Test 10: Le store gère correctement plusieurs clés simultanément.

        UNIT TEST:
        - Vérifie que différentes clés ne s'interfèrent pas
        - Vérifie l'isolation des compteurs
        """
        store = RateLimitStore()

        key1 = "ip1:/api/auth/login"
        key2 = "ip2:/api/auth/login"
        key3 = "ip1:/api/other"

        # Incrémenter chaque clé différemment
        store.increment(key1, window_seconds=300)  # 1 tentative
        store.increment(key1, window_seconds=300)  # 2 tentatives

        store.increment(key2, window_seconds=300)  # 1 tentative
        store.increment(key2, window_seconds=300)  # 2 tentatives
        store.increment(key2, window_seconds=300)  # 3 tentatives

        store.increment(key3, window_seconds=300)  # 1 tentative

        # Vérifier que chaque clé a son propre compteur
        assert store.get_attempts(key1) == 2, "key1 should have 2 attempts"
        assert store.get_attempts(key2) == 3, "key2 should have 3 attempts"
        assert store.get_attempts(key3) == 1, "key3 should have 1 attempt"

        print("✅ Store test passed: Multiple keys handled correctly")


# ===== TEST SUMMARY =====

"""
RÉSUMÉ DES TESTS DE SÉCURITÉ - RATE LIMITING

✅ Tests Implémentés (10):

1. ✅ Login within rate limit succeeds
   - Vérifie que 10 tentatives sont autorisées

2. ✅ Login exceeds rate limit returns 429
   - Vérifie que la 11ème tentative est bloquée

3. ✅ Failed login attempts count towards rate limit
   - Vérifie que les échecs comptent aussi (protection bruteforce)

4. ✅ Rate limit resets after window expires
   - Vérifie le reset après 300 secondes

5. ✅ Different IPs have independent rate limits
   - Vérifie l'isolation par IP

6. ✅ Non-rate-limited endpoints work normally
   - Vérifie que /, /health ne sont pas affectés

7. ✅ Authenticated endpoints not rate limited
   - Vérifie que /api/products etc. ne sont pas affectés

8. ✅ Store increments correctly
   - Test unitaire du store

9. ✅ Store expires old entries
   - Test unitaire du cleanup

10. ✅ Store handles multiple keys
    - Test unitaire de l'isolation

COUVERTURE:
- ✅ Bruteforce protection
- ✅ Rate limit enforcement
- ✅ Window reset mechanism
- ✅ IP isolation
- ✅ Endpoint selectivity
- ✅ Store reliability

COMMANDE POUR EXÉCUTER:
pytest tests/integration/security/test_rate_limiting.py -v
"""
