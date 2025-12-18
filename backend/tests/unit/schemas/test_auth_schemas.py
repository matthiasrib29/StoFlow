"""
Tests unitaires pour les schemas d'authentification.

Couverture:
- LoginRequest validation
- RegisterRequest validation (password complexity, SIRET, account_type)
- TokenResponse structure
- RefreshRequest/RefreshResponse

Author: Claude
Date: 2025-12-10
"""

import pytest
from pydantic import ValidationError

from schemas.auth_schemas import (
    LoginRequest,
    TokenResponse,
    RefreshRequest,
    RefreshResponse,
    RegisterRequest,
)


class TestLoginRequest:
    """Tests pour le schema LoginRequest."""

    def test_valid_login(self):
        """Test login valide."""
        login = LoginRequest(email="test@example.com", password="password123")

        assert login.email == "test@example.com"
        assert login.password == "password123"

    def test_invalid_email(self):
        """Test avec email invalide."""
        with pytest.raises(ValidationError) as exc_info:
            LoginRequest(email="invalid-email", password="password123")

        assert "email" in str(exc_info.value).lower()

    def test_password_too_short(self):
        """Test avec mot de passe trop court."""
        with pytest.raises(ValidationError) as exc_info:
            LoginRequest(email="test@example.com", password="short")

        assert "password" in str(exc_info.value).lower()

    def test_missing_email(self):
        """Test sans email."""
        with pytest.raises(ValidationError) as exc_info:
            LoginRequest(password="password123")

        assert "email" in str(exc_info.value).lower()

    def test_missing_password(self):
        """Test sans mot de passe."""
        with pytest.raises(ValidationError) as exc_info:
            LoginRequest(email="test@example.com")

        assert "password" in str(exc_info.value).lower()


class TestTokenResponse:
    """Tests pour le schema TokenResponse."""

    def test_valid_response(self):
        """Test réponse token valide."""
        response = TokenResponse(
            access_token="access.token.here",
            refresh_token="refresh.token.here",
            user_id=1,
            role="user",
            subscription_tier="starter"
        )

        assert response.access_token == "access.token.here"
        assert response.refresh_token == "refresh.token.here"
        assert response.token_type == "bearer"
        assert response.user_id == 1
        assert response.role == "user"
        assert response.subscription_tier == "starter"

    def test_default_token_type(self):
        """Test que token_type a une valeur par défaut."""
        response = TokenResponse(
            access_token="test",
            refresh_token="test",
            user_id=1,
            role="admin",
            subscription_tier="premium"
        )

        assert response.token_type == "bearer"


class TestRefreshRequest:
    """Tests pour le schema RefreshRequest."""

    def test_valid_request(self):
        """Test requête refresh valide."""
        request = RefreshRequest(refresh_token="some.refresh.token")

        assert request.refresh_token == "some.refresh.token"

    def test_missing_refresh_token(self):
        """Test sans refresh token."""
        with pytest.raises(ValidationError):
            RefreshRequest()


class TestRefreshResponse:
    """Tests pour le schema RefreshResponse."""

    def test_valid_response(self):
        """Test réponse refresh valide."""
        response = RefreshResponse(access_token="new.access.token")

        assert response.access_token == "new.access.token"
        assert response.token_type == "bearer"


class TestRegisterRequestPasswordComplexity:
    """Tests pour la validation de complexité du mot de passe."""

    def test_valid_password(self):
        """Test mot de passe valide (toutes les règles)."""
        register = RegisterRequest(
            email="test@example.com",
            password="SecurePass123!",
            full_name="Test User"
        )

        assert register.password == "SecurePass123!"

    def test_password_too_short(self):
        """Test mot de passe trop court (< 12 chars)."""
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(
                email="test@example.com",
                password="Short1!",  # 7 chars
                full_name="Test User"
            )

        assert "12 characters" in str(exc_info.value)

    def test_password_missing_uppercase(self):
        """Test mot de passe sans majuscule."""
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(
                email="test@example.com",
                password="securepassword123!",  # pas de majuscule
                full_name="Test User"
            )

        assert "uppercase" in str(exc_info.value)

    def test_password_missing_lowercase(self):
        """Test mot de passe sans minuscule."""
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(
                email="test@example.com",
                password="SECUREPASSWORD123!",  # pas de minuscule
                full_name="Test User"
            )

        assert "lowercase" in str(exc_info.value)

    def test_password_missing_digit(self):
        """Test mot de passe sans chiffre."""
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(
                email="test@example.com",
                password="SecurePassword!",  # pas de chiffre
                full_name="Test User"
            )

        assert "digit" in str(exc_info.value)

    def test_password_missing_special_char(self):
        """Test mot de passe sans caractère spécial."""
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(
                email="test@example.com",
                password="SecurePassword123",  # pas de spécial
                full_name="Test User"
            )

        assert "special character" in str(exc_info.value)


class TestRegisterRequestAccountType:
    """Tests pour la validation du type de compte."""

    def test_valid_individual(self):
        """Test type 'individual' valide."""
        register = RegisterRequest(
            email="test@example.com",
            password="SecurePass123!",
            full_name="Test User",
            account_type="individual"
        )

        assert register.account_type == "individual"

    def test_valid_professional(self):
        """Test type 'professional' valide."""
        register = RegisterRequest(
            email="test@example.com",
            password="SecurePass123!",
            full_name="Test User",
            account_type="professional"
        )

        assert register.account_type == "professional"

    def test_invalid_account_type(self):
        """Test type de compte invalide."""
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(
                email="test@example.com",
                password="SecurePass123!",
                full_name="Test User",
                account_type="invalid_type"
            )

        assert "account_type" in str(exc_info.value)

    def test_default_account_type(self):
        """Test que le type par défaut est 'individual'."""
        register = RegisterRequest(
            email="test@example.com",
            password="SecurePass123!",
            full_name="Test User"
        )

        assert register.account_type == "individual"


