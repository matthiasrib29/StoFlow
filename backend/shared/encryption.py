"""
Encryption Service for Sensitive Data

Provides encryption/decryption for sensitive data like OAuth tokens.
Uses Fernet symmetric encryption (AES-128-CBC with HMAC).

Security (2025-12-23):
- Tokens OAuth2 (eBay, Etsy) should be encrypted at rest
- Encryption key must be stored securely (env var, not in code)
- Key rotation support via decrypt_with_fallback()

Author: Claude
Date: 2025-12-23
"""

import base64
import hashlib
import logging
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)


class EncryptionService:
    """
    Service for encrypting/decrypting sensitive data.

    Uses Fernet symmetric encryption which provides:
    - AES-128-CBC encryption
    - HMAC-SHA256 authentication
    - Timestamp-based token validation

    Usage:
        # Initialize with key from settings
        encryption = EncryptionService(settings.encryption_key)

        # Encrypt sensitive data
        encrypted = encryption.encrypt("my-secret-token")

        # Decrypt data
        decrypted = encryption.decrypt(encrypted)
    """

    def __init__(self, key: Optional[str] = None, previous_key: Optional[str] = None):
        """
        Initialize encryption service.

        Args:
            key: Encryption key (32 bytes base64-encoded or any string that will be hashed)
            previous_key: Previous key for rotation support
        """
        self._cipher: Optional[Fernet] = None
        self._previous_cipher: Optional[Fernet] = None

        if key:
            self._cipher = self._create_cipher(key)
            logger.debug("Encryption service initialized with primary key")

        if previous_key:
            self._previous_cipher = self._create_cipher(previous_key)
            logger.debug("Encryption service initialized with fallback key")

    def _create_cipher(self, key: str) -> Fernet:
        """
        Create a Fernet cipher from a key string.

        If the key is not a valid Fernet key (44 chars base64),
        we derive one using SHA-256 hash.

        Args:
            key: Any string to use as encryption key

        Returns:
            Fernet cipher instance
        """
        # Try to use key directly if it's a valid Fernet key
        try:
            if len(key) == 44 and key.endswith("="):
                return Fernet(key.encode())
        except Exception:
            pass

        # Derive a Fernet-compatible key from the input
        # Fernet requires exactly 32 bytes, base64-encoded (44 chars)
        derived_key = hashlib.sha256(key.encode()).digest()
        fernet_key = base64.urlsafe_b64encode(derived_key)
        return Fernet(fernet_key)

    @property
    def is_configured(self) -> bool:
        """Check if encryption is properly configured."""
        return self._cipher is not None

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a string.

        Args:
            plaintext: String to encrypt

        Returns:
            Base64-encoded encrypted string

        Raises:
            ValueError: If encryption is not configured or plaintext is empty
        """
        if not self._cipher:
            raise ValueError(
                "Encryption not configured. Set ENCRYPTION_KEY in environment."
            )

        if not plaintext:
            return ""

        try:
            encrypted = self._cipher.encrypt(plaintext.encode())
            return encrypted.decode()
        except Exception as e:
            logger.error(f"Encryption failed: {type(e).__name__}")
            raise ValueError("Encryption failed") from e

    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt a string.

        Args:
            ciphertext: Base64-encoded encrypted string

        Returns:
            Decrypted string

        Raises:
            ValueError: If decryption fails or encryption is not configured
        """
        if not self._cipher:
            raise ValueError(
                "Encryption not configured. Set ENCRYPTION_KEY in environment."
            )

        if not ciphertext:
            return ""

        try:
            decrypted = self._cipher.decrypt(ciphertext.encode())
            return decrypted.decode()
        except InvalidToken:
            # Try with previous key if available (key rotation support)
            if self._previous_cipher:
                try:
                    decrypted = self._previous_cipher.decrypt(ciphertext.encode())
                    logger.info("Decrypted with previous key (rotation in progress)")
                    return decrypted.decode()
                except InvalidToken:
                    pass
            logger.warning("Decryption failed: invalid token")
            raise ValueError("Decryption failed: invalid or corrupted data")
        except Exception as e:
            logger.error(f"Decryption failed: {type(e).__name__}")
            raise ValueError("Decryption failed") from e

    def encrypt_if_configured(self, plaintext: str) -> str:
        """
        Encrypt if encryption is configured, otherwise return plaintext.

        This is useful during migration when some data may not be encrypted yet.

        Args:
            plaintext: String to encrypt

        Returns:
            Encrypted string if configured, otherwise plaintext
        """
        if not self.is_configured:
            logger.warning("Encryption not configured, storing plaintext")
            return plaintext
        return self.encrypt(plaintext)

    def decrypt_if_encrypted(self, data: str) -> str:
        """
        Decrypt if data appears to be encrypted, otherwise return as-is.

        Fernet tokens start with 'gAAAAA' (base64-encoded version + timestamp).

        Args:
            data: String that may or may not be encrypted

        Returns:
            Decrypted string if encrypted, otherwise original string
        """
        if not data:
            return ""

        if not self.is_configured:
            return data

        # Fernet tokens are base64 and start with specific pattern
        if data.startswith("gAAAAA"):
            try:
                return self.decrypt(data)
            except ValueError:
                # Not actually encrypted or corrupted
                logger.warning("Data looks encrypted but decryption failed")
                return data

        return data


# Singleton instance - initialized lazily
_encryption_service: Optional[EncryptionService] = None


def get_encryption_service() -> EncryptionService:
    """
    Get the encryption service singleton.

    Lazily initializes with settings.encryption_key if available.

    Returns:
        EncryptionService instance
    """
    global _encryption_service

    if _encryption_service is None:
        from shared.config import settings

        key = getattr(settings, "encryption_key", None)
        previous_key = getattr(settings, "encryption_key_previous", None)

        _encryption_service = EncryptionService(key, previous_key)

        if not _encryption_service.is_configured:
            logger.warning(
                "Encryption service not configured. "
                "Set ENCRYPTION_KEY in .env for encrypted storage of sensitive data."
            )

    return _encryption_service


def encrypt_token(token: str) -> str:
    """
    Convenience function to encrypt a token.

    Args:
        token: Token to encrypt

    Returns:
        Encrypted token or original if encryption not configured
    """
    return get_encryption_service().encrypt_if_configured(token)


def decrypt_token(token: str) -> str:
    """
    Convenience function to decrypt a token.

    Args:
        token: Token to decrypt

    Returns:
        Decrypted token
    """
    return get_encryption_service().decrypt_if_encrypted(token)


def generate_encryption_key() -> str:
    """
    Generate a new Fernet encryption key.

    Use this to generate a key for ENCRYPTION_KEY env var.

    Returns:
        Base64-encoded 32-byte key (44 characters)

    Example:
        python -c "from shared.encryption import generate_encryption_key; print(generate_encryption_key())"
    """
    return Fernet.generate_key().decode()
