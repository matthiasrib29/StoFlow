# 🧪 Guide des Tests - Stoflow Backend

Ce guide explique comment exécuter les tests avec PostgreSQL (Docker).

## 📋 Prérequis

- Docker et Docker Compose installés
- Python 3.12+ avec venv activé
- Dependencies installées (`pip install -r requirements.txt`)

## 🚀 Quick Start

### 1. Démarrer la base de données de test

```bash
# Démarrer le conteneur PostgreSQL de test
./scripts/test_db.sh start

# Ou manuellement avec docker-compose
docker-compose -f docker-compose.test.yml up -d
```

**Attendre que la DB soit prête** (~5 secondes)

### 2. Lancer les tests

```bash
# Activer le virtualenv
source venv/bin/activate

# Lancer TOUS les tests
pytest

# Lancer les tests de sécurité uniquement
pytest tests/integration/security/ -v

# Lancer les tests de rate limiting
pytest tests/integration/security/test_rate_limiting.py -v

# Lancer les tests d'isolation multi-user
pytest tests/integration/security/test_multi_user_isolation.py -v
```

### 3. Arrêter la base de données de test

```bash
# Arrêter et supprimer le conteneur
./scripts/test_db.sh stop

# Ou manuellement
docker-compose -f docker-compose.test.yml down -v
```

---

## 🛠️ Commandes Utiles

### Gestion de la DB de test

```bash
# Voir le status de la DB
./scripts/test_db.sh status

# Voir les logs en temps réel
./scripts/test_db.sh logs

# Ouvrir un shell PostgreSQL
./scripts/test_db.sh shell

# Redémarrer la DB (cleanup complet)
./scripts/test_db.sh restart
```

### Pytest - Options avancées

```bash
# Mode verbeux avec détails
pytest tests/integration/security/ -vv

# Arrêter au premier échec
pytest tests/integration/security/ -x

# Mode verbeux avec print() visible
pytest tests/integration/security/ -vv -s

# Lancer un test spécifique
pytest tests/integration/security/test_rate_limiting.py::TestLoginRateLimiting::test_login_within_rate_limit_succeeds -v

# Coverage report
pytest --cov=. --cov-report=html
```

---

## 📊 Architecture des Tests

### Structure

```
tests/
├── conftest.py                          # Configuration pytest + fixtures
├── integration/
│   ├── security/
│   │   ├── test_multi_user_isolation.py # Tests isolation user_1 vs user_2
│   │   └── test_rate_limiting.py        # Tests rate limiting (bruteforce)
│   └── api/
│       └── test_products.py             # Tests CRUD products
└── unit/                                # Tests unitaires (à venir)
```

### Fixtures disponibles

| Fixture | Scope | Description |
|---------|-------|-------------|
| `setup_test_database` | session | Setup DB: migrations + schemas user_1, user_2 |
| `db_session` | function | Session DB propre pour chaque test |
| `cleanup_data` | function | Nettoie les données après chaque test |
| `client` | function | TestClient FastAPI avec override DB |
| `test_user` | function | Crée un utilisateur ADMIN de test |
| `auth_headers` | function | Headers JWT pour requêtes authentifiées |

---

## 🏗️ Comment fonctionnent les tests

### 1. Session Scope (une fois au début)

```python
@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    # 1. Applique les migrations Alembic
    command.upgrade(alembic_cfg, "head")

    # 2. Crée les schemas user_1, user_2
    conn.execute(text("CREATE SCHEMA user_1"))

    # 3. Crée les tables products, product_images...
    Product.__table__.create(bind=conn)
```

**Résultat:** Structure DB identique à la production ✅

### 2. Function Scope (avant chaque test)

```python
@pytest.fixture(scope="function")
def db_session():
    session = TestingSessionLocal()
    yield session
    session.rollback()  # Annule les modifications du test
```

**Résultat:** Chaque test est isolé, pas de pollution ✅

### 3. Cleanup (après chaque test)

```python
@pytest.fixture(scope="function", autouse=True)
def cleanup_data(db_session):
    yield  # Test runs
    db_session.execute(text("TRUNCATE TABLE public.users CASCADE"))
    db_session.commit()
```

