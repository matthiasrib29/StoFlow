# Architecture Stoflow Backend

**Version:** 1.0
**Dernière mise à jour:** 2025-12-08

---

## 🏗️ Vue d'ensemble

Stoflow est une plateforme SaaS multi-tenant pour publication automatisée de produits sur plusieurs marketplaces (Vinted, eBay, Etsy, etc.) avec génération de descriptions par IA.

**Tagline:** "Flow your products everywhere"

---

## 🎯 Stratégie Multi-Tenant

### Schema par Utilisateur (PostgreSQL)

Chaque utilisateur possède son propre schema PostgreSQL (`user_{id}`) pour une isolation maximale des données.

```
stoflow_db
├── public (tables communes)
│   ├── users
│   ├── subscription_quotas
│   ├── platform_mappings
│   ├── clothing_prices
│   └── ai_credits
├── product_attributes (attributs partagés)
│   ├── brands, categories, colors, sizes
│   ├── conditions, materials, fits, genders
│   └── seasons, closures, decades, etc.
├── template_tenant (template pour nouveaux users)
│   ├── products, product_images
│   ├── plugin_tasks, plugin_queue
│   └── vinted_*, ebay_* tables
├── user_1 (isolation données user 1)
│   ├── products
│   ├── product_images
│   ├── plugin_tasks
│   └── vinted_credentials, ebay_credentials, etc.
└── user_2 (isolation données user 2)
    └── ...
```

**Avantages:**
- ✅ Isolation sécurisée maximale
- ✅ Performances indépendantes
- ✅ 1 seule connexion PostgreSQL
- ✅ Backup par client
- ✅ Queries cross-tenant possibles via `public`

**Implémentation:**

```python
# shared/database.py
def set_user_schema(db: Session, user_id: int) -> None:
    """Configure le search_path PostgreSQL pour isoler l'utilisateur."""
    schema_name = f"user_{user_id}"
    db.execute(text(f"SET search_path TO {schema_name}, public"))
```

---

## 📁 Structure du Projet

```
Stoflow_BackEnd/
├── api/                    # FastAPI endpoints
│   ├── auth.py            # Authentification JWT
│   ├── products.py        # CRUD produits
│   ├── integrations.py    # Plateformes externes
│   └── plugin.py          # Communication plugin navigateur
├── models/                # SQLAlchemy models
│   ├── public/           # Schema public (partagé)
│   │   ├── tenant.py
│   │   ├── user.py
│   │   ├── category.py
│   │   └── brand.py, color.py, size.py, etc.
│   └── user/             # Schema client_X (isolé)
│       ├── product.py
│       ├── product_image.py
│       ├── publication_history.py
│       └── ai_generation_log.py
├── services/             # Logique métier
│   ├── auth_service.py
│   ├── product_service.py
│   ├── category_service.py
│   ├── file_service.py
│   ├── vinted/          # Intégration Vinted
│   │   ├── vinted_adapter.py
│   │   ├── vinted_mapper.py
│   │   ├── vinted_importer.py
│   │   └── vinted_publisher.py
│   └── validators.py
├── middleware/           # Middlewares
│   ├── tenant_middleware.py
│   ├── rate_limit.py
│   └── security_headers.py
├── schemas/              # Pydantic schemas
│   ├── auth_schemas.py
│   └── product_schemas.py
├── shared/               # Configuration & utils
│   ├── config.py        # Configuration centralisée
│   ├── database.py      # Session DB multi-tenant
│   └── datetime_utils.py
├── migrations/           # Alembic migrations
│   └── versions/
├── scripts/             # Scripts utilitaires
│   ├── seed_categories.py
│   ├── seed_product_attributes.py
│   └── api_bridge_server.py  # Pont backend<->plugin
└── tests/               # Tests
    ├── unit/
    ├── integration/
    └── conftest.py
```

---

## 🔐 Authentification & Autorisation

### JWT avec Multi-tenant

```python
# Payload JWT
{
    "sub": user.id,
    "tenant_id": tenant.id,
    "role": "admin|user"
}
```

### Flow d'authentification

1. **Register:** `POST /api/auth/register`
   - Crée le tenant
   - Crée le schema PostgreSQL `client_{id}`
   - Crée l'utilisateur admin
   - Retourne JWT token

2. **Login:** `POST /api/auth/login?source=web|plugin|mobile`
   - Vérifie credentials
   - Retourne JWT + refresh token
   - Tracking de la source de connexion

3. **Protected Routes:**
   ```python
   @router.get("/products")
   def get_products(
       current_user: User = Depends(get_current_user),
       db: Session = Depends(get_db)
   ):
       # Tenant isolation automatique via middleware
   ```

---

## 🔄 Cycle de Vie d'un Produit

### Statuts (MVP)

```python
class ProductStatus(str, Enum):
    DRAFT = "draft"           # Brouillon
    PUBLISHED = "published"   # Publié (visible)
    SOLD = "sold"            # Vendu
    ARCHIVED = "archived"    # Archivé
```

### Transitions Autorisées

```
DRAFT → PUBLISHED
PUBLISHED → SOLD
PUBLISHED → ARCHIVED
SOLD → ARCHIVED
ARCHIVED → [TERMINAL]
```

**Soft Delete:** `deleted_at IS NOT NULL` (masqué de toutes les queries)

**Règle critique:**
- ❌ Cannot publish with `stock_quantity = 0`
- ❌ Cannot modify deleted products
- ❌ No transition from ARCHIVED

---

## 🗄️ Modèle de Données Principal

### Tables Public (Partagées)

**tenants**
```sql
id, name, email, subscription_tier, subscription_status,
max_products, max_platforms, ai_credits_monthly,
is_active, created_at, updated_at
```

