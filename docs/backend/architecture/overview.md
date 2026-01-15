# Stoflow Backend

**Version:** 1.0.0
**Tagline:** "Flow your products everywhere"

---

## 🎯 Qu'est-ce que Stoflow ?

Stoflow est une plateforme SaaS multi-tenant qui permet aux vendeurs e-commerce de publier automatiquement leurs produits sur plusieurs marketplaces (Vinted, eBay, Etsy, etc.) avec génération de descriptions par IA.

**Fonctionnalités principales:**
- 🚀 Publication multi-plateforme automatisée
- 🤖 Génération de descriptions par IA
- 📊 Gestion centralisée des produits
- 🔄 Synchronisation bidirectionnelle
- 📈 Analytics et statistiques
- 🏢 Architecture multi-tenant isolée

---

## 🛠️ Stack Technique

**Backend:**
- Python 3.12
- FastAPI (API REST)
- SQLAlchemy 2.0 (ORM)
- Alembic (Migrations)
- Pydantic (Validation)

**Base de Données:**
- PostgreSQL 15+ (Multi-tenant schemas)
- Redis (Cache & Rate limiting)

**Outils:**
- pytest (Tests)
- uvicorn (ASGI server)

---

## 📋 Prérequis

- Python 3.12+
- PostgreSQL 15+
- Redis 7+
- Git

---

## 🚀 Installation Rapide

### 1. Cloner le Repository

```bash
git clone https://github.com/votre-org/stoflow-backend.git
cd stoflow-backend
```

### 2. Créer l'Environnement Virtuel

```bash
python3.12 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

### 3. Installer les Dépendances

```bash
pip install -r requirements.txt
```

### 4. Configuration Base de Données

**Créer la base de données:**

```bash
# PostgreSQL
createdb stoflow_db

# Ou via psql
psql -U postgres
CREATE DATABASE stoflow_db;
```

**Fichier `.env`:**

Créer un fichier `.env` à la racine du projet:

```bash
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/stoflow_db

# Redis
REDIS_URL=redis://:password@localhost:6379/0

# JWT
JWT_SECRET_KEY=your-super-secret-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440
JWT_REFRESH_EXPIRE_DAYS=7

# Multi-tenant
TENANT_SCHEMA_PREFIX=client_
TENANT_MAX_SCHEMAS=1000

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# Environment
ENVIRONMENT=development
DEBUG=True
```

### 5. Initialiser la Base de Données

```bash
# Exécuter les migrations
alembic upgrade head

# Seeder les catégories et attributs
python scripts/seed_categories.py
python scripts/seed_product_attributes.py
```

### 6. Lancer le Serveur

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Accès:**
- API: http://localhost:8000
- Documentation Swagger: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

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
│   └── user/             # Schema client_X (isolé)
├── services/             # Logique métier
│   ├── auth_service.py
│   ├── product_service.py
│   ├── category_service.py
│   ├── file_service.py
│   └── vinted/          # Intégration Vinted
├── middleware/           # Middlewares
│   ├── tenant_middleware.py
│   ├── rate_limit.py
│   └── security_headers.py
├── schemas/              # Pydantic schemas
│   ├── auth_schemas.py
│   └── product_schemas.py
├── shared/               # Configuration & utils
│   ├── config.py
│   ├── database.py
│   └── datetime_utils.py
├── migrations/           # Alembic migrations
├── scripts/             # Scripts utilitaires
├── tests/               # Tests
└── docs/                # Documentation
```

---

## 🔑 Premiers Pas

### 1. Créer un Compte

```bash
POST /api/auth/register
```

**Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "full_name": "John Doe",
  "business_name": "Mon Shop",
  "account_type": "business",
  "business_type": "reseller",
  "estimated_products": "100_500"
}
```

**Réponse:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "user_id": 1,
  "tenant_id": 1,
  "role": "admin"
}
```

### 2. Se Connecter

```bash
POST /api/auth/login
```

**Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

### 3. Créer un Produit

```bash
POST /api/products
Authorization: Bearer <token>
```

**Body:**
```json
{
  "sku": "TSHIRT-001",
  "title": "T-shirt Nike Noir",
  "description": "T-shirt Nike en excellent état",
  "price": 15.00,
  "cost_price": 8.00,
  "stock_quantity": 1,
  "category": "t-shirts",
  "brand": "Nike",
  "size": "M",
  "color": "black",
  "gender": "men",
  "condition": "very_good"
}
```

### 4. Lister les Produits

```bash
GET /api/products?status=draft
Authorization: Bearer <token>
```

---

## 🔌 Intégrations

### Plugin Navigateur (Vinted)

Le plugin Firefox/Chrome permet d'interagir avec Vinted via le navigateur de l'utilisateur.

**Installation:**
1. Lancer le serveur API Bridge:
   ```bash
   python scripts/api_bridge_server.py
   ```

2. Ouvrir http://localhost:8000 dans Firefox

