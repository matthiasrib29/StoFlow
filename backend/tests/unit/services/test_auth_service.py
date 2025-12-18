"""
Tests unitaires pour AuthService.

Couverture:
- Hash et vérification de mots de passe (bcrypt)
- Création et vérification de tokens JWT (access/refresh)
- Authentification utilisateur
- Refresh de tokens
- Limites d'abonnement

Author: Claude
Date: 2025-12-10
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch, MagicMock
from jose import jwt

from services.auth_service import AuthService
from models.public.user import SubscriptionTier
from shared.datetime_utils import utc_now


class TestHashPassword:
    """Tests pour la méthode hash_password."""

    def test_hash_password_returns_string(self):
        """Test que hash_password retourne une string."""
        result = AuthService.hash_password("testpassword")
        assert isinstance(result, str)

    def test_hash_password_different_from_input(self):
        """Test que le hash est différent du mot de passe."""
        password = "mypassword123"
        hashed = AuthService.hash_password(password)
        assert hashed != password

    def test_hash_password_unique_salt(self):
        """Test que chaque hash est unique (salt différent)."""
        password = "samepassword"
        hash1 = AuthService.hash_password(password)
        hash2 = AuthService.hash_password(password)
        assert hash1 != hash2  # Salts différents

    def test_hash_password_bcrypt_format(self):
        """Test que le hash est au format bcrypt."""
        hashed = AuthService.hash_password("password")
        # bcrypt hash starts with $2a$, $2b$, or $2y$
        assert hashed.startswith('$2')

    def test_hash_password_handles_special_chars(self):
        """Test hash avec caractères spéciaux."""
        password = "p@$$w0rd!#%&*()éàü"
        hashed = AuthService.hash_password(password)
        assert isinstance(hashed, str)
        assert len(hashed) > 0


class TestVerifyPassword:
    """Tests pour la méthode verify_password."""

    def test_verify_correct_password(self):
        """Test vérification mot de passe correct."""
        password = "correctpassword"
        hashed = AuthService.hash_password(password)

        assert AuthService.verify_password(password, hashed) is True

    def test_verify_wrong_password(self):
        """Test vérification mot de passe incorrect."""
        password = "correctpassword"
        wrong_password = "wrongpassword"
        hashed = AuthService.hash_password(password)

        assert AuthService.verify_password(wrong_password, hashed) is False

    def test_verify_empty_password(self):
        """Test vérification avec mot de passe vide."""
        hashed = AuthService.hash_password("somepassword")

        assert AuthService.verify_password("", hashed) is False

    def test_verify_special_chars(self):
        """Test vérification avec caractères spéciaux."""
        password = "p@$$w0rd!éàü"
        hashed = AuthService.hash_password(password)

        assert AuthService.verify_password(password, hashed) is True
        assert AuthService.verify_password("different", hashed) is False

    def test_verify_case_sensitive(self):
        """Test que la vérification est sensible à la casse."""
        password = "MyPassword"
        hashed = AuthService.hash_password(password)

        assert AuthService.verify_password("MyPassword", hashed) is True
        assert AuthService.verify_password("mypassword", hashed) is False
        assert AuthService.verify_password("MYPASSWORD", hashed) is False


class TestCreateAccessToken:
    """Tests pour la méthode create_access_token."""

    @patch('services.auth_service.settings')
    def test_create_access_token_returns_string(self, mock_settings):
        """Test que create_access_token retourne une string."""
        mock_settings.jwt_secret_key = "test_secret"
        mock_settings.jwt_algorithm = "HS256"

        token = AuthService.create_access_token(user_id=1, role="user")

        assert isinstance(token, str)
        assert len(token) > 0

    @patch('services.auth_service.settings')
    def test_access_token_contains_user_id(self, mock_settings):
        """Test que le token contient user_id."""
        mock_settings.jwt_secret_key = "test_secret"
        mock_settings.jwt_algorithm = "HS256"

        token = AuthService.create_access_token(user_id=123, role="user")
        payload = jwt.decode(token, "test_secret", algorithms=["HS256"])

        assert payload["user_id"] == 123

    @patch('services.auth_service.settings')
    def test_access_token_contains_role(self, mock_settings):
        """Test que le token contient le rôle."""
        mock_settings.jwt_secret_key = "test_secret"
        mock_settings.jwt_algorithm = "HS256"

        token = AuthService.create_access_token(user_id=1, role="admin")
        payload = jwt.decode(token, "test_secret", algorithms=["HS256"])

        assert payload["role"] == "admin"

    @patch('services.auth_service.settings')
    def test_access_token_type_is_access(self, mock_settings):
        """Test que le type de token est 'access'."""
        mock_settings.jwt_secret_key = "test_secret"
        mock_settings.jwt_algorithm = "HS256"

        token = AuthService.create_access_token(user_id=1, role="user")
        payload = jwt.decode(token, "test_secret", algorithms=["HS256"])

        assert payload["type"] == "access"

    @patch('services.auth_service.settings')
    def test_access_token_has_expiration(self, mock_settings):
        """Test que le token a une expiration."""
        mock_settings.jwt_secret_key = "test_secret"
        mock_settings.jwt_algorithm = "HS256"

        token = AuthService.create_access_token(user_id=1, role="user")
        payload = jwt.decode(token, "test_secret", algorithms=["HS256"])

        assert "exp" in payload
        # Expiration dans environ 1 heure
        exp_datetime = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        now = utc_now()
        diff = exp_datetime - now
        assert 55 <= diff.total_seconds() / 60 <= 65  # Entre 55 et 65 minutes


class TestCreateRefreshToken:
    """Tests pour la méthode create_refresh_token."""

    @patch('services.auth_service.settings')
    def test_create_refresh_token_returns_string(self, mock_settings):
        """Test que create_refresh_token retourne une string."""
        mock_settings.jwt_secret_key = "test_secret"
        mock_settings.jwt_algorithm = "HS256"

        token = AuthService.create_refresh_token(user_id=1)

        assert isinstance(token, str)
        assert len(token) > 0

    @patch('services.auth_service.settings')
    def test_refresh_token_contains_user_id(self, mock_settings):
        """Test que le refresh token contient user_id."""
        mock_settings.jwt_secret_key = "test_secret"
        mock_settings.jwt_algorithm = "HS256"

        token = AuthService.create_refresh_token(user_id=456)
        payload = jwt.decode(token, "test_secret", algorithms=["HS256"])

        assert payload["user_id"] == 456

    @patch('services.auth_service.settings')
    def test_refresh_token_type_is_refresh(self, mock_settings):
        """Test que le type de token est 'refresh'."""
        mock_settings.jwt_secret_key = "test_secret"
        mock_settings.jwt_algorithm = "HS256"

        token = AuthService.create_refresh_token(user_id=1)
        payload = jwt.decode(token, "test_secret", algorithms=["HS256"])

        assert payload["type"] == "refresh"

    @patch('services.auth_service.settings')
    def test_refresh_token_no_role(self, mock_settings):
        """Test que le refresh token n'a pas de rôle."""
        mock_settings.jwt_secret_key = "test_secret"
        mock_settings.jwt_algorithm = "HS256"

        token = AuthService.create_refresh_token(user_id=1)
        payload = jwt.decode(token, "test_secret", algorithms=["HS256"])

        assert "role" not in payload

    @patch('services.auth_service.settings')
    def test_refresh_token_7_days_expiration(self, mock_settings):
        """Test que le refresh token expire dans 7 jours."""
        mock_settings.jwt_secret_key = "test_secret"
        mock_settings.jwt_algorithm = "HS256"

        token = AuthService.create_refresh_token(user_id=1)
        payload = jwt.decode(token, "test_secret", algorithms=["HS256"])

        exp_datetime = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        now = utc_now()
        diff = exp_datetime - now
        # Entre 6.9 et 7.1 jours
        assert 6.9 <= diff.days + diff.seconds / 86400 <= 7.1


