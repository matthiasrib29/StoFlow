"""
Tests pour la migration JWT HS256 → RS256 (asymétrique).

Couverture:
- Création de tokens avec RS256 (clés RSA)
- Vérification de tokens RS256
- Fallback vers HS256 pour tokens anciens (migration en douceur)
- Validation du type de token (access vs refresh)
- Logs de fallback HS256 pour monitoring

Author: Claude
Date: 2026-01-07
"""

import pytest
from datetime import timedelta
from unittest.mock import Mock, patch, MagicMock
from jose import jwt
from pathlib import Path

from services.auth_service import AuthService
from shared.datetime_utils import utc_now


# RSA keypair pour tests (ces clés existent déjà dans backend/keys/)
RSA_PRIVATE_KEY = Path(__file__).parent.parent.parent.parent / "keys" / "private_key.pem"
RSA_PUBLIC_KEY = Path(__file__).parent.parent.parent.parent / "keys" / "public_key.pem"


@pytest.fixture
def rsa_keys():
    """Charge les clés RSA depuis les fichiers."""
    if not RSA_PRIVATE_KEY.exists() or not RSA_PUBLIC_KEY.exists():
        pytest.skip("RSA keys not generated yet. Run: openssl genrsa -out backend/keys/private_key.pem 2048")

    return {
        "private": RSA_PRIVATE_KEY.read_text(),
        "public": RSA_PUBLIC_KEY.read_text(),
    }


class TestCreateAccessTokenRS256:
    """Tests pour create_access_token avec RS256."""

    @patch('services.auth_service.settings')
    def test_create_access_token_rs256(self, mock_settings, rsa_keys):
        """Test création d'access token en RS256."""
        mock_settings.jwt_private_key_pem = rsa_keys["private"]
        mock_settings.jwt_access_token_expire_minutes = 15

        token = AuthService.create_access_token(user_id=1, role="user")

        assert isinstance(token, str)
        assert len(token) > 0

        # Vérifier que le token est signé avec RS256
        payload = jwt.decode(token, rsa_keys["public"], algorithms=["RS256"])
        assert payload["user_id"] == 1
        assert payload["role"] == "user"
        assert payload["type"] == "access"

    @patch('services.auth_service.settings')
    def test_access_token_uses_correct_algorithm(self, mock_settings, rsa_keys):
        """Test que le token utilise RS256 (pas HS256)."""
        mock_settings.jwt_private_key_pem = rsa_keys["private"]
        mock_settings.jwt_access_token_expire_minutes = 15

        token = AuthService.create_access_token(user_id=1, role="user")

        # Décoder sans vérification pour lire le header
        header = jwt.get_unverified_header(token)
        assert header["alg"] == "RS256"

    @patch('services.auth_service.settings')
    def test_access_token_expiration_15_minutes(self, mock_settings, rsa_keys):
        """Test que l'access token expire en 15 minutes."""
        mock_settings.jwt_private_key_pem = rsa_keys["private"]
        mock_settings.jwt_access_token_expire_minutes = 15

        token = AuthService.create_access_token(user_id=1, role="user")
        payload = jwt.decode(token, rsa_keys["public"], algorithms=["RS256"])

        exp_datetime = payload["exp"]
        iat_datetime = payload["iat"]

        # Différence entre exp et iat doit être d'environ 15 minutes
        diff_seconds = exp_datetime - iat_datetime
        expected_seconds = 15 * 60
        assert abs(diff_seconds - expected_seconds) < 5  # Tolérance 5 sec

    @patch('services.auth_service.settings')
    def test_create_access_token_raises_without_private_key(self, mock_settings):
        """Test que create_access_token lève une exception sans clé privée."""
        mock_settings.jwt_private_key_pem = None

        with pytest.raises(ValueError, match="JWT_PRIVATE_KEY_PEM not configured"):
            AuthService.create_access_token(user_id=1, role="user")


