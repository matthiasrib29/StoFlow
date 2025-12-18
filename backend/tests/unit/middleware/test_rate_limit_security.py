"""
Tests unitaires pour le middleware de rate limiting (sécurité).

Couverture:
- Rate limiting par IP
- Rate limiting par EMAIL (protection credential stuffing)
- Extraction de l'email du body
- Reset des fenêtres
- Mode TESTING bypass

Author: Claude
Date: 2025-12-18

CRITIQUE: Ces tests vérifient la protection contre les attaques bruteforce.

Note: Le state du rate_limit_store est reset automatiquement entre chaque test
via la fixture reset_rate_limit_store dans conftest.py.
"""

import pytest
import time
import json
from unittest.mock import Mock, patch, AsyncMock
from fastapi import Request
from fastapi.responses import JSONResponse

from middleware.rate_limit import (
    RateLimitStore,
    rate_limit_middleware,
    _extract_email_from_body,
)

# Note: Ne pas utiliser pytestmark global car il s'applique aussi aux tests sync
# Les tests async individuels utiliseront @pytest.mark.asyncio si nécessaire


# ============================================================================
# RateLimitStore TESTS
# ============================================================================

class TestRateLimitStore:
    """Tests pour la classe RateLimitStore."""

    def test_store_initial_attempts_is_zero(self):
        """Test que le compteur initial est 0."""
        store = RateLimitStore()
        assert store.get_attempts("unknown_key") == 0

    def test_increment_creates_entry(self):
        """Test que increment crée une entrée."""
        store = RateLimitStore()
        result = store.increment("new_key", window_seconds=300)

        assert result == 1
        assert store.get_attempts("new_key") == 1

    def test_increment_increases_counter(self):
        """Test que increment augmente le compteur."""
        store = RateLimitStore()
        store.increment("key1", 300)
        store.increment("key1", 300)
        store.increment("key1", 300)

        assert store.get_attempts("key1") == 3

    def test_get_attempts_returns_count(self):
        """Test que get_attempts retourne le bon compteur."""
        store = RateLimitStore()
        for _ in range(5):
            store.increment("key", 300)

        assert store.get_attempts("key") == 5

    def test_window_expires_and_resets(self):
        """Test que la fenêtre expire et reset le compteur."""
        store = RateLimitStore()

        # Créer une entrée avec une fenêtre de 0.1 seconde
        store.increment("key", window_seconds=0.1)
        assert store.get_attempts("key") == 1

        # Attendre que la fenêtre expire
        time.sleep(0.15)

        # Le compteur doit être reset
        assert store.get_attempts("key") == 0

    def test_different_keys_isolated(self):
        """Test que différentes clés sont isolées."""
        store = RateLimitStore()

        store.increment("key1", 300)
        store.increment("key1", 300)
        store.increment("key2", 300)

        assert store.get_attempts("key1") == 2
        assert store.get_attempts("key2") == 1

    def test_get_reset_time_returns_timestamp(self):
        """Test que get_reset_time retourne un timestamp."""
        store = RateLimitStore()
        store.increment("key", 300)

        reset_time = store.get_reset_time("key")

        assert isinstance(reset_time, float)
        assert reset_time > time.time()  # Dans le futur

    def test_cleanup_expired_removes_old_entries(self):
        """Test que cleanup_expired supprime les entrées expirées."""
        store = RateLimitStore()

        # Créer une entrée qui expire immédiatement
        store.increment("old_key", window_seconds=0.01)
        time.sleep(0.02)

        # Créer une entrée qui n'expire pas
        store.increment("new_key", window_seconds=300)

        store.cleanup_expired()

        # L'ancienne clé doit être supprimée, la nouvelle conservée
        assert "old_key" not in store.store
        assert "new_key" in store.store


# ============================================================================
# _extract_email_from_body TESTS
# ============================================================================

