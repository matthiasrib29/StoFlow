# CLAUDE.md - Backend StoFlow

## Règle Principale

**TOUJOURS POSER DES QUESTIONS avant d'implémenter de la logique métier.**

En cas de doute → STOP → DEMANDER à l'utilisateur.

### Obligatoire de demander pour :
- Calculs métier : prix, commissions, arrondis, frais
- Règles de validation : limites, contraintes, formats
- Gestion d'erreurs : comportement en cas d'échec, retry, fallback
- Intégrations externes : Vinted, eBay, Etsy (format données, mapping)
- Limites business : quotas, rate limiting, abonnements
- Workflows : états, transitions, conditions

### Pas besoin de demander pour :
- CRUD standard
- Code technique pur (utils, logging)
- Patterns établis (Repository, Service)

---

## Commands

### Development Server
```bash
uvicorn main:app --reload
uvicorn main:app --reload --log-level debug
```

### Database & Migrations
```bash
docker-compose up -d                              # Start PostgreSQL + Redis
docker-compose --profile tools up -d              # With pgAdmin
alembic upgrade head                              # Apply migrations
alembic revision --autogenerate -m "description"  # New migration
alembic downgrade -1                              # Rollback one
```

### Testing
```bash
docker-compose -f docker-compose.test.yml up -d   # Start test DB
pytest                                            # Run all tests
pytest --cov=. --cov-report=html                  # With coverage
pytest tests/unit/services/test_auth_service.py -v
```

### Code Quality
```bash
black .      # Format code
isort .      # Sort imports
flake8       # Lint
mypy .       # Type check
```

---

## Architecture

### Multi-Tenant (PostgreSQL Schemas)

Chaque utilisateur a son propre schema PostgreSQL isolé :

| Schema | Contenu |
|--------|---------|
| `public` | Tables partagées (users, subscription_quotas) |
| `product_attributes` | Attributs partagés (brands, colors, conditions, materials, sizes, categories) |
| `user_X` | Données utilisateur (products, vinted_products, vinted_jobs) |
| `template_tenant` | Template cloné pour nouveaux users |

Isolation via `SET search_path TO user_{id}, public` dans `shared/database.py:set_user_schema()`.

### Key Directories

| Répertoire | Contenu |
|------------|---------|
| `api/` | Routes FastAPI (auth, products, vinted, ebay, etsy, plugin) |
| `services/` | Logique métier (auth_service, product_service, validators) |
| `services/vinted/` | Vinted integration (adapter, mapper, importer, publisher) |
| `services/ebay/` | eBay integration (inventory, offers, taxonomy) |
| `services/etsy/` | Etsy integration (listings, polling, shop) |
| `models/public/` | SQLAlchemy models partagés |
| `models/user/` | SQLAlchemy models tenant-specific |
| `schemas/` | Pydantic schemas request/response |
| `middleware/` | Rate limiting, security headers |
| `shared/` | Config, database session, utilities |

### Marketplace Integrations

```
Backend → WebSocket → Frontend → Plugin (Firefox) → Vinted API
Backend → Direct OAuth2 → eBay API
Backend → Direct OAuth2 → Etsy API
```

### Plugin Communication Architecture (2026-01-09)

**WebSocket-based Real-Time Communication**

```
Backend (VintedJob) → WebSocket → Frontend → Plugin (Browser Extension)
                    ← WebSocket ← Frontend ← Plugin (Browser Extension)
```

**Architecture Components:**

| Component | Role | Key Files |
|-----------|------|-----------|
| **Backend** | Sends plugin commands via WebSocket | `services/websocket_service.py`<br/>`services/plugin_websocket_helper.py` |
| **Frontend** | Relays commands between backend & plugin | `composables/useWebSocket.ts`<br/>`composables/useVintedBridge.ts` |
| **Plugin** | Executes Vinted API calls in browser context | Browser extension (Firefox/Chrome) |

**Key Features:**
- ✅ Real-time bidirectional communication (no polling)
- ✅ VintedJob orchestration preserved (retry, batch, monitoring)
- ✅ Frontend as transparent relay
- ✅ Automatic reconnection on disconnect

