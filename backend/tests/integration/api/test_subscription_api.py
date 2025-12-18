"""
Tests d'intégration pour l'API Subscription.

Objectif: Vérifier que l'endpoint /subscription/upgrade fonctionne correctement
et qu'il est impossible de contourner les quotas via l'API.

Business Rules (2025-12-09):
- USER peut upgrade/downgrade son propre abonnement
- ADMIN peut upgrade/downgrade son propre abonnement
- SUPPORT ne peut PAS modifier (lecture seule)
- Les quotas sont mis à jour immédiatement après upgrade

Author: Claude
Date: 2025-12-09
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import text

from models.public.user import User, UserRole, SubscriptionTier
from models.public.subscription_quota import SubscriptionQuota
from models.user.product import Product, ProductStatus
from services.auth_service import AuthService


# ===== FIXTURES =====

@pytest.fixture
def free_user(db_session: Session):
    """Crée un utilisateur FREE avec quota associé."""
    # S'assurer que les quotas existent
    quota_free = db_session.query(SubscriptionQuota).filter(
        SubscriptionQuota.tier == SubscriptionTier.FREE
    ).first()

    if not quota_free:
        quota_free = SubscriptionQuota(
            id=1,
            tier=SubscriptionTier.FREE,
            max_products=30,
            max_platforms=2,
            ai_credits_monthly=15,
        )
        db_session.add(quota_free)
        db_session.commit()
        db_session.refresh(quota_free)

    user = User(
        email="free@test.com",
        hashed_password=AuthService.hash_password("TestPassword123!"),
        full_name="Free User",
        role=UserRole.USER,
        subscription_tier=SubscriptionTier.FREE,
        subscription_tier_id=quota_free.id,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def pro_user(db_session: Session):
    """Crée un utilisateur PRO avec quota associé."""
    quota_pro = db_session.query(SubscriptionQuota).filter(
        SubscriptionQuota.tier == SubscriptionTier.PRO
    ).first()

    if not quota_pro:
        quota_pro = SubscriptionQuota(
            id=3,
            tier=SubscriptionTier.PRO,
            max_products=500,
            max_platforms=5,
            ai_credits_monthly=250,
        )
        db_session.add(quota_pro)
        db_session.commit()
        db_session.refresh(quota_pro)

    user = User(
        email="pro@test.com",
        hashed_password=AuthService.hash_password("TestPassword123!"),
        full_name="Pro User",
        role=UserRole.USER,
        subscription_tier=SubscriptionTier.PRO,
        subscription_tier_id=quota_pro.id,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def support_user(db_session: Session):
    """Crée un utilisateur SUPPORT avec quota associé."""
    quota_free = db_session.query(SubscriptionQuota).filter(
        SubscriptionQuota.tier == SubscriptionTier.FREE
    ).first()

    if not quota_free:
        quota_free = SubscriptionQuota(
            id=1,
            tier=SubscriptionTier.FREE,
            max_products=30,
            max_platforms=2,
            ai_credits_monthly=15,
        )
        db_session.add(quota_free)
        db_session.commit()
        db_session.refresh(quota_free)

    user = User(
        email="support@test.com",
        hashed_password=AuthService.hash_password("TestPassword123!"),
        full_name="Support User",
        role=UserRole.SUPPORT,
        subscription_tier=SubscriptionTier.FREE,
        subscription_tier_id=quota_free.id,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def get_auth_headers(client: TestClient, email: str, password: str):
    """Récupère les headers d'authentification."""
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200, f"Login failed: {response.json()}"
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def seed_subscription_quotas(db_session: Session):
    """Seed tous les quotas d'abonnement si ils n'existent pas."""
    quotas_data = [
        (1, SubscriptionTier.FREE, 30, 2, 15),
        (2, SubscriptionTier.STARTER, 150, 3, 75),
        (3, SubscriptionTier.PRO, 500, 5, 250),
        (4, SubscriptionTier.ENTERPRISE, 999999, 999999, 999999),
    ]

    for quota_id, tier, max_prod, max_plat, ai_cred in quotas_data:
        existing = db_session.query(SubscriptionQuota).filter(
            SubscriptionQuota.tier == tier
        ).first()

        if not existing:
            quota = SubscriptionQuota(
                id=quota_id,
                tier=tier,
                max_products=max_prod,
                max_platforms=max_plat,
                ai_credits_monthly=ai_cred,
            )
            db_session.add(quota)

    db_session.commit()


