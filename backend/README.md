# StoFlow Backend

API REST pour la gestion et publication de produits sur marketplaces (Vinted, eBay, Etsy).

## Stack Technique

| Technologie | Version | Role |
|-------------|---------|------|
| **FastAPI** | 0.115.0 | Framework web async |
| **SQLAlchemy** | 2.0.35 | ORM |
| **Alembic** | 1.14.0 | Migrations |
| **PostgreSQL** | 15+ | Base de donnees |
| **Pydantic** | 2.10.1 | Validation et schemas |
| **python-socketio** | 5.11.0 | WebSocket temps reel |
| **APScheduler** | 3.10.4 | Taches planifiees |
| **Stripe** | 11.3.0 | Paiements |
| **boto3** | 1.35.0 | Cloudflare R2 storage |
| **google-genai** | 1.0.0+ | Google Gemini (IA) |
| **httpx** | 0.27.2 | Client HTTP async |
| **Pytest** | - | Tests |

## Fonctionnalites Implementees

### Authentification
- JWT tokens (access + refresh)
- Rotation des secrets JWT
- RBAC (roles et permissions)
- Protection timing attacks

### Produits
- CRUD complet avec soft delete
- Upload images vers Cloudflare R2
- Generation de texte IA (titre, description via Gemini)
- Gestion des statuts (draft, published, sold, archived)

### Intégrations Marketplaces

#### Vinted (via Plugin WebSocket)
- Import/sync des produits
- Publication d'annonces
- Synchronisation des commandes
- Messagerie (inbox sync)
- Jobs asynchrones avec retry

#### eBay (API directe OAuth2)
- OAuth2 flow complet
- Publication via Inventory API
- Sync des commandes (Fulfillment API)
- Gestion retours et remboursements
- Annulations et litiges
- Webhook notifications

#### Etsy (API directe OAuth2)
- OAuth2 flow complet
- Publication de listings
- Sync des commandes
- Polling automatique

### Paiements (Stripe)
- Checkout sessions
- Webhooks
- Gestion abonnements

### Multi-Tenant
- Schema PostgreSQL par utilisateur (`user_{id}`)
- Isolation complete des donnees
- Schema `template_tenant` pour nouveaux users

### Admin
- Gestion utilisateurs
- Gestion attributs (categories, marques, couleurs...)
- Statistiques globales
- Audit logs

## Quick Start

```bash
# Environnement virtuel
python -m venv .venv
source .venv/bin/activate

# Dependances
pip install -r requirements.txt

# Docker (PostgreSQL + Redis)
docker-compose up -d

# Migrations
alembic upgrade head

# Serveur dev
uvicorn main:app --reload --port 8000
```

## Structure du Projet

```
backend/
├── api/                    # Routes FastAPI
│   ├── auth.py             # Authentification
│   ├── products/           # CRUD produits
│   ├── vinted/             # Routes Vinted
│   ├── ebay/               # Routes eBay
│   ├── etsy/               # Routes Etsy
│   ├── stripe_routes.py    # Paiements
│   ├── subscription.py     # Abonnements
│   └── admin*.py           # Admin routes
├── services/               # Logique metier
│   ├── auth_service.py
│   ├── product_service.py
│   ├── vinted/             # Services Vinted
│   ├── ebay/               # Services eBay
│   ├── etsy/               # Services Etsy
│   ├── stripe/             # Services Stripe
│   └── ai/                 # Generation IA
├── models/
│   ├── public/             # Tables partagees
│   └── user/               # Tables par tenant
├── schemas/                # Pydantic schemas
├── migrations/             # Alembic migrations
├── shared/                 # Config, database, utils
└── tests/
    ├── unit/
    └── integration/
```

## Architecture Multi-Tenant

| Schema | Contenu |
|--------|---------|
| `public` | users, subscription_quotas |
| `product_attributes` | brands, colors, conditions, materials, sizes, categories |
| `user_{id}` | products, vinted_products, marketplace_jobs, orders |
| `template_tenant` | Template clone pour nouveaux users |

Isolation via `SET search_path TO user_{id}, public` par requete.

## Communication avec Plugin Vinted

```
Backend (Job) --> WebSocket --> Frontend --> Plugin (Browser) --> Vinted API
              <-- WebSocket <-- Frontend <-- Plugin (Browser) <--
```

Le plugin navigateur intercepte les appels API Vinted. Le backend orchestre via des Jobs.

## API Documentation

Swagger UI disponible sur `/docs` en developpement.

## Configuration

### Variables d'Environnement

```env
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/stoflow

# JWT
JWT_SECRET_KEY=your-secret-key
JWT_SECRET_KEY_PREVIOUS=old-secret-for-rotation

# Cloudflare R2
R2_ACCOUNT_ID=xxx
R2_ACCESS_KEY_ID=xxx
R2_SECRET_ACCESS_KEY=xxx
R2_BUCKET_NAME=stoflow-images

# Stripe
STRIPE_SECRET_KEY=sk_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx

# eBay
EBAY_CLIENT_ID=xxx
EBAY_CLIENT_SECRET=xxx
EBAY_REDIRECT_URI=xxx

# Etsy
ETSY_API_KEY=xxx
ETSY_SHARED_SECRET=xxx

# Google Gemini
GOOGLE_API_KEY=xxx
```

## Scripts

```bash
# Dev server
uvicorn main:app --reload

# Tests
pytest
pytest --cov=. --cov-report=html

# Migrations
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade -1

# Code quality
black .
isort .
flake8
```

## Tests

```bash
# Demarrer la BDD de test
docker-compose -f docker-compose.test.yml up -d

# Lancer les tests
pytest

# Avec couverture
pytest --cov=. --cov-report=html
```

---

**Derniere mise a jour :** 2026-01-20
**Python version recommandee :** 3.11+
