import os
"""
User Model - Schema Public (Simplified - No Tenant)

Ce modèle représente un utilisateur de la plateforme.
Les mots de passe sont hashés avec bcrypt.

Business Rules (Updated: 2025-12-07):
- Email globalement unique (un email = un seul compte dans toute la plateforme)
- Mot de passe haché avec bcrypt (min 8 caractères lors de la création)
- Role: 'admin' ou 'user' (admin a tous les droits, user limité)
- is_active=False empêche la connexion
- Chaque user a son propre schema PostgreSQL (user_{id}) pour isolation maximale
- Limites d'abonnement (max_products, max_platforms) directement sur User
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, Enum as SQLEnum, Index, Integer, String, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.database import Base


class UserRole(str, Enum):
    """
    Rôles utilisateur disponibles.

    Permissions par rôle:
    - ADMIN: Accès complet (gestion utilisateurs, abonnements, configuration)
    - USER: Accès limité à ses propres données (produits, intégrations)
    - SUPPORT: Lecture seule sur tous les utilisateurs, peut réinitialiser mots de passe
    """
    ADMIN = "admin"
    USER = "user"
    SUPPORT = "support"


class SubscriptionTier(str, Enum):
    """Tiers d'abonnement disponibles."""
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class AccountType(str, Enum):
    """Types de compte disponibles."""
    INDIVIDUAL = "individual"  # Particulier
    PROFESSIONAL = "professional"  # Entreprise/Professionnel


class BusinessType(str, Enum):
    """Types d'activité business."""
    RESALE = "resale"  # Revente
    DROPSHIPPING = "dropshipping"  # Dropshipping
    ARTISAN = "artisan"  # Artisanat
    RETAIL = "retail"  # Commerce de détail
    OTHER = "other"  # Autre


class EstimatedProducts(str, Enum):
    """Nombre de produits estimé."""
    RANGE_0_50 = "0-50"
    RANGE_50_200 = "50-200"
    RANGE_200_500 = "200-500"
    RANGE_500_PLUS = "500+"


