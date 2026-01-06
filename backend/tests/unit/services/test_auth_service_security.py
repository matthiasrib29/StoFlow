"""
Tests unitaires pour les fonctionnalités de sécurité de AuthService.

Couverture:
- Account Lockout (verrouillage après échecs de login)
- Email Verification (vérification email)
- JWT Secret Rotation (rotation de secrets)

Author: Claude
Date: 2025-12-18
Updated: 2026-01-06 (migrated to UserRepository mocks)
"""

import pytest
from datetime import timedelta
from unittest.mock import Mock, patch, MagicMock
from jose import jwt

from services.auth_service import AuthService
from shared.datetime_utils import utc_now


# ============================================================================
# ACCOUNT LOCKOUT TESTS
# ============================================================================

class TestAccountLockout:
    """Tests du système de verrouillage après échecs de login."""

    @patch('services.auth_service.UserRepository')
    def test_failed_login_increments_counter(self, mock_repo):
        """Test que failed_login_attempts est incrémenté à chaque échec."""
        mock_db = Mock()
        mock_user = Mock()
        mock_user.id = 1
        mock_user.email = "test@example.com"
        mock_user.is_active = True
        mock_user.hashed_password = AuthService.hash_password("correct_password")
        mock_user.locked_until = None
        mock_user.failed_login_attempts = 0

        mock_repo.get_by_email.return_value = mock_user

        # Tentative avec mauvais mot de passe
        result = AuthService.authenticate_user(mock_db, "test@example.com", "wrong_password")

        assert result is None
        mock_repo.increment_failed_login.assert_called_once_with(mock_db, mock_user)
        mock_db.commit.assert_called()

    @patch('services.auth_service.UserRepository')
    def test_multiple_failed_attempts_increment_counter(self, mock_repo):
        """Test que le compteur s'incrémente à chaque tentative."""
        mock_db = Mock()
        mock_user = Mock()
        mock_user.id = 1
        mock_user.email = "test@example.com"
        mock_user.is_active = True
        mock_user.hashed_password = AuthService.hash_password("correct_password")
        mock_user.locked_until = None
        mock_user.failed_login_attempts = 3  # Déjà 3 échecs

        mock_repo.get_by_email.return_value = mock_user

        result = AuthService.authenticate_user(mock_db, "test@example.com", "wrong")

        assert result is None
        mock_repo.increment_failed_login.assert_called_once()

    @patch('services.auth_service.UserRepository')
    def test_account_locked_after_5_failed_attempts(self, mock_repo):
        """Test que le compte est verrouillé après 5 échecs."""
        mock_db = Mock()
        mock_user = Mock()
        mock_user.id = 1
        mock_user.email = "test@example.com"
        mock_user.is_active = True
        mock_user.hashed_password = AuthService.hash_password("correct_password")
        mock_user.locked_until = None
        mock_user.failed_login_attempts = 4  # 4 échecs, le 5ème va verrouiller

        mock_repo.get_by_email.return_value = mock_user

        # Simulate increment_failed_login setting attempts to 5
        def increment_side_effect(db, user):
            user.failed_login_attempts = 5
        mock_repo.increment_failed_login.side_effect = increment_side_effect

        result = AuthService.authenticate_user(mock_db, "test@example.com", "wrong")

        assert result is None
        mock_repo.increment_failed_login.assert_called_once()
        mock_repo.lock_account.assert_called_once()

    @patch('services.auth_service.UserRepository')
    def test_locked_account_rejects_login(self, mock_repo):
        """Test qu'un compte verrouillé ne peut pas se connecter."""
        mock_db = Mock()
        mock_user = Mock()
        mock_user.id = 1
        mock_user.email = "test@example.com"
        mock_user.is_active = True
        mock_user.hashed_password = AuthService.hash_password("correct_password")
        mock_user.locked_until = utc_now() + timedelta(minutes=15)  # Verrouillé
        mock_user.failed_login_attempts = 5

        mock_repo.get_by_email.return_value = mock_user

        # Même avec le bon mot de passe, le login doit échouer
        result = AuthService.authenticate_user(mock_db, "test@example.com", "correct_password")

        assert result is None

    @patch('services.auth_service.UserRepository')
    def test_account_unlocks_after_lockout_duration(self, mock_repo):
        """Test qu'un compte se déverrouille après la durée de blocage."""
        mock_db = Mock()
        mock_user = Mock()
        mock_user.id = 1
        mock_user.email = "test@example.com"
        mock_user.is_active = True
        mock_user.hashed_password = AuthService.hash_password("correct_password")
        mock_user.locked_until = utc_now() - timedelta(minutes=1)  # Expiré
        mock_user.failed_login_attempts = 5
        mock_user.schema_name = "user_1"

        mock_repo.get_by_email.return_value = mock_user

        # Login doit réussir car le verrouillage est expiré
        result = AuthService.authenticate_user(mock_db, "test@example.com", "correct_password")

        assert result is not None
        assert result.id == 1

    @patch('services.auth_service.UserRepository')
    def test_successful_login_resets_failed_attempts(self, mock_repo):
        """Test qu'un login réussi reset le compteur d'échecs."""
        mock_db = Mock()
        mock_user = Mock()
        mock_user.id = 1
        mock_user.email = "test@example.com"
        mock_user.is_active = True
        mock_user.hashed_password = AuthService.hash_password("correct_password")
        mock_user.locked_until = None
        mock_user.failed_login_attempts = 3  # Avait 3 échecs
        mock_user.last_failed_login = utc_now() - timedelta(hours=1)
        mock_user.schema_name = "user_1"

        mock_repo.get_by_email.return_value = mock_user

        result = AuthService.authenticate_user(mock_db, "test@example.com", "correct_password")

        assert result is not None
        mock_repo.reset_login_failures.assert_called_once_with(mock_db, mock_user)
        mock_repo.update_login_stats.assert_called_once()

    def test_lockout_constants_correct_values(self):
        """Test que les constantes de lockout ont les bonnes valeurs."""
        assert AuthService.MAX_FAILED_ATTEMPTS == 5
        assert AuthService.LOCKOUT_DURATION_MINUTES == 30