**Résultat:** Données effacées, structure gardée ✅

---

## 🎯 Tests de Sécurité P0

### Test 1: Isolation Multi-User

**Fichier:** `tests/integration/security/test_multi_user_isolation.py`

**Ce qui est testé:**
- ✅ User1 ne peut pas voir les produits de User2
- ✅ User1 ne peut pas modifier les produits de User2
- ✅ User1 ne peut pas supprimer les produits de User2
- ✅ Chaque user voit uniquement ses propres produits
- ✅ User1 ne peut pas supprimer les images de User2

**Pourquoi PostgreSQL est nécessaire:**
- Utilise `SET search_path TO user_1, public` (pas supporté par SQLite)
- Crée vraiment les schemas `user_1`, `user_2` en PostgreSQL
- Tests réalistes de l'isolation multi-tenant

### Test 2: Rate Limiting

**Fichier:** `tests/integration/security/test_rate_limiting.py`

**Ce qui est testé:**
- ✅ 10 tentatives de login autorisées
- ✅ 11ème tentative retourne 429 Too Many Requests
- ✅ Les échecs comptent vers la limite (anti-bruteforce)
- ✅ La fenêtre se reset après 300 secondes
- ✅ IPs différentes ont des limites indépendantes

**Config:**
- `/api/auth/login`: 10 tentatives / 5 minutes par IP
- Autres endpoints: pas de limite

---

## 🔧 Troubleshooting

### La DB ne démarre pas

```bash
# Vérifier que Docker fonctionne
docker ps

# Voir les logs d'erreur
docker-compose -f docker-compose.test.yml logs

# Le port 5433 est peut-être occupé
lsof -i :5433
```

### Les tests échouent avec "cannot connect"

```bash
# S'assurer que la DB est démarrée
./scripts/test_db.sh status

# Vérifier la connexion
docker-compose -f docker-compose.test.yml exec test_db pg_isready -U stoflow_test
```

### Les migrations Alembic échouent

```bash
# Vérifier les migrations localement
alembic current
alembic history

# Reset complet de la DB de test
./scripts/test_db.sh restart
pytest tests/integration/security/ -v
```

### Conflit de port avec PostgreSQL prod

Si tu as déjà PostgreSQL sur le port 5432 ou 5433:

```yaml
# docker-compose.test.yml (déjà configuré)
ports:
  - "5434:5432"  # Port différent de la prod ✅
```

---

## 📈 Best Practices

### ✅ À FAIRE

```bash
# Toujours démarrer la DB avant les tests
./scripts/test_db.sh start
pytest

# Arrêter la DB après les tests (libère la RAM)
./scripts/test_db.sh stop
```

### ❌ À NE PAS FAIRE

```bash
# Ne PAS modifier les migrations pendant que les tests tournent
alembic revision -m "..." # ← Attends que les tests finissent

# Ne PAS utiliser la prod DB pour les tests
export TEST_DATABASE_URL="postgresql://localhost:5432/stoflow_prod" # ❌ DANGER

# Ne PAS commit les données de test
git status  # Vérifie qu'il n'y a pas de .sql ou dumps
```

---

## 🎓 Pour aller plus loin

### Ajouter un nouveau test de sécurité

1. Créer le fichier dans `tests/integration/security/`
2. Utiliser les fixtures existantes (`client`, `db_session`, `auth_headers`)
3. Documenter le test avec des docstrings
4. Lancer : `pytest tests/integration/security/test_nouveau.py -v`

### Tester avec des données spécifiques

```python
@pytest.fixture
def user_with_10_products(db_session, test_user):
    """Crée un user avec 10 produits."""
    user, _ = test_user
    db_session.execute(text(f"SET search_path TO user_{user.id}, public"))

    for i in range(10):
        product = Product(title=f"Product {i}", price=10.0 + i)
        db_session.add(product)

    db_session.commit()
    return user
```

---

## 📚 Ressources

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Alembic Migrations](https://alembic.sqlalchemy.org/)
- [PostgreSQL Schemas](https://www.postgresql.org/docs/current/ddl-schemas.html)

---

**Bon courage avec les tests ! 🚀**
