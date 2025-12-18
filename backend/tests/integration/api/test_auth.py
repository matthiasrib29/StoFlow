"""
Tests for Authentication

Tests unitaires et d'intégration pour le système d'authentification.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from models.public.user import User, UserRole
from services.auth_service import AuthService


class TestAuthService:
    """Tests pour le service d'authentification."""

    def test_hash_password(self):
        """Test du hashage de mot de passe."""
        password = "securepassword123"
        hashed = AuthService.hash_password(password)

        # Le hash ne doit pas être le mot de passe en clair
        assert hashed != password
        # Le hash doit commencer par $2b$ (bcrypt)
        assert hashed.startswith("$2b$")

    def test_verify_password_correct(self):
        """Test de vérification avec un mot de passe correct."""
        password = "securepassword123"
        hashed = AuthService.hash_password(password)

        # Le mot de passe correct doit être vérifié
        assert AuthService.verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test de vérification avec un mot de passe incorrect."""
        password = "securepassword123"
        wrong_password = "wrongpassword"
        hashed = AuthService.hash_password(password)

        # Le mauvais mot de passe ne doit pas être vérifié
        assert AuthService.verify_password(wrong_password, hashed) is False

    def test_authenticate_user_success(self, db_session: Session, test_user):
        """Test d'authentification réussie."""
        user, password = test_user

        # Authentification avec email et mot de passe corrects
        authenticated_user = AuthService.authenticate_user(
            db=db_session,
            email=user.email,
            password=password
        )

        assert authenticated_user is not None
        assert authenticated_user.id == user.id
        assert authenticated_user.email == user.email
        # last_login doit être mis à jour
        assert authenticated_user.last_login is not None

    def test_authenticate_user_wrong_password(self, db_session: Session, test_user):
        """Test d'authentification avec mot de passe incorrect."""
        user, _ = test_user

        # Authentification avec mauvais mot de passe
        authenticated_user = AuthService.authenticate_user(
            db=db_session,
            email=user.email,
            password="wrongpassword"
        )

        assert authenticated_user is None

    def test_authenticate_user_email_not_found(self, db_session: Session):
        """Test d'authentification avec email inexistant."""
        authenticated_user = AuthService.authenticate_user(
            db=db_session,
            email="nonexistent@test.com",
            password="anypassword"
        )

        assert authenticated_user is None

    def test_authenticate_user_inactive(self, db_session: Session, test_user):
        """Test d'authentification avec utilisateur inactif."""
        user, password = test_user

        # Désactiver l'utilisateur
        user.is_active = False
        db_session.commit()

        # L'authentification doit échouer
        authenticated_user = AuthService.authenticate_user(
            db=db_session,
            email=user.email,
            password=password
        )

        assert authenticated_user is None

    def test_create_access_token(self):
        """Test de création d'access token."""
        token = AuthService.create_access_token(
            user_id=1,
            role="admin"
        )

        # Le token doit être une string non vide
        assert isinstance(token, str)
        assert len(token) > 0

        # Vérifier qu'on peut décoder le token
        payload = AuthService.verify_token(token, token_type="access")
        assert payload is not None
        assert payload["user_id"] == 1
        assert payload["role"] == "admin"
        assert payload["type"] == "access"

    def test_create_refresh_token(self):
        """Test de création de refresh token."""
        token = AuthService.create_refresh_token(
            user_id=1
        )

        # Le token doit être une string non vide
        assert isinstance(token, str)
        assert len(token) > 0

        # Vérifier qu'on peut décoder le token
        payload = AuthService.verify_token(token, token_type="refresh")
        assert payload is not None
        assert payload["user_id"] == 1
        assert payload["type"] == "refresh"
        # Le refresh token ne doit PAS contenir le role
        assert "role" not in payload

    def test_verify_token_invalid(self):
        """Test de vérification d'un token invalide."""
        payload = AuthService.verify_token("invalid.token.here", token_type="access")
        assert payload is None

    def test_verify_token_wrong_type(self):
        """Test de vérification avec mauvais type de token."""
        # Créer un access token
        token = AuthService.create_access_token(
            user_id=1,
            role="admin"
        )

        # Essayer de le vérifier comme refresh token
        payload = AuthService.verify_token(token, token_type="refresh")
        assert payload is None