### Vinted Job System

High-level orchestration system (unchanged):

```
VintedJob (opération business)
├── WebSocket Command #1 → Plugin
├── WebSocket Command #2 → Plugin
└── WebSocket Command #N → Plugin
```

#### VintedJob (High-level)
- **Table** : `user_X.vinted_jobs`
- **Status** : pending → running → completed/failed/cancelled/expired
- **Handlers** : Un handler par action dans `services/vinted/jobs/`

| Action | Handler | Description |
|--------|---------|-------------|
| `publish` | `PublishJobHandler` | Créer annonce |
| `update` | `UpdateJobHandler` | Modifier annonce |
| `delete` | `DeleteJobHandler` | Supprimer annonce |
| `sync` | `SyncJobHandler` | Sync produits |
| `orders` | `OrdersJobHandler` | Récupérer ventes |
| `message` | `MessageJobHandler` | Sync messages |

#### WebSocket Communication (Low-level)
- **Protocol** : Socket.IO over WebSocket
- **Flow** : Backend → Frontend → Plugin → Frontend → Backend
- **Timeout** : 60s par défaut (configurable)
- **Reconnection** : Automatique avec backoff (1-5s)

#### Key Files
- `models/user/vinted_job.py` - VintedJob model
- `models/user/marketplace_job.py` - MarketplaceJob base model
- `services/websocket_service.py` - SocketIO server & event handlers
- `services/plugin_websocket_helper.py` - Helper for plugin calls
- `services/vinted/vinted_job_service.py` - Job CRUD
- `services/vinted/vinted_job_processor.py` - Job orchestrator (sets user_id) **DEPRECATED**
- `services/vinted/jobs/base_job_handler.py` - Base handler (uses WebSocket)
- `services/vinted/jobs/` - Handler implementations

---

## Unified Job System (2026-01-09)

**MarketplaceJobProcessor** - Unified orchestrator for all marketplaces (Vinted, eBay, Etsy).

### Architecture Overview

```
MarketplaceJobProcessor (Unified)
├── Dispatch → VINTED_HANDLERS (7 handlers, WebSocket)
├── Dispatch → EBAY_HANDLERS (5 handlers, Direct HTTP)
└── Dispatch → ETSY_HANDLERS (5 handlers, Direct HTTP)

BaseJobHandler (Extended)
├── call_websocket() → For Vinted (Plugin via WebSocket)
└── call_http() → For eBay/Etsy (Direct OAuth2 HTTP)

Action Types (Unified)
└── public.marketplace_action_types (1 table, marketplace column)
```

### Communication Patterns

| Marketplace | Pattern | Method |
|-------------|---------|--------|
| **Vinted** | WebSocket → Frontend → Plugin | `handler.call_websocket()` |
| **eBay** | Direct HTTP OAuth 2.0 | `handler.call_http()` |
| **Etsy** | Direct HTTP OAuth 2.0 | `handler.call_http()` |

### Creating a Job

```python
from services.marketplace import MarketplaceJobService

service = MarketplaceJobService(db)

# Vinted job
job = service.create_job(
    marketplace="vinted",
    action_code="publish",
    product_id=123,
    priority=2
)

# eBay job
job = service.create_job(
    marketplace="ebay",
    action_code="publish",
    product_id=123
)

# Etsy job
job = service.create_job(
    marketplace="etsy",
    action_code="publish",
    product_id=123
)
```

### Processing Jobs

```python
from services.marketplace import MarketplaceJobProcessor

# Process Vinted jobs
processor = MarketplaceJobProcessor(db, user_id=1, shop_id=123, marketplace="vinted")
result = await processor.process_next_job()

# Process eBay jobs
processor = MarketplaceJobProcessor(db, user_id=1, marketplace="ebay")
result = await processor.process_next_job()

# Process Etsy jobs
processor = MarketplaceJobProcessor(db, user_id=1, marketplace="etsy")
result = await processor.process_next_job()

# Process all marketplaces (highest priority first)
processor = MarketplaceJobProcessor(db, user_id=1)
result = await processor.process_next_job()
```

