"""
Tests E2E pour le lockout de compte et rotation JWT.

Couverture:
- Flow de lockout et deblocage de compte
- Rotation de secret JWT transparente
- Tentatives de connexion concurrentes

Author: Claude
Date: 2025-12-22 (refactored from test_auth_flows.py)
"""

import pytest
from datetime import timedelta
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from models.public.user import User, UserRole, SubscriptionTier
from models.public.subscription_quota import SubscriptionQuota
from services.auth_service import AuthService
from shared.datetime_utils import utc_now


def ensure_quota_exists(db_session: Session) -> SubscriptionQuota:
    """Helper to ensure FREE quota exists."""
    quota = db_session.query(SubscriptionQuota).filter(
        SubscriptionQuota.tier == SubscriptionTier.FREE
    ).first()
    if not quota:
        quota = SubscriptionQuota(
            id=1,
            tier=SubscriptionTier.FREE,
            max_products=30,
            max_platforms=2,
            ai_credits_monthly=15,
        )
        db_session.add(quota)
        db_session.commit()
    return quota


class TestAccountLockoutFlow:
    """Tests E2E du flow de lockout/deblocage de compte."""

    def test_account_lockout_after_failed_attempts(
        self, client: TestClient, db_session: Session
    ):
        """
        Test du lockout apres trop de tentatives echouees.

        Verifie que:
        1. Le compteur de tentatives s'incremente
        2. Le compte se verrouille apres 5 echecs
        3. Les tentatives suivantes sont rejetees meme avec bon password
        """
        quota = ensure_quota_exists(db_session)

        user = User(
            email="lockout@test.com",
            hashed_password=AuthService.hash_password("SecurePass123!"),
            full_name="Lockout User",
            role=UserRole.USER,
            subscription_tier=SubscriptionTier.FREE,
            subscription_tier_id=quota.id,
            is_active=True,
            failed_login_attempts=0,
        )
        db_session.add(user)
        db_session.commit()

        for i in range(5):
            response = client.post(
                "/api/auth/login",
                json={
                    "email": "lockout@test.com",
                    "password": "wrongpassword"
                }
            )
            assert response.status_code == 401

        db_session.refresh(user)
        assert user.failed_login_attempts >= 5
        assert user.locked_until is not None

        response = client.post(
            "/api/auth/login",
            json={
                "email": "lockout@test.com",
                "password": "SecurePass123!"
            }
        )
        assert response.status_code == 401

    def test_account_auto_unlock_after_lockout_duration(
        self, client: TestClient, db_session: Session
    ):
        """
        Test du deblocage automatique apres la duree de lockout.

        Verifie que:
        1. Le compte verrouille se debloque apres 30 min
        2. Le login avec bon password fonctionne apres deblocage
        3. Le compteur est reinitialise
        """
        quota = ensure_quota_exists(db_session)

        user = User(
            email="unlock@test.com",
            hashed_password=AuthService.hash_password("SecurePass123!"),
            full_name="Unlock User",
            role=UserRole.USER,
            subscription_tier=SubscriptionTier.FREE,
            subscription_tier_id=quota.id,
            is_active=True,
            failed_login_attempts=5,
            locked_until=utc_now() - timedelta(minutes=1),
        )
        db_session.add(user)
        db_session.commit()

        response = client.post(
            "/api/auth/login",
            json={
                "email": "unlock@test.com",
                "password": "SecurePass123!"
            }
        )

        assert response.status_code == 200

        db_session.refresh(user)
        assert user.failed_login_attempts == 0
        assert user.locked_until is None

    def test_successful_login_resets_failed_attempts(
        self, client: TestClient, db_session: Session
    ):
        """Test qu'un login reussi remet le compteur a zero."""
        quota = ensure_quota_exists(db_session)

        user = User(
            email="reset@test.com",
            hashed_password=AuthService.hash_password("SecurePass123!"),
            full_name="Reset User",
            role=UserRole.USER,
            subscription_tier=SubscriptionTier.FREE,
            subscription_tier_id=quota.id,
            is_active=True,
            failed_login_attempts=3,
        )
        db_session.add(user)
        db_session.commit()

        response = client.post(
            "/api/auth/login",
            json={
                "email": "reset@test.com",
                "password": "SecurePass123!"
            }
        )

        assert response.status_code == 200

        db_session.refresh(user)
        assert user.failed_login_attempts == 0