# ============================================================================
# EMAIL VERIFICATION TESTS
# ============================================================================

class TestEmailVerification:
    """Tests du système de vérification email."""

    def test_generate_email_verification_token_returns_string(self):
        """Test que generate_email_verification_token retourne une string."""
        mock_db = Mock()
        mock_user = Mock()
        mock_user.id = 1

        token = AuthService.generate_email_verification_token(mock_user, mock_db)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_generate_email_verification_token_is_url_safe(self):
        """Test que le token est URL-safe (base64)."""
        mock_db = Mock()
        mock_user = Mock()
        mock_user.id = 1

        token = AuthService.generate_email_verification_token(mock_user, mock_db)

        # URL-safe base64 ne contient que ces caractères
        import re
        assert re.match(r'^[A-Za-z0-9_-]+$', token)

    def test_generate_email_verification_token_stores_hash(self):
        """Test que le hash du token est sauvegardé (pas le token original)."""
        mock_db = Mock()
        mock_user = Mock()
        mock_user.id = 1

        token = AuthService.generate_email_verification_token(mock_user, mock_db)

        # Le token stocké est un hash SHA-256 (64 caractères hex)
        assert mock_user.email_verification_token != token
        assert len(mock_user.email_verification_token) == 64  # SHA-256 hex
        assert mock_user.email_verification_expires is not None
        mock_db.commit.assert_called_once()

    def test_verification_token_expires_after_24_hours(self):
        """Test que le token expire après 24 heures."""
        mock_db = Mock()
        mock_user = Mock()
        mock_user.id = 1

        AuthService.generate_email_verification_token(mock_user, mock_db)

        # Vérifier que l'expiration est dans environ 24 heures
        expires = mock_user.email_verification_expires
        diff = (expires - utc_now()).total_seconds() / 3600
        assert 23.9 <= diff <= 24.1

    def test_verify_email_token_with_valid_token(self):
        """Test vérification avec token valide."""
        mock_db = Mock()
        mock_user = Mock()
        mock_user.id = 1
        mock_user.email = "test@example.com"
        mock_user.email_verification_expires = utc_now() + timedelta(hours=12)
        mock_user.email_verified = False

        # Generate a token and capture the hash
        raw_token = "test_token_12345"
        token_hash = AuthService._hash_token(raw_token)
        mock_user.email_verification_token = token_hash

        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        result = AuthService.verify_email_token(mock_db, raw_token)

        assert result is not None
        assert result.id == 1
        assert mock_user.email_verified is True
        assert mock_user.email_verification_token is None
        assert mock_user.email_verification_expires is None
        mock_db.commit.assert_called()

    def test_verify_email_token_with_expired_token(self):
        """Test vérification avec token expiré."""
        mock_db = Mock()
        mock_user = Mock()
        mock_user.id = 1
        mock_user.email_verification_expires = utc_now() - timedelta(hours=1)  # Expiré
        mock_user.email_verified = False

        raw_token = "expired_token"
        token_hash = AuthService._hash_token(raw_token)
        mock_user.email_verification_token = token_hash

        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        result = AuthService.verify_email_token(mock_db, raw_token)

        assert result is None
        # L'utilisateur ne doit pas être marqué comme vérifié
        assert mock_user.email_verified is False

    def test_verify_email_token_with_invalid_token(self):
        """Test vérification avec token invalide."""
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = AuthService.verify_email_token(mock_db, "nonexistent_token")

        assert result is None

    def test_verify_email_token_clears_token_after_use(self):
        """Test que le token est supprimé après utilisation."""
        mock_db = Mock()
        mock_user = Mock()
        mock_user.id = 1
        mock_user.email = "test@example.com"
        mock_user.email_verification_expires = utc_now() + timedelta(hours=12)
        mock_user.email_verified = False

        raw_token = "single_use_token"
        token_hash = AuthService._hash_token(raw_token)
        mock_user.email_verification_token = token_hash

        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        AuthService.verify_email_token(mock_db, raw_token)

        assert mock_user.email_verification_token is None
        assert mock_user.email_verification_expires is None

    def test_is_email_verified_true(self):
        """Test is_email_verified retourne True si vérifié."""
        mock_user = Mock()
        mock_user.email_verified = True

        assert AuthService.is_email_verified(mock_user) is True

    def test_is_email_verified_false(self):
        """Test is_email_verified retourne False si non vérifié."""
        mock_user = Mock()
        mock_user.email_verified = False

        assert AuthService.is_email_verified(mock_user) is False

    def test_is_email_verified_none(self):
        """Test is_email_verified avec valeur None (cas edge)."""
        mock_user = Mock()
        mock_user.email_verified = None

        assert AuthService.is_email_verified(mock_user) is False

    def test_already_verified_email_rejected(self):
        """Test qu'un email déjà vérifié ne peut pas être revérifié."""
        mock_db = Mock()
        mock_user = Mock()
        mock_user.id = 1
        mock_user.email_verified = True  # Déjà vérifié

        raw_token = "reuse_token"
        token_hash = AuthService._hash_token(raw_token)
        mock_user.email_verification_token = token_hash
        mock_user.email_verification_expires = utc_now() + timedelta(hours=12)

        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        result = AuthService.verify_email_token(mock_db, raw_token)

        assert result is None


