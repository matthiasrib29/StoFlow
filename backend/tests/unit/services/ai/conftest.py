"""
Pytest Configuration pour les tests AI.

Ces tests utilisent la vraie base de données (contrairement aux autres tests unitaires)
car ils testent des interactions complexes avec la DB (credits, logging, etc.).

Ce conftest.py réactive les fixtures DB du conftest.py root.
"""

import pytest
from sqlalchemy import select, text

# Import fixtures from root conftest
from tests.conftest import (
    TestingSessionLocal,
    _run_cleanup,
)


# Re-enable cleanup for AI tests that use real DB
@pytest.fixture(scope="function", autouse=True)
def cleanup_data(request):
    """
    Réactive le cleanup pour les tests AI qui utilisent la vraie DB.
    """
    print(f"\n[AI cleanup_data] BEFORE test: {request.node.name}")
    _run_cleanup()

    # Register finalizer for cleanup AFTER test
    request.addfinalizer(_run_cleanup)

    yield


@pytest.fixture(scope="function")
def test_user():
    """
    Fixture locale pour créer un utilisateur de test.
    Utilise sa propre session pour éviter les conflits.
    """
    from models.public.user import User, SubscriptionTier
    from models.public.subscription_quota import SubscriptionQuota
    from services.auth_service import AuthService

    session = TestingSessionLocal()

    try:
        # Clean existing user if any (to handle leftover from previous tests)
        session.execute(text("DELETE FROM public.ai_credits WHERE user_id IN (SELECT id FROM public.users WHERE email = 'admin@test.com')"))
        session.execute(text("DELETE FROM public.users WHERE email = 'admin@test.com'"))
        session.commit()

        # Get or create FREE quota
        stmt = select(SubscriptionQuota).where(SubscriptionQuota.tier == SubscriptionTier.FREE)
        quota_free = session.execute(stmt).scalar_one_or_none()

        if not quota_free:
            quota_free = SubscriptionQuota(
                id=1,
                tier=SubscriptionTier.FREE,
                max_products=30,
                max_platforms=2,
                ai_credits_monthly=15,
            )
            session.add(quota_free)
            session.commit()
            session.refresh(quota_free)

        password_plain = "securepassword123"
        user = User(
            email="admin@test.com",
            hashed_password=AuthService.hash_password(password_plain),
            full_name="Admin User",
            role="admin",
            subscription_tier=SubscriptionTier.FREE,
            subscription_tier_id=quota_free.id,
            is_active=True,
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        yield user, password_plain
    finally:
        session.close()


@pytest.fixture(scope="function")
def db_session(test_user):
    """
    Session DB pour les tests AI.

    Configure le search_path et schema_translate_map vers le schéma utilisateur.
    Le schema_translate_map permet de mapper 'tenant' → 'user_{id}' pour les
    modèles qui ont schema='tenant' (comme AIGenerationLog).
    """
    from sqlalchemy.orm import Session

    user, _ = test_user
    user_schema = f"user_{user.id}"

    # Get engine from TestingSessionLocal and create connection with schema_translate_map
    engine = TestingSessionLocal.kw.get('bind')
    if engine is None:
        # Fallback: get from session
        temp_session = TestingSessionLocal()
        engine = temp_session.bind
        temp_session.close()

    # Create connection with schema_translate_map
    connection = engine.connect().execution_options(
        schema_translate_map={"tenant": user_schema}
    )

    # Create session bound to this connection
    session = Session(bind=connection)

    try:
        # Also set search path for non-tenant tables
        session.execute(text(f"SET search_path TO {user_schema}, public"))
        yield session
    finally:
        session.close()
        connection.close()


@pytest.fixture(scope="function")
def free_quota(db_session):
    """
    Fixture qui retourne le quota FREE existant ou en crée un si nécessaire.
    """
    from models.public.subscription_quota import SubscriptionQuota
    from models.public.user import SubscriptionTier

    stmt = select(SubscriptionQuota).where(SubscriptionQuota.tier == SubscriptionTier.FREE)
    quota = db_session.execute(stmt).scalar_one_or_none()

    if not quota:
        quota = SubscriptionQuota(
            tier=SubscriptionTier.FREE,
            max_products=30,
            max_platforms=2,
            ai_credits_monthly=15,
        )
        db_session.add(quota)
        db_session.commit()
        db_session.refresh(quota)

    return quota


@pytest.fixture(scope="function")
def test_product(db_session, test_user):
    """
    Fixture locale pour créer un produit de test dans le schema utilisateur.

    Utilise SQL direct au lieu de l'ORM pour éviter les problèmes de FK
    quand les tables de référence ne sont pas chargées dans le metadata.
    """
    import json

    user, _ = test_user
    user_schema = f"user_{user.id}"

    # Create product via SQL to avoid ORM FK resolution issues
    images = json.dumps([
        {"url": "https://example.com/img1.jpg", "order": 0},
        {"url": "https://example.com/img2.jpg", "order": 1}
    ])

    result = db_session.execute(text(f"""
        INSERT INTO {user_schema}.products
        (title, description, price, stock_quantity, category, brand, condition, size_original, gender, images, status)
        VALUES
        ('Test Product', 'Test description', 25.99, 10, 'T-shirt', 'Nike', 8, 'M', 'Men', :images, 'DRAFT')
        RETURNING id, title, description, price, stock_quantity, category, brand, condition, size_original, gender, images, status
    """), {"images": images})

    row = result.fetchone()
    db_session.commit()

    # Create a simple object to hold the product data
    class SimpleProduct:
        def __init__(self, row):
            self.id = row[0]
            self.title = row[1]
            self.description = row[2]
            self.price = row[3]
            self.stock_quantity = row[4]
            self.category = row[5]
            self.brand = row[6]
            self.condition = row[7]
            self.size_original = row[8]
            self.gender = row[9]
            self._images = row[10]
            self.status = row[11]

        @property
        def images(self):
            return self._images if isinstance(self._images, list) else json.loads(self._images)

        @images.setter
        def images(self, value):
            self._images = value

    return SimpleProduct(row)