class TestJWTSecretRotationFlow:
    """Tests E2E de la rotation de secret JWT."""

    @patch('services.auth_service.settings')
    def test_seamless_rotation_for_active_users(self, mock_settings, db_session: Session):
        """
        Test que la rotation de secret est transparente pour les utilisateurs.

        Scenario:
        1. User obtient un token avec ancien secret
        2. Admin fait la rotation (nouveau secret, ancien en backup)
        3. Token de l'user continue de fonctionner
        """
        mock_settings.jwt_secret_key = "old_secret_key_12345"
        mock_settings.jwt_secret_key_previous = None
        mock_settings.jwt_algorithm = "HS256"

        old_token = AuthService.create_access_token(user_id=1, role="user")

        payload = AuthService.verify_token(old_token, token_type="access")
        assert payload is not None
        assert payload["user_id"] == 1

        mock_settings.jwt_secret_key = "new_secret_key_67890"
        mock_settings.jwt_secret_key_previous = "old_secret_key_12345"

        payload_after_rotation = AuthService.verify_token(old_token, token_type="access")
        assert payload_after_rotation is not None
        assert payload_after_rotation["user_id"] == 1

        new_token = AuthService.create_access_token(user_id=2, role="user")
        payload_new = AuthService.verify_token(new_token, token_type="access")
        assert payload_new is not None
        assert payload_new["user_id"] == 2

    @patch('services.auth_service.settings')
    def test_old_tokens_fail_after_grace_period(self, mock_settings):
        """
        Test que les anciens tokens echouent apres suppression du backup.

        Scenario:
        1. Token cree avec ancien secret
        2. Rotation avec grace period
        3. Grace period terminee (backup supprime)
        4. Ancien token doit echouer
        """
        mock_settings.jwt_secret_key = "old_secret_key"
        mock_settings.jwt_secret_key_previous = None
        mock_settings.jwt_algorithm = "HS256"

        old_token = AuthService.create_access_token(user_id=1, role="user")

        mock_settings.jwt_secret_key = "new_secret_key"
        mock_settings.jwt_secret_key_previous = None

        payload = AuthService.verify_token(old_token, token_type="access")
        assert payload is None


class TestConcurrentLoginFlow:
    """Tests de scenarios de connexion concurrents."""

    def test_same_user_multiple_sessions(
        self, client: TestClient, db_session: Session
    ):
        """
        Test qu'un utilisateur peut avoir plusieurs sessions actives.

        Verifie que:
        1. Plusieurs logins generent differents tokens
        2. Tous les tokens sont valides simultanement
        """
        quota = ensure_quota_exists(db_session)

        user = User(
            email="multisession@test.com",
            hashed_password=AuthService.hash_password("SecurePass123!"),
            full_name="Multi Session User",
            role=UserRole.USER,
            subscription_tier=SubscriptionTier.FREE,
            subscription_tier_id=quota.id,
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        tokens = []
        for _ in range(3):
            response = client.post(
                "/api/auth/login",
                json={
                    "email": "multisession@test.com",
                    "password": "SecurePass123!"
                }
            )
            assert response.status_code == 200
            tokens.append(response.json()["access_token"])

        assert len(set(tokens)) == 3

        for token in tokens:
            payload = AuthService.verify_token(token, token_type="access")
            assert payload is not None
            assert payload["user_id"] == user.id

    def test_login_with_different_sources(
        self, client: TestClient, db_session: Session
    ):
        """Test des logins depuis differentes sources (web, plugin, mobile)."""
        quota = ensure_quota_exists(db_session)

        user = User(
            email="multisource@test.com",
            hashed_password=AuthService.hash_password("SecurePass123!"),
            full_name="Multi Source User",
            role=UserRole.USER,
            subscription_tier=SubscriptionTier.FREE,
            subscription_tier_id=quota.id,
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        sources = ["web", "plugin", "mobile"]
        for source in sources:
            response = client.post(
                f"/api/auth/login?source={source}",
                json={
                    "email": "multisource@test.com",
                    "password": "SecurePass123!"
                }
            )
            assert response.status_code == 200
            assert "access_token" in response.json()