3. Charger le plugin Stoflow dans Firefox

4. Se connecter sur Vinted

**Voir:** `docs/PLUGIN_INTEGRATION.md` pour plus de détails.

---

## 🧪 Tests

### Lancer Tous les Tests

```bash
pytest
```

### Tests Unitaires Seulement

```bash
pytest tests/unit/
```

### Tests avec Coverage

```bash
pytest --cov=. --cov-report=html
```

### Tests Critiques Business Logic

```bash
pytest tests/test_products_critical.py -v
```

**Coverage Target:** 80% minimum pour modules critiques

---

## 📊 Architecture Multi-Tenant

Stoflow utilise une architecture **schema-per-tenant** avec PostgreSQL:

```
stoflow_db
├── public (tables communes)
│   ├── tenants
│   ├── users
│   ├── subscriptions
│   ├── categories, brands, colors, sizes, etc.
│   └── platform_mappings
├── client_1 (isolation données client 1)
│   ├── products
│   ├── product_images
│   ├── publications_history
│   └── ai_generations_log
└── client_2 (isolation données client 2)
    └── ...
```

**Avantages:**
- ✅ Isolation sécurisée maximale
- ✅ Performances indépendantes
- ✅ 1 seule connexion PostgreSQL
- ✅ Backup par client
- ✅ Queries cross-tenant possibles via `public`

---

## 🔒 Sécurité

**Pratiques Implémentées:**
- ✅ Mots de passe hashés avec bcrypt (12 rounds)
- ✅ JWT tokens (HS256, expiration 24h access / 7 jours refresh)
- ✅ SQL injection protection via SQLAlchemy
- ✅ CORS configuré pour frontend autorisé uniquement
- ✅ Rate limiting Redis-based
- ✅ Timing attack protection (random delay 100-300ms sur login)
- ✅ Schema isolation multi-tenant
- ✅ FK validation pour tous les attributs

---

## 📈 Monitoring & Logs

**Niveaux de Log:**
- **DEBUG:** Développement (SQL queries, détails)
- **INFO:** Production (actions utilisateur)
- **WARNING:** Avertissements (rate limit proche)
- **ERROR:** Erreurs critiques (API failure, DB error)

**Fichiers de Log:**
- Console: stdout (développement)
- Fichier: `logs/stoflow.log` (rotation automatique 10MB)

**Health Check:**
```bash
GET /health
```

---

## 🌐 Variables d'Environnement

| Variable | Description | Défaut |
|----------|-------------|---------|
| `DATABASE_URL` | URL PostgreSQL | `postgresql://...` |
| `REDIS_URL` | URL Redis | `redis://...` |
| `JWT_SECRET_KEY` | Clé secrète JWT | **OBLIGATOIRE** |
| `JWT_ALGORITHM` | Algorithme JWT | `HS256` |
| `JWT_EXPIRE_MINUTES` | Expiration access token | `1440` (24h) |
| `JWT_REFRESH_EXPIRE_DAYS` | Expiration refresh token | `7` |
| `TENANT_SCHEMA_PREFIX` | Préfixe schema tenant | `client_` |
| `TENANT_MAX_SCHEMAS` | Max schemas tenant | `1000` |
| `CORS_ORIGINS` | Origins CORS autorisés | `http://localhost:3000` |
| `ENVIRONMENT` | Environnement | `development` |
| `DEBUG` | Mode debug | `True` |

---

## 🛠️ Commandes Utiles

### Base de Données

```bash
# Créer une nouvelle migration
alembic revision --autogenerate -m "description"

# Appliquer les migrations
alembic upgrade head

# Revenir en arrière
alembic downgrade -1

# Voir l'historique
alembic history
```

### Développement

```bash
# Lancer le serveur en mode dev
uvicorn main:app --reload

# Lancer avec logs debug
uvicorn main:app --reload --log-level debug

# Lancer sur un port différent
uvicorn main:app --reload --port 8080
```

### Tests

```bash
# Tests avec output verbose
pytest -v

# Tests pour un fichier spécifique
pytest tests/test_auth.py

# Tests avec markers
pytest -m "not slow"
```

---

## 📚 Documentation Complète

- **Architecture:** `docs/ARCHITECTURE.md`
- **Business Logic:** `docs/BUSINESS_LOGIC.md`
- **Plugin Integration:** `docs/PLUGIN_INTEGRATION.md`
- **MVP Roadmap:** `docs/MVP_ROADMAP.md`

---

## 🤝 Contribution

### Workflow Git

```
main (production)
└── develop (staging)
    ├── feature/nom-feature
    ├── fix/nom-bug
    └── refactor/nom-refactor
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

## 📞 Support

- **Issues:** https://github.com/votre-org/stoflow-backend/issues
- **Documentation:** https://docs.stoflow.com
- **Email:** support@stoflow.com

---

## 📄 Licence

Copyright © 2025 Stoflow. Tous droits réservés.

---

**Dernière mise à jour:** 2025-12-08
