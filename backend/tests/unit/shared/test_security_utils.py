"""
Tests unitaires pour les utilitaires de sécurité (shared/security_utils.py).

Couverture:
- redact_email: masquage RGPD des emails
- redact_password: masquage des mots de passe
- sanitize_for_log: sanitization complète des dictionnaires

Author: Claude
Date: 2025-12-23

CRITIQUE: Ces tests vérifient la conformité RGPD des logs.
"""

import pytest
from unittest.mock import patch


# ============================================================================
# redact_email TESTS
# ============================================================================

class TestRedactEmail:
    """Tests pour la fonction redact_email."""

    @patch('shared.security_utils.settings')
    def test_redact_email_in_production(self, mock_settings):
        """Test redact_email masque correctement en production."""
        mock_settings.is_production = True

        from shared.security_utils import redact_email

        result = redact_email("john.doe@example.com")

        # Doit masquer: j***@e***.com
        assert result == "j***@e***.com"

    @patch('shared.security_utils.settings')
    def test_redact_email_in_development(self, mock_settings):
        """Test redact_email garde l'email complet en dev."""
        mock_settings.is_production = False

        from shared.security_utils import redact_email

        result = redact_email("john.doe@example.com")

        # En dev, l'email reste complet
        assert result == "john.doe@example.com"

    @patch('shared.security_utils.settings')
    def test_redact_email_none(self, mock_settings):
        """Test redact_email avec None."""
        mock_settings.is_production = True

        from shared.security_utils import redact_email

        result = redact_email(None)

        assert result == "<empty>"

    @patch('shared.security_utils.settings')
    def test_redact_email_empty_string(self, mock_settings):
        """Test redact_email avec string vide."""
        mock_settings.is_production = True

        from shared.security_utils import redact_email

        result = redact_email("")

        assert result == "<empty>"

    @patch('shared.security_utils.settings')
    def test_redact_email_invalid_no_at(self, mock_settings):
        """Test redact_email avec email invalide (pas de @)."""
        mock_settings.is_production = True

        from shared.security_utils import redact_email

        result = redact_email("not-an-email")

        assert result == "<invalid>"

    @patch('shared.security_utils.settings')
    def test_redact_email_single_char_local(self, mock_settings):
        """Test redact_email avec partie locale d'un seul caractère."""
        mock_settings.is_production = True

        from shared.security_utils import redact_email

        result = redact_email("a@example.com")

        # Partie locale = 1 char -> "***"
        assert result == "***@e***.com"

    @patch('shared.security_utils.settings')
    def test_redact_email_subdomain(self, mock_settings):
        """Test redact_email avec sous-domaine."""
        mock_settings.is_production = True

        from shared.security_utils import redact_email

        result = redact_email("user@mail.example.co.uk")

        # Doit garder le TLD final
        assert result == "u***@m***.uk"

    @patch('shared.security_utils.settings')
    def test_redact_email_various_emails(self, mock_settings):
        """Test redact_email avec différents formats d'emails."""
        mock_settings.is_production = True

        from shared.security_utils import redact_email

        test_cases = [
            ("test@gmail.com", "t***@g***.com"),
            ("john.doe@company.org", "j***@c***.org"),
            ("admin@localhost.local", "a***@l***.local"),
        ]

        for email, expected in test_cases:
            result = redact_email(email)
            assert result == expected, f"Failed for {email}: got {result}, expected {expected}"


# ============================================================================
# redact_password TESTS
# ============================================================================

