"""
Authentication Schemas

Schemas Pydantic pour la validation des requêtes/réponses d'authentification.
"""

import re

from pydantic import BaseModel, EmailStr, Field, field_validator


class LoginRequest(BaseModel):
    """Schema pour la requête de login."""

    email: EmailStr = Field(..., description="Email de l'utilisateur (globalement unique)")
    password: str = Field(..., min_length=8, description="Mot de passe (min 8 caractères)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "user@example.com",
                "password": "secretpassword"
            }
        }
    }


class TokenResponse(BaseModel):
    """Schema pour la réponse contenant les tokens (simplifié sans tenant)."""

    access_token: str = Field(..., description="Access token JWT (valide 1h)")
    refresh_token: str = Field(..., description="Refresh token JWT (valide 7 jours)")
    token_type: str = Field(default="bearer", description="Type de token")
    user_id: int = Field(..., description="ID de l'utilisateur")
    role: str = Field(..., description="Rôle de l'utilisateur (admin ou user)")
    subscription_tier: str = Field(..., description="Tier d'abonnement (starter, standard, premium, business, enterprise)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "user_id": 1,
                "role": "user",
                "subscription_tier": "starter"
            }
        }
    }


class RefreshRequest(BaseModel):
    """Schema pour la requête de refresh token."""

    refresh_token: str = Field(..., description="Refresh token JWT")

    model_config = {
        "json_schema_extra": {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }
    }


class RefreshResponse(BaseModel):
    """Schema pour la réponse de refresh token."""

    access_token: str = Field(..., description="Nouveau access token JWT (valide 1h)")
    token_type: str = Field(default="bearer", description="Type de token")

    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer"
            }
        }
    }


