# Week 0 : Setup Infrastructure - Guide Détaillé

**Projet :** Stoflow Backend
**Durée :** 5 jours (adaptable selon disponibilité)
**Objectif :** Mettre en place l'environnement de développement complet et fonctionnel

---

## 📋 Vue d'Ensemble Week 0

### Ce qui sera accompli
- ✅ Structure projet backend organisée
- ✅ Environnement Python 3.12 avec venv
- ✅ PostgreSQL + Redis via Docker Compose
- ✅ Configuration Alembic pour migrations
- ✅ Dépendances Python installées (FastAPI, SQLAlchemy, etc.)
- ✅ Git configuré avec .gitignore adapté
- ✅ Tests de connexion DB et Redis
- ✅ Documentation setup dans README.md

### Prérequis Validés
- ✅ OS : Linux (Ubuntu/Debian)
- ✅ Python 3.12.3
- ✅ Node.js 18.19.1 (pour futurs besoins frontend)
- ✅ Docker 29.0.4
- ✅ Docker Compose v2.39.2
- ✅ Code Vinted partiel existant (à migrer)

---

## 📅 Planning Détaillé

### Jour 1-2 : Setup Projet Backend (6-8h)

#### Étape 1.1 : Structure de Répertoires (30 min)

**Objectif :** Créer l'architecture de dossiers propre et scalable

```bash
cd /home/maribeiro/Stoflow/Stoflow_BackEnd

# Créer la structure complète
mkdir -p api/{routes,middleware,dependencies}
mkdir -p models/{public,tenant}
mkdir -p services/{vinted,ai,monitoring}
mkdir -p repositories
mkdir -p workers
mkdir -p migrations
mkdir -p shared
mkdir -p tests/{unit,integration,e2e}
mkdir -p scripts
mkdir -p docs
```

**Résultat attendu :**
```
Stoflow_BackEnd/
├── api/
│   ├── __init__.py
│   ├── main.py                    # Point d'entrée FastAPI
│   ├── routes/                    # Endpoints API
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── products.py
│   │   ├── vinted.py
│   │   └── ai.py
│   ├── middleware/                # Middlewares custom
│   │   ├── __init__.py
│   │   ├── tenant.py              # Isolation multi-tenant
│   │   └── auth.py                # Vérification JWT
│   └── dependencies/              # Dependencies FastAPI
│       ├── __init__.py
│       ├── database.py
│       └── auth.py
├── models/
│   ├── __init__.py
│   ├── public/                    # Models schema public
│   │   ├── __init__.py
│   │   ├── tenant.py
│   │   ├── user.py
│   │   ├── subscription.py
│   │   └── platform_mapping.py
│   └── tenant/                    # Models schema client_X
│       ├── __init__.py
│       ├── product.py
│       ├── vinted_product.py
│       └── publication_history.py
├── services/
│   ├── __init__.py
│   ├── auth_service.py
│   ├── tenant_service.py
│   ├── rate_limiter.py
│   ├── vinted/                    # Code Vinted à migrer ici
│   │   ├── __init__.py
│   │   ├── vinted_client.py
│   │   ├── vinted_converter.py
│   │   ├── vinted_mapping.py
│   │   ├── vinted_pricing.py
│   │   └── vinted_validator.py
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── openai_service.py
│   │   └── prompt_templates.py
│   └── monitoring/
│       ├── __init__.py
│       └── logger.py
├── repositories/
│   ├── __init__.py
│   ├── base_repository.py
│   ├── tenant_repository.py
│   ├── user_repository.py
│   ├── product_repository.py
│   └── vinted_repository.py
├── workers/
│   ├── __init__.py
│   └── vinted_worker.py           # RQ worker publication
├── migrations/                    # Alembic
│   ├── alembic.ini
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── shared/
│   ├── __init__.py
│   ├── config.py                  # Configuration centralisée
│   ├── database.py                # Session DB
│   ├── redis_client.py            # Client Redis
│   └── logging_setup.py           # Configuration logs
├── tests/
│   ├── __init__.py
│   ├── conftest.py                # Fixtures pytest
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_auth_service.py
│   │   └── test_rate_limiter.py
│   ├── integration/
│   │   ├── __init__.py
│   │   ├── test_api_products.py
│   │   └── test_vinted_publish.py
│   └── e2e/
│       ├── __init__.py
│       └── test_publication_flow.py
├── scripts/
│   ├── __init__.py
│   ├── create_demo_tenant.py      # Script création tenant test
│   ├── test_db_connection.py      # Test connexion PostgreSQL
│   ├── test_redis_connection.py   # Test connexion Redis
│   └── migrate_vinted_code.py     # Helper migration code existant
├── docs/
│   ├── API.md                     # Documentation API
│   ├── DATABASE.md                # Schéma BDD
│   └── DEVELOPMENT.md             # Guide dev
├── .env.example                   # Template variables env
├── .gitignore
├── requirements.txt               # Dépendances Python
├── requirements-dev.txt           # Dépendances dev (tests, etc.)
├── docker-compose.yml             # PostgreSQL + Redis
├── README.md                      # Documentation principale
├── BUSINESS_PLAN.md               # (déjà existant)
├── MVP1_ROADMAP.md                # (déjà existant)
└── WEEK0_SETUP.md                 # (ce document)
```

**Actions :**
```bash
# Créer tous les __init__.py nécessaires
touch api/__init__.py
touch api/routes/__init__.py
touch api/middleware/__init__.py
touch api/dependencies/__init__.py
touch models/__init__.py
touch models/public/__init__.py
touch models/tenant/__init__.py
touch services/__init__.py
touch services/vinted/__init__.py
touch services/ai/__init__.py
touch services/monitoring/__init__.py
touch repositories/__init__.py
touch workers/__init__.py
touch shared/__init__.py
touch tests/__init__.py
touch tests/unit/__init__.py
touch tests/integration/__init__.py
touch tests/e2e/__init__.py
touch scripts/__init__.py
```

---

#### Étape 1.2 : Environnement Virtuel Python (15 min)

**Objectif :** Isoler les dépendances Python du projet

