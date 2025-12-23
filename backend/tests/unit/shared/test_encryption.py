"""
Tests unitaires pour le service de chiffrement (shared/encryption.py).

Couverture:
- EncryptionService: encrypt/decrypt
- Key derivation from arbitrary strings
- Key rotation support
- Error handling
- Convenience functions (encrypt_token, decrypt_token)

Author: Claude
Date: 2025-12-23

CRITIQUE: Ces tests vérifient que les tokens OAuth2 peuvent être chiffrés/déchiffrés correctement.
"""

import pytest
from unittest.mock import patch, MagicMock

from cryptography.fernet import Fernet


class TestEncryptionService:
    """Tests pour la classe EncryptionService."""

    def test_encryption_service_init_with_valid_fernet_key(self):
        """Test initialisation avec une clé Fernet valide."""
        from shared.encryption import EncryptionService

        # Générer une clé Fernet valide
        valid_key = Fernet.generate_key().decode()

        service = EncryptionService(key=valid_key)

        assert service.is_configured is True

    def test_encryption_service_init_with_arbitrary_string(self):
        """Test initialisation avec une string arbitraire (dérivation de clé)."""
        from shared.encryption import EncryptionService

        # String quelconque - sera dérivée via SHA-256
        arbitrary_key = "my-super-secret-key-that-is-not-fernet-format"

        service = EncryptionService(key=arbitrary_key)

        assert service.is_configured is True

    def test_encryption_service_init_without_key(self):
        """Test initialisation sans clé."""
        from shared.encryption import EncryptionService

        service = EncryptionService(key=None)

        assert service.is_configured is False

    def test_encrypt_and_decrypt_roundtrip(self):
        """Test que encrypt -> decrypt retourne la valeur originale."""
        from shared.encryption import EncryptionService

        key = Fernet.generate_key().decode()
        service = EncryptionService(key=key)

        original = "my-secret-oauth-token-12345"

        encrypted = service.encrypt(original)
        decrypted = service.decrypt(encrypted)

        assert decrypted == original
        assert encrypted != original  # Le chiffré est différent de l'original

    def test_encrypt_produces_different_output_each_time(self):
        """Test que le même plaintext produit des chiffrés différents (IV aléatoire)."""
        from shared.encryption import EncryptionService

        key = Fernet.generate_key().decode()
        service = EncryptionService(key=key)

        plaintext = "same-token"

        encrypted1 = service.encrypt(plaintext)
        encrypted2 = service.encrypt(plaintext)

        # Les deux chiffrés doivent être différents (IV aléatoire)
        assert encrypted1 != encrypted2

        # Mais les deux doivent déchiffrer vers la même valeur
        assert service.decrypt(encrypted1) == plaintext
        assert service.decrypt(encrypted2) == plaintext

    def test_encrypt_empty_string(self):
        """Test encryption d'une string vide."""
        from shared.encryption import EncryptionService

        key = Fernet.generate_key().decode()
        service = EncryptionService(key=key)

        result = service.encrypt("")

        assert result == ""

    def test_decrypt_empty_string(self):
        """Test decryption d'une string vide."""
        from shared.encryption import EncryptionService

        key = Fernet.generate_key().decode()
        service = EncryptionService(key=key)

        result = service.decrypt("")

        assert result == ""

    def test_encrypt_without_key_raises_error(self):
        """Test que encrypt sans clé lève une erreur."""
        from shared.encryption import EncryptionService

        service = EncryptionService(key=None)

        with pytest.raises(ValueError) as exc_info:
            service.encrypt("some-token")

        assert "not configured" in str(exc_info.value).lower()

    def test_decrypt_without_key_raises_error(self):
        """Test que decrypt sans clé lève une erreur."""
        from shared.encryption import EncryptionService

        service = EncryptionService(key=None)

        with pytest.raises(ValueError) as exc_info:
            service.decrypt("some-encrypted-data")

        assert "not configured" in str(exc_info.value).lower()

    def test_decrypt_with_wrong_key_raises_error(self):
        """Test que decrypt avec mauvaise clé lève une erreur."""
        from shared.encryption import EncryptionService

        key1 = Fernet.generate_key().decode()
        key2 = Fernet.generate_key().decode()

        service1 = EncryptionService(key=key1)
        service2 = EncryptionService(key=key2)

        encrypted = service1.encrypt("my-secret")

        with pytest.raises(ValueError) as exc_info:
            service2.decrypt(encrypted)

        assert "failed" in str(exc_info.value).lower()

    def test_decrypt_corrupted_data_raises_error(self):
        """Test que decrypt de données corrompues lève une erreur."""
        from shared.encryption import EncryptionService

        key = Fernet.generate_key().decode()
        service = EncryptionService(key=key)

        with pytest.raises(ValueError) as exc_info:
            service.decrypt("not-a-valid-fernet-token")

        assert "failed" in str(exc_info.value).lower()