# ============================================================================
# JWT SECRET ROTATION TESTS
# ============================================================================

class TestJWTSecretRotation:
    """Tests de la rotation de secrets JWT (grace period)."""

    @patch('services.auth_service.settings')
    def test_verify_token_accepts_current_secret(self, mock_settings):
        """Test que verify_token accepte le secret actuel."""
        mock_settings.jwt_secret_key = "current_secret"
        mock_settings.jwt_secret_key_previous = None
        mock_settings.jwt_algorithm = "HS256"
        mock_settings.jwt_access_token_expire_minutes = 60

        token = AuthService.create_access_token(user_id=1, role="user")
        payload = AuthService.verify_token(token, token_type="access")

        assert payload is not None
        assert payload["user_id"] == 1

    @patch('services.auth_service.settings')
    def test_verify_token_accepts_previous_secret_during_rotation(self, mock_settings):
        """Test que verify_token accepte l'ancien secret pendant la rotation."""
        # Créer un token avec l'ancien secret
        old_secret = "old_secret_key"
        old_payload = {
            "user_id": 1,
            "role": "user",
            "type": "access",
            "exp": utc_now() + timedelta(hours=1),
            "iat": utc_now(),
        }
        old_token = jwt.encode(old_payload, old_secret, algorithm="HS256")

        # Configurer la rotation (nouveau secret actuel, ancien en backup)
        mock_settings.jwt_secret_key = "new_secret_key"
        mock_settings.jwt_secret_key_previous = old_secret
        mock_settings.jwt_algorithm = "HS256"

        # Vérifier que l'ancien token est toujours valide
        payload = AuthService.verify_token(old_token, token_type="access")

        assert payload is not None
        assert payload["user_id"] == 1

    @patch('services.auth_service.settings')
    def test_verify_token_tries_current_secret_first(self, mock_settings):
        """Test que verify_token essaie d'abord le secret actuel."""
        current_secret = "current_secret"
        old_secret = "old_secret"

        mock_settings.jwt_secret_key = current_secret
        mock_settings.jwt_secret_key_previous = old_secret
        mock_settings.jwt_algorithm = "HS256"
        mock_settings.jwt_access_token_expire_minutes = 60

        # Créer un token avec le secret actuel
        token = AuthService.create_access_token(user_id=1, role="user")

        # Vérifier - doit réussir avec le premier secret (actuel)
        payload = AuthService.verify_token(token, token_type="access")

        assert payload is not None
        assert payload["user_id"] == 1

    @patch('services.auth_service.settings')
    def test_verify_token_rejects_when_both_secrets_fail(self, mock_settings):
        """Test que verify_token rejette si les deux secrets échouent."""
        mock_settings.jwt_secret_key = "current_secret"
        mock_settings.jwt_secret_key_previous = "old_secret"
        mock_settings.jwt_algorithm = "HS256"

        # Créer un token avec un secret totalement différent
        wrong_secret = "completely_wrong_secret"
        wrong_payload = {
            "user_id": 1,
            "role": "user",
            "type": "access",
            "exp": utc_now() + timedelta(hours=1),
            "iat": utc_now(),
        }
        wrong_token = jwt.encode(wrong_payload, wrong_secret, algorithm="HS256")

        # Vérifier - doit échouer car ni actuel ni ancien ne marchent
        payload = AuthService.verify_token(wrong_token, token_type="access")

        assert payload is None

    @patch('services.auth_service.settings')
    def test_new_tokens_use_current_secret(self, mock_settings):
        """Test que les nouveaux tokens utilisent le secret actuel."""
        current_secret = "current_secret"
        old_secret = "old_secret"

        mock_settings.jwt_secret_key = current_secret
        mock_settings.jwt_secret_key_previous = old_secret
        mock_settings.jwt_algorithm = "HS256"
        mock_settings.jwt_access_token_expire_minutes = 60

        # Créer un nouveau token
        token = AuthService.create_access_token(user_id=1, role="user")

        # Vérifier qu'il est signé avec le secret actuel
        payload = jwt.decode(token, current_secret, algorithms=["HS256"])
        assert payload["user_id"] == 1

        # Vérifier qu'il n'est PAS valide avec l'ancien secret seul
        with pytest.raises(jwt.JWTError):
            jwt.decode(token, old_secret, algorithms=["HS256"])

    @patch('services.auth_service.settings')
    def test_rotation_with_no_previous_secret(self, mock_settings):
        """Test verify_token sans ancien secret configuré."""
        mock_settings.jwt_secret_key = "only_secret"
        mock_settings.jwt_secret_key_previous = None
        mock_settings.jwt_algorithm = "HS256"
        mock_settings.jwt_access_token_expire_minutes = 60

        token = AuthService.create_access_token(user_id=1, role="user")
        payload = AuthService.verify_token(token, token_type="access")

        assert payload is not None
        assert payload["user_id"] == 1

    @patch('services.auth_service.settings')
    def test_rotation_with_empty_previous_secret(self, mock_settings):
        """Test verify_token avec ancien secret vide."""
        mock_settings.jwt_secret_key = "current_secret"
        mock_settings.jwt_secret_key_previous = ""  # String vide = pas de rotation
        mock_settings.jwt_algorithm = "HS256"
        mock_settings.jwt_access_token_expire_minutes = 60

        token = AuthService.create_access_token(user_id=1, role="user")
        payload = AuthService.verify_token(token, token_type="access")

        assert payload is not None


