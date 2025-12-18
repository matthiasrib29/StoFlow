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
# Se placer dans le répertoire du projet
cd /home/maribeiro/Stoflow/Stoflow_BackEnd

# Créer environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installer dépendances
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Configurer variables d'environnement
cp .env.example .env
# Éditer .env avec vos valeurs (optionnel pour dev)

# Démarrer services (PostgreSQL + Redis)
docker compose up -d

# Tester l'infrastructure
python scripts/test_all_infrastructure.py
```

### Lancer l'API (à venir - Week 1)

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
│   ├── config.py       # Configuration centralisée
│   ├── database.py     # Session DB multi-tenant
│   ├── redis_client.py # Client Redis & RQ
│   └── logging_setup.py # Configuration logs
├── tests/               # Tests unitaires & intégration
├── scripts/             # Scripts utilitaires
│   ├── test_config.py
│   ├── test_db_connection.py
│   ├── test_redis_connection.py
│   └── test_all_infrastructure.py
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

### RQ Workers (à venir - Week 1)

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

# Tests infrastructure
python scripts/test_all_infrastructure.py
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

## 🐳 Services Docker

### PostgreSQL
- **Port :** 5433 (5432 déjà utilisé)
- **Database :** stoflow_db
- **User :** stoflow_user
- **Password :** stoflow_dev_password_2024

### Redis
- **Port :** 6379
- **Password :** stoflow_redis_dev_pass

### pgAdmin (optionnel)
```bash
# Démarrer pgAdmin
docker compose --profile tools up -d pgadmin

# Accéder à http://localhost:5050
# Login: admin@stoflow.local / admin
```

---

## 🔗 Ressources

- **Documentation API :** http://localhost:8000/docs (à venir)
- **Business Plan :** `BUSINESS_PLAN.md`
- **Roadmap MVP :** `MVP1_ROADMAP.md`
- **Setup Week 0 :** `WEEK0_SETUP.md`

---

## 📝 État du Projet

**Version :** 0.1.0 (Week 0 - Infrastructure Setup)
**Status :** ✅ Infrastructure opérationnelle
**Dernière mise à jour :** 2024-12-04

### ✅ Terminé (Week 0)
- Structure projet backend
- Configuration environnement (Pydantic Settings)
- Docker Compose (PostgreSQL + Redis)
- Clients Database & Redis
- Système de logging
- Configuration Alembic multi-tenant
- Tests infrastructure complets

### 🚧 En cours (Week 1-2)
- Architecture multi-tenant (models SQLAlchemy)
- API authentification
- Middleware multi-tenant

---

## 👥 Contribution

Voir `CONTRIBUTING.md` (à créer)

---

## 📝 Licence

Propriétaire - Stoflow © 2024