class TestCreateRefreshTokenRS256:
    """Tests pour create_refresh_token avec RS256."""

    @patch('services.auth_service.settings')
    def test_create_refresh_token_rs256(self, mock_settings, rsa_keys):
        """Test création de refresh token en RS256."""
        mock_settings.jwt_private_key_pem = rsa_keys["private"]
        mock_settings.jwt_refresh_token_expire_days = 7

        token = AuthService.create_refresh_token(user_id=1)

        assert isinstance(token, str)
        assert len(token) > 0

        # Vérifier que le token est signé avec RS256
        payload = jwt.decode(token, rsa_keys["public"], algorithms=["RS256"])
        assert payload["user_id"] == 1
        assert payload["type"] == "refresh"

    @patch('services.auth_service.settings')
    def test_refresh_token_uses_rs256(self, mock_settings, rsa_keys):
        """Test que le refresh token utilise RS256."""
        mock_settings.jwt_private_key_pem = rsa_keys["private"]
        mock_settings.jwt_refresh_token_expire_days = 7

        token = AuthService.create_refresh_token(user_id=1)

        header = jwt.get_unverified_header(token)
        assert header["alg"] == "RS256"

    @patch('services.auth_service.settings')
    def test_refresh_token_expiration_7_days(self, mock_settings, rsa_keys):
        """Test que le refresh token expire en 7 jours."""
        mock_settings.jwt_private_key_pem = rsa_keys["private"]
        mock_settings.jwt_refresh_token_expire_days = 7

        token = AuthService.create_refresh_token(user_id=1)
        payload = jwt.decode(token, rsa_keys["public"], algorithms=["RS256"])

        diff_seconds = payload["exp"] - payload["iat"]
        expected_seconds = 7 * 24 * 60 * 60  # 7 jours
        assert abs(diff_seconds - expected_seconds) < 5


class TestVerifyTokenRS256:
    """Tests pour verify_token avec RS256."""

    @patch('services.auth_service.settings')
    def test_verify_rs256_token(self, mock_settings, rsa_keys):
        """Test vérification d'un token RS256."""
        mock_settings.jwt_private_key_pem = rsa_keys["private"]
        mock_settings.jwt_public_key_pem = rsa_keys["public"]
        mock_settings.jwt_secret_key = "old_hs256_secret"
        mock_settings.jwt_secret_key_previous = None
        mock_settings.jwt_access_token_expire_minutes = 15

        token = AuthService.create_access_token(user_id=1, role="user")
        payload = AuthService.verify_token(token, token_type="access")

        assert payload is not None
        assert payload["user_id"] == 1
        assert payload["role"] == "user"
        assert payload["type"] == "access"

    @patch('services.auth_service.settings')
    def test_verify_refresh_token_rs256(self, mock_settings, rsa_keys):
        """Test vérification d'un refresh token RS256."""
        mock_settings.jwt_private_key_pem = rsa_keys["private"]
        mock_settings.jwt_public_key_pem = rsa_keys["public"]
        mock_settings.jwt_secret_key = "old_hs256_secret"
        mock_settings.jwt_secret_key_previous = None
        mock_settings.jwt_refresh_token_expire_days = 7

        token = AuthService.create_refresh_token(user_id=1)
        payload = AuthService.verify_token(token, token_type="refresh")

        assert payload is not None
        assert payload["user_id"] == 1
        assert payload["type"] == "refresh"

    @patch('services.auth_service.settings')
    def test_verify_wrong_token_type_returns_none(self, mock_settings, rsa_keys):
        """Test que vérifier avec mauvais type retourne None."""
        mock_settings.jwt_private_key_pem = rsa_keys["private"]
        mock_settings.jwt_public_key_pem = rsa_keys["public"]
        mock_settings.jwt_secret_key = "old_hs256_secret"
        mock_settings.jwt_secret_key_previous = None
        mock_settings.jwt_access_token_expire_minutes = 15

        access_token = AuthService.create_access_token(user_id=1, role="user")

        # Essayer de vérifier comme refresh token doit échouer
        payload = AuthService.verify_token(access_token, token_type="refresh")
        assert payload is None

    @patch('services.auth_service.settings')
    def test_verify_invalid_token_returns_none(self, mock_settings, rsa_keys):
        """Test que vérifier un token invalide retourne None."""
        mock_settings.jwt_public_key_pem = rsa_keys["public"]
        mock_settings.jwt_secret_key = "old_hs256_secret"
        mock_settings.jwt_secret_key_previous = None

        payload = AuthService.verify_token("invalid.token.here", token_type="access")
        assert payload is None