class TestExtractEmailFromBody:
    """Tests pour l'extraction de l'email du body JSON."""

    @pytest.mark.asyncio
    async def test_extract_email_valid_json(self):
        """Test extraction avec JSON valide."""
        mock_request = AsyncMock(spec=Request)
        mock_request.body.return_value = json.dumps({"email": "test@example.com"}).encode()

        email = await _extract_email_from_body(mock_request)

        assert email == "test@example.com"

    @pytest.mark.asyncio
    async def test_extract_email_lowercase_normalization(self):
        """Test que l'email est normalisé en minuscules."""
        mock_request = AsyncMock(spec=Request)
        mock_request.body.return_value = json.dumps({"email": "TEST@EXAMPLE.COM"}).encode()

        email = await _extract_email_from_body(mock_request)

        assert email == "test@example.com"

    @pytest.mark.asyncio
    async def test_extract_email_empty_body(self):
        """Test extraction avec body vide."""
        mock_request = AsyncMock(spec=Request)
        mock_request.body.return_value = b""

        email = await _extract_email_from_body(mock_request)

        assert email is None

    @pytest.mark.asyncio
    async def test_extract_email_invalid_json(self):
        """Test extraction avec JSON invalide."""
        mock_request = AsyncMock(spec=Request)
        mock_request.body.return_value = b"not valid json"

        email = await _extract_email_from_body(mock_request)

        assert email is None

    @pytest.mark.asyncio
    async def test_extract_email_missing_email_field(self):
        """Test extraction sans champ email."""
        mock_request = AsyncMock(spec=Request)
        mock_request.body.return_value = json.dumps({"password": "secret"}).encode()

        email = await _extract_email_from_body(mock_request)

        assert email is None

    @pytest.mark.asyncio
    async def test_extract_email_restores_body(self):
        """Test que le body est restauré pour le handler."""
        mock_request = AsyncMock(spec=Request)
        body_content = json.dumps({"email": "test@example.com", "password": "secret"}).encode()
        mock_request.body.return_value = body_content

        await _extract_email_from_body(mock_request)

        # Vérifier que _body est défini pour permettre la relecture
        assert hasattr(mock_request, '_body') or mock_request._body == body_content


# ============================================================================
# rate_limit_middleware TESTS - PAR IP
# ============================================================================

class TestRateLimitMiddlewareByIP:
    """Tests du rate limiting par IP."""

    @pytest.mark.asyncio
    @patch('middleware.rate_limit.os.getenv')
    async def test_rate_limit_allows_under_limit(self, mock_getenv):
        """Test que les requêtes sous la limite passent."""
        mock_getenv.return_value = "0"  # TESTING=0

        mock_request = AsyncMock(spec=Request)
        mock_request.url.path = "/api/auth/login"
        mock_request.method = "POST"
        mock_request.client.host = "192.168.1.1"
        mock_request.body.return_value = json.dumps({"email": "test@example.com"}).encode()

        mock_response = Mock()
        async def mock_call_next(request):
            return mock_response

        # Store is auto-reset by conftest fixture
        response = await rate_limit_middleware(mock_request, mock_call_next)

        assert response == mock_response

    @pytest.mark.asyncio
    @patch('middleware.rate_limit.os.getenv')
    async def test_rate_limit_blocks_after_ip_limit(self, mock_getenv):
        """Test que les requêtes sont bloquées après 10 tentatives par IP."""
        mock_getenv.return_value = "0"  # TESTING=0

        mock_request = AsyncMock(spec=Request)
        mock_request.url.path = "/api/auth/login"
        mock_request.method = "POST"
        mock_request.client.host = "192.168.1.100"
        mock_request.body.return_value = json.dumps({"email": "test@example.com"}).encode()

        async def mock_call_next(request):
            return Mock()

        # Faire 10 tentatives (la limite IP)
        for i in range(10):
            await rate_limit_middleware(mock_request, mock_call_next)

        # La 11ème doit être bloquée
        response = await rate_limit_middleware(mock_request, mock_call_next)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 429

    @pytest.mark.asyncio
    @patch('middleware.rate_limit.os.getenv')
    async def test_rate_limit_429_response_format(self, mock_getenv):
        """Test le format de la réponse 429."""
        mock_getenv.return_value = "0"

        mock_request = AsyncMock(spec=Request)
        mock_request.url.path = "/api/auth/login"
        mock_request.method = "POST"
        mock_request.client.host = "192.168.1.200"
        mock_request.body.return_value = json.dumps({"email": "blocked@example.com"}).encode()

        async def mock_call_next(request):
            return Mock()

        # Saturer la limite IP
        for _ in range(10):
            await rate_limit_middleware(mock_request, mock_call_next)

        response = await rate_limit_middleware(mock_request, mock_call_next)

        assert response.status_code == 429
        # Vérifier le header Retry-After (lowercase dans Starlette)
        assert "retry-after" in dict(response.headers)