class User(Base):
    """
    Modèle User - Représente un utilisateur de la plateforme (simplifié sans tenant).

    Attributes:
        # Authentication
        id: Identifiant unique de l'utilisateur
        email: Email de l'utilisateur (globalement unique)
        hashed_password: Mot de passe haché (bcrypt)

        # Business info
        full_name: Nom complet de l'utilisateur
        role: Rôle (admin ou user)
        is_active: Statut actif/inactif (bloque la connexion si False)
        last_login: Date de dernière connexion

        # Onboarding fields (Added: 2024-12-08)
        business_name: Nom de l'entreprise ou de la boutique (nullable)
        account_type: Type de compte (individual ou professional)
        business_type: Type d'activité (resale, dropshipping, artisan, retail, other)
        estimated_products: Nombre de produits estimé (0-50, 50-200, 200-500, 500+)

        # Professional fields (conditionnels)
        siret: Numéro SIRET (France) - uniquement pour les professionnels
        vat_number: Numéro de TVA intracommunautaire - uniquement pour les professionnels

        # Contact
        phone: Numéro de téléphone (nullable)
        country: Code pays ISO 3166-1 alpha-2 (FR par défaut)
        language: Code langue ISO 639-1 (fr par défaut)

        # Subscription fields (moved from Tenant)
        subscription_tier: Tier d'abonnement (starter, standard, premium, business, enterprise)
        subscription_status: Statut de l'abonnement (active, suspended, cancelled)
        subscription_tier_id: FK vers subscription_quotas (limites et prix)
        subscription_quota: Relation vers les quotas de l'abonnement

        # Usage counters (Added: 2025-12-10)
        current_products_count: Nombre actuel de produits actifs
        current_platforms_count: Nombre actuel de plateformes connectées

        # AI Credits (merged from ai_credits table - 2026-01-22)
        ai_credits_purchased: Crédits IA achetés (cumulables, n'expirent jamais)
        ai_credits_used_this_month: Crédits IA utilisés ce mois-ci
        ai_credits_last_reset_date: Date du dernier reset mensuel

        created_at: Date de création
        updated_at: Date de dernière modification
    """

    __tablename__ = "users"
    __table_args__ = (
        # Composite index for login query optimization (email + is_active)
        Index("idx_users_email_active", "email", "is_active"),
        {"schema": "public"}
    )

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Authentication Fields
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # Business Fields
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole, name="user_role", create_type=True),
        default=UserRole.USER,
        nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Onboarding Fields (Added: 2024-12-08)
    business_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Nom de l'entreprise ou de la boutique"
    )
    account_type: Mapped[AccountType] = mapped_column(
        SQLEnum(AccountType, name="account_type", create_type=False, values_callable=lambda x: [e.value for e in x]),
        default=AccountType.INDIVIDUAL,
        nullable=False,
        comment="Type de compte: individual (particulier) ou professional (entreprise)"
    )
    business_type: Mapped[BusinessType | None] = mapped_column(
        SQLEnum(BusinessType, name="business_type", create_type=False, values_callable=lambda x: [e.value for e in x]),
        nullable=True,
        comment="Type d'activité: resale, dropshipping, artisan, retail, other"
    )
    estimated_products: Mapped[EstimatedProducts | None] = mapped_column(
        SQLEnum(EstimatedProducts, name="estimated_products", create_type=False, values_callable=lambda x: [e.value for e in x]),
        nullable=True,
        comment="Nombre de produits estimé: 0-50, 50-200, 200-500, 500+"
    )

    # Professional Fields (conditionnels si account_type = professional)
    siret: Mapped[str | None] = mapped_column(
        String(14),
        nullable=True,
        comment="Numéro SIRET (France) - uniquement pour les professionnels"
    )
    vat_number: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="Numéro de TVA intracommunautaire - uniquement pour les professionnels"
    )

    # Contact Fields
    phone: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="Numéro de téléphone"
    )
    country: Mapped[str] = mapped_column(
        String(2),
        default="FR",
        nullable=False,
        comment="Code pays ISO 3166-1 alpha-2 (FR, BE, CH, etc.)"
    )
    language: Mapped[str] = mapped_column(
        String(2),
        default="fr",
        nullable=False,
        comment="Code langue ISO 639-1 (fr, en, etc.)"
    )

    # Text Generator Preferences (Added: 2026-01-13)
    default_title_format: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Default title format: 1=Ultra Complete, 2=Technical, 3=Style & Trend"
    )
    default_description_style: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Default description style: 1=Professional, 2=Storytelling, 3=Minimalist"
    )

    # Subscription Fields (moved from Tenant model)
    subscription_tier: Mapped[SubscriptionTier] = mapped_column(
        SQLEnum(SubscriptionTier, name="subscription_tier", create_type=True),
        default=SubscriptionTier.FREE,
        nullable=False
    )
    subscription_status: Mapped[str] = mapped_column(
        String(50),
        default="active",
        nullable=False,
        comment="active, suspended, cancelled"
    )

    # Foreign key vers subscription_quotas (Added: 2025-12-09)
    subscription_tier_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("public.subscription_quotas.id"),
        nullable=False
    )

    # Relation vers SubscriptionQuota (Added: 2025-12-09)
    subscription_quota: Mapped["SubscriptionQuota"] = relationship(
        "SubscriptionQuota",
        back_populates="users"
    )

    # Usage counters (Added: 2025-12-10)
    current_products_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Nombre actuel de produits actifs de l'utilisateur"
    )
    current_platforms_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Nombre actuel de plateformes connectées"
    )

    # Stripe Integration (Added: 2025-12-10)
    stripe_customer_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
        comment="ID du customer Stripe (cus_xxx)"
    )
    stripe_subscription_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="ID de la subscription Stripe active (sub_xxx)"
    )

    # AI Credits (merged from ai_credits table - 2026-01-22)
    ai_credits_purchased: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Purchased AI credits (cumulative, never expire)"
    )
    ai_credits_used_this_month: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="AI credits used this month"
    )
    ai_credits_last_reset_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Last monthly reset date"
    )

    # Note: Vinted connection data is stored in VintedConnection table (user_{id}.vinted_connection)
    # See models/user/vinted_connection.py for the source of truth

    # Security: Failed login tracking (Added: 2025-12-18)
    failed_login_attempts: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Nombre de tentatives de connexion échouées consécutives"
    )
    last_failed_login: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Date de la dernière tentative de connexion échouée"
    )
    locked_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Date jusqu'à laquelle le compte est verrouillé"
    )

    # Email verification (Added: 2025-12-18)
    email_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Email vérifié par l'utilisateur"
    )
    email_verification_token: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        comment="Token de vérification d'email"
    )
    email_verification_expires: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Date d'expiration du token de vérification"
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

    @property
    def schema_name(self) -> str:
        """Retourne le nom du schema PostgreSQL pour cet utilisateur."""
        return f"user_{self.id}"

    def get_remaining_ai_credits(self, monthly_credits: int) -> int:
        """
        Calculate remaining AI credits for this user.

        Args:
            monthly_credits: Monthly credits from subscription

        Returns:
            int: Remaining credits available
        """
        total = monthly_credits + self.ai_credits_purchased
        return max(0, total - self.ai_credits_used_this_month)

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', role={self.role}, tier={self.subscription_tier})>"