class TestRegisterRequestBusinessType:
    """Tests pour la validation du type d'activité."""

    def test_valid_business_types(self):
        """Test types d'activité valides."""
        valid_types = ['resale', 'dropshipping', 'artisan', 'retail', 'other']

        for btype in valid_types:
            register = RegisterRequest(
                email="test@example.com",
                password="SecurePass123!",
                full_name="Test User",
                business_type=btype
            )
            assert register.business_type == btype

    def test_invalid_business_type(self):
        """Test type d'activité invalide."""
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(
                email="test@example.com",
                password="SecurePass123!",
                full_name="Test User",
                business_type="invalid"
            )

        assert "business_type" in str(exc_info.value)

    def test_none_business_type(self):
        """Test que business_type peut être None."""
        register = RegisterRequest(
            email="test@example.com",
            password="SecurePass123!",
            full_name="Test User",
            business_type=None
        )

        assert register.business_type is None


class TestRegisterRequestEstimatedProducts:
    """Tests pour la validation des produits estimés."""

    def test_valid_ranges(self):
        """Test ranges valides."""
        valid_ranges = ['0-50', '50-200', '200-500', '500+']

        for range_val in valid_ranges:
            register = RegisterRequest(
                email="test@example.com",
                password="SecurePass123!",
                full_name="Test User",
                estimated_products=range_val
            )
            assert register.estimated_products == range_val

    def test_invalid_range(self):
        """Test range invalide."""
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(
                email="test@example.com",
                password="SecurePass123!",
                full_name="Test User",
                estimated_products="100-150"
            )

        assert "estimated_products" in str(exc_info.value)


class TestRegisterRequestSIRET:
    """Tests pour la validation du SIRET."""

    def test_valid_siret(self):
        """Test SIRET valide (14 chiffres)."""
        register = RegisterRequest(
            email="test@example.com",
            password="SecurePass123!",
            full_name="Test User",
            siret="12345678901234"
        )

        assert register.siret == "12345678901234"

    def test_siret_valid_14_digits(self):
        """Test SIRET valide (exactement 14 chiffres)."""
        register = RegisterRequest(
            email="test@example.com",
            password="SecurePass123!",
            full_name="Test User",
            siret="12345678901234"
        )

        assert register.siret == "12345678901234"

    def test_siret_too_short(self):
        """Test SIRET trop court."""
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(
                email="test@example.com",
                password="SecurePass123!",
                full_name="Test User",
                siret="1234567890123"  # 13 chiffres
            )

        assert "SIRET" in str(exc_info.value) or "siret" in str(exc_info.value).lower()

    def test_siret_too_long(self):
        """Test SIRET trop long."""
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(
                email="test@example.com",
                password="SecurePass123!",
                full_name="Test User",
                siret="123456789012345"  # 15 chiffres
            )

        assert "SIRET" in str(exc_info.value) or "siret" in str(exc_info.value).lower()

    def test_siret_with_letters(self):
        """Test SIRET avec lettres (invalide)."""
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(
                email="test@example.com",
                password="SecurePass123!",
                full_name="Test User",
                siret="1234567890123A"
            )

        assert "SIRET" in str(exc_info.value) or "siret" in str(exc_info.value).lower()


class TestRegisterRequestCountryLanguage:
    """Tests pour la validation country/language."""

    def test_country_uppercase(self):
        """Test que country est converti en majuscules."""
        register = RegisterRequest(
            email="test@example.com",
            password="SecurePass123!",
            full_name="Test User",
            country="fr"
        )

        assert register.country == "FR"

    def test_language_lowercase(self):
        """Test que language est converti en minuscules."""
        register = RegisterRequest(
            email="test@example.com",
            password="SecurePass123!",
            full_name="Test User",
            language="FR"
        )

        assert register.language == "fr"

    def test_default_country(self):
        """Test que le pays par défaut est FR."""
        register = RegisterRequest(
            email="test@example.com",
            password="SecurePass123!",
            full_name="Test User"
        )

        assert register.country == "FR"

    def test_default_language(self):
        """Test que la langue par défaut est fr."""
        register = RegisterRequest(
            email="test@example.com",
            password="SecurePass123!",
            full_name="Test User"
        )

        assert register.language == "fr"


class TestRegisterRequestFullValidation:
    """Tests pour la validation complète."""

    def test_full_individual_registration(self):
        """Test inscription complète particulier."""
        register = RegisterRequest(
            email="john@example.com",
            password="SecurePass123!",
            full_name="John Doe",
            business_name="Ma Boutique",
            account_type="individual",
            business_type="resale",
            estimated_products="0-50",
            country="FR",
            language="fr"
        )

        assert register.email == "john@example.com"
        assert register.full_name == "John Doe"
        assert register.account_type == "individual"

    def test_full_professional_registration(self):
        """Test inscription complète professionnel."""
        register = RegisterRequest(
            email="pro@business.fr",
            password="SecurePass123!",
            full_name="Jean Dupont",
            business_name="Dupont SARL",
            account_type="professional",
            business_type="retail",
            estimated_products="200-500",
            siret="12345678901234",
            vat_number="FR12345678901",
            phone="+33612345678",
            country="FR",
            language="fr"
        )

        assert register.account_type == "professional"
        assert register.siret == "12345678901234"
        assert register.vat_number == "FR12345678901"