```bash
cd /home/maribeiro/Stoflow/Stoflow_BackEnd

# Créer environnement virtuel avec Python 3.12
python3 -m venv venv

# Activer l'environnement
source venv/bin/activate

# Vérifier version Python dans le venv
python --version  # Doit afficher Python 3.12.3

# Mettre à jour pip
pip install --upgrade pip setuptools wheel
```

**⚠️ Important :** À chaque nouvelle session terminal :
```bash
cd /home/maribeiro/Stoflow/Stoflow_BackEnd
source venv/bin/activate
```

**Vérification :**
```bash
which python  # Doit pointer vers .../Stoflow_BackEnd/venv/bin/python
```

---

#### Étape 1.3 : Fichier requirements.txt (30 min)

**Objectif :** Définir toutes les dépendances Python nécessaires

**Créer `requirements.txt` :**
```txt
# Web Framework
fastapi==0.115.0
uvicorn[standard]==0.32.0
python-multipart==0.0.12

# Database
sqlalchemy==2.0.35
alembic==1.14.0
psycopg2-binary==2.9.9

# Redis & Workers
redis==5.2.0
rq==2.0.0

# Authentication & Security
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-dotenv==1.0.1
pydantic==2.10.1
pydantic-settings==2.6.1

# OpenAI
openai==1.54.3

# HTTP Client (pour Vinted)
httpx==0.27.2
requests==2.32.3

# Utils
python-dateutil==2.9.0
pillow==11.0.0
```

**Créer `requirements-dev.txt` :**
```txt
# Testing
pytest==8.3.3
pytest-asyncio==0.24.0
pytest-cov==6.0.0
httpx==0.27.2  # Pour tests API

# Code Quality
black==24.10.0
flake8==7.1.1
mypy==1.13.0
isort==5.13.2

# Development Tools
ipython==8.29.0
```

**Actions :**
```bash
# Installer dépendances principales
pip install -r requirements.txt

# Installer dépendances dev
pip install -r requirements-dev.txt

# Vérifier installation
pip list | grep fastapi
pip list | grep sqlalchemy
pip list | grep redis
```

---

#### Étape 1.4 : Configuration Git (45 min)

**Objectif :** Initialiser le repo Git avec bonnes pratiques

**Créer `.gitignore` :**
```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/
build/
dist/
*.egg-info/
.eggs/

# PyCharm / IDEs
.idea/
.vscode/
*.swp
*.swo
*~

# Environment variables
.env
.env.local
.env.*.local

# Database
*.db
*.sqlite3
*.sql
pgdata/

# Logs
logs/
*.log

# OS
.DS_Store
Thumbs.db

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/

# Alembic
alembic/versions/*.pyc

# Temporary files
tmp/
temp/
*.tmp

# Secrets
secrets/
*.pem
*.key
credentials.json

# Docker
docker-compose.override.yml
```

**Initialiser Git (si pas déjà fait) :**
```bash
cd /home/maribeiro/Stoflow/Stoflow_BackEnd

# Vérifier si Git existe déjà
git status

# Si pas de repo Git, initialiser
git init

# Configurer user (si pas déjà fait globalement)
git config user.name "Ton Nom"
git config user.email "ton@email.com"

# Ajouter .gitignore
git add .gitignore

# Premier commit
git add .
git commit -m "chore: initial project structure with Week 0 setup"

# Créer branches
git branch develop
git checkout develop
```

**Structure branches recommandée :**
```
main        → Production (stable)
develop     → Développement (branch principale dev)
feature/*   → Nouvelles features
fix/*       → Bug fixes
```

---

#### Étape 1.5 : Configuration Docker Compose (1h)

**Objectif :** Configurer PostgreSQL et Redis pour le développement

**Créer `docker-compose.yml` :**
```yaml
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    container_name: stoflow_postgres
    environment:
      POSTGRES_DB: stoflow_db
      POSTGRES_USER: stoflow_user
      POSTGRES_PASSWORD: stoflow_dev_password_2024
      POSTGRES_HOST_AUTH_METHOD: scram-sha-256
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init_db.sql:/docker-entrypoint-initdb.d/init_db.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U stoflow_user -d stoflow_db"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - stoflow_network

  # Redis Cache & Queue
  redis:
    image: redis:7-alpine
    container_name: stoflow_redis
    command: redis-server --appendonly yes --requirepass stoflow_redis_dev_pass
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - stoflow_network

  # pgAdmin (optionnel, pour visualiser la BDD)
  pgadmin:
    image: dpage/pgadmin4:latest
    container_name: stoflow_pgadmin
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@stoflow.local
      PGADMIN_DEFAULT_PASSWORD: admin
      PGADMIN_CONFIG_SERVER_MODE: 'False'
    ports:
      - "5050:80"
    depends_on:
      - postgres
    networks:
      - stoflow_network
    profiles:
      - tools  # Démarrer avec: docker compose --profile tools up

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local

networks:
  stoflow_network:
    driver: bridge
```

**Créer script d'initialisation `scripts/init_db.sql` :**
```sql
-- Script d'initialisation PostgreSQL
-- Exécuté automatiquement au premier démarrage

-- Créer schema public (par défaut)
CREATE SCHEMA IF NOT EXISTS public;

-- Commenter pour documentation
COMMENT ON SCHEMA public IS 'Schema partagé pour tables communes (tenants, users, etc.)';

-- Extensions utiles
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- Pour recherche texte

-- Log
DO $$
BEGIN
    RAISE NOTICE 'Database stoflow_db initialized successfully';
END $$;
```

**Actions :**
```bash
# Créer le dossier scripts si pas encore fait
mkdir -p scripts

# Créer init_db.sql (voir contenu ci-dessus)

# Démarrer les services
docker compose up -d postgres redis

# Vérifier les logs
docker compose logs -f postgres
# Attendre message "database system is ready to accept connections"
# Ctrl+C pour quitter les logs

# Vérifier status
docker compose ps
# Les 2 services doivent être "healthy"

# Optionnel : démarrer pgAdmin
docker compose --profile tools up -d pgadmin
# Accéder à http://localhost:5050
# Login: admin@stoflow.local / admin
```