# ===== TESTS GET /subscription/info =====


def test_get_subscription_info_success(client: TestClient, free_user):
    """✅ USER peut consulter ses infos d'abonnement."""
    headers = get_auth_headers(client, "free@test.com", "TestPassword123!")

    response = client.get("/api/subscription/info", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == free_user.id
    assert data["current_tier"] == "free"
    assert data["max_products"] == 30
    assert data["max_platforms"] == 2
    assert data["ai_credits_monthly"] == 15


def test_get_subscription_info_requires_auth(client: TestClient):
    """❌ Consulter les infos requiert une authentification."""
    response = client.get("/api/subscription/info")
    assert response.status_code == 403  # FastAPI returns 403 Forbidden when auth fails


# ===== TESTS GET /subscription/tiers =====


def test_get_available_tiers_success(client: TestClient, free_user, db_session: Session):
    """✅ USER peut voir tous les tiers disponibles."""
    seed_subscription_quotas(db_session)
    headers = get_auth_headers(client, "free@test.com", "TestPassword123!")

    response = client.get("/api/subscription/tiers", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data["tiers"]) == 4
    assert data["tiers"][0]["tier"] == "free"
    assert data["tiers"][0]["is_current"] is True
    assert data["tiers"][1]["is_current"] is False


# ===== TESTS POST /subscription/upgrade =====


def test_upgrade_free_to_pro_success(client: TestClient, free_user, db_session: Session):
    """✅ USER peut upgrade FREE → PRO."""
    seed_subscription_quotas(db_session)
    headers = get_auth_headers(client, "free@test.com", "TestPassword123!")

    # Upgrade vers PRO
    response = client.post(
        "/api/subscription/upgrade",
        headers=headers,
        json={"new_tier": "pro"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["current_tier"] == "pro"
    assert data["max_products"] == 500
    assert data["max_platforms"] == 5
    assert data["ai_credits_monthly"] == 250


def test_downgrade_pro_to_free_success(client: TestClient, pro_user, db_session: Session):
    """✅ USER peut downgrade PRO → FREE."""
    seed_subscription_quotas(db_session)
    headers = get_auth_headers(client, "pro@test.com", "TestPassword123!")

    # Downgrade vers FREE
    response = client.post(
        "/api/subscription/upgrade",
        headers=headers,
        json={"new_tier": "free"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["current_tier"] == "free"
    assert data["max_products"] == 30


def test_support_cannot_upgrade(client: TestClient, support_user, db_session: Session):
    """❌ SUPPORT ne peut PAS upgrade (lecture seule)."""
    seed_subscription_quotas(db_session)
    headers = get_auth_headers(client, "support@test.com", "TestPassword123!")

    response = client.post(
        "/api/subscription/upgrade",
        headers=headers,
        json={"new_tier": "pro"},
    )

    assert response.status_code == 403
    assert "SUPPORT ne peut pas modifier" in response.json()["detail"]


def test_upgrade_invalid_tier_fails(client: TestClient, free_user):
    """❌ Upgrade vers un tier invalide échoue."""
    headers = get_auth_headers(client, "free@test.com", "TestPassword123!")

    response = client.post(
        "/api/subscription/upgrade",
        headers=headers,
        json={"new_tier": "invalid_tier"},
    )

    assert response.status_code == 422  # Validation error


def test_upgrade_requires_auth(client: TestClient):
    """❌ Upgrade requiert une authentification."""
    response = client.post(
        "/api/subscription/upgrade",
        json={"new_tier": "pro"},
    )
    assert response.status_code == 403  # FastAPI returns 403 Forbidden when auth fails


# ===== TESTS QUOTAS APRÈS UPGRADE =====


def test_quotas_updated_immediately_after_upgrade(
    client: TestClient, free_user, db_session: Session
):
    """✅ Les quotas sont mis à jour immédiatement après upgrade."""
    seed_subscription_quotas(db_session)
    headers = get_auth_headers(client, "free@test.com", "TestPassword123!")

    # Créer 30 produits (limite FREE) dans le schema user
    db_session.execute(text(f"SET search_path TO user_{free_user.id}, public"))
    import time
    timestamp = int(time.time() * 1000000)  # Microseconds for uniqueness
    for i in range(30):
        product = Product(
            title=f"Product {i} - {timestamp}",  # Unique title to avoid constraint violations
            description="Test description",
            price=10.0,
            status=ProductStatus.PUBLISHED,
            category="test",  # Required field
            condition="good"  # Required field
        )
        db_session.add(product)
    db_session.commit()

    # Vérifier que la limite est atteinte
    info_response = client.get("/api/subscription/info", headers=headers)
    assert info_response.json()["max_products"] == 30

    # Upgrade vers PRO
    upgrade_response = client.post(
        "/api/subscription/upgrade",
        headers=headers,
        json={"new_tier": "pro"},
    )
    assert upgrade_response.status_code == 200

    # Vérifier que les quotas sont immédiatement mis à jour
    info_response2 = client.get("/api/subscription/info", headers=headers)
    data = info_response2.json()
    assert data["current_tier"] == "pro"
    assert data["max_products"] == 500


def test_cannot_bypass_quotas_with_direct_api_call(
    client: TestClient, free_user, db_session: Session
):
    """❌ Impossible de contourner les quotas avec un appel direct à l'API."""
    seed_subscription_quotas(db_session)
    headers = get_auth_headers(client, "free@test.com", "TestPassword123!")

    # Créer 30 produits (limite FREE) dans le schema user
    db_session.execute(text(f"SET search_path TO user_{free_user.id}, public"))
    import time
    timestamp = int(time.time() * 1000000)  # Microseconds for uniqueness
    for i in range(30):
        product = Product(
            title=f"Product {i} - {timestamp}",  # Unique title to avoid constraint violations
            description="Test description",
            price=10.0,
            status=ProductStatus.PUBLISHED,
            category="test",  # Required field
            condition="good"  # Required field
        )
        db_session.add(product)
    db_session.commit()

    # Tenter de créer un 31ème produit via l'API
    product_response = client.post(
        "/api/products/",
        headers=headers,
        json={
            "title": "Product 31",
            "description": "Test",
            "price": 10.0,
            "category": "Tops",
            "brand": "Nike",
            "condition": "Good",
            "label_size": "M",
            "color": "Black",
        },
    )

    # Doit échouer avec 403 (limite atteinte)
    assert product_response.status_code == 403
    detail = product_response.json()["detail"]
    assert "Limite de produits atteinte" in detail["message"]


# ===== TESTS EDGE CASES =====


def test_upgrade_to_same_tier_is_idempotent(client: TestClient, free_user, db_session: Session):
    """✅ Upgrade vers le même tier est idempotent (pas d'erreur)."""
    seed_subscription_quotas(db_session)
    headers = get_auth_headers(client, "free@test.com", "TestPassword123!")

    # Upgrade vers FREE (même tier)
    response = client.post(
        "/api/subscription/upgrade",
        headers=headers,
        json={"new_tier": "free"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["current_tier"] == "free"


def test_multiple_upgrades_in_sequence(client: TestClient, free_user, db_session: Session):
    """✅ Plusieurs upgrades successifs fonctionnent correctement."""
    seed_subscription_quotas(db_session)
    headers = get_auth_headers(client, "free@test.com", "TestPassword123!")

    # FREE → STARTER
    response1 = client.post(
        "/api/subscription/upgrade",
        headers=headers,
        json={"new_tier": "starter"},
    )
    assert response1.status_code == 200
    assert response1.json()["current_tier"] == "starter"

    # STARTER → PRO
    response2 = client.post(
        "/api/subscription/upgrade",
        headers=headers,
        json={"new_tier": "pro"},
    )
    assert response2.status_code == 200
    assert response2.json()["current_tier"] == "pro"

    # PRO → ENTERPRISE
    response3 = client.post(
        "/api/subscription/upgrade",
        headers=headers,
        json={"new_tier": "enterprise"},
    )
    assert response3.status_code == 200
    assert response3.json()["current_tier"] == "enterprise"
    assert response3.json()["max_products"] == 999999
