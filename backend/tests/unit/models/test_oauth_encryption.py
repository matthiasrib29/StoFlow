"""
Unit tests for OAuth token encryption in credentials models.

Tests the encryption/decryption of access_token and refresh_token.

Author: Claude
Date: 2026-01-12
"""

import pytest
from models.user.ebay_credentials import EbayCredentials
from models.user.etsy_credentials import EtsyCredentials
from shared.encryption import EncryptionService


class TestEbayCredentialsEncryption:
    """Test eBay credentials token encryption."""

    def test_set_access_token_encrypts(self):
        """Setting access_token should encrypt and clear plaintext."""
        creds = EbayCredentials()

        # Set token
        creds.set_access_token("test-access-token")

        # Should have encrypted version
        assert creds.access_token_encrypted is not None
        assert isinstance(creds.access_token_encrypted, bytes)

        # Should clear plaintext
        assert creds.access_token is None

    def test_get_access_token_decrypts(self):
        """Getting access_token should decrypt encrypted version."""
        creds = EbayCredentials()

        # Set token
        original_token = "test-access-token"
        creds.set_access_token(original_token)

        # Get token should decrypt
        decrypted = creds.get_access_token()
        assert decrypted == original_token

    def test_set_refresh_token_encrypts(self):
        """Setting refresh_token should encrypt and clear plaintext."""
        creds = EbayCredentials()

        # Set token
        creds.set_refresh_token("test-refresh-token")

        # Should have encrypted version
        assert creds.refresh_token_encrypted is not None
        assert isinstance(creds.refresh_token_encrypted, bytes)

        # Should clear plaintext
        assert creds.refresh_token is None

    def test_get_refresh_token_decrypts(self):
        """Getting refresh_token should decrypt encrypted version."""
        creds = EbayCredentials()

        # Set token
        original_token = "test-refresh-token"
        creds.set_refresh_token(original_token)

        # Get token should decrypt
        decrypted = creds.get_refresh_token()
        assert decrypted == original_token

    def test_set_token_none_clears_both(self):
        """Setting token to None should clear both encrypted and plaintext."""
        creds = EbayCredentials()

        # Set token first
        creds.set_access_token("test-token")

        # Set to None
        creds.set_access_token(None)

        # Both should be None
        assert creds.access_token_encrypted is None
        assert creds.access_token is None

    def test_get_token_fallback_to_plaintext(self):
        """During migration, should fallback to plaintext if no encrypted version."""
        creds = EbayCredentials()

        # Set plaintext directly (simulating old data)
        creds.access_token = "plaintext-token"

        # Should return plaintext as fallback
        assert creds.get_access_token() == "plaintext-token"

    def test_has_valid_tokens_uses_encrypted(self):
        """has_valid_tokens property should work with encrypted tokens."""
        creds = EbayCredentials()

        # No tokens
        assert not creds.has_valid_tokens

        # Set access_token only
        creds.set_access_token("access-token")
        assert not creds.has_valid_tokens  # Need both

        # Set refresh_token
        creds.set_refresh_token("refresh-token")
        assert creds.has_valid_tokens  # Both present


class TestEtsyCredentialsEncryption:
    """Test Etsy credentials token encryption."""

    def test_set_access_token_encrypts(self):
        """Setting access_token should encrypt and clear plaintext."""
        creds = EtsyCredentials()

        # Set token
        creds.set_access_token("test-access-token")

        # Should have encrypted version
        assert creds.access_token_encrypted is not None
        assert isinstance(creds.access_token_encrypted, bytes)

        # Should clear plaintext
        assert creds.access_token is None

    def test_get_access_token_decrypts(self):
        """Getting access_token should decrypt encrypted version."""
        creds = EtsyCredentials()

        # Set token
        original_token = "test-access-token"
        creds.set_access_token(original_token)

        # Get token should decrypt
        decrypted = creds.get_access_token()
        assert decrypted == original_token

    def test_set_refresh_token_encrypts(self):
        """Setting refresh_token should encrypt and clear plaintext."""
        creds = EtsyCredentials()

        # Set token
        creds.set_refresh_token("test-refresh-token")

        # Should have encrypted version
        assert creds.refresh_token_encrypted is not None
        assert isinstance(creds.refresh_token_encrypted, bytes)

        # Should clear plaintext
        assert creds.refresh_token is None

    def test_get_refresh_token_decrypts(self):
        """Getting refresh_token should decrypt encrypted version."""
        creds = EtsyCredentials()

        # Set token
        original_token = "test-refresh-token"
        creds.set_refresh_token(original_token)

        # Get token should decrypt
        decrypted = creds.get_refresh_token()
        assert decrypted == original_token

    def test_get_token_fallback_to_plaintext(self):
        """During migration, should fallback to plaintext if no encrypted version."""
        creds = EtsyCredentials()

        # Set plaintext directly (simulating old data)
        creds.access_token = "plaintext-token"

        # Should return plaintext as fallback
        assert creds.get_access_token() == "plaintext-token"

    def test_has_valid_tokens_uses_encrypted(self):
        """has_valid_tokens property should work with encrypted tokens."""
        creds = EtsyCredentials()

        # No tokens
        assert not creds.has_valid_tokens

        # Set access_token only
        creds.set_access_token("access-token")
        assert not creds.has_valid_tokens  # Need both

        # Set refresh_token
        creds.set_refresh_token("refresh-token")
        assert creds.has_valid_tokens  # Both present
