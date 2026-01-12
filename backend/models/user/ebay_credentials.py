"""
EbayCredentials Model - Schema user_{id}

Stocke les credentials OAuth2 et informations du compte eBay de l'utilisateur.

Business Rules:
- Un user = un compte eBay
- OAuth2 avec access_token (expire 2h) et refresh_token (expire 18 mois)
- Le backend gère le refresh automatique des tokens
- Tokens stockés de manière sécurisée dans le schema utilisateur

Author: Claude
Date: 2025-12-11
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, Float, Integer, LargeBinary, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class EbayCredentials(Base):
    """
    Modèle EbayCredentials - Credentials OAuth2 et informations du compte eBay.

    Attributes:
        # Identifiants
        id: Identifiant unique (PK)
        ebay_user_id: ID utilisateur sur eBay

        # Account Information
        username: Username eBay (ex: shop.ton.outfit)
        email: Email du compte eBay
        account_type: Type de compte (BUSINESS ou INDIVIDUAL)
        business_name: Nom de l'entreprise (si BUSINESS)
        first_name: Prénom (si INDIVIDUAL)
        last_name: Nom (si INDIVIDUAL)
        phone: Numéro de téléphone
        address: Adresse complète
        marketplace: Marketplace d'inscription (EBAY_FR, EBAY_US, etc.)

        # Seller Reputation
        feedback_score: Score de feedback
        feedback_percentage: Pourcentage de feedback positif
        seller_level: Niveau vendeur (top_rated, above_standard, standard, below_standard)
        registration_date: Date d'inscription sur eBay

        # OAuth2 Tokens
        access_token: Token d'accès OAuth2 (expire 2h)
        refresh_token: Token de rafraîchissement OAuth2 (expire 18 mois)
        access_token_expires_at: Date d'expiration du access_token
        refresh_token_expires_at: Date d'expiration du refresh_token

        # Environment
        sandbox_mode: True si utilise eBay Sandbox (dev), False si Production

        # Status
        is_connected: True si les credentials sont valides
        last_sync: Dernière synchronisation réussie

        # Timestamps
        created_at: Date de création
        updated_at: Date de dernière modification
    """

    __tablename__ = "ebay_credentials"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # eBay User ID
    ebay_user_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        comment="ID utilisateur eBay"
    )

    # Account Information (from Commerce Identity API / Trading API)
    username: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Username eBay (ex: shop.ton.outfit)"
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Email du compte eBay"
    )
    account_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Type de compte: BUSINESS ou INDIVIDUAL"
    )

    # Business Account Info
    business_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Nom de l'entreprise (si BUSINESS)"
    )

    # Individual Account Info
    first_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Prénom (si INDIVIDUAL)"
    )
    last_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Nom (si INDIVIDUAL)"
    )

    # Contact Info
    phone: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Numéro de téléphone"
    )
    address: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Adresse complète"
    )
    marketplace: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Marketplace d'inscription (EBAY_FR, EBAY_US, etc.)"
    )

    # Seller Reputation
    feedback_score: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        default=0,
        comment="Score de feedback"
    )
    feedback_percentage: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        default=0.0,
        comment="Pourcentage de feedback positif"
    )
    seller_level: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Niveau vendeur (top_rated, above_standard, standard, below_standard)"
    )
    registration_date: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Date d'inscription sur eBay"
    )

    # OAuth2 Tokens (DEPRECATED - use encrypted columns)
    access_token: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="DEPRECATED - use access_token_encrypted (2026-01-12)"
    )
    refresh_token: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="DEPRECATED - use refresh_token_encrypted (2026-01-12)"
    )

    # OAuth2 Tokens (ENCRYPTED - Security 2026-01-12)
    access_token_encrypted: Mapped[Optional[bytes]] = mapped_column(
        LargeBinary,
        nullable=True,
        comment="Encrypted OAuth2 Access Token (expire 2h)"
    )
    refresh_token_encrypted: Mapped[Optional[bytes]] = mapped_column(
        LargeBinary,
        nullable=True,
        comment="Encrypted OAuth2 Refresh Token (expire 18 mois)"
    )

    # Token Expiration
    access_token_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Date d'expiration du access_token"
    )
    refresh_token_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Date d'expiration du refresh_token"
    )

    # Environment (sandbox vs production)
    sandbox_mode: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="True si utilise eBay Sandbox"
    )

    # Status
    is_connected: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="True si les credentials sont valides"
    )
    last_sync: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Dernière synchronisation réussie"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<EbayCredentials(id={self.id}, "
            f"ebay_user_id='{self.ebay_user_id}', "
            f"is_connected={self.is_connected}, "
            f"sandbox={self.sandbox_mode})>"
        )

    # ========== TOKEN ENCRYPTION/DECRYPTION (Security 2026-01-12) ==========

    def get_access_token(self) -> Optional[str]:
        """
        Get decrypted access token.

        Migration fallback: Returns plaintext token if encrypted version not available.

        Returns:
            Decrypted access token or None
        """
        if self.access_token_encrypted:
            from shared.encryption import decrypt_token
            return decrypt_token(self.access_token_encrypted.decode() if isinstance(self.access_token_encrypted, bytes) else self.access_token_encrypted)

        # Fallback during migration
        return self.access_token

    def set_access_token(self, token: Optional[str]) -> None:
        """
        Set and encrypt access token.

        Args:
            token: Plaintext access token to encrypt
        """
        if token:
            from shared.encryption import encrypt_token
            encrypted = encrypt_token(token)
            self.access_token_encrypted = encrypted.encode() if isinstance(encrypted, str) else encrypted
            self.access_token = None  # Clear plaintext
        else:
            self.access_token_encrypted = None
            self.access_token = None

    def get_refresh_token(self) -> Optional[str]:
        """
        Get decrypted refresh token.

        Migration fallback: Returns plaintext token if encrypted version not available.

        Returns:
            Decrypted refresh token or None
        """
        if self.refresh_token_encrypted:
            from shared.encryption import decrypt_token
            return decrypt_token(self.refresh_token_encrypted.decode() if isinstance(self.refresh_token_encrypted, bytes) else self.refresh_token_encrypted)

        # Fallback during migration
        return self.refresh_token

    def set_refresh_token(self, token: Optional[str]) -> None:
        """
        Set and encrypt refresh token.

        Args:
            token: Plaintext refresh token to encrypt
        """
        if token:
            from shared.encryption import encrypt_token
            encrypted = encrypt_token(token)
            self.refresh_token_encrypted = encrypted.encode() if isinstance(encrypted, str) else encrypted
            self.refresh_token = None  # Clear plaintext
        else:
            self.refresh_token_encrypted = None
            self.refresh_token = None

    @property
    def has_valid_tokens(self) -> bool:
        """Vérifie si les tokens OAuth2 sont présents."""
        return bool(self.get_access_token() and self.get_refresh_token())

    @property
    def is_access_token_expired(self) -> bool:
        """Vérifie si l'access_token est expiré."""
        if not self.access_token_expires_at:
            return True
        return datetime.now(self.access_token_expires_at.tzinfo) > self.access_token_expires_at

    @property
    def is_refresh_token_expired(self) -> bool:
        """Vérifie si le refresh_token est expiré."""
        if not self.refresh_token_expires_at:
            return True
        return datetime.now(self.refresh_token_expires_at.tzinfo) > self.refresh_token_expires_at

    @property
    def needs_refresh(self) -> bool:
        """Vérifie si l'access_token doit être rafraîchi."""
        return self.has_valid_tokens and self.is_access_token_expired and not self.is_refresh_token_expired