class TestRedactPassword:
    """Tests pour la fonction redact_password."""

    @patch('shared.security_utils.settings')
    def test_redact_password_in_production(self, mock_settings):
        """Test redact_password masque complètement en production."""
        mock_settings.is_production = True

        from shared.security_utils import redact_password

        result = redact_password("MySecretPassword123")

        assert result == "******"

    @patch('shared.security_utils.settings')
    def test_redact_password_in_development(self, mock_settings):
        """Test redact_password montre 3 premiers chars en dev."""
        mock_settings.is_production = False

        from shared.security_utils import redact_password

        result = redact_password("MySecretPassword123")

        assert result == "MyS***"

    @patch('shared.security_utils.settings')
    def test_redact_password_none(self, mock_settings):
        """Test redact_password avec None."""
        mock_settings.is_production = True

        from shared.security_utils import redact_password

        result = redact_password(None)

        assert result == "<empty>"

    @patch('shared.security_utils.settings')
    def test_redact_password_empty_string(self, mock_settings):
        """Test redact_password avec string vide."""
        mock_settings.is_production = True

        from shared.security_utils import redact_password

        result = redact_password("")

        assert result == "<empty>"

    @patch('shared.security_utils.settings')
    def test_redact_password_short_in_dev(self, mock_settings):
        """Test redact_password avec password court en dev."""
        mock_settings.is_production = False

        from shared.security_utils import redact_password

        # Password de 3 chars ou moins
        result = redact_password("abc")

        assert result == "***"

    @patch('shared.security_utils.settings')
    def test_redact_password_short_in_prod(self, mock_settings):
        """Test redact_password avec password court en production."""
        mock_settings.is_production = True

        from shared.security_utils import redact_password

        result = redact_password("ab")

        assert result == "******"


# ============================================================================
# sanitize_for_log TESTS
# ============================================================================