class TestVerifyToken:
    """Tests pour la méthode verify_token."""

    @patch('services.auth_service.settings')
    def test_verify_valid_access_token(self, mock_settings):
        """Test vérification d'un access token valide."""
        mock_settings.jwt_secret_key = "test_secret"
        mock_settings.jwt_algorithm = "HS256"

        token = AuthService.create_access_token(user_id=1, role="user")
        payload = AuthService.verify_token(token, token_type="access")

        assert payload is not None
        assert payload["user_id"] == 1
        assert payload["role"] == "user"

    @patch('services.auth_service.settings')
    def test_verify_valid_refresh_token(self, mock_settings):
        """Test vérification d'un refresh token valide."""
        mock_settings.jwt_secret_key = "test_secret"
        mock_settings.jwt_algorithm = "HS256"

        token = AuthService.create_refresh_token(user_id=1)
        payload = AuthService.verify_token(token, token_type="refresh")

        assert payload is not None
        assert payload["user_id"] == 1
        assert payload["type"] == "refresh"

    @patch('services.auth_service.settings')
    def test_verify_wrong_token_type(self, mock_settings):
        """Test vérification avec mauvais type de token."""
        mock_settings.jwt_secret_key = "test_secret"
        mock_settings.jwt_algorithm = "HS256"

        access_token = AuthService.create_access_token(user_id=1, role="user")
        # Essayer de vérifier comme refresh token
        payload = AuthService.verify_token(access_token, token_type="refresh")

        assert payload is None

    @patch('services.auth_service.settings')
    def test_verify_invalid_token(self, mock_settings):
        """Test vérification d'un token invalide."""
        mock_settings.jwt_secret_key = "test_secret"
        mock_settings.jwt_algorithm = "HS256"

        payload = AuthService.verify_token("invalid.token.here")

        assert payload is None

    @patch('services.auth_service.settings')
    def test_verify_expired_token(self, mock_settings):
        """Test vérification d'un token expiré."""
        mock_settings.jwt_secret_key = "test_secret"
        mock_settings.jwt_algorithm = "HS256"

        # Créer un token expiré manuellement
        expired_payload = {
            "user_id": 1,
            "role": "user",
            "type": "access",
            "exp": utc_now() - timedelta(hours=1),
            "iat": utc_now() - timedelta(hours=2),
        }
        expired_token = jwt.encode(expired_payload, "test_secret", algorithm="HS256")

        payload = AuthService.verify_token(expired_token)

        assert payload is None