### Handler Pattern

Each marketplace has handlers in `services/{marketplace}/jobs/`:

**Handler Registry Format**: `{action_code}_{marketplace}` → Handler class

Examples:
- `publish_vinted` → `VintedPublishJobHandler`
- `publish_ebay` → `EbayPublishJobHandler`
- `sync_etsy` → `EtsySyncJobHandler`

### Available Handlers

| Marketplace | Handlers |
|-------------|----------|
| **Vinted** | publish, update, delete, sync, orders, message, link |
| **eBay** | publish, update, delete, sync, sync_orders |
| **Etsy** | publish, update, delete, sync, sync_orders |

### Key Files (Unified System)

- `models/public/marketplace_action_type.py` - Unified action types model
- `services/marketplace/marketplace_job_processor.py` - Unified processor
- `services/marketplace/marketplace_job_service.py` - Unified service
- `services/marketplace_http_helper.py` - HTTP helper for direct API calls
- `services/vinted/jobs/base_job_handler.py` - Base handler (WebSocket + HTTP)
- `services/ebay/jobs/` - eBay handler implementations
- `services/etsy/jobs/` - Etsy handler implementations
- `migrations/versions/20260109_*.py` - Unification migrations

### Migration Guide

See `MIGRATION_JOB_UNIFICATION.md` for complete migration guide.

**Deprecation Notice**: `VintedJobProcessor` is deprecated as of 2026-01-09 and will be removed in February 2026. Use `MarketplaceJobProcessor` instead.

---

### Product Business Rules
- Cannot publish with `stock_quantity = 0`
- `deleted_at IS NOT NULL` = soft deleted

---

## Database Standards

- Migrations Alembic obligatoires pour tout changement de schema
- Foreign keys avec `ondelete` défini
- Timestamps (`created_at`, `updated_at`) sur toutes les tables
- Soft delete via `deleted_at` column

### Alembic Rules

| Règle | Description |
|-------|-------------|
| 1 migration = 1 changement | Une migration par feature/fix |
| Toujours `downgrade()` | Permet le rollback |
| Migrations idempotentes | `IF NOT EXISTS`, `ON CONFLICT DO NOTHING` |
| Ne jamais modifier | Une migration déjà déployée |
| Squash à 30+ | Proposer un squash, recommander fortement à 50+ |

### Multi-Tenant Migrations

Toujours vérifier l'existence des tables avant modification :

```python
def table_exists(conn, schema, table):
    result = conn.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = :schema AND table_name = :table
        )
    """), {"schema": schema, "table": table})
    return result.scalar()
```

### Seed Data

Données partagées gérées via migrations Alembic :