**Commandes utiles Docker Compose :**
```bash
# Démarrer services
docker compose up -d

# Arrêter services
docker compose down

# Voir logs
docker compose logs -f [service_name]

# Redémarrer un service
docker compose restart postgres

# Supprimer volumes (⚠️ PERTE DONNÉES)
docker compose down -v

# Reconstruire images
docker compose build --no-cache
```

---

### Jour 3-4 : Configuration Base (6-8h)

#### Étape 2.1 : Configuration Centralisée (1h)

**Objectif :** Créer le système de configuration avec variables d'environnement

**Créer `.env.example` :**
```bash
# =============================================================================
# STOFLOW BACKEND - CONFIGURATION DÉVELOPPEMENT
# =============================================================================
# Copier ce fichier en .env et adapter les valeurs

# -----------------------------------------------------------------------------
# APPLICATION
# -----------------------------------------------------------------------------
APP_NAME=Stoflow
APP_ENV=development
DEBUG=true
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=1

# -----------------------------------------------------------------------------
# DATABASE - PostgreSQL
# -----------------------------------------------------------------------------
DB_HOST=localhost
DB_PORT=5432
DB_NAME=stoflow_db
DB_USER=stoflow_user
DB_PASSWORD=stoflow_dev_password_2024
DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}

# Pool SQLAlchemy
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600

# -----------------------------------------------------------------------------
# REDIS - Cache & Queue
# -----------------------------------------------------------------------------
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=stoflow_redis_dev_pass
REDIS_DB=0
REDIS_URL=redis://:${REDIS_PASSWORD}@${REDIS_HOST}:${REDIS_PORT}/${REDIS_DB}

# -----------------------------------------------------------------------------
# JWT AUTHENTICATION
# -----------------------------------------------------------------------------
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production-min-32-chars
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Password hashing
PASSWORD_HASH_ROUNDS=12

# -----------------------------------------------------------------------------
# OPENAI - Génération Descriptions
# -----------------------------------------------------------------------------
OPENAI_API_KEY=sk-proj-your-openai-api-key-here
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_MAX_TOKENS=500
OPENAI_TEMPERATURE=0.7

# Cache IA
AI_CACHE_TTL_SECONDS=2592000  # 30 jours
AI_CACHE_ENABLED=true

# -----------------------------------------------------------------------------
# VINTED - Configuration Publication
# -----------------------------------------------------------------------------
VINTED_BASE_URL=https://www.vinted.fr
VINTED_API_URL=https://www.vinted.fr/api/v2

# Rate Limiting
VINTED_RATE_LIMIT_MAX=40
VINTED_RATE_LIMIT_WINDOW_HOURS=2
VINTED_REQUEST_DELAY_MIN_SECONDS=20
VINTED_REQUEST_DELAY_MAX_SECONDS=50

# Retry
VINTED_MAX_RETRIES=3
VINTED_RETRY_DELAY_SECONDS=60

# -----------------------------------------------------------------------------
# LOGGING
# -----------------------------------------------------------------------------
LOG_LEVEL=DEBUG
LOG_FORMAT=detailed
LOG_FILE_ENABLED=true
LOG_FILE_PATH=logs/stoflow.log
LOG_FILE_MAX_BYTES=10485760  # 10MB
LOG_FILE_BACKUP_COUNT=5

# -----------------------------------------------------------------------------
# CORS - Frontend URLs autorisées
# -----------------------------------------------------------------------------
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
CORS_ALLOW_CREDENTIALS=true

# -----------------------------------------------------------------------------
# RQ WORKERS
# -----------------------------------------------------------------------------
RQ_QUEUE_DEFAULT=default
RQ_QUEUE_VINTED=vinted_publications
RQ_QUEUE_AI=ai_generations
RQ_JOB_TIMEOUT=300  # 5 minutes
RQ_RESULT_TTL=3600  # 1 heure

# -----------------------------------------------------------------------------
# MULTI-TENANT
# -----------------------------------------------------------------------------
TENANT_SCHEMA_PREFIX=client_
TENANT_MAX_SCHEMAS=1000

# -----------------------------------------------------------------------------
# MONITORING & METRICS
# -----------------------------------------------------------------------------
SENTRY_DSN=  # À remplir en production
SENTRY_ENVIRONMENT=development
SENTRY_TRACES_SAMPLE_RATE=0.1
```

**Créer `.env` (copie pour développement) :**
```bash
cp .env.example .env
# Éditer .env et remplacer les valeurs sensibles si nécessaire
```

**Créer `shared/config.py` :**
```python
"""
Configuration centralisée de l'application Stoflow.
Charge les variables d'environnement et fournit un objet Settings.
"""
from functools import lru_cache
from typing import List, Optional

from pydantic import Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration application via variables d'environnement."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "Stoflow"
    app_env: str = Field(default="development", pattern="^(development|staging|production)$")
    debug: bool = True
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 1

    # Database
    database_url: PostgresDsn
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_timeout: int = 30
    db_pool_recycle: int = 3600

    # Redis
    redis_url: RedisDsn

    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 1440
    password_hash_rounds: int = 12

    # OpenAI
    openai_api_key: str
    openai_model: str = "gpt-4-turbo-preview"
    openai_max_tokens: int = 500
    openai_temperature: float = 0.7
    ai_cache_ttl_seconds: int = 2592000
    ai_cache_enabled: bool = True

    # Vinted
    vinted_base_url: str = "https://www.vinted.fr"
    vinted_api_url: str = "https://www.vinted.fr/api/v2"
    vinted_rate_limit_max: int = 40
    vinted_rate_limit_window_hours: int = 2
    vinted_request_delay_min_seconds: int = 20
    vinted_request_delay_max_seconds: int = 50
    vinted_max_retries: int = 3
    vinted_retry_delay_seconds: int = 60

    # Logging
    log_level: str = "DEBUG"
    log_format: str = "detailed"
    log_file_enabled: bool = True
    log_file_path: str = "logs/stoflow.log"
    log_file_max_bytes: int = 10485760
    log_file_backup_count: int = 5

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:8080"
    cors_allow_credentials: bool = True

    # RQ Workers
    rq_queue_default: str = "default"
    rq_queue_vinted: str = "vinted_publications"
    rq_queue_ai: str = "ai_generations"
    rq_job_timeout: int = 300
    rq_result_ttl: int = 3600

    # Multi-tenant
    tenant_schema_prefix: str = "client_"
    tenant_max_schemas: int = 1000

    # Monitoring
    sentry_dsn: Optional[str] = None
    sentry_environment: str = "development"
    sentry_traces_sample_rate: float = 0.1

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str) -> List[str]:
        """Parse CORS origins string to list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.app_env == "production"


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Using lru_cache ensures settings are loaded only once.
    """
    return Settings()


# Instance globale pour import facile
settings = get_settings()
```

