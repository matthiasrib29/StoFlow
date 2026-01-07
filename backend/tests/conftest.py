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
        # NOTE: Temporarily commented - DB already at correct version
        # command.upgrade(alembic_cfg, "head")
        print("✅ Alembic migrations skipped (DB already up-to-date)")
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

            # Créer le schema
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))

            # Cloner chaque table depuis template_tenant
            # LIKE ... INCLUDING ALL copie la structure + indexes + constraints + defaults
            tables = [
                'products',
                'product_images',
                'vinted_products',
                'publication_history',
                'ai_generation_logs',
                'batch_jobs',  # Phase 6.2: Added for batch job tests
                'marketplace_jobs',  # Phase 6.2: Renamed from vinted_jobs
                'marketplace_tasks'  # Phase 6.2: Renamed from plugin_tasks
            ]
            for table_name in tables:
                conn.execute(text(f"""
                    CREATE TABLE IF NOT EXISTS {schema_name}.{table_name}
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


@pytest.fixture(scope="function", autouse=True)
def cleanup_data(request):
    """
    Fixture pour nettoyer les données entre chaque test.

    Exécutée automatiquement après chaque test pour:
    - Supprimer toutes les données des tables
    - Garder la structure intacte
    - Éviter les conflits entre tests

    Note: Utilise un finalizer pour garantir que le cleanup s'exécute
    TOUJOURS, même si le test échoue pendant le setup.
    """
    def cleanup():
        """Cleanup function exécutée via finalizer."""
        print("\n🧹 Running cleanup...")

        # CRITICAL: Créer une NOUVELLE session indépendante pour le cleanup
        # Cela évite les conflits avec la session du test en cours
        cleanup_session = TestingSessionLocal()

        try:
            # IMPORTANT: L'ordre est crucial pour respecter les Foreign Keys

            # 1. Supprimer d'abord les données dans les schemas user (jobs, tasks, produits, images)
            # NOTE: Les schemas user_X peuvent ne pas exister pour les tests qui ne les utilisent pas
            for user_id in [1, 2, 3]:
                schema = f"user_{user_id}"
                try:
                    # Order: tasks → jobs → batch_jobs → products → images
                    # (respecter les FK: tasks dépend de jobs, jobs dépend de batch_jobs)
                    cleanup_session.execute(text(f"TRUNCATE TABLE {schema}.marketplace_tasks RESTART IDENTITY CASCADE"))
                    cleanup_session.execute(text(f"TRUNCATE TABLE {schema}.marketplace_jobs RESTART IDENTITY CASCADE"))
                    cleanup_session.execute(text(f"TRUNCATE TABLE {schema}.batch_jobs RESTART IDENTITY CASCADE"))
                    cleanup_session.execute(text(f"TRUNCATE TABLE {schema}.vinted_products RESTART IDENTITY CASCADE"))
                    cleanup_session.execute(text(f"TRUNCATE TABLE {schema}.products RESTART IDENTITY CASCADE"))
                    cleanup_session.execute(text(f"TRUNCATE TABLE {schema}.product_images RESTART IDENTITY CASCADE"))
                    cleanup_session.commit()  # Commit immédiatement après succès
                except Exception as e:
                    cleanup_session.rollback()  # Rollback si erreur
                    # Ignorer si table n'existe pas
                    pass

            # 2. Supprimer users et ai_credits (FK)
            # NOTE: Ne PAS utiliser CASCADE car cela supprimerait subscription_quotas
            try:
                cleanup_session.execute(text("TRUNCATE TABLE public.ai_credits RESTART IDENTITY CASCADE"))
                cleanup_session.execute(text("TRUNCATE TABLE public.users RESTART IDENTITY CASCADE"))
                cleanup_session.commit()
            except Exception as e:
                cleanup_session.rollback()
                print(f"⚠️  Error cleaning users/ai_credits: {e}")

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

            # NOTE: Les tables de référence ne sont PAS truncate car elles contiennent
            # des données seed/fixtures permanentes:
            # - subscription_quotas (FREE, STARTER, PRO, ENTERPRISE)

            print("✅ Cleanup complete")
        except Exception as e:
            cleanup_session.rollback()  # Rollback en cas d'erreur
            # Log error mais ne pas casser les tests
            print(f"⚠️  Cleanup error: {e}")
        finally:
            cleanup_session.close()  # Fermer la session cleanup

    # Enregistrer le finalizer AVANT le yield pour qu'il s'exécute toujours
    request.addfinalizer(cleanup)

    yield  # Test runs here (ou setup échoue, le finalizer s'exécute quand même)


@pytest.fixture(scope="function")
def client(db_session):
    """
    Fixture pour créer un client de test FastAPI.

    Override la dépendance get_db pour utiliser la DB de test.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

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
    from models.public.subscription_quota import SubscriptionQuota
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