# ============================================================================
# JWT TOKEN TYPE VALIDATION TESTS
# ============================================================================

class TestJWTTokenTypeValidation:
    """Tests de validation du type de token JWT."""

    @patch('services.auth_service.settings')
    def test_access_token_rejected_as_refresh(self, mock_settings):
        """Test qu'un access token est rejeté si utilisé comme refresh."""
        mock_settings.jwt_secret_key = "test_secret"
        mock_settings.jwt_secret_key_previous = None
        mock_settings.jwt_algorithm = "HS256"
        mock_settings.jwt_access_token_expire_minutes = 60

        access_token = AuthService.create_access_token(user_id=1, role="user")
        payload = AuthService.verify_token(access_token, token_type="refresh")

        assert payload is None

    @patch('services.auth_service.settings')
    def test_refresh_token_rejected_as_access(self, mock_settings):
        """Test qu'un refresh token est rejeté si utilisé comme access."""
        mock_settings.jwt_secret_key = "test_secret"
        mock_settings.jwt_secret_key_previous = None
        mock_settings.jwt_algorithm = "HS256"
        mock_settings.jwt_refresh_token_expire_days = 7

        refresh_token = AuthService.create_refresh_token(user_id=1)
        payload = AuthService.verify_token(refresh_token, token_type="access")

        assert payload is None

    @patch('services.auth_service.settings')
    def test_token_without_type_rejected(self, mock_settings):
        """Test qu'un token sans champ 'type' est rejeté."""
        mock_settings.jwt_secret_key = "test_secret"
        mock_settings.jwt_secret_key_previous = None
        mock_settings.jwt_algorithm = "HS256"

        # Créer un token sans le champ 'type'
        payload_without_type = {
            "user_id": 1,
            "role": "user",
            "exp": utc_now() + timedelta(hours=1),
            "iat": utc_now(),
        }
        token = jwt.encode(payload_without_type, "test_secret", algorithm="HS256")

        result = AuthService.verify_token(token, token_type="access")

        assert result is None