**Tester la configuration :**
```python
# Créer scripts/test_config.py
"""Test configuration loading."""
from shared.config import settings


def test_config():
    """Test que la configuration se charge correctement."""
    print("=== STOFLOW CONFIGURATION ===")
    print(f"App Name: {settings.app_name}")
    print(f"Environment: {settings.app_env}")
    print(f"Debug: {settings.debug}")
    print(f"\nDatabase URL: {settings.database_url}")
    print(f"Redis URL: {settings.redis_url}")
    print(f"\nJWT Secret (first 10 chars): {settings.jwt_secret_key[:10]}...")
    print(f"OpenAI API Key (first 10 chars): {settings.openai_api_key[:10]}...")
    print(f"\nVinted Rate Limit: {settings.vinted_rate_limit_max} req / {settings.vinted_rate_limit_window_hours}h")
    print(f"CORS Origins: {settings.cors_origins}")
    print("\n✅ Configuration loaded successfully!")


if __name__ == "__main__":
    test_config()
```

```bash
# Exécuter le test
python scripts/test_config.py
```

---

#### Étape 2.2 : Configuration Database & Redis Clients (1h30)

**Créer `shared/database.py` :**
```python
"""
Database session management avec support multi-tenant.
"""
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from shared.config import settings

# Base pour models SQLAlchemy
Base = declarative_base()

# Engine PostgreSQL (connexion globale)
engine = create_engine(
    str(settings.database_url),
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_timeout=settings.db_pool_timeout,
    pool_recycle=settings.db_pool_recycle,
    pool_pre_ping=True,  # Vérifier connexion avant usage
    echo=settings.debug,  # Log SQL queries en mode debug
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Event listener for database connection (future use)."""
    pass


def get_db() -> Generator[Session, None, None]:
    """
    Dependency pour FastAPI : fournit une session database.

    Usage dans routes:
        @app.get("/api/endpoint")
        def my_endpoint(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context manager pour sessions DB hors FastAPI.

    Usage:
        with get_db_context() as db:
            user = db.query(User).first()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def set_tenant_schema(db: Session, tenant_id: int) -> None:
    """
    Configure le search_path PostgreSQL pour isoler le tenant.

    Args:
        db: Session SQLAlchemy
        tenant_id: ID du tenant
    """
    schema_name = f"{settings.tenant_schema_prefix}{tenant_id}"
    db.execute(text(f"SET search_path TO {schema_name}, public"))


def create_tenant_schema(tenant_id: int) -> None:
    """
    Crée un nouveau schema PostgreSQL pour un tenant.

    Args:
        tenant_id: ID du tenant
    """
    schema_name = f"{settings.tenant_schema_prefix}{tenant_id}"

    with get_db_context() as db:
        # Créer le schema
        db.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))

        # Ajouter commentaire pour documentation
        db.execute(
            text(f"COMMENT ON SCHEMA {schema_name} IS 'Tenant {tenant_id} data isolation'")
        )

        db.commit()


def check_database_connection() -> bool:
    """
    Vérifie la connexion à la base de données.

    Returns:
        True si connexion OK, False sinon
    """
    try:
        with get_db_context() as db:
            db.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
```

**Créer `shared/redis_client.py` :**
```python
"""
Redis client pour cache et queue RQ.
"""
from typing import Any, Optional

import redis
from redis import Redis
from rq import Queue

from shared.config import settings


class RedisClient:
    """Wrapper pour client Redis."""

    def __init__(self):
        """Initialize Redis connection."""
        self._client: Optional[Redis] = None
        self._queues: dict[str, Queue] = {}

    @property
    def client(self) -> Redis:
        """Get or create Redis client."""
        if self._client is None:
            self._client = redis.from_url(
                str(settings.redis_url),
                decode_responses=True,
            )
        return self._client

    def ping(self) -> bool:
        """
        Test Redis connection.

        Returns:
            True if connection OK, False otherwise
        """
        try:
            return self.client.ping()
        except Exception as e:
            print(f"❌ Redis connection failed: {e}")
            return False

    def get_queue(self, queue_name: str) -> Queue:
        """
        Get RQ queue by name.

        Args:
            queue_name: Name of the queue

        Returns:
            RQ Queue instance
        """
        if queue_name not in self._queues:
            self._queues[queue_name] = Queue(
                queue_name,
                connection=self.client,
            )
        return self._queues[queue_name]

    def set_with_ttl(self, key: str, value: Any, ttl_seconds: int) -> bool:
        """
        Set value with TTL in Redis.

        Args:
            key: Redis key
            value: Value to store
            ttl_seconds: Time to live in seconds

        Returns:
            True if success
        """
        try:
            return self.client.setex(key, ttl_seconds, value)
        except Exception as e:
            print(f"❌ Redis set failed: {e}")
            return False

    def get(self, key: str) -> Optional[str]:
        """
        Get value from Redis.

        Args:
            key: Redis key

        Returns:
            Value or None if not found
        """
        try:
            return self.client.get(key)
        except Exception as e:
            print(f"❌ Redis get failed: {e}")
            return None

    def delete(self, key: str) -> bool:
        """
        Delete key from Redis.

        Args:
            key: Redis key

        Returns:
            True if deleted
        """
        try:
            return bool(self.client.delete(key))
        except Exception as e:
            print(f"❌ Redis delete failed: {e}")
            return False

    def close(self) -> None:
        """Close Redis connection."""
        if self._client:
            self._client.close()
            self._client = None


# Instance globale
redis_client = RedisClient()


def get_redis() -> Redis:
    """
    Dependency pour FastAPI : fournit le client Redis.

    Usage dans routes:
        @app.get("/api/endpoint")
        def my_endpoint(redis: Redis = Depends(get_redis)):
            ...
    """
    return redis_client.client


def check_redis_connection() -> bool:
    """
    Vérifie la connexion Redis.

    Returns:
        True si connexion OK, False sinon
    """
    return redis_client.ping()
```

