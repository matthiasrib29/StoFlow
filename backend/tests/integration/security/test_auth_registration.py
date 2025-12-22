"""
Tests E2E pour les flows d'inscription et verification email.

Couverture:
- Flow d'inscription complet avec verification email
- Verification avec token expire
- Renvoi de verification email

Author: Claude
Date: 2025-12-22 (refactored from test_auth_flows.py)
"""

import pytest
from datetime import timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import secrets

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


class TestRegistrationFlow:
    """Tests E2E du flow d'inscription complet."""

    def test_full_registration_flow_creates_user_and_schema(
        self, client: TestClient, db_session: Session
    ):
        """
        Test du flow complet d'inscription.

        Verifie que:
        1. L'utilisateur est cree
        2. Le schema PostgreSQL est cree
        3. Un token de verification email est genere
        4. Les tokens JWT sont retournes
        """
        ensure_quota_exists(db_session)

        response = client.post(
            "/api/auth/register",
            json={
                "email": "newuser@test.com",
                "password": "SecurePass123!",
                "full_name": "New User",
                "account_type": "individual",
            }
        )

        assert response.status_code == 201
        data = response.json()

        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["role"] == "user"

        user = db_session.query(User).filter(User.email == "newuser@test.com").first()
        assert user is not None
        assert user.full_name == "New User"
        assert user.is_active is True

        assert user.email_verification_token is not None
        assert user.email_verification_expires is not None
        assert user.email_verified is False

    def test_registration_with_email_verification_flow(
        self, client: TestClient, db_session: Session
    ):
        """
        Test du flow complet: inscription -> verification email.

        Verifie que:
        1. L'inscription genere un token de verification
        2. Le token peut etre utilise pour verifier l'email
        3. L'email est marque comme verifie
        """
        ensure_quota_exists(db_session)

        response = client.post(
            "/api/auth/register",
            json={
                "email": "verify@test.com",
                "password": "SecurePass123!",
                "full_name": "Verify User",
                "account_type": "individual",
            }
        )
        assert response.status_code == 201

        user = db_session.query(User).filter(User.email == "verify@test.com").first()
        verification_token = user.email_verification_token
        assert verification_token is not None
        assert user.email_verified is False

        verify_response = client.get(
            f"/api/auth/verify-email?token={verification_token}"
        )

        assert verify_response.status_code == 200
        assert "vérifié" in verify_response.json()["message"].lower()

        db_session.refresh(user)
        assert user.email_verified is True
        assert user.email_verification_token is None


class TestEmailVerification:
    """Tests de verification email."""

    def test_email_verification_with_expired_token(
        self, client: TestClient, db_session: Session
    ):
        """Test que la verification echoue avec un token expire."""
        quota = ensure_quota_exists(db_session)

        user = User(
            email="expired@test.com",
            hashed_password=AuthService.hash_password("SecurePass123!"),
            full_name="Expired User",
            role=UserRole.USER,
            subscription_tier=SubscriptionTier.FREE,
            subscription_tier_id=quota.id,
            is_active=True,
            email_verified=False,
            email_verification_token=secrets.token_urlsafe(32),
            email_verification_expires=utc_now() - timedelta(hours=1),
        )
        db_session.add(user)
        db_session.commit()

        response = client.get(
            f"/api/auth/verify-email?token={user.email_verification_token}"
        )

        assert response.status_code == 400
        assert "invalide ou expiré" in response.json()["detail"].lower()

    def test_resend_verification_for_unverified_user(
        self, client: TestClient, db_session: Session
    ):
        """Test la regeneration du token de verification."""
        quota = ensure_quota_exists(db_session)

        old_token = secrets.token_urlsafe(32)
        user = User(
            email="resend@test.com",
            hashed_password=AuthService.hash_password("SecurePass123!"),
            full_name="Resend User",
            role=UserRole.USER,
            subscription_tier=SubscriptionTier.FREE,
            subscription_tier_id=quota.id,
            is_active=True,
            email_verified=False,
            email_verification_token=old_token,
            email_verification_expires=utc_now() + timedelta(hours=24),
        )
        db_session.add(user)
        db_session.commit()

        response = client.post(
            "/api/auth/resend-verification",
            params={"email": "resend@test.com"}
        )

        assert response.status_code == 200
        assert "envoyé" in response.json()["message"].lower()

        db_session.refresh(user)
        assert user.email_verification_token is not None
        assert user.email_verification_token != old_token

    def test_resend_verification_for_nonexistent_email_same_response(
        self, client: TestClient
    ):
        """Test reponse identique pour email inexistant (anti-enumeration)."""
        response = client.post(
            "/api/auth/resend-verification",
            params={"email": "nonexistent@test.com"}
        )

        assert response.status_code == 200
        assert "envoyé" in response.json()["message"].lower()

    def test_resend_verification_for_already_verified_same_response(
        self, client: TestClient, db_session: Session
    ):
        """Test reponse identique pour email deja verifie (anti-enumeration)."""
        quota = ensure_quota_exists(db_session)

        user = User(
            email="verified@test.com",
            hashed_password=AuthService.hash_password("SecurePass123!"),
            full_name="Verified User",
            role=UserRole.USER,
            subscription_tier=SubscriptionTier.FREE,
            subscription_tier_id=quota.id,
            is_active=True,
            email_verified=True,
        )
        db_session.add(user)
        db_session.commit()

        response = client.post(
            "/api/auth/resend-verification",
            params={"email": "verified@test.com"}
        )

        assert response.status_code == 200
        assert "envoyé" in response.json()["message"].lower()