class TestAuthenticateUser:
    """Tests pour la méthode authenticate_user."""

    def test_authenticate_valid_user(self):
        """Test authentification utilisateur valide."""
        mock_db = Mock()
        mock_user = Mock()
        mock_user.id = 1
        mock_user.email = "test@example.com"
        mock_user.is_active = True
        mock_user.hashed_password = AuthService.hash_password("password123")
        mock_user.locked_until = None
        mock_user.failed_login_attempts = 0

        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        result = AuthService.authenticate_user(mock_db, "test@example.com", "password123")

        assert result is not None
        assert result.id == 1

    def test_authenticate_user_not_found(self):
        """Test authentification utilisateur non trouvé."""
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = AuthService.authenticate_user(mock_db, "unknown@example.com", "password")

        assert result is None

    def test_authenticate_inactive_user(self):
        """Test authentification utilisateur inactif."""
        mock_db = Mock()
        mock_user = Mock()
        mock_user.is_active = False
        mock_user.locked_until = None
        mock_user.failed_login_attempts = 0

        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        result = AuthService.authenticate_user(mock_db, "inactive@example.com", "password")

        assert result is None

    def test_authenticate_wrong_password(self):
        """Test authentification avec mauvais mot de passe."""
        mock_db = Mock()
        mock_user = Mock()
        mock_user.id = 2
        mock_user.email = "test@example.com"
        mock_user.is_active = True
        mock_user.hashed_password = AuthService.hash_password("correctpassword")
        mock_user.locked_until = None
        mock_user.failed_login_attempts = 0

        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        result = AuthService.authenticate_user(mock_db, "test@example.com", "wrongpassword")

        assert result is None

    def test_authenticate_updates_last_login(self):
        """Test que last_login est mis à jour."""
        mock_db = Mock()
        mock_user = Mock()
        mock_user.id = 1
        mock_user.email = "test@example.com"
        mock_user.is_active = True
        mock_user.hashed_password = AuthService.hash_password("password")
        mock_user.last_login = None
        mock_user.locked_until = None
        mock_user.failed_login_attempts = 0

        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        AuthService.authenticate_user(mock_db, "test@example.com", "password")

        assert mock_user.last_login is not None
        mock_db.commit.assert_called_once()