---

#### Étape 2.3 : Configuration Logging (45 min)

**Créer `shared/logging_setup.py` :**
```python
"""
Configuration centralisée du système de logging.
"""
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from shared.config import settings


def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
) -> logging.Logger:
    """
    Configure le système de logging.

    Args:
        log_level: Niveau de log (DEBUG, INFO, WARNING, ERROR)
        log_file: Chemin du fichier log (optionnel)

    Returns:
        Logger configuré
    """
    level = log_level or settings.log_level

    # Format des logs
    if settings.log_format == "detailed":
        log_format = (
            "[%(asctime)s] %(levelname)-8s "
            "%(name)s:%(funcName)s:%(lineno)d - %(message)s"
        )
    else:
        log_format = "[%(asctime)s] %(levelname)-8s - %(message)s"

    date_format = "%Y-%m-%d %H:%M:%S"

    # Configurer le logger racine
    logger = logging.getLogger("stoflow")
    logger.setLevel(getattr(logging, level.upper()))

    # Supprimer handlers existants
    logger.handlers.clear()

    # Handler console (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    console_handler.setFormatter(
        logging.Formatter(log_format, datefmt=date_format)
    )
    logger.addHandler(console_handler)

    # Handler fichier (si activé)
    if settings.log_file_enabled:
        file_path = Path(log_file or settings.log_file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            file_path,
            maxBytes=settings.log_file_max_bytes,
            backupCount=settings.log_file_backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(getattr(logging, level.upper()))
        file_handler.setFormatter(
            logging.Formatter(log_format, datefmt=date_format)
        )
        logger.addHandler(file_handler)

    # Ne pas propager aux loggers parents
    logger.propagate = False

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Récupère un logger avec le nom spécifié.

    Args:
        name: Nom du logger (généralement __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(f"stoflow.{name}")


# Logger principal de l'application
logger = setup_logging()
```

**Tester le logging :**
```python
# Créer scripts/test_logging.py
"""Test logging configuration."""
from shared.logging_setup import get_logger

logger = get_logger(__name__)


def test_logging():
    """Test différents niveaux de log."""
    logger.debug("🔍 This is a DEBUG message")
    logger.info("ℹ️  This is an INFO message")
    logger.warning("⚠️  This is a WARNING message")
    logger.error("❌ This is an ERROR message")

    try:
        1 / 0
    except ZeroDivisionError:
        logger.exception("💥 This is an EXCEPTION with traceback")

    print("\n✅ Logging test completed. Check logs/ directory.")


if __name__ == "__main__":
    test_logging()
```

```bash
# Créer dossier logs
mkdir -p logs

# Exécuter test
python scripts/test_logging.py

# Vérifier le fichier log
cat logs/stoflow.log
```

---

#### Étape 2.4 : Configuration Alembic (1h30)

**Objectif :** Configurer Alembic pour gérer les migrations multi-schema

**Initialiser Alembic :**
```bash
cd /home/maribeiro/Stoflow/Stoflow_BackEnd

# Activer venv
source venv/bin/activate

# Initialiser Alembic dans le dossier migrations/
alembic init migrations

# Vérifier structure créée
ls -la migrations/
```

**Éditer `alembic.ini` :**
```ini
# Alembic configuration for Stoflow multi-tenant database

[alembic]
# Path to migration scripts
script_location = migrations

# Template for generating migration file names
file_template = %%(year)d%%(month).2d%%(day).2d_%%(hour).2d%%(minute).2d_%%(slug)s

# Timezone for migration timestamps
timezone = Europe/Paris

# Logging configuration
[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = INFO
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stdout,)
level = NOTSET
formatter = generic

[formatter_generic]
format = [%(asctime)s] %(levelname)-8s %(name)s - %(message)s
datefmt = %Y-%m-%d %H:%M:%S
```

**Éditer `migrations/env.py` pour support multi-schema :**
```python
"""
Alembic environment configuration with multi-tenant support.
"""
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool, text

# Ajouter le projet au path Python
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Importer configuration et models
from shared.config import settings
from shared.database import Base

# Import all models here pour autodétection
# from models.public.tenant import Tenant
# from models.public.user import User
# ... autres imports quand les models seront créés

# Alembic Config object
config = context.config

# Setup logging depuis alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata pour autodétection des changements
target_metadata = Base.metadata


def get_url():
    """Get database URL from settings."""
    return str(settings.database_url)


def get_all_client_schemas(connection):
    """
    Récupère tous les schemas clients existants.

    Returns:
        Liste des noms de schemas (ex: ['client_1', 'client_2'])
    """
    result = connection.execute(
        text(f"""
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name LIKE '{settings.tenant_schema_prefix}%'
            ORDER BY schema_name
        """)
    )
    return [row[0] for row in result.fetchall()]


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.
    Configure context with just a URL and not an Engine.
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.
    Support multi-schema pour multi-tenant.
    """
    # Configuration engine
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        # 1. Migration du schema PUBLIC (tables communes)
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=False,  # Seulement public
        )

        with context.begin_transaction():
            # Set search_path to public
            connection.execute(text("SET search_path TO public"))
            context.run_migrations()

        # 2. Migration de tous les schemas CLIENTS
        client_schemas = get_all_client_schemas(connection)

        for schema_name in client_schemas:
            print(f"🔄 Migrating schema: {schema_name}")

            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                version_table_schema=schema_name,
            )

            with context.begin_transaction():
                # Set search_path to client schema
                connection.execute(text(f"SET search_path TO {schema_name}, public"))
                context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

**Tester Alembic :**
```bash
# Vérifier configuration
alembic current