class TestKeyRotation:
    """Tests pour le support de rotation de clés."""

    def test_decrypt_with_previous_key(self):
        """Test que decrypt fonctionne avec l'ancienne clé pendant la rotation."""
        from shared.encryption import EncryptionService

        old_key = Fernet.generate_key().decode()
        new_key = Fernet.generate_key().decode()

        # Chiffrer avec l'ancienne clé
        old_service = EncryptionService(key=old_key)
        encrypted = old_service.encrypt("my-secret-token")

        # Créer un nouveau service avec rotation (new_key + old_key en fallback)
        rotated_service = EncryptionService(key=new_key, previous_key=old_key)

        # Doit pouvoir déchiffrer avec l'ancienne clé
        decrypted = rotated_service.decrypt(encrypted)

        assert decrypted == "my-secret-token"

    def test_encrypt_uses_new_key_after_rotation(self):
        """Test que encrypt utilise la nouvelle clé après rotation."""
        from shared.encryption import EncryptionService

        old_key = Fernet.generate_key().decode()
        new_key = Fernet.generate_key().decode()

        rotated_service = EncryptionService(key=new_key, previous_key=old_key)
        new_service = EncryptionService(key=new_key)

        # Chiffrer avec le service en rotation
        encrypted = rotated_service.encrypt("new-secret")

        # Le nouveau service (sans fallback) doit pouvoir déchiffrer
        decrypted = new_service.decrypt(encrypted)

        assert decrypted == "new-secret"


class TestConvenienceFunctions:
    """Tests pour les fonctions utilitaires encrypt_token/decrypt_token."""

    def test_encrypt_if_configured_with_key(self):
        """Test encrypt_if_configured avec clé configurée."""
        from shared.encryption import EncryptionService

        key = Fernet.generate_key().decode()
        service = EncryptionService(key=key)

        result = service.encrypt_if_configured("my-token")

        # Devrait être chiffré
        assert result != "my-token"
        assert result.startswith("gAAAAA")  # Fernet token prefix

    def test_encrypt_if_configured_without_key(self):
        """Test encrypt_if_configured sans clé (retourne plaintext)."""
        from shared.encryption import EncryptionService

        service = EncryptionService(key=None)

        result = service.encrypt_if_configured("my-token")

        # Devrait retourner le plaintext (pas de chiffrement)
        assert result == "my-token"

    def test_decrypt_if_encrypted_with_fernet_token(self):
        """Test decrypt_if_encrypted avec un token Fernet valide."""
        from shared.encryption import EncryptionService

        key = Fernet.generate_key().decode()
        service = EncryptionService(key=key)

        # Chiffrer d'abord
        encrypted = service.encrypt("my-secret")

        # decrypt_if_encrypted doit reconnaître et déchiffrer
        result = service.decrypt_if_encrypted(encrypted)

        assert result == "my-secret"

    def test_decrypt_if_encrypted_with_plaintext(self):
        """Test decrypt_if_encrypted avec du plaintext (non chiffré)."""
        from shared.encryption import EncryptionService

        key = Fernet.generate_key().decode()
        service = EncryptionService(key=key)

        # Passer du plaintext (ne commence pas par gAAAAA)
        plaintext = "not-encrypted-token"

        result = service.decrypt_if_encrypted(plaintext)

        # Devrait retourner le plaintext tel quel
        assert result == plaintext

    def test_decrypt_if_encrypted_with_empty_string(self):
        """Test decrypt_if_encrypted avec string vide."""
        from shared.encryption import EncryptionService

        key = Fernet.generate_key().decode()
        service = EncryptionService(key=key)

        result = service.decrypt_if_encrypted("")

        assert result == ""