**users**
```sql
id, tenant_id, email, hashed_password, full_name, role,
business_name, account_type, business_type, estimated_products,
siret, vat_number, phone, country, language,
is_active, is_verified, last_login, created_at, updated_at
```

**categories** (hiérarchie)
```sql
name_en, name_fr, parent_category, gender, created_at
```

**Attributs partagés:** brands, colors, sizes, materials, fits, seasons, conditions, etc.

### Tables User Schema (Isolées)

**products**
```sql
id, sku, title, description, price, cost_price, stock_quantity,
category, brand, size, color, material, fit, gender, season, condition,
label_size, decade, closure, condition_sup,
model, origin, pattern, style,
dim1-6 (dimensions), status, published_at, sold_at,
created_at, updated_at, deleted_at
```

**product_images**
```sql
id, product_id, image_path, display_order, created_at
```

**publications_history**
```sql
id, product_id, platform, action, status, error_message,
started_at, completed_at, created_at
```

---

## 🔌 Intégrations Plateformes

### Architecture Adapter Pattern

```python
# services/vinted/vinted_adapter.py
class VintedAdapter:
    """
    Adapte les produits Stoflow vers le format Vinted
    """

    def to_vinted_format(product: Product) -> dict:
        """Convertit Product → Vinted API format"""

    def from_vinted_format(vinted_data: dict) -> Product:
        """Convertit Vinted API → Product"""
```

### Communication Backend ↔ Plugin

Le plugin Firefox agit comme un **proxy** pour accéder à l'API Vinted avec les cookies utilisateur.

**Architecture:**
```
Backend Python
    ↓ HTTP POST
API Bridge Server (FastAPI, port 8000)
    ↓ Page HTML
Plugin Firefox (Content Script)
    ↓ fetch() avec credentials
Vinted API
```

**Voir:** `docs/PLUGIN_INTEGRATION.md` pour détails complets

---

## 🚀 Déploiement & Infrastructure

### Stack Technique

**Backend:**
- Python 3.12
- FastAPI (API REST)
- SQLAlchemy 2.0 (ORM)
- Alembic (Migrations)
- Pydantic (Validation)

**Base de Données:**
- PostgreSQL 15+ (Multi-tenant schemas)
- Redis (Cache & Rate limiting)

**Monitoring:**
- Logs structurés (rotation 10MB)
- Health checks (`/health`)

### Variables d'Environnement

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/stoflow_db

# Redis
REDIS_URL=redis://:pass@localhost:6379/0

# JWT
JWT_SECRET_KEY=your-super-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# Multi-tenant
TENANT_SCHEMA_PREFIX=client_
TENANT_MAX_SCHEMAS=1000

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
```

---

## 🔒 Sécurité

### Pratiques Implémentées

✅ **Mots de passe:** Hashés avec bcrypt (12 rounds)
✅ **JWT tokens:** HS256, expiration 24h (access) / 7 jours (refresh)
✅ **SQL injection:** Parameterized queries via SQLAlchemy
✅ **CORS:** Configuré pour frontend autorisé uniquement
✅ **Rate limiting:** Redis-based (40 req/2h par compte Vinted)
✅ **Timing attack:** Random delay 100-300ms sur login

### Isolation Multi-Tenant

✅ **Schema isolation:** Requêtes limitées au schema du tenant
✅ **FK validation:** Tous les attributs validés avant insertion
✅ **Middleware:** Applique `search_path` automatiquement
✅ **Soft delete awareness:** Produits supprimés exclus des queries

---

## 📊 Monitoring & Logs

### Niveaux de Log

- **DEBUG:** Développement (SQL queries, détails)
- **INFO:** Production (actions utilisateur)
- **WARNING:** Avertissements (rate limit proche)
- **ERROR:** Erreurs critiques (API failure, DB error)

### Logs Structurés

```python
logger.info(
    f"[AUTH] User authenticated: user_id={user.id}, "
    f"tenant_id={tenant.id}, source={source}"
)

logger.error(
    f"[VINTED] Publication failed: product_id={product.id}, "
    f"error={error}, tenant_id={tenant_id}"
)
```

### Fichiers de Log

- **Console:** stdout (développement)
- **Fichier:** `logs/stoflow.log` (rotation automatique)

---

## 🧪 Tests

### Structure

```
tests/
├── unit/              # Tests unitaires services
│   ├── models/
│   ├── services/
│   └── utils/
├── integration/       # Tests API + DB
│   ├── api/
│   └── database/
└── conftest.py       # Fixtures pytest
```

### Commandes

```bash
# Tous les tests
pytest

# Tests unitaires seulement
pytest tests/unit/

# Avec coverage
pytest --cov=. --cov-report=html

# Tests critiques business logic
pytest tests/test_products_critical.py -v
```

### Coverage Target

**Minimum 80%** pour les modules critiques:
- `services/product_service.py`
- `services/auth_service.py`
- `api/products.py`
- `api/auth.py`

---

## 🔄 Workflow Git

```
main (production)
├── develop (staging)
│   ├── feature/auth-onboarding
│   ├── feature/vinted-publish
│   ├── fix/product-business-logic
│   └── refactor/category-service
```

### Commit Messages

```bash
feat: add vinted publication endpoint
fix: prevent publishing products with zero stock
docs: update API documentation
test: add critical business logic tests
refactor: simplify category hierarchy validation
```

---

## 📚 Références

- **Business Logic:** `docs/BUSINESS_LOGIC.md`
- **Plugin Integration:** `docs/PLUGIN_INTEGRATION.md`
- **MVP Roadmap:** `docs/MVP_ROADMAP.md`
- **Quick Reference:** `docs/QUICK_REFERENCE.md`

---

**Dernière mise à jour:** 2025-12-08