# Devrait afficher quelque chose comme:
# INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
# INFO  [alembic.runtime.migration] Will assume transactional DDL.
```

---

### Jour 5 : Tests Infrastructure & Documentation (4-6h)

#### Étape 3.1 : Scripts de Test (2h)

**Créer `scripts/test_db_connection.py` :**
```python
"""
Test PostgreSQL connection and basic operations.
"""
from sqlalchemy import text

from shared.database import check_database_connection, get_db_context
from shared.logging_setup import get_logger

logger = get_logger(__name__)


def test_database():
    """Test database connection and queries."""
    print("\n" + "="*60)
    print("🔍 TESTING POSTGRESQL CONNECTION")
    print("="*60)

    # Test 1: Basic connection
    print("\n1️⃣  Testing basic connection...")
    if check_database_connection():
        print("   ✅ Database connection OK")
    else:
        print("   ❌ Database connection FAILED")
        return False

    # Test 2: Query version
    print("\n2️⃣  Testing PostgreSQL version...")
    try:
        with get_db_context() as db:
            result = db.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"   ✅ PostgreSQL version: {version.split(',')[0]}")
    except Exception as e:
        print(f"   ❌ Version query failed: {e}")
        return False

    # Test 3: List schemas
    print("\n3️⃣  Testing schemas listing...")
    try:
        with get_db_context() as db:
            result = db.execute(text("""
                SELECT schema_name
                FROM information_schema.schemata
                WHERE schema_name NOT IN ('pg_catalog', 'information_schema')
                ORDER BY schema_name
            """))
            schemas = [row[0] for row in result.fetchall()]
            print(f"   ✅ Found {len(schemas)} schemas: {', '.join(schemas)}")
    except Exception as e:
        print(f"   ❌ Schemas listing failed: {e}")
        return False

    # Test 4: Create test table
    print("\n4️⃣  Testing table creation...")
    try:
        with get_db_context() as db:
            db.execute(text("""
                CREATE TABLE IF NOT EXISTS public.test_connection (
                    id SERIAL PRIMARY KEY,
                    message TEXT,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """))
            db.commit()
            print("   ✅ Test table created")

            # Insert test row
            db.execute(text("""
                INSERT INTO public.test_connection (message)
                VALUES ('Hello from Stoflow!')
            """))
            db.commit()
            print("   ✅ Test row inserted")

            # Query test row
            result = db.execute(text("SELECT * FROM public.test_connection LIMIT 1"))
            row = result.fetchone()
            print(f"   ✅ Test row retrieved: {row}")

            # Clean up
            db.execute(text("DROP TABLE public.test_connection"))
            db.commit()
            print("   ✅ Test table cleaned up")

    except Exception as e:
        print(f"   ❌ Table operations failed: {e}")
        return False

    print("\n" + "="*60)
    print("✅ ALL POSTGRESQL TESTS PASSED")
    print("="*60 + "\n")

    return True


if __name__ == "__main__":
    success = test_database()
    exit(0 if success else 1)
```

**Créer `scripts/test_redis_connection.py` :**
```python
"""
Test Redis connection and basic operations.
"""
import time

from shared.logging_setup import get_logger
from shared.redis_client import check_redis_connection, redis_client

logger = get_logger(__name__)


def test_redis():
    """Test Redis connection and operations."""
    print("\n" + "="*60)
    print("🔍 TESTING REDIS CONNECTION")
    print("="*60)

    # Test 1: Basic connection
    print("\n1️⃣  Testing basic connection...")
    if check_redis_connection():
        print("   ✅ Redis connection OK")
    else:
        print("   ❌ Redis connection FAILED")
        return False

    # Test 2: Set/Get operations
    print("\n2️⃣  Testing SET/GET operations...")
    try:
        test_key = "stoflow:test:key"
        test_value = "Hello Stoflow!"

        # Set value
        redis_client.client.set(test_key, test_value)
        print(f"   ✅ SET {test_key} = {test_value}")

        # Get value
        retrieved = redis_client.client.get(test_key)
        assert retrieved == test_value, f"Expected {test_value}, got {retrieved}"
        print(f"   ✅ GET {test_key} = {retrieved}")

        # Delete
        redis_client.client.delete(test_key)
        print(f"   ✅ DELETE {test_key}")

    except Exception as e:
        print(f"   ❌ SET/GET failed: {e}")
        return False

    # Test 3: TTL operations
    print("\n3️⃣  Testing TTL operations...")
    try:
        ttl_key = "stoflow:test:ttl"
        ttl_seconds = 2

        # Set with TTL
        redis_client.set_with_ttl(ttl_key, "expires soon", ttl_seconds)
        print(f"   ✅ SET {ttl_key} with TTL={ttl_seconds}s")

        # Check exists
        exists = redis_client.client.exists(ttl_key)
        assert exists, "Key should exist"
        print(f"   ✅ Key exists immediately")

        # Wait for expiration
        print(f"   ⏳ Waiting {ttl_seconds}s for expiration...")
        time.sleep(ttl_seconds + 0.5)

        # Check expired
        exists_after = redis_client.client.exists(ttl_key)
        assert not exists_after, "Key should have expired"
        print(f"   ✅ Key expired as expected")

    except Exception as e:
        print(f"   ❌ TTL test failed: {e}")
        return False

    # Test 4: Counter operations (pour rate limiting)
    print("\n4️⃣  Testing counter operations...")
    try:
        counter_key = "stoflow:test:counter"

        # Increment
        count1 = redis_client.client.incr(counter_key)
        print(f"   ✅ INCR {counter_key} = {count1}")

        count2 = redis_client.client.incr(counter_key)
        print(f"   ✅ INCR {counter_key} = {count2}")

        assert count2 == count1 + 1, "Counter should increment"

        # Get value
        final_count = int(redis_client.client.get(counter_key))
        assert final_count == 2, "Final count should be 2"
        print(f"   ✅ Final counter value: {final_count}")

        # Clean up
        redis_client.client.delete(counter_key)

    except Exception as e:
        print(f"   ❌ Counter test failed: {e}")
        return False

    # Test 5: List operations (pour RQ queues)
    print("\n5️⃣  Testing list operations (RQ simulation)...")
    try:
        list_key = "stoflow:test:queue"

        # Push items
        redis_client.client.rpush(list_key, "job1", "job2", "job3")
        print(f"   ✅ RPUSH {list_key} with 3 jobs")

        # Get list length
        length = redis_client.client.llen(list_key)
        assert length == 3, f"Expected 3 items, got {length}"
        print(f"   ✅ LLEN {list_key} = {length}")

        # Pop item
        item = redis_client.client.lpop(list_key)
        print(f"   ✅ LPOP {list_key} = {item}")

        # Clean up
        redis_client.client.delete(list_key)

    except Exception as e:
        print(f"   ❌ List operations failed: {e}")
        return False

    print("\n" + "="*60)
    print("✅ ALL REDIS TESTS PASSED")
    print("="*60 + "\n")

    return True


