"""
Pytest Configuration et Fixtures

Ce fichier contient les fixtures partagées pour tous les tests.

NOTE: Utilise PostgreSQL (Docker) pour des tests réalistes avec schemas multi-tenant.
"""

import os
import sys

# CRITICAL: Set DISABLE_RATE_LIMIT=1 to disable rate limiting middleware in tests
# NOTE: Do NOT use TESTING=1 as it would intercept "SET search_path" (see shared/database.py event listener)
os.environ["DISABLE_RATE_LIMIT"] = "1"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from alembic.config import Config
from alembic import command

from main import app
from models.public.user import User, UserRole, SubscriptionTier
from services.auth_service import AuthService
from shared.database import Base, get_db

# CRITICAL: Import all models so they're registered with Base.metadata
import models  # This imports all models from models/__init__.py

# ===== DATABASE CONFIGURATION =====

# PostgreSQL Test Database (Docker)
SQLALCHEMY_TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://stoflow_test:test_password_123@localhost:5434/stoflow_test"
)

# Create engine for PostgreSQL
engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    pool_pre_ping=True,  # Vérifie la connexion avant usage
    echo=False,  # Pas de logs SQL pendant les tests
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ===== SESSION SCOPE FIXTURES =====

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """
    Fixture session-scope pour setup/teardown de la base de données de test.

    Exécuté UNE SEULE FOIS au début de la session de test:
    1. Applique toutes les migrations Alembic (structure = prod)
    2. Crée les schemas user_1, user_2 pour tests multi-tenant
    3. Cleanup complet à la fin de tous les tests
    """
    print("\n🚀 Setting up test database...")

    # Vérifier que la DB est accessible
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
            print("✅ Database connection successful")
    except Exception as e:
        print(f"❌ Cannot connect to test database: {e}")
        print(f"   URL: {SQLALCHEMY_TEST_DATABASE_URL}")
        print("\n💡 Start the test database with:")
        print("   docker-compose -f docker-compose.test.yml up -d")
        sys.exit(1)

    # Appliquer les migrations Alembic pour créer la structure identique à prod/dev
    print("📦 Applying Alembic migrations...")
    try:
        # Configurer Alembic pour utiliser la DB de test
        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", SQLALCHEMY_TEST_DATABASE_URL)

        # Appliquer toutes les migrations jusqu'à la version HEAD
        # Cela crée:
        # - Schema public (users, subscription_quotas, clothing_prices)
        # - Schema product_attributes (brands, categories, colors, conditions, etc.)
        # - Schema template_tenant (products, product_images, vinted_products, etc.)
        command.upgrade(alembic_cfg, "head")
        print("✅ Alembic migrations applied")
    except Exception as e:
        print(f"⚠️  Error applying migrations: {e}")
        raise

    # Créer les schemas user_1, user_2, user_3 pour les tests en clonant template_tenant
    # NOTE (2025-12-10): On clone la structure depuis template_tenant pour garantir
    # que les schemas de test ont EXACTEMENT la même structure que ceux créés en production
    print("🏗️  Creating user schemas by cloning template_tenant...")
    with engine.connect() as conn:
        for user_id in [1, 2, 3]:
            schema_name = f"user_{user_id}"
            print(f"   Creating {schema_name}...")

            # DROP et recréer le schema pour garantir la structure à jour
            # (les migrations peuvent avoir modifié template_tenant)
            conn.execute(text(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE"))
            conn.execute(text(f"CREATE SCHEMA {schema_name}"))

            # Cloner dynamiquement toutes les tables depuis template_tenant
            # LIKE ... INCLUDING ALL copie la structure + indexes + constraints + defaults
            # NOTE (2026-01-14): Liste dynamique au lieu de hardcodée pour éviter les oublis
            # lors de l'ajout de nouvelles tables (ebay_*, etsy_*, etc.)
            result = conn.execute(text("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'template_tenant'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result]
            for table_name in tables:
                conn.execute(text(f"""
                    CREATE TABLE {schema_name}.{table_name}
                    (LIKE template_tenant.{table_name} INCLUDING ALL)
                """))

            print(f"   ✅ {schema_name} created with {len(tables)} tables")

        conn.commit()
        print("✅ User schemas created (user_1, user_2, user_3)")

    print("✅ Test database ready!\n")

    yield  # Tests run here

    # Cleanup après TOUS les tests
    print("\n🧹 Cleaning up test database (session teardown)...")
    # NOTE (2025-12-09): On ne DROP PAS les schemas user_1/user_2 car ils seront
    # réutilisés à la prochaine session de tests. Le cleanup_data fixture vide déjà
    # les données entre chaque test.
    print("✅ Session cleanup complete")


# ===== FUNCTION SCOPE FIXTURES =====

@pytest.fixture(scope="function")
def db_session():
    """
    Fixture pour créer une session de base de données de test.

    Cette fixture (function-scope):
    - Fournit une session DB propre pour chaque test
    - Les données sont nettoyées par cleanup_data (TRUNCATE) après chaque test
    - Les tables existent déjà (créées par setup_test_database)
    """
    # Créer une session
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        # NOTE: Ne PAS faire de rollback() ici !
        # Le cleanup_data fixture utilise TRUNCATE pour nettoyer les données.
        # Un rollback() ici annulerait les commits du test, et le cleanup ne verrait aucune donnée.
        session.close()


def _run_cleanup():
    """
    Fonction de cleanup partagée pour nettoyer les données de test.

    Supprime toutes les données des tables en respectant l'ordre des FK.
    """
    # CRITICAL: Créer une NOUVELLE session indépendante pour le cleanup
    # Cela évite les conflits avec la session du test en cours
    cleanup_session = TestingSessionLocal()
    print("\n[CLEANUP] Starting cleanup...")

    try:
        # IMPORTANT: L'ordre est crucial pour respecter les Foreign Keys

        # 1. Supprimer d'abord les données dans les schemas user (jobs, produits, images)
        # NOTE: Les schemas user_X peuvent ne pas exister pour les tests qui ne les utilisent pas
        # NOTE (2026-01-09): marketplace_tasks removed - WebSocket replaced polling
        for user_id in [1, 2, 3]:
            schema = f"user_{user_id}"
            # Execute each TRUNCATE separately to avoid cascading failures
            tables_to_truncate = [
                "marketplace_jobs",
                "batch_jobs",
                "vinted_products",
                "products",
                "product_images",
                "ai_generation_logs",
                "publication_history"
            ]
            for table in tables_to_truncate:
                try:
                    cleanup_session.execute(text(f"TRUNCATE TABLE {schema}.{table} RESTART IDENTITY CASCADE"))
                    cleanup_session.commit()
                except Exception:
                    cleanup_session.rollback()
                    # Table may not exist, continue to next

        # 2. Supprimer users et ai_credits (FK)
        # NOTE: Ne PAS utiliser CASCADE car cela supprimerait subscription_quotas
        try:
            cleanup_session.execute(text("TRUNCATE TABLE public.ai_credits RESTART IDENTITY CASCADE"))
            cleanup_session.execute(text("TRUNCATE TABLE public.users RESTART IDENTITY CASCADE"))
            cleanup_session.commit()
            print("[CLEANUP] Users cleaned successfully")
        except Exception as e:
            cleanup_session.rollback()
            print(f"[CLEANUP] ERROR cleaning users: {e}")

        # 3. Supprimer les tables d'attributs (dans product_attributes schema)
        try:
            cleanup_session.execute(text("TRUNCATE TABLE product_attributes.brands CASCADE"))
            cleanup_session.execute(text("TRUNCATE TABLE product_attributes.categories CASCADE"))
            cleanup_session.execute(text("TRUNCATE TABLE product_attributes.colors CASCADE"))
            cleanup_session.execute(text("TRUNCATE TABLE product_attributes.conditions CASCADE"))
            cleanup_session.execute(text("TRUNCATE TABLE product_attributes.sizes_normalized CASCADE"))
            cleanup_session.execute(text("TRUNCATE TABLE product_attributes.sizes_original CASCADE"))
            cleanup_session.execute(text("TRUNCATE TABLE product_attributes.materials CASCADE"))
            cleanup_session.execute(text("TRUNCATE TABLE product_attributes.fits CASCADE"))
            cleanup_session.execute(text("TRUNCATE TABLE product_attributes.genders CASCADE"))
            cleanup_session.execute(text("TRUNCATE TABLE product_attributes.seasons CASCADE"))
            cleanup_session.commit()  # Commit immédiatement après succès
        except Exception:
            cleanup_session.rollback()  # Rollback si erreur

        # 4. Supprimer clothing_prices (table indépendante)
        try:
            cleanup_session.execute(text("TRUNCATE TABLE public.clothing_prices CASCADE"))
            cleanup_session.commit()  # Commit immédiatement après succès
        except Exception:
            cleanup_session.rollback()  # Rollback si erreur

        # 5. Supprimer brand_groups et models (tables pricing)
        try:
            cleanup_session.execute(text("TRUNCATE TABLE public.brand_groups RESTART IDENTITY CASCADE"))
            cleanup_session.commit()
        except Exception:
            cleanup_session.rollback()

        try:
            cleanup_session.execute(text("TRUNCATE TABLE public.models RESTART IDENTITY CASCADE"))
            cleanup_session.commit()
        except Exception:
            cleanup_session.rollback()

        # NOTE: Les tables de référence ne sont PAS truncate car elles contiennent
        # des données seed/fixtures permanentes:
        # - subscription_quotas (FREE, STARTER, PRO, ENTERPRISE)

    except Exception as e:
        cleanup_session.rollback()  # Rollback en cas d'erreur
    finally:
        cleanup_session.close()  # Fermer la session cleanup


@pytest.fixture(scope="function", autouse=True)
def cleanup_data(request):
    """
    Fixture pour nettoyer les données entre chaque test.

    Exécutée automatiquement AVANT et APRÈS chaque test pour:
    - Supprimer toutes les données des tables
    - Garder la structure intacte
    - Éviter les conflits entre tests
    - Garantir un état propre même si la session précédente a crashé

    Note: Le cleanup s'exécute:
    1. AVANT le test (pour nettoyer les données résiduelles)
    2. APRÈS le test (via finalizer, même si le test échoue)
    """
    print(f"\n[FIXTURE cleanup_data] BEFORE test: {request.node.name}")
    # BEFORE: Nettoyer avant chaque test pour garantir un état propre
    # Cela gère le cas où la session précédente a crashé sans cleanup
    _run_cleanup()
    print(f"[FIXTURE cleanup_data] BEFORE cleanup done")

    # Enregistrer le finalizer pour le cleanup APRÈS le test
    request.addfinalizer(_run_cleanup)

    yield  # Test runs here


@pytest.fixture(scope="function")
def client(db_session, test_user):
    """
    Fixture pour créer un client de test FastAPI.

    Override les dépendances get_db et get_user_db pour utiliser la DB de test.
    """
    from api.dependencies import get_user_db

    user, _ = test_user

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    def override_get_user_db():
        """Override get_user_db to use test session and user."""
        try:
            yield db_session, user
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_user_db] = override_get_user_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(db_session: Session):
    """
    Fixture pour créer un utilisateur de test.

    Args:
        db_session: Session de base de données

    Returns:
        tuple: (User, password_plain) - L'utilisateur et son mot de passe en clair
    """
    # S'assurer que les quotas existent
    from sqlalchemy import select
    from models.public.subscription_quota import SubscriptionQuota
    stmt = select(SubscriptionQuota).where(SubscriptionQuota.tier == SubscriptionTier.FREE)
    quota_free = db_session.execute(stmt).scalar_one_or_none()

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

    password_plain = "securepassword123"
    user = User(
        email="admin@test.com",
        hashed_password=AuthService.hash_password(password_plain),
        full_name="Test Admin",
        role=UserRole.ADMIN,
        subscription_tier=SubscriptionTier.FREE,
        subscription_tier_id=quota_free.id,
        is_active=True,
        email_verified=True  # Mark email as verified for tests
        # Note: schema_name is auto-generated as "user_{id}" after commit
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # Retourner l'utilisateur ET le mot de passe en clair (pour les tests de login)
    return user, password_plain


@pytest.fixture(scope="function")
def auth_headers(client: TestClient, test_user):
    """
    Fixture pour obtenir les headers d'authentification.

    Args:
        client: Client de test FastAPI
        test_user: Tuple (User, password_plain)

    Returns:
        dict: Headers avec Authorization Bearer token
    """
    user, password = test_user

    # Login pour obtenir le token
    response = client.post(
        "/api/auth/login",
        json={
            "email": user.email,
            "password": password
        }
    )

    assert response.status_code == 200, f"Login failed: {response.json()}"
    data = response.json()

    return {
        "Authorization": f"Bearer {data['access_token']}"
    }


@pytest.fixture(scope="function")
def seed_attributes(db_session: Session):
    """
    Fixture pour seed les attributs de produits dans product_attributes schema.

    Crée des données de test pour:
    - brands, categories, colors, conditions, sizes
    - materials, fits, genders, seasons

    Note: Utilise merge() pour éviter les erreurs de duplicate key si les données
    existent déjà (migrations Alembic peuvent avoir seed des données).
    """
    from models.public.brand import Brand
    from models.public.category import Category
    from models.public.color import Color
    from models.public.condition import Condition
    from models.public.size_normalized import SizeNormalized
    from models.public.material import Material
    from models.public.fit import Fit
    from models.public.gender import Gender
    from models.public.season import Season

    # Brands - use merge to avoid duplicates
    brands = [
        Brand(name="Levi's"),
        Brand(name="Nike"),
        Brand(name="Adidas"),
    ]
    for b in brands:
        db_session.merge(b)

    # Categories
    categories = [
        Category(name_en="Jeans", name_fr="Jeans"),
        Category(name_en="Tops", name_fr="Hauts"),
        Category(name_en="Jackets", name_fr="Vestes"),
    ]
    for c in categories:
        db_session.merge(c)

    # Colors
    colors = [
        Color(name_en="Blue", name_fr="Bleu"),
        Color(name_en="Black", name_fr="Noir"),
        Color(name_en="White", name_fr="Blanc"),
    ]
    for c in colors:
        db_session.merge(c)

    # Conditions
    conditions = [
        Condition(note=10, name_en="NEW_WITH_TAGS", name_fr="Neuf avec étiquettes"),
        Condition(note=8, name_en="EXCELLENT", name_fr="Excellent état"),
        Condition(note=6, name_en="GOOD", name_fr="Bon état"),
        Condition(note=4, name_en="FAIR", name_fr="État correct"),
    ]
    for c in conditions:
        db_session.merge(c)

    # Sizes
    sizes = [
        SizeNormalized(name_en="XS", name_fr="XS"),
        SizeNormalized(name_en="S", name_fr="S"),
        SizeNormalized(name_en="M", name_fr="M"),
        SizeNormalized(name_en="L", name_fr="L"),
        SizeNormalized(name_en="XL", name_fr="XL"),
    ]
    for s in sizes:
        db_session.merge(s)

    # Materials
    materials = [
        Material(name_en="Cotton", name_fr="Coton"),
        Material(name_en="Polyester", name_fr="Polyester"),
        Material(name_en="Denim", name_fr="Denim"),
    ]
    for m in materials:
        db_session.merge(m)

    # Fits
    fits = [
        Fit(name_en="Slim", name_fr="Slim"),
        Fit(name_en="Regular", name_fr="Regular"),
        Fit(name_en="Loose", name_fr="Loose"),
    ]
    for f in fits:
        db_session.merge(f)

    # Genders
    genders = [
        Gender(name_en="Men", name_fr="Homme"),
        Gender(name_en="Women", name_fr="Femme"),
        Gender(name_en="Unisex", name_fr="Unisexe"),
    ]
    for g in genders:
        db_session.merge(g)

    # Seasons
    seasons = [
        Season(name_en="All-Season", name_fr="Toutes saisons"),
        Season(name_en="Summer", name_fr="Été"),
        Season(name_en="Winter", name_fr="Hiver"),
    ]
    for s in seasons:
        db_session.merge(s)

    db_session.commit()

    yield

    # Cleanup is handled by cleanup_data fixture


@pytest.fixture(scope="function")
def test_product(db_session: Session, test_user):
    """
    Fixture to create a test product in the user's schema.

    Args:
        db_session: Database session
        test_user: Tuple (User, password_plain)

    Returns:
        Product: Test product with basic attributes
    """
    from models.user.product import Product
    from sqlalchemy import text

    user, _ = test_user

    # Set search path to user schema
    db_session.execute(text(f"SET search_path TO user_{user.id}, public"))

    product = Product(
        title="Test Product",
        description="Test description",
        price=25.99,
        stock_quantity=10,
        category="T-shirt",
        brand="Nike",
        condition="EXCELLENT",
        size_original="M",
        color="Blue",
        material="Cotton",
        gender="Men",
        images=[
            {"url": "https://example.com/img1.jpg", "order": 0},
            {"url": "https://example.com/img2.jpg", "order": 1}
        ]
    )

    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)

    return product
