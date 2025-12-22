"""
Tests E2E pour les workflows d'authentification complets et securite.

Couverture:
- Cycle de vie utilisateur complet
- Limites de securite (token types, expiration)
- Protection timing attack

Author: Claude
Date: 2025-12-22 (refactored from test_auth_flows.py)
"""

import pytest
import time
from datetime import timedelta
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


class TestCompleteAuthWorkflow:
    """Tests de workflows d'authentification complets."""

    def test_full_user_lifecycle(
        self, client: TestClient, db_session: Session
    ):
        """
        Test du cycle de vie complet d'un utilisateur.

        Flow:
        1. Inscription
        2. Verification email
        3. Login
        4. Refresh token
        5. Acces API protegee
        """
        ensure_quota_exists(db_session)

        # Step 1: Register
        register_response = client.post(
            "/api/auth/register",
            json={
                "email": "lifecycle@test.com",
                "password": "SecurePass123!",
                "full_name": "Lifecycle User",
                "account_type": "individual",
            }
        )
        assert register_response.status_code == 201

        # Step 2: Verify email
        user = db_session.query(User).filter(
            User.email == "lifecycle@test.com"
        ).first()
        verify_response = client.get(
            f"/api/auth/verify-email?token={user.email_verification_token}"
        )
        assert verify_response.status_code == 200

        # Step 3: Login
        login_response = client.post(
            "/api/auth/login",
            json={
                "email": "lifecycle@test.com",
                "password": "SecurePass123!"
            }
        )
        assert login_response.status_code == 200
        login_tokens = login_response.json()

        # Step 4: Refresh token
        refresh_response = client.post(
            "/api/auth/refresh",
            json={
                "refresh_token": login_tokens["refresh_token"]
            }
        )
        assert refresh_response.status_code == 200
        new_access_token = refresh_response.json()["access_token"]

        # Step 5: Verify token is valid
        payload = AuthService.verify_token(new_access_token, token_type="access")
        assert payload is not None
        assert payload["user_id"] == user.id

    def test_inactive_user_cannot_login(
        self, client: TestClient, db_session: Session
    ):
        """Test qu'un utilisateur desactive ne peut pas se connecter."""
        quota = ensure_quota_exists(db_session)

        user = User(
            email="inactive@test.com",
            hashed_password=AuthService.hash_password("SecurePass123!"),
            full_name="Inactive User",
            role=UserRole.USER,
            subscription_tier=SubscriptionTier.FREE,
            subscription_tier_id=quota.id,
            is_active=False,
        )
        db_session.add(user)
        db_session.commit()

        response = client.post(
            "/api/auth/login",
            json={
                "email": "inactive@test.com",
                "password": "SecurePass123!"
            }
        )

        assert response.status_code == 401

    def test_duplicate_registration_fails(
        self, client: TestClient, db_session: Session
    ):
        """Test qu'une inscription avec email existant echoue."""
        quota = ensure_quota_exists(db_session)

        user = User(
            email="duplicate@test.com",
            hashed_password=AuthService.hash_password("SecurePass123!"),
            full_name="First User",
            role=UserRole.USER,
            subscription_tier=SubscriptionTier.FREE,
            subscription_tier_id=quota.id,
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        response = client.post(
            "/api/auth/register",
            json={
                "email": "duplicate@test.com",
                "password": "AnotherPass456!",
                "full_name": "Second User",
                "account_type": "individual",
            }
        )

        assert response.status_code == 400
        assert "existe déjà" in response.json()["detail"].lower()


class TestSecurityBoundaries:
    """Tests des limites de securite."""

    def test_access_token_cannot_refresh(
        self, client: TestClient, db_session: Session
    ):
        """Test qu'un access token ne peut pas etre utilise pour refresh."""
        quota = ensure_quota_exists(db_session)

        user = User(
            email="tokentype@test.com",
            hashed_password=AuthService.hash_password("SecurePass123!"),
            full_name="Token Type User",
            role=UserRole.USER,
            subscription_tier=SubscriptionTier.FREE,
            subscription_tier_id=quota.id,
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        login_response = client.post(
            "/api/auth/login",
            json={
                "email": "tokentype@test.com",
                "password": "SecurePass123!"
            }
        )
        assert login_response.status_code == 200
        access_token = login_response.json()["access_token"]

        refresh_response = client.post(
            "/api/auth/refresh",
            json={
                "refresh_token": access_token
            }
        )

        assert refresh_response.status_code == 401

    def test_expired_refresh_token_rejected(self, client: TestClient):
        """Test qu'un refresh token expire est rejete."""
        from jose import jwt
        from shared.config import settings

        expired_payload = {
            "user_id": 1,
            "type": "refresh",
            "exp": utc_now() - timedelta(hours=1),
            "iat": utc_now() - timedelta(days=8),
        }
        expired_token = jwt.encode(
            expired_payload,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm
        )

        response = client.post(
            "/api/auth/refresh",
            json={
                "refresh_token": expired_token
            }
        )

        assert response.status_code == 401

    def test_malformed_token_rejected(self, client: TestClient):
        """Test qu'un token malforme est rejete."""
        response = client.post(
            "/api/auth/refresh",
            json={
                "refresh_token": "not.a.valid.jwt.token"
            }
        )

        assert response.status_code == 401

    def test_timing_attack_protection_active(
        self, client: TestClient, db_session: Session
    ):
        """
        Test que le delai anti-timing attack est actif.

        Note: Ce test verifie que le login prend un temps minimum
        pour proteger contre les timing attacks qui pourraient
        reveler si un email existe.
        """
        quota = ensure_quota_exists(db_session)

        user = User(
            email="timing@test.com",
            hashed_password=AuthService.hash_password("SecurePass123!"),
            full_name="Timing User",
            role=UserRole.USER,
            subscription_tier=SubscriptionTier.FREE,
            subscription_tier_id=quota.id,
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        # Test with existing user (wrong password)
        start_existing = time.time()
        client.post(
            "/api/auth/login",
            json={
                "email": "timing@test.com",
                "password": "wrongpassword"
            }
        )
        time_existing = time.time() - start_existing

        # Test with non-existing user
        start_nonexistent = time.time()
        client.post(
            "/api/auth/login",
            json={
                "email": "nonexistent@test.com",
                "password": "anypassword1"
            }
        )
        time_nonexistent = time.time() - start_nonexistent

        # Both should take at least 50ms (timing attack protection)
        assert time_existing >= 0.05
        assert time_nonexistent >= 0.05