if __name__ == "__main__":
    success = test_redis()
    exit(0 if success else 1)
```

**Créer `scripts/test_all_infrastructure.py` :**
```python
"""
Run all infrastructure tests.
"""
import sys

from test_config import test_config
from test_db_connection import test_database
from test_redis_connection import test_redis


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("🚀 STOFLOW INFRASTRUCTURE TESTS")
    print("="*60)

    results = {
        "Configuration": False,
        "PostgreSQL": False,
        "Redis": False,
    }

    # Test 1: Configuration
    try:
        test_config()
        results["Configuration"] = True
    except Exception as e:
        print(f"\n❌ Configuration test failed: {e}")

    # Test 2: PostgreSQL
    try:
        results["PostgreSQL"] = test_database()
    except Exception as e:
        print(f"\n❌ PostgreSQL test failed: {e}")

    # Test 3: Redis
    try:
        results["Redis"] = test_redis()
    except Exception as e:
        print(f"\n❌ Redis test failed: {e}")

    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:.<40} {status}")

    all_passed = all(results.values())

    if all_passed:
        print("\n🎉 ALL TESTS PASSED - Infrastructure ready!")
        return 0
    else:
        print("\n⚠️  SOME TESTS FAILED - Check errors above")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
```

**Exécuter tous les tests :**
```bash
# Démarrer services Docker
docker compose up -d

# Attendre que les services soient prêts
sleep 5

# Exécuter tous les tests
python scripts/test_all_infrastructure.py
```

---

#### Étape 3.2 : Documentation README.md (1h30)

**Créer/Mettre à jour `README.md` :**
```markdown
# Stoflow Backend

**Tagline:** "Flow your products everywhere"

Plateforme SaaS multi-tenant pour publication automatisée de produits sur plusieurs marketplaces (Vinted, eBay, Etsy, etc.) avec génération de descriptions par IA.

---

## 🚀 Quick Start

### Prérequis

- Python 3.12+
- Docker & Docker Compose
- Git

### Installation

```bash
# Cloner le projet
cd /home/maribeiro/Stoflow/Stoflow_BackEnd

# Créer environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installer dépendances
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Configurer variables d'environnement
cp .env.example .env
# Éditer .env avec vos valeurs

# Démarrer services (PostgreSQL + Redis)
docker compose up -d

# Exécuter migrations
alembic upgrade head

# Tester l'infrastructure
python scripts/test_all_infrastructure.py
```

### Lancer l'API

```bash
# Mode développement (auto-reload)
uvicorn api.main:app --reload --port 8000

# Accéder à la documentation
# http://localhost:8000/docs (Swagger)
# http://localhost:8000/redoc (ReDoc)
```

---

## 📁 Structure du Projet

```
Stoflow_BackEnd/
├── api/                    # API FastAPI
│   ├── routes/            # Endpoints
│   ├── middleware/        # Middlewares custom
│   └── dependencies/      # Dependencies FastAPI
├── models/                # SQLAlchemy models
│   ├── public/           # Tables schema public
│   └── tenant/           # Tables schema client_X
├── services/             # Logique métier
│   ├── vinted/          # Intégration Vinted
│   ├── ai/              # Génération descriptions IA
│   └── monitoring/      # Logging & metrics
├── repositories/         # Accès données
├── workers/             # RQ workers async
├── migrations/          # Alembic migrations
├── shared/              # Configuration & utils
├── tests/               # Tests unitaires & intégration
├── scripts/             # Scripts utilitaires
└── docs/                # Documentation
```

---

## 🛠️ Commandes Utiles

### Docker

```bash
# Démarrer services
docker compose up -d

# Arrêter services
docker compose down

# Voir logs
docker compose logs -f postgres

# Redémarrer un service
docker compose restart redis

# Supprimer volumes (⚠️ perte données)
docker compose down -v
```

### Alembic (Migrations)

```bash
# Créer migration
alembic revision --autogenerate -m "description"

# Appliquer migrations
alembic upgrade head

# Revenir en arrière
alembic downgrade -1

# Voir historique
alembic history

# Status actuel
alembic current
```

### RQ Workers

```bash
# Démarrer worker default
rq worker --url redis://:stoflow_redis_dev_pass@localhost:6379/0

# Démarrer worker Vinted
rq worker vinted_publications --url redis://:stoflow_redis_dev_pass@localhost:6379/0

# Dashboard RQ (optionnel)
pip install rq-dashboard
rq-dashboard --redis-url redis://:stoflow_redis_dev_pass@localhost:6379/0
# Accéder à http://localhost:9181
```

### Tests

```bash
# Tous les tests
pytest

# Tests unitaires seulement
pytest tests/unit/

# Avec coverage
pytest --cov=. --cov-report=html

# Tests spécifiques
pytest tests/unit/test_auth_service.py -v
```

### Code Quality

```bash
# Format code (Black)
black .

# Check linting (Flake8)
flake8 .

# Sort imports (isort)
isort .

# Type checking (mypy)
mypy .
```

---

## 🏗️ Architecture Multi-Tenant

### Stratégie : Schema par Client

Chaque client (tenant) possède son propre schema PostgreSQL :