class TestGenerateEncryptionKey:
    """Tests pour la génération de clés."""

    def test_generate_encryption_key_format(self):
        """Test que generate_encryption_key produit une clé Fernet valide."""
        from shared.encryption import generate_encryption_key

        key = generate_encryption_key()

        # Clé Fernet = 44 caractères base64
        assert len(key) == 44
        assert key.endswith("=")

        # Doit être utilisable pour créer un Fernet
        fernet = Fernet(key.encode())
        assert fernet is not None

    def test_generate_encryption_key_unique(self):
        """Test que chaque appel génère une clé différente."""
        from shared.encryption import generate_encryption_key

        key1 = generate_encryption_key()
        key2 = generate_encryption_key()

        assert key1 != key2


class TestSingletonService:
    """Tests pour le singleton get_encryption_service."""

    def test_encryption_service_configured_with_key(self):
        """Test EncryptionService is configured when key is provided."""
        from shared.encryption import EncryptionService

        key = Fernet.generate_key().decode()
        service = EncryptionService(key=key)

        assert service.is_configured is True

    def test_encryption_service_not_configured_without_key(self):
        """Test EncryptionService is not configured without key."""
        from shared.encryption import EncryptionService

        service = EncryptionService(key=None)

        assert service.is_configured is False

    def test_get_encryption_service_returns_singleton(self):
        """Test that get_encryption_service returns consistent instance."""
        import shared.encryption

        # Reset singleton
        shared.encryption._encryption_service = None

        # First call
        service1 = shared.encryption.get_encryption_service()
        # Second call should return same instance
        service2 = shared.encryption.get_encryption_service()

        assert service1 is service2

        # Cleanup
        shared.encryption._encryption_service = None


class TestSpecialCharacters:
    """Tests avec caractères spéciaux et unicode."""

    def test_encrypt_decrypt_unicode(self):
        """Test encryption/decryption avec caractères unicode."""
        from shared.encryption import EncryptionService

        key = Fernet.generate_key().decode()
        service = EncryptionService(key=key)

        # Token avec caractères spéciaux
        original = "token-with-émojis-🔐-and-中文"

        encrypted = service.encrypt(original)
        decrypted = service.decrypt(encrypted)

        assert decrypted == original

    def test_encrypt_decrypt_long_token(self):
        """Test encryption/decryption avec token très long."""
        from shared.encryption import EncryptionService

        key = Fernet.generate_key().decode()
        service = EncryptionService(key=key)

        # Token très long (simule un JWT)
        original = "eyJ" + "a" * 10000 + ".very.long.token"

        encrypted = service.encrypt(original)
        decrypted = service.decrypt(encrypted)

        assert decrypted == original

    def test_encrypt_decrypt_special_chars(self):
        """Test encryption/decryption avec caractères spéciaux JSON."""
        from shared.encryption import EncryptionService

        key = Fernet.generate_key().decode()
        service = EncryptionService(key=key)

        # Token avec caractères qui pourraient poser problème en JSON
        original = '{"key": "value with \\"quotes\\" and \\n newlines"}'

        encrypted = service.encrypt(original)
        decrypted = service.decrypt(encrypted)

        assert decrypted == original