class RegisterRequest(BaseModel):
    """
    Schema pour la requête d'inscription (simplifié sans tenant).

    Business Rules (Security - Updated: 2024-12-08):
    - Password min 12 caractères
    - Requis: 1 majuscule, 1 minuscule, 1 chiffre, 1 caractère spécial
    - Onboarding: business_name, account_type, business_type, estimated_products
    - Si account_type = 'professional': siret et vat_number peuvent être fournis
    """

    # Champs obligatoires de base
    email: EmailStr = Field(..., description="Email de l'utilisateur (globalement unique)")
    password: str = Field(
        ...,
        min_length=12,
        description="Mot de passe (min 12 chars, 1 maj, 1 min, 1 chiffre, 1 spécial !@#$%^&*)"
    )
    full_name: str = Field(..., min_length=1, max_length=255, description="Nom complet de l'utilisateur")

    # Champs onboarding (Ajoutés: 2024-12-08)
    business_name: str | None = Field(None, max_length=255, description="Nom de l'entreprise ou de la boutique")
    account_type: str = Field(
        default="individual",
        description="Type de compte: 'individual' (particulier) ou 'professional' (entreprise)"
    )
    business_type: str | None = Field(
        None,
        description="Type d'activité: 'resale', 'dropshipping', 'artisan', 'retail', 'other'"
    )
    estimated_products: str | None = Field(
        None,
        description="Nombre de produits estimé: '0-50', '50-200', '200-500', '500+'"
    )

    # Champs professionnels (optionnels, requis si account_type = 'professional')
    siret: str | None = Field(None, min_length=14, max_length=14, description="Numéro SIRET (14 chiffres, France)")
    vat_number: str | None = Field(None, max_length=20, description="Numéro de TVA intracommunautaire")

    # Champs de contact
    phone: str | None = Field(None, max_length=20, description="Numéro de téléphone")
    country: str = Field(default="FR", max_length=2, description="Code pays ISO 3166-1 alpha-2 (FR, BE, CH, etc.)")
    language: str = Field(default="fr", max_length=2, description="Code langue ISO 639-1 (fr, en, etc.)")

    # ===== SECURITY VALIDATION (2025-12-05): Password Complexity =====
    @field_validator('password')
    @classmethod
    def validate_password_complexity(cls, value: str) -> str:
        """
        Valide la complexité du mot de passe.

        Business Rules (Security - 2025-12-05):
        - Min 12 caractères
        - Au moins 1 majuscule (A-Z)
        - Au moins 1 minuscule (a-z)
        - Au moins 1 chiffre (0-9)
        - Au moins 1 caractère spécial (!@#$%^&*)

        Raises:
            ValueError: Si password ne respecte pas la politique
        """
        errors = []

        if len(value) < 12:
            errors.append("Password must be at least 12 characters long")

        if not re.search(r'[A-Z]', value):
            errors.append("Password must contain at least 1 uppercase letter (A-Z)")

        if not re.search(r'[a-z]', value):
            errors.append("Password must contain at least 1 lowercase letter (a-z)")

        if not re.search(r'[0-9]', value):
            errors.append("Password must contain at least 1 digit (0-9)")

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
            errors.append("Password must contain at least 1 special character (!@#$%^&*)")

        if errors:
            raise ValueError(
                "Password does not meet complexity requirements:\n" +
                "\n".join(f"  - {err}" for err in errors)
            )

        return value

    @field_validator('account_type')
    @classmethod
    def validate_account_type(cls, value: str) -> str:
        """Valide que account_type est 'individual' ou 'professional'."""
        valid_types = ['individual', 'professional']
        if value not in valid_types:
            raise ValueError(f"account_type must be one of: {', '.join(valid_types)}")
        return value

    @field_validator('business_type')
    @classmethod
    def validate_business_type(cls, value: str | None) -> str | None:
        """Valide que business_type est dans les valeurs autorisées."""
        if value is None:
            return None
        valid_types = ['resale', 'dropshipping', 'artisan', 'retail', 'other']
        if value not in valid_types:
            raise ValueError(f"business_type must be one of: {', '.join(valid_types)}")
        return value

    @field_validator('estimated_products')
    @classmethod
    def validate_estimated_products(cls, value: str | None) -> str | None:
        """Valide que estimated_products est dans les ranges autorisés."""
        if value is None:
            return None
        valid_ranges = ['0-50', '50-200', '200-500', '500+']
        if value not in valid_ranges:
            raise ValueError(f"estimated_products must be one of: {', '.join(valid_ranges)}")
        return value

    @field_validator('siret')
    @classmethod
    def validate_siret(cls, value: str | None) -> str | None:
        """Valide le format du SIRET (14 chiffres)."""
        if value is None:
            return None
        # Enlever les espaces
        value = value.replace(' ', '')
        if not re.match(r'^\d{14}$', value):
            raise ValueError("SIRET must be exactly 14 digits")
        return value

    @field_validator('country')
    @classmethod
    def validate_country(cls, value: str) -> str:
        """Valide que le code pays est en majuscules (ISO 3166-1 alpha-2)."""
        return value.upper()

    @field_validator('language')
    @classmethod
    def validate_language(cls, value: str) -> str:
        """Valide que le code langue est en minuscules (ISO 639-1)."""
        return value.lower()

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "title": "Inscription Particulier",
                    "description": "Exemple d'inscription pour un particulier",
                    "value": {
                        "email": "john.doe@example.com",
                        "password": "SecurePass123!",
                        "full_name": "John Doe",
                        "business_name": "Ma Boutique",
                        "account_type": "individual",
                        "business_type": "resale",
                        "estimated_products": "0-50",
                        "country": "FR",
                        "language": "fr"
                    }
                },
                {
                    "title": "Inscription Professionnel",
                    "description": "Exemple d'inscription pour un professionnel",
                    "value": {
                        "email": "contact@mybusiness.fr",
                        "password": "SecurePass123!",
                        "full_name": "Jean Dupont",
                        "business_name": "Dupont SARL",
                        "account_type": "professional",
                        "business_type": "retail",
                        "estimated_products": "200-500",
                        "siret": "12345678901234",
                        "vat_number": "FR12345678901",
                        "phone": "+33612345678",
                        "country": "FR",
                        "language": "fr"
                    }
                }
            ]
        }
    }