```
stoflow_db
├── public (tables communes)
│   ├── tenants
│   ├── users
│   └── subscriptions
├── client_1 (isolation données client 1)
│   ├── products
│   ├── vinted_products
│   └── publications_history
├── client_2 (isolation données client 2)
│   └── ...
```

**Avantages :**
- ✅ Isolation sécurisée
- ✅ Performances indépendantes
- ✅ Backup par client
- ✅ 1 seule connexion PostgreSQL

---

## 🔐 Sécurité

- Mots de passe hashés avec bcrypt (12 rounds)
- JWT tokens pour authentification
- Cookies Vinted chiffrés en BDD (Fernet)
- Variables sensibles dans `.env` (non commité)
- SQL injection prevention (parameterized queries)
- CORS configuré pour frontend autorisé

---

## 📊 Monitoring & Logs

Logs disponibles dans :
- Console (stdout) en mode développement
- Fichier `logs/stoflow.log` (rotation 10MB)

Niveaux de log :
- DEBUG : Développement
- INFO : Production
- WARNING : Avertissements
- ERROR : Erreurs critiques

---

## 🔗 Ressources

- **Documentation API :** http://localhost:8000/docs
- **Business Plan :** `BUSINESS_PLAN.md`
- **Roadmap MVP :** `MVP1_ROADMAP.md`
- **Setup Week 0 :** `WEEK0_SETUP.md`

---

## 👥 Contribution

Voir `CONTRIBUTING.md` (à créer)

---

## 📝 Licence

Propriétaire - Stoflow © 2024

---

**Version :** 0.1.0 (Week 0 - Infrastructure Setup)
**Dernière mise à jour :** 2024-12-04
```

---

## ✅ Checklist Finale Week 0

### Infrastructure
- [ ] Docker Compose configuré (PostgreSQL + Redis)
- [ ] Services démarrés et healthy
- [ ] Test connexion PostgreSQL OK
- [ ] Test connexion Redis OK

### Python Backend
- [ ] Environnement virtuel créé et activé
- [ ] `requirements.txt` et `requirements-dev.txt` créés
- [ ] Toutes dépendances installées
- [ ] Structure répertoires créée
- [ ] Tous `__init__.py` créés

### Configuration
- [ ] `.env.example` créé avec toutes les variables
- [ ] `.env` créé et configuré
- [ ] `shared/config.py` créé et testé
- [ ] `shared/database.py` créé et testé
- [ ] `shared/redis_client.py` créé et testé
- [ ] `shared/logging_setup.py` créé et testé

### Alembic
- [ ] Alembic initialisé
- [ ] `alembic.ini` configuré
- [ ] `migrations/env.py` adapté pour multi-tenant
- [ ] Test `alembic current` OK

### Git
- [ ] `.gitignore` créé et configuré
- [ ] Repo Git initialisé (si nécessaire)
- [ ] Branch `develop` créée
- [ ] Premier commit fait

### Tests & Documentation
- [ ] `scripts/test_config.py` créé et exécuté
- [ ] `scripts/test_db_connection.py` créé et exécuté
- [ ] `scripts/test_redis_connection.py` créé et exécuté
- [ ] `scripts/test_all_infrastructure.py` créé et exécuté
- [ ] Tous les tests passent ✅
- [ ] `README.md` créé avec documentation complète
- [ ] `WEEK0_SETUP.md` (ce document) créé

### Optionnel
- [ ] pgAdmin accessible (si profile tools activé)
- [ ] Logs créés dans `logs/stoflow.log`
- [ ] Code formaté avec Black
- [ ] Pre-commit hooks configurés (optionnel)

---

## 🎯 Résultat Attendu

À la fin de la Week 0, vous devez avoir :

1. ✅ **Environnement de développement fonctionnel**
   - Python 3.12 + venv
   - PostgreSQL + Redis via Docker
   - Toutes dépendances installées

2. ✅ **Structure projet propre**
   - Répertoires organisés logiquement
   - Configuration centralisée
   - Logging configuré

3. ✅ **Infrastructure testée**
   - Connexion BDD OK
   - Connexion Redis OK
   - Alembic prêt pour migrations

4. ✅ **Documentation complète**
   - README.md avec quick start
   - Setup détaillé (ce document)
   - Scripts de test commentés

5. ✅ **Git configuré**
   - .gitignore adapté
   - Branches créées
   - Premier commit

---

## 🚦 Prochaines Étapes

Après avoir complété la Week 0 avec succès, passer à :

**Week 1-2 : Architecture Multi-Tenant**
- Création des models SQLAlchemy
- Migrations Alembic (public + tenant schemas)
- API authentification
- Middleware multi-tenant

Voir `MVP1_ROADMAP.md` pour détails.

---

## ❓ Problèmes Fréquents

### Docker Compose ne démarre pas

```bash
# Vérifier logs
docker compose logs postgres

# Problème de port déjà utilisé
sudo lsof -i :5432
# Arrêter le service qui utilise le port

# Recréer les containers
docker compose down -v
docker compose up -d
```

### Erreur "module not found"

```bash
# Vérifier que venv est activé
which python  # Doit pointer vers venv/

# Réinstaller dépendances
pip install -r requirements.txt --force-reinstall
```

### Alembic "can't locate revision"

```bash
# Supprimer alembic_version table
# Se reconnecter à PostgreSQL
docker exec -it stoflow_postgres psql -U stoflow_user -d stoflow_db
# DROP TABLE alembic_version;

# Réinitialiser
alembic stamp head
```

### Redis connection refused

```bash
# Vérifier que Redis tourne
docker compose ps redis

# Redémarrer Redis
docker compose restart redis

# Test manuel
redis-cli -h localhost -p 6379 -a stoflow_redis_dev_pass
# > PING
# PONG
```

---

## 📞 Support

Pour questions ou problèmes :
1. Vérifier cette documentation
2. Consulter `README.md`
3. Chercher dans issues GitHub (si repo existe)
4. Contacter l'équipe

---

**Document créé le :** 2024-12-04
**Durée estimée Week 0 :** 5 jours (adaptable)
**Status :** ✅ Ready to use

🚀 **Bonne chance pour le setup !**