class TestHS256Fallback:
    """Tests pour le fallback HS256 (migration en douceur)."""

    @patch('services.auth_service.settings')
    @patch('services.auth_service.logger')
    def test_verify_old_hs256_token_with_fallback(self, mock_logger, mock_settings, rsa_keys):
        """Test que les anciens tokens HS256 fonctionnent avec fallback."""
        # Créer un ancien token HS256
        old_secret = "old_jwt_secret_key"
        old_payload = {
            "user_id": 1,
            "role": "user",
            "type": "access",
            "exp": int((utc_now() + timedelta(hours=1)).timestamp()),
            "iat": int(utc_now().timestamp()),
        }
        old_hs256_token = jwt.encode(old_payload, old_secret, algorithm="HS256")

        # Configuration pour le fallback: RS256 échoue, HS256 réussit
        mock_settings.jwt_public_key_pem = rsa_keys["public"]  # RS256 échouera
        mock_settings.jwt_secret_key = old_secret  # HS256 réussira
        mock_settings.jwt_secret_key_previous = None

        # Vérifier le token
        payload = AuthService.verify_token(old_hs256_token, token_type="access")

        assert payload is not None
        assert payload["user_id"] == 1
        assert payload["role"] == "user"

        # Vérifier que le fallback est loggé
        assert mock_logger.warning.called
        call_args = str(mock_logger.warning.call_args)
        assert "HS256 fallback" in call_args
        assert "migration in progress" in call_args

    @patch('services.auth_service.settings')
    @patch('services.auth_service.logger')
    def test_verify_hs256_logs_warning(self, mock_logger, mock_settings, rsa_keys):
        """Test que le fallback HS256 produit un warning log."""
        old_secret = "old_secret"
        old_payload = {
            "user_id=": 1,
            "type": "access",
            "exp": int((utc_now() + timedelta(hours=1)).timestamp()),
            "iat": int(utc_now().timestamp()),
        }
        old_token = jwt.encode(old_payload, old_secret, algorithm="HS256")

        mock_settings.jwt_public_key_pem = rsa_keys["public"]
        mock_settings.jwt_secret_key = old_secret
        mock_settings.jwt_secret_key_previous = None

        AuthService.verify_token(old_token, token_type="access")

        # Le warning doit être loggé
        mock_logger.warning.assert_called()

    @patch('services.auth_service.settings')
    def test_verify_invalid_hs256_returns_none(self, mock_settings, rsa_keys):
        """Test que un token HS256 invalide retourne None."""
        mock_settings.jwt_public_key_pem = rsa_keys["public"]
        mock_settings.jwt_secret_key = "wrong_secret"
        mock_settings.jwt_secret_key_previous = None

        old_payload = {
            "user_id": 1,
            "type": "access",
            "exp": int((utc_now() + timedelta(hours=1)).timestamp()),
            "iat": int(utc_now().timestamp()),
        }
        token = jwt.encode(old_payload, "correct_secret", algorithm="HS256")

        # Vérifier avec mauvais secret doit échouer
        payload = AuthService.verify_token(token, token_type="access")
        assert payload is None


class TestMigrationScenarios:
    """Tests d'intégration pour les scénarios de migration."""

    @patch('services.auth_service.settings')
    def test_new_rs256_tokens_work_immediately(self, mock_settings, rsa_keys):
        """Test que les nouveaux tokens RS256 fonctionnent dès la migration."""
        mock_settings.jwt_private_key_pem = rsa_keys["private"]
        mock_settings.jwt_public_key_pem = rsa_keys["public"]
        mock_settings.jwt_secret_key = "old_hs256_secret"
        mock_settings.jwt_secret_key_previous = None
        mock_settings.jwt_access_token_expire_minutes = 15
        mock_settings.jwt_refresh_token_expire_days = 7

        # Créer des tokens RS256
        access_token = AuthService.create_access_token(user_id=1, role="user")
        refresh_token = AuthService.create_refresh_token(user_id=1)

        # Vérifier les tokens
        access_payload = AuthService.verify_token(access_token, token_type="access")
        refresh_payload = AuthService.verify_token(refresh_token, token_type="refresh")

        assert access_payload["user_id"] == 1
        assert refresh_payload["user_id"] == 1

    @patch('services.auth_service.settings')
    @patch('services.auth_service.logger')
    def test_old_hs256_tokens_still_work_during_migration(self, mock_logger, mock_settings, rsa_keys):
        """Test que les anciens tokens HS256 fonctionnent pendant la migration."""
        old_secret = "old_jwt_secret_key"

        # Créer un ancien token HS256
        old_payload = {
            "user_id": 1,
            "role": "admin",
            "type": "access",
            "exp": int((utc_now() + timedelta(hours=1)).timestamp()),
            "iat": int(utc_now().timestamp()),
        }
        old_hs256_token = jwt.encode(old_payload, old_secret, algorithm="HS256")

        # Configuration: les nouveaux tokens sont RS256, mais on supporte HS256
        mock_settings.jwt_private_key_pem = rsa_keys["private"]
        mock_settings.jwt_public_key_pem = rsa_keys["public"]
        mock_settings.jwt_secret_key = old_secret
        mock_settings.jwt_secret_key_previous = None

        # Créer un nouveau token RS256
        new_rs256_token = AuthService.create_access_token(user_id=2, role="user")

        # Vérifier les deux tokens
        old_payload = AuthService.verify_token(old_hs256_token, token_type="access")
        new_payload = AuthService.verify_token(new_rs256_token, token_type="access")

        assert old_payload["user_id"] == 1
        assert old_payload["role"] == "admin"
        assert new_payload["user_id"] == 2

        # Le fallback HS256 doit être loggé comme warning
        assert mock_logger.warning.called