class TestAuthAPI:
    """Tests pour les routes API d'authentification."""

    def test_login_success(self, client: TestClient, test_user):
        """Test de login réussi."""
        user, password = test_user

        response = client.post(
            "/api/auth/login",
            json={
                "email": user.email,
                "password": password
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Vérifier la structure de la réponse
        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data
        assert "user_id" in data
        assert "role" in data

        # Vérifier les valeurs
        assert data["token_type"] == "bearer"
        assert data["user_id"] == user.id
        assert data["role"] == user.role.value

    def test_login_wrong_password(self, client: TestClient, test_user):
        """Test de login avec mauvais mot de passe."""
        user, _ = test_user

        response = client.post(
            "/api/auth/login",
            json={
                "email": user.email,
                "password": "wrongpassword"
            }
        )

        assert response.status_code == 401
        assert "detail" in response.json()

    def test_login_email_not_found(self, client: TestClient):
        """Test de login avec email inexistant."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "nonexistent@test.com",
                "password": "anypassword"
            }
        )

        assert response.status_code == 401
        assert "detail" in response.json()

    def test_login_invalid_email_format(self, client: TestClient):
        """Test de login avec format d'email invalide."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "invalid-email",
                "password": "anypassword"
            }
        )

        # Pydantic validation error (422)
        assert response.status_code == 422

    def test_login_short_password(self, client: TestClient):
        """Test de login avec mot de passe trop court."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "test@test.com",
                "password": "short"  # < 8 caractères
            }
        )

        # Pydantic validation error (422)
        assert response.status_code == 422

    def test_refresh_token_success(self, client: TestClient, test_user):
        """Test de refresh de token réussi."""
        user, password = test_user

        # Login pour obtenir le refresh token
        login_response = client.post(
            "/api/auth/login",
            json={
                "email": user.email,
                "password": password
            }
        )

        assert login_response.status_code == 200
        refresh_token = login_response.json()["refresh_token"]

        # Refresh le token
        response = client.post(
            "/api/auth/refresh",
            json={
                "refresh_token": refresh_token
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Vérifier la structure
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"

    def test_refresh_token_invalid(self, client: TestClient):
        """Test de refresh avec token invalide."""
        response = client.post(
            "/api/auth/refresh",
            json={
                "refresh_token": "invalid.token.here"
            }
        )

        assert response.status_code == 401
        assert "detail" in response.json()

    def test_refresh_token_with_access_token(self, client: TestClient, test_user):
        """Test de refresh avec un access token (au lieu d'un refresh token)."""
        user, password = test_user

        # Login pour obtenir l'access token
        login_response = client.post(
            "/api/auth/login",
            json={
                "email": user.email,
                "password": password
            }
        )

        assert login_response.status_code == 200
        access_token = login_response.json()["access_token"]

        # Essayer de refresh avec l'access token (devrait échouer)
        response = client.post(
            "/api/auth/refresh",
            json={
                "refresh_token": access_token
            }
        )

        assert response.status_code == 401

    def test_login_with_source_parameter(self, client: TestClient, test_user):
        """Test de login avec paramètre source (plugin, mobile, etc)."""
        user, password = test_user

        # Test avec source=plugin
        response = client.post(
            "/api/auth/login?source=plugin",
            json={
                "email": user.email,
                "password": password
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Vérifier la structure de la réponse (identique)
        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"

    def test_login_with_mobile_source(self, client: TestClient, test_user):
        """Test de login avec source=mobile."""
        user, password = test_user

        response = client.post(
            "/api/auth/login?source=mobile",
            json={
                "email": user.email,
                "password": password
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
