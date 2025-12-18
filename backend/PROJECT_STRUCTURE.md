# Structure du Projet Stoflow Backend

**Dernière mise à jour:** 2025-12-08

---

## 📁 Structure Racine

```
Stoflow_BackEnd/
├── CLAUDE.md                 # Instructions pour Claude Code
├── main.py                   # Point d'entrée FastAPI
├── requirements.txt          # Dépendances Python
├── requirements-dev.txt      # Dépendances développement
├── alembic.ini              # Configuration Alembic
├── docker-compose.yml       # Orchestration Docker
│
├── api/                     # Endpoints FastAPI
├── models/                  # Modèles SQLAlchemy
├── services/                # Logique métier
├── schemas/                 # Schémas Pydantic
├── middleware/              # Middlewares (tenant, rate limit, etc.)
├── migrations/              # Migrations Alembic
├── scripts/                 # Scripts utilitaires
├── tests/                   # Tests automatisés
├── docs/                    # Documentation
├── logs/                    # Fichiers de logs
└── repositories/            # Repositories (pattern Repository)
```

---

## 📚 Documentation (`docs/`)

### Fichiers Principaux

| Fichier | Description | Quand le lire |
|---------|-------------|---------------|
| **INDEX.md** | Index de la documentation | Point d'entrée navigation |
| **README.md** | Guide démarrage rapide | Installation & setup |
| **ARCHITECTURE.md** | Architecture technique | Comprendre le système |
| **BUSINESS_LOGIC.md** | Règles métier | Avant implémenter features |
| **MVP_ROADMAP.md** | Roadmap 8 semaines | Suivre avancement projet |
| **PLUGIN_INTEGRATION.md** | Intégration plugin | Travailler sur Vinted |

### Archive

`docs/archive_old_docs/` - Ancienne documentation consolidée (21 fichiers)

---

## 🧪 Tests (`tests/`)

```
tests/
├── conftest.py              # Configuration pytest & fixtures
├── unit/                    # Tests unitaires
│   ├── models/             # Tests des modèles
│   ├── services/           # Tests des services
│   └── utils/              # Tests des utilitaires
├── integration/            # Tests d'intégration
│   ├── api/               # Tests endpoints API
│   └── database/          # Tests DB
├── e2e/                    # Tests end-to-end
└── manual/                 # Tests manuels/diagnostic
    ├── README.md
    ├── test_func_now_bug.py
    └── test_refactoring.py
```

### Exécuter les tests

```bash
# Tous les tests
pytest

# Tests unitaires seulement
pytest tests/unit/

# Tests avec coverage
pytest --cov=. --cov-report=html

# Test manuel spécifique
python tests/manual/test_func_now_bug.py
```

---

## 🔧 API (`api/`)

```
api/
├── auth.py                 # Authentification JWT
├── products.py             # CRUD produits
├── integrations.py         # Intégrations (Vinted, eBay, etc.)
├── plugin.py               # Communication plugin navigateur
├── dependencies/           # Dépendances FastAPI
└── middleware/             # Middlewares spécifiques API
```

---

## 🗄️ Modèles (`models/`)

```
models/
├── public/                 # Schema public (partagé)
│   ├── user.py            # Utilisateurs
│   ├── tenant.py          # Tenants
│   ├── category.py        # Catégories
│   ├── brand.py, color.py, size.py, etc.
│   └── platform_mapping.py
└── user/                   # Schema client_X (isolé)
    ├── product.py         # Produits
    ├── product_image.py   # Images produits
    ├── publication_history.py
    └── ai_generation_log.py
```

---

## ⚙️ Services (`services/`)

```
services/
├── auth_service.py         # Authentification
├── product_service.py      # Gestion produits
├── category_service.py     # Gestion catégories
├── file_service.py         # Upload fichiers
├── user_schema_service.py  # Gestion schemas tenants
├── plugin_task_service.py  # Tâches plugin
├── validators.py           # Validations business
└── vinted/                 # Intégration Vinted
    ├── vinted_adapter.py
    ├── vinted_mapper.py
    ├── vinted_importer.py
    └── vinted_publisher.py
```

---

## 🔄 Migrations (`migrations/`)

```
migrations/
├── env.py                  # Configuration Alembic
├── versions/               # Migrations actives
│   ├── 20251207_0050_init_simplified_schema.py
│   ├── 20251208_0949_add_onboarding_fields_to_users.py
│   └── ...
└── versions_old/           # Migrations archivées
```

### Commandes Alembic

```bash
# Créer une migration
alembic revision --autogenerate -m "description"

# Appliquer migrations
alembic upgrade head

# Revenir en arrière
alembic downgrade -1
```

---

## 🛠️ Scripts (`scripts/`)

```
scripts/
├── seed_categories.py           # Seed catégories
├── seed_product_attributes.py   # Seed attributs
├── init_db.py                  # Initialiser DB
├── api_bridge_server.py        # Serveur pont plugin
└── test_*.py                   # Scripts de test
```

---

## 🔒 Middleware (`middleware/`)

```
middleware/
├── tenant_middleware.py    # Isolation multi-tenant
├── rate_limit.py          # Rate limiting
└── security_headers.py    # Headers sécurité
```

---

## 📦 Schémas Pydantic (`schemas/`)

```
schemas/
├── auth_schemas.py        # Schémas authentification
└── product_schemas.py     # Schémas produits
```

---

## 🗂️ Repositories (`repositories/`)

Pattern Repository pour accès données (si utilisé).

---

## 📝 Fichiers Racine Importants

| Fichier | Description |
|---------|-------------|
| `CLAUDE.md` | Instructions pour Claude Code (ne pas modifier) |
| `main.py` | Point d'entrée application FastAPI |
| `requirements.txt` | Dépendances Python production |
| `requirements-dev.txt` | Dépendances développement |
| `alembic.ini` | Configuration migrations Alembic |
| `docker-compose.yml` | Configuration Docker |

---

## 🚀 Commandes Rapides

### Développement

```bash
# Lancer le serveur
uvicorn main:app --reload

# Lancer avec logs debug
uvicorn main:app --reload --log-level debug

# Lancer tests
pytest
```

### Base de Données

```bash
# Appliquer migrations
alembic upgrade head

# Seed données
python scripts/seed_categories.py
python scripts/seed_product_attributes.py
```

---

**Dernière mise à jour:** 2025-12-08