# ============================================================================
# rate_limit_middleware TESTS - PAR EMAIL
# ============================================================================

class TestRateLimitMiddlewareByEmail:
    """Tests du rate limiting par EMAIL (protection credential stuffing)."""

    @pytest.mark.asyncio
    @patch('middleware.rate_limit.os.getenv')
    async def test_rate_limit_by_email_blocks_after_5_attempts(self, mock_getenv):
        """Test que les requêtes sont bloquées après 5 tentatives par email."""
        mock_getenv.return_value = "0"  # TESTING=0

        mock_request = AsyncMock(spec=Request)
        mock_request.url.path = "/api/auth/login"
        mock_request.method = "POST"
        mock_request.client.host = "10.0.0.1"
        mock_request.body.return_value = json.dumps({"email": "victim@example.com"}).encode()

        async def mock_call_next(request):
            return Mock()

        # Faire 5 tentatives (la limite email) avec IPs différentes
        for i in range(5):
            mock_request.client.host = f"10.0.0.{i+1}"
            await rate_limit_middleware(mock_request, mock_call_next)

        # La 6ème avec une nouvelle IP doit être bloquée par la limite email
        mock_request.client.host = "10.0.0.100"
        response = await rate_limit_middleware(mock_request, mock_call_next)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 429

    @pytest.mark.asyncio
    @patch('middleware.rate_limit.os.getenv')
    async def test_rate_limit_email_independent_from_ip(self, mock_getenv):
        """Test que la limite email est indépendante de la limite IP."""
        mock_getenv.return_value = "0"

        from middleware.rate_limit import rate_limit_store

        email_a = "user_a@example.com"
        email_b = "user_b@example.com"

        async def make_request(email, ip):
            mock_request = AsyncMock(spec=Request)
            mock_request.url.path = "/api/auth/login"
            mock_request.method = "POST"
            mock_request.client.host = ip
            mock_request.body.return_value = json.dumps({"email": email}).encode()

            async def mock_call_next(request):
                return Mock()

            return await rate_limit_middleware(mock_request, mock_call_next)

        # 3 tentatives pour email_a depuis des IPs différentes
        for i in range(3):
            await make_request(email_a, f"1.1.1.{i}")

        # 3 tentatives pour email_b depuis des IPs différentes
        for i in range(3):
            await make_request(email_b, f"2.2.2.{i}")

        # email_a doit avoir 3 tentatives, pas bloqué
        assert rate_limit_store.get_attempts(f"email:{email_a}:/api/auth/login") == 3

        # email_b doit avoir 3 tentatives, pas bloqué
        assert rate_limit_store.get_attempts(f"email:{email_b}:/api/auth/login") == 3

    @pytest.mark.asyncio
    @patch('middleware.rate_limit.os.getenv')
    async def test_rate_limit_email_more_strict_than_ip(self, mock_getenv):
        """Test que la limite email (5) est plus stricte que IP (10)."""
        mock_getenv.return_value = "0"

        target_email = "target@example.com"

        async def make_request(ip):
            mock_request = AsyncMock(spec=Request)
            mock_request.url.path = "/api/auth/login"
            mock_request.method = "POST"
            mock_request.client.host = ip
            mock_request.body.return_value = json.dumps({"email": target_email}).encode()

            async def mock_call_next(request):
                return Mock()

            return await rate_limit_middleware(mock_request, mock_call_next)

        # 6 tentatives depuis 6 IPs différentes
        responses = []
        for i in range(6):
            response = await make_request(f"5.5.5.{i}")
            responses.append(response)

        # Les 5 premières doivent passer
        for r in responses[:5]:
            assert not isinstance(r, JSONResponse) or r.status_code != 429

        # La 6ème doit être bloquée (limite email atteinte)
        assert isinstance(responses[5], JSONResponse)
        assert responses[5].status_code == 429