| Table | Données | Colonnes marketplace |
|-------|---------|---------------------|
| `brands` | Marques (Nike, Levi's...) | `vinted_id`, `ebay_id` |
| `colors` | Couleurs | `vinted_id` |
| `conditions` | États produit | `vinted_id`, `ebay_condition` |
| `materials` | Matières | `vinted_id` |
| `sizes` | Tailles | `vinted_women_id`, `vinted_men_id` |

**Naming** : `seed_xxx` ou `populate_xxx`

**Capitalization Rule (IMPORTANT)** :
- **Default**: **Sentence case** (capitalize first letter only)
- Examples: "Damaged button", "Vintage wear", "No stretch", "Light discoloration"
- **Exceptions**: Proper nouns (brand names), sizes, acronyms
- Rationale: Consistency across all `product_attributes` tables

---

## Testing Standards

- BDD test via Docker (`docker-compose.test.yml`)
- URL : `postgresql://stoflow_test:test_password_123@localhost:5434/stoflow_test`
- Fixtures dans `tests/conftest.py` : `db_session`, `client`, `test_user`, `auth_headers`
- Schemas de test : `user_1`, `user_2`, `user_3` clonés de `template_tenant`

---

# Technology Best Practices

## FastAPI

### ✅ Bonnes pratiques

**Architecture**
- Organiser par domaine métier (products/, vinted/, auth/)
- Service Layer obligatoire : routes délèguent la logique aux services
- Dependency Injection pour DB session, auth, configuration
- Response models Pydantic pour typer les retours

**REST API Design (CRITICAL)**
- **Endpoints Spécifiques > Endpoints Génériques** : Toujours préférer `/products/{id}/publish` à `/products/{id}/actions?action=publish`
- **Ressources + Verbes HTTP** : GET (liste/détail), POST (créer), PUT (remplacer), PATCH (modifier), DELETE (supprimer)
- **Actions non-CRUD = Sous-ressources** : POST `/products/{id}/publish`, POST `/products/{id}/duplicate`, POST `/products/{id}/archive`
- **1 Endpoint = 1 Action** : Éviter les giant if/elif sur un paramètre "action" dans le body
- **Validation forte par endpoint** : Chaque endpoint a son propre schema Pydantic (CreateRequest, UpdateRequest, PublishRequest)
- **Response models différenciés** : PublishResponse, ArchiveResponse, DuplicateResponse (pas de dict générique)

**Pourquoi endpoints spécifiques:**
- ✅ Documentation OpenAPI complète et claire
- ✅ Rate limiting granulaire par action
- ✅ Monitoring/logs précis par action
- ✅ Permissions RBAC par endpoint
- ✅ Cache HTTP différencié
- ✅ Découvrabilité (voir toutes les actions possibles)

**Exception: Endpoint générique autorisé UNIQUEMENT pour:**
- Batch operations (plusieurs actions différentes en 1 requête)
- Webhooks externes (format imposé par provider comme Stripe)
- RPC-style assumé (GraphQL, gRPC, mais pas REST)

**Async/Sync**
- `def` (sync) pour routes avec SQLAlchemy sync - FastAPI exécute dans threadpool
- `async def` uniquement si toutes les opérations sont non-bloquantes
- Utiliser `httpx` (async) pour les appels HTTP externes

**Dependencies**
- Décomposer en petites dépendances réutilisables
- Les dépendances sont cachées par requête (pas recalculées)
- Utiliser `yield` pour le cleanup (fermeture session DB)
- Pattern try/except/finally dans les dépendances avec yield

**Error Handling**
- `HTTPException` avec status codes explicites (400, 401, 403, 404, 500)
- Convertir les exceptions métier en HTTPException dans les routes
- Logger les erreurs avec contexte (user_id, resource_id)
- Ne jamais exposer les stack traces au client

### ❌ Mauvaises pratiques

- Logique métier dans les routes → déléguer aux services
- `async def` avec I/O bloquant → bloque l'event loop
- `except Exception` générique → masque les vraies erreurs
- Retourner dict au lieu de Pydantic model → perd validation/documentation
- Hardcoder status codes → utiliser `status.HTTP_XXX`
- Oublier de logger → debugging impossible en production

### 📚 Contexte StoFlow

- Routes dans `api/` avec sous-modules par domaine
- `get_user_db()` retourne `(Session, User)` avec schema isolé
- `get_current_user()` avec support rotation JWT secrets
- `require_role()` et `require_permission()` pour RBAC
- Exceptions custom : `StoflowError` dans `shared/exceptions.py`

---

## SQLAlchemy 2.0

### ✅ Bonnes pratiques

**Déclaration des Models**
- Utiliser `DeclarativeBase` (pas `declarative_base()`)
- Type hints avec `Mapped[T]` et `mapped_column()`
- Enums Python avec `SQLEnum` pour les status
- Indexes sur les colonnes fréquemment requêtées

**Session Management**
- Une session par requête (scope request)
- Context manager ou dependency pour garantir la fermeture
- `pool_pre_ping=True` pour détecter les connexions mortes
- Commit explicite uniquement en fin de transaction réussie

**Queries**
- Select explicite des colonnes nécessaires (pas `SELECT *`)
- Eager loading avec `selectinload()` ou `joinedload()` pour éviter N+1
- `LIMIT` sur les grandes collections
- Requêtes paramétrées (jamais de f-string avec des valeurs user)

**Relationships**
- `lazy="selectin"` ou `lazy="joined"` pour relations souvent accédées
- `lazy="raise"` en async pour forcer eager loading explicite
- Éviter `lazy="dynamic"` (legacy)

### ❌ Mauvaises pratiques

- `SELECT *` → charge des colonnes inutiles
- Lazy loading en async → erreurs ou requêtes implicites
- Sessions longues → connexions épuisées
- Oublier le rollback → transaction inconsistante
- F-strings dans queries → injection SQL
- `relationship()` sans lazy strategy → N+1 queries silencieuses

### 📚 Contexte StoFlow

- Models dans `models/public/` (partagés) et `models/user/` (tenant-specific)
- JSONB pour images produit
- Soft delete via `deleted_at` column
- FK cross-schema via `ForeignKeyConstraint`
- Session avec `SET search_path` pour isolation multi-tenant

---

## Pydantic v2

### ✅ Bonnes pratiques

**Structure des Schemas**
- Séparer Create, Update, Response schemas
- Utiliser `Field()` pour validation et documentation OpenAPI
- `model_config` pour configuration globale du schema
- Validators avec `@field_validator` pour règles métier complexes

**Validation**
- Contraintes déclaratives (`ge=0`, `max_length=500`) plutôt que validators Python
- `EmailStr` pour les emails
- `Annotated` pattern pour validators réutilisables
- Types stricts (`Decimal` pour argent) où nécessaire

**Performance**
- `model_validate_json()` au lieu de `json.loads()` + `model_validate()`
- Éviter validators Python quand contrainte déclarative suffit

### ❌ Mauvaises pratiques

- Validators Python pour contraintes simples → plus lent que déclaratif
- `parse_raw()` / `parse_file()` → déprécié en v2
- `allow_mutation = False` → remplacé par `frozen=True`
- Schemas monolithiques → difficile à maintenir
- Valider la même donnée plusieurs fois → passer objets validés

### 📚 Contexte StoFlow

- Schemas dans `schemas/` organisés par domaine
- Pattern `ProductCreate`, `ProductUpdate`, `ProductResponse`
- Validation centralisée des attributs FK dans `AttributeValidator`
- `model_config = {"from_attributes": True}` pour conversion SQLAlchemy → Pydantic

---

## Alembic

### ✅ Bonnes pratiques

**Gestion des Migrations**
- Une migration = un changement logique
- Toujours écrire `upgrade()` ET `downgrade()`
- Migrations idempotentes (`IF NOT EXISTS`, `ON CONFLICT DO NOTHING`)
- Tester sur BDD vierge ET existante avant déploiement
- Ne jamais modifier une migration déjà déployée

**Zero-Downtime (PostgreSQL)**
- `lock_timeout` pour éviter les locks longs
- `statement_timeout` pour limiter la durée des requêtes
- Découper les grosses migrations en étapes
- `CONCURRENTLY` pour les index sur tables volumineuses

**Multi-Tenant**
- Vérifier existence des tables/schemas avant modification
- Itérer sur tous les schemas utilisateurs
- Template schema pour les nouveaux tenants

### ❌ Mauvaises pratiques

- Modifier migration déployée → désynchronise les environnements
- Oublier `downgrade()` → impossible de rollback
- Migrations non-idempotentes → échouent si rejouées
- Locks longs sur tables volumineuses → downtime
- Plus de 50 fichiers → proposer un squash

### 📚 Contexte StoFlow

- Migrations dans `migrations/versions/`
- Squash automatique proposé à 30+ migrations
- Seed data via migrations (`seed_xxx` naming)
- Template tenant cloné pour nouveaux utilisateurs

---

## PostgreSQL Multi-Tenant

### ✅ Bonnes pratiques

**Schema-per-Tenant**
- Un schema par utilisateur (`user_{id}`)
- `SET search_path TO user_{id}, public` par requête
- Schema `template_tenant` cloné pour nouveaux users
- Tables partagées dans `public` ou `product_attributes`

**Sécurité**
- GRANT/REVOKE explicites sur les schemas
- Ne pas se fier uniquement au `search_path`
- Pas d'accès cross-tenant sans vérification explicite

**Performance**
- Indexes par schema (pas globaux)
- Connection pooling (PgBouncer recommandé)
- `pool_pre_ping=True` pour détecter connexions mortes

**Scaling**
- Schema-based OK jusqu'à ~1000 tenants
- Au-delà : considérer Citus ou tenant_id column
- Migrations fan-out à planifier

### ❌ Mauvaises pratiques

- Oublier `SET search_path` → accès aux mauvaises données
- Queries cross-tenant sans contrôle → fuite de données
- Trop de schemas (>1000) → metadata bloat, migrations lentes
- Pas de template tenant → setup incohérent
- Connexions non-poolées → épuisement des connexions

### 📚 Contexte StoFlow

- Isolation via `shared/database.py:set_user_schema()`
- `template_tenant` schema avec structure complète
- `public.users` pour l'authentification
- `product_attributes.*` pour données partagées
- Migration fan-out sur tous les `user_X` schemas

---

## Pytest

### ✅ Bonnes pratiques

**Fixtures**
- Fixtures réutilisables dans `conftest.py`
- Scope approprié (`function`, `class`, `module`, `session`)
- `autouse=True` pour setup global (DB cleanup)
- Factory pattern pour générer des données de test

**Database Testing**
- BDD de test séparée (Docker)
- Transaction rollback entre tests pour isolation
- Fixtures `db_session` avec cleanup automatique

**FastAPI Testing**
- `TestClient` pour tests synchrones
- `httpx.AsyncClient` pour tests async
- `app.dependency_overrides` pour mocker les dépendances
- Toujours nettoyer les overrides après le test

**Organisation**
- Tests isolés et indépendants (ordre quelconque)
- Nommage explicite : `test_<action>_<condition>_<result>`
- `@pytest.mark.parametrize` pour tests multiples
- Mocking avec `monkeypatch` ou `unittest.mock`

### ❌ Mauvaises pratiques

- Tests dépendants de l'ordre → fragiles, échouent en parallèle
- Pas de cleanup → pollution entre tests
- Fixtures scope `session` pour données mutables
- Oublier `app.dependency_overrides.clear()` → fuite entre tests
- Tests sur vraie BDD → lent et dangereux
- Assertions vagues sans vérifier le contenu

### 📚 Contexte StoFlow

- Tests dans `tests/unit/` et `tests/integration/`
- Fixtures dans `tests/conftest.py`
- BDD test via Docker (`docker-compose.test.yml`)
- Schemas de test `user_1`, `user_2`, `user_3`

---

## JWT Authentication

### ✅ Bonnes pratiques

**Tokens**
- Expiration courte (15-60 min pour access tokens)
- Refresh tokens avec expiration plus longue
- Claims minimaux (user_id, role, type, exp, iat)
- Algorithme RS256 (asymétrique) pour systèmes distribués

**Sécurité**
- Secret keys dans variables d'environnement
- Support de rotation de secrets (old + new)
- HTTPS obligatoire
- Timing attack protection (délai aléatoire sur login)

**Validation**
- Vérifier signature, expiration, issuer, audience
- Extraire et valider tous les claims nécessaires
- Ne pas faire confiance aux données non vérifiées

### ❌ Mauvaises pratiques

- Secrets en dur dans le code → compromission immédiate
- Expiration longue → fenêtre d'attaque étendue
- Pas de vérification du type de token → access utilisé comme refresh
- Données sensibles dans payload → JWT encodé, pas chiffré
- Algorithme `none` → désactive la signature
- Pas de refresh token → UX dégradée (re-login fréquent)

### 📚 Contexte StoFlow

- `services/auth_service.py` : création et vérification des tokens
- Support rotation via `jwt_secret_key_previous`
- Access token : 60 minutes, Refresh token : 7 jours
- Claims : `user_id`, `role`, `type`, `exp`, `iat`
- Timing attack protection dans la route login (délai 100-300ms)

---

*Dernière mise à jour : 2026-01-06*