class TestSanitizeForLog:
    """Tests pour la fonction sanitize_for_log."""

    @patch('shared.security_utils.settings')
    def test_sanitize_for_log_password_fields(self, mock_settings):
        """Test sanitize_for_log masque les champs password."""
        mock_settings.is_production = True

        from shared.security_utils import sanitize_for_log

        data = {
            "username": "john",
            "password": "secret123",
            "hashed_password": "bcrypt_hash_here",
        }

        result = sanitize_for_log(data)

        assert result["username"] == "john"  # Non sensible
        assert result["password"] == "******"
        assert result["hashed_password"] == "******"

    @patch('shared.security_utils.settings')
    def test_sanitize_for_log_token_fields(self, mock_settings):
        """Test sanitize_for_log masque les champs token."""
        mock_settings.is_production = True

        from shared.security_utils import sanitize_for_log

        data = {
            "user_id": 123,
            "token": "jwt-token-here",
            "access_token": "oauth-access-token",
            "refresh_token": "oauth-refresh-token",
        }

        result = sanitize_for_log(data)

        assert result["user_id"] == 123  # Non sensible
        assert result["token"] == "******"
        assert result["access_token"] == "******"
        assert result["refresh_token"] == "******"

    @patch('shared.security_utils.settings')
    def test_sanitize_for_log_api_key_fields(self, mock_settings):
        """Test sanitize_for_log masque les champs api_key."""
        mock_settings.is_production = True

        from shared.security_utils import sanitize_for_log

        data = {
            "api_key": "sk-1234567890",
            "secret_key": "my-secret-key",
            "jwt_secret_key": "jwt-secret",
        }

        result = sanitize_for_log(data)

        assert result["api_key"] == "******"
        assert result["secret_key"] == "******"
        assert result["jwt_secret_key"] == "******"

    @patch('shared.security_utils.settings')
    def test_sanitize_for_log_email_fields(self, mock_settings):
        """Test sanitize_for_log masque les champs email (RGPD)."""
        mock_settings.is_production = True

        from shared.security_utils import sanitize_for_log

        data = {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "user_email": "user@company.org",
            "owner_email": "owner@domain.fr",
        }

        result = sanitize_for_log(data)

        assert result["name"] == "John Doe"  # Non sensible
        assert result["email"] == "j***@e***.com"
        assert result["user_email"] == "u***@c***.org"
        assert result["owner_email"] == "o***@d***.fr"

    @patch('shared.security_utils.settings')
    def test_sanitize_for_log_case_insensitive(self, mock_settings):
        """Test sanitize_for_log est case-insensitive."""
        mock_settings.is_production = True

        from shared.security_utils import sanitize_for_log

        data = {
            "PASSWORD": "secret",
            "Email": "test@test.com",
            "API_KEY": "key123",
        }

        result = sanitize_for_log(data)

        assert result["PASSWORD"] == "******"
        assert result["Email"] == "t***@t***.com"
        assert result["API_KEY"] == "******"

    @patch('shared.security_utils.settings')
    def test_sanitize_for_log_preserves_original(self, mock_settings):
        """Test sanitize_for_log ne modifie pas le dictionnaire original."""
        mock_settings.is_production = True

        from shared.security_utils import sanitize_for_log

        original = {"password": "secret", "email": "test@test.com"}
        original_copy = original.copy()

        sanitize_for_log(original)

        # L'original ne doit pas être modifié
        assert original == original_copy

    @patch('shared.security_utils.settings')
    def test_sanitize_for_log_with_none_values(self, mock_settings):
        """Test sanitize_for_log avec valeurs None."""
        mock_settings.is_production = True

        from shared.security_utils import sanitize_for_log

        data = {
            "password": None,
            "email": None,
        }

        result = sanitize_for_log(data)

        assert result["password"] == "<empty>"
        assert result["email"] == "<empty>"

    @patch('shared.security_utils.settings')
    def test_sanitize_for_log_empty_dict(self, mock_settings):
        """Test sanitize_for_log avec dictionnaire vide."""
        mock_settings.is_production = True

        from shared.security_utils import sanitize_for_log

        result = sanitize_for_log({})

        assert result == {}

    @patch('shared.security_utils.settings')
    def test_sanitize_for_log_nested_not_sanitized(self, mock_settings):
        """Test sanitize_for_log ne sanitize pas les dictionnaires imbriqués."""
        mock_settings.is_production = True

        from shared.security_utils import sanitize_for_log

        data = {
            "user": {
                "email": "nested@test.com",  # Ne sera pas sanitizé
                "password": "nested-secret",  # Ne sera pas sanitizé
            },
            "email": "top@test.com",  # Sera sanitizé
        }

        result = sanitize_for_log(data)

        # Top-level est sanitizé
        assert result["email"] == "t***@t***.com"

        # Nested n'est PAS sanitizé (limitation actuelle)
        assert result["user"]["email"] == "nested@test.com"
        assert result["user"]["password"] == "nested-secret"


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestSecurityUtilsIntegration:
    """Tests d'intégration pour les utilitaires de sécurité."""

    @patch('shared.security_utils.settings')
    def test_full_sanitization_flow(self, mock_settings):
        """Test complet de sanitization d'un objet de log typique."""
        mock_settings.is_production = True

        from shared.security_utils import sanitize_for_log

        # Simule un log de création d'utilisateur
        log_data = {
            "action": "user_created",
            "user_id": 42,
            "email": "new.user@company.com",
            "password": "TempPassword123!",
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "ip_address": "192.168.1.100",
            "timestamp": "2025-12-23T10:00:00Z",
        }

        result = sanitize_for_log(log_data)

        # Données non sensibles préservées
        assert result["action"] == "user_created"
        assert result["user_id"] == 42
        assert result["ip_address"] == "192.168.1.100"
        assert result["timestamp"] == "2025-12-23T10:00:00Z"

        # Données sensibles masquées
        assert result["email"] == "n***@c***.com"
        assert result["password"] == "******"
        assert result["access_token"] == "******"

    @patch('shared.security_utils.settings')
    def test_dev_mode_shows_more_info(self, mock_settings):
        """Test que le mode dev montre plus d'informations."""
        mock_settings.is_production = False

        from shared.security_utils import sanitize_for_log

        log_data = {
            "email": "debug@test.com",
            "password": "DebugPassword123",
        }

        result = sanitize_for_log(log_data)

        # En dev, l'email est complet
        assert result["email"] == "debug@test.com"

        # Le password montre 3 premiers chars
        assert result["password"] == "Deb***"