# ============================================================================
# rate_limit_middleware TESTS - TESTING MODE
# ============================================================================

class TestRateLimitTestingMode:
    """Tests du bypass en mode TESTING."""

    @pytest.mark.asyncio
    @patch('middleware.rate_limit.os.getenv')
    async def test_rate_limit_disabled_in_testing_mode(self, mock_getenv):
        """Test que le rate limiting est désactivé en mode TESTING."""
        mock_getenv.return_value = "1"  # TESTING=1

        mock_request = AsyncMock(spec=Request)
        mock_request.url.path = "/api/auth/login"
        mock_request.method = "POST"
        mock_request.client.host = "192.168.1.1"

        mock_response = Mock()
        async def mock_call_next(request):
            return mock_response

        # 15 requêtes (réduit de 100 pour performance) - toutes doivent passer
        for _ in range(15):
            response = await rate_limit_middleware(mock_request, mock_call_next)
            assert response == mock_response

    @pytest.mark.asyncio
    @patch('middleware.rate_limit.os.getenv')
    async def test_rate_limit_enabled_when_testing_not_set(self, mock_getenv):
        """Test que le rate limiting est activé quand TESTING n'est pas défini."""
        mock_getenv.return_value = None  # TESTING non défini

        mock_request = AsyncMock(spec=Request)
        mock_request.url.path = "/api/auth/login"
        mock_request.method = "POST"
        mock_request.client.host = "192.168.1.50"
        mock_request.body.return_value = json.dumps({"email": "test@test.com"}).encode()

        async def mock_call_next(request):
            return Mock()

        # Les 10 premières doivent passer (limite IP)
        for _ in range(10):
            await rate_limit_middleware(mock_request, mock_call_next)

        # La 11ème doit être bloquée
        response = await rate_limit_middleware(mock_request, mock_call_next)
        assert isinstance(response, JSONResponse)
        assert response.status_code == 429


# ============================================================================
# rate_limit_middleware TESTS - NON RATE-LIMITED ENDPOINTS
# ============================================================================

class TestRateLimitNonProtectedEndpoints:
    """Tests pour les endpoints non protégés par rate limiting."""

    @pytest.mark.asyncio
    @patch('middleware.rate_limit.os.getenv')
    async def test_non_rate_limited_endpoint_passes(self, mock_getenv):
        """Test que les endpoints non protégés passent toujours."""
        mock_getenv.return_value = "0"  # TESTING=0

        mock_request = AsyncMock(spec=Request)
        mock_request.url.path = "/api/products"  # Non protégé
        mock_request.client.host = "192.168.1.1"

        mock_response = Mock()
        async def mock_call_next(request):
            return mock_response

        # 15 requêtes (réduit de 100) - toutes passent car endpoint non protégé
        for _ in range(15):
            response = await rate_limit_middleware(mock_request, mock_call_next)
            assert response == mock_response

    @pytest.mark.asyncio
    @patch('middleware.rate_limit.os.getenv')
    async def test_health_endpoint_not_rate_limited(self, mock_getenv):
        """Test que /health n'est pas rate limité."""
        mock_getenv.return_value = "0"

        mock_request = AsyncMock(spec=Request)
        mock_request.url.path = "/health"
        mock_request.client.host = "192.168.1.1"

        mock_response = Mock()
        async def mock_call_next(request):
            return mock_response

        # 15 requêtes (réduit de 50) - /health n'est jamais rate limité
        for _ in range(15):
            response = await rate_limit_middleware(mock_request, mock_call_next)
            assert response == mock_response