class TestGetUserFromToken:
    """Tests pour la méthode get_user_from_token."""

    @patch('services.auth_service.settings')
    def test_get_user_valid_token(self, mock_settings):
        """Test récupération utilisateur avec token valide."""
        mock_settings.jwt_secret_key = "test_secret"
        mock_settings.jwt_algorithm = "HS256"

        mock_db = Mock()
        mock_user = Mock()
        mock_user.id = 1
        mock_user.is_active = True

        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        token = AuthService.create_access_token(user_id=1, role="user")
        result = AuthService.get_user_from_token(mock_db, token)

        assert result is not None
        assert result.id == 1

    @patch('services.auth_service.settings')
    def test_get_user_invalid_token(self, mock_settings):
        """Test récupération utilisateur avec token invalide."""
        mock_settings.jwt_secret_key = "test_secret"
        mock_settings.jwt_algorithm = "HS256"

        mock_db = Mock()

        result = AuthService.get_user_from_token(mock_db, "invalid.token")

        assert result is None

    @patch('services.auth_service.settings')
    def test_get_user_inactive_user(self, mock_settings):
        """Test récupération utilisateur inactif."""
        mock_settings.jwt_secret_key = "test_secret"
        mock_settings.jwt_algorithm = "HS256"

        mock_db = Mock()
        mock_user = Mock()
        mock_user.id = 1
        mock_user.is_active = False

        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        token = AuthService.create_access_token(user_id=1, role="user")
        result = AuthService.get_user_from_token(mock_db, token)

        assert result is None


class TestRefreshAccessToken:
    """Tests pour la méthode refresh_access_token."""

    @patch('services.auth_service.settings')
    def test_refresh_valid_token(self, mock_settings):
        """Test refresh avec token valide."""
        mock_settings.jwt_secret_key = "test_secret"
        mock_settings.jwt_algorithm = "HS256"

        mock_db = Mock()
        mock_user = Mock()
        mock_user.id = 1
        mock_user.is_active = True
        mock_user.role = Mock()
        mock_user.role.value = "user"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        refresh_token = AuthService.create_refresh_token(user_id=1)
        result = AuthService.refresh_access_token(mock_db, refresh_token)

        assert result is not None
        assert "access_token" in result
        assert result["token_type"] == "bearer"

    @patch('services.auth_service.settings')
    def test_refresh_invalid_token(self, mock_settings):
        """Test refresh avec token invalide."""
        mock_settings.jwt_secret_key = "test_secret"
        mock_settings.jwt_algorithm = "HS256"

        mock_db = Mock()

        result = AuthService.refresh_access_token(mock_db, "invalid.token")

        assert result is None

    @patch('services.auth_service.settings')
    def test_refresh_inactive_user(self, mock_settings):
        """Test refresh avec utilisateur inactif."""
        mock_settings.jwt_secret_key = "test_secret"
        mock_settings.jwt_algorithm = "HS256"

        mock_db = Mock()
        mock_user = Mock()
        mock_user.id = 1
        mock_user.is_active = False

        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        refresh_token = AuthService.create_refresh_token(user_id=1)
        result = AuthService.refresh_access_token(mock_db, refresh_token)

        assert result is None

    @patch('services.auth_service.settings')
    def test_refresh_with_access_token_fails(self, mock_settings):
        """Test refresh avec un access token (doit échouer)."""
        mock_settings.jwt_secret_key = "test_secret"
        mock_settings.jwt_algorithm = "HS256"

        mock_db = Mock()

        access_token = AuthService.create_access_token(user_id=1, role="user")
        result = AuthService.refresh_access_token(mock_db, access_token)

        assert result is None


# NOTE (2025-12-12): TestGetSubscriptionLimits SUPPRIMÉE
# La méthode AuthService.get_subscription_limits() a été supprimée car elle contenait
# des valeurs hardcodées en conflit avec la table subscription_quotas.
#
# Les limites d'abonnement sont maintenant gérées par:
# - Table: public.subscription_quotas
# - Model: models/public/subscription_quota.py
# - Helpers: shared/subscription_limits.py
#
# Pour tester les limites, créer des tests d'intégration qui utilisent la DB.
