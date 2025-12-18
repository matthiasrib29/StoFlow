# Simplification: Tenant → User uniquement

**Date:** 2025-12-07
**Objectif:** Supprimer toute logique de tenant et gérer uniquement les users avec isolation par schema PostgreSQL

---

## ✅ Modifications effectuées

### 1. Models (models/public/user.py)

**Changements:**
- ❌ Supprimé `tenant_id` (Foreign Key)
- ❌ Supprimé relation `tenant`
- ✅ Ajouté `subscription_tier` (Enum: starter, standard, premium, business, enterprise)
- ✅ Ajouté `subscription_status` (active, suspended, cancelled)
- ✅ Ajouté `max_products`, `max_platforms`, `ai_credits_monthly`
- ✅ Ajouté champs Vinted: `vinted_cookies`, `vinted_user_id`, `vinted_username`
- ✅ Ajouté property `schema_name` → retourne `user_{id}`

**Fichiers supprimés (renommés .OLD):**
- `models/public/tenant.py.OLD`
- `models/public/subscription.py.OLD`

---

### 2. Services

#### services/auth_service.py
**Changements:**
- ✅ `create_access_token(user_id, role)` - supprimé param `tenant_id`
- ✅ `create_refresh_token(user_id)` - supprimé param `tenant_id`
- ✅ `authenticate_user()` - supprimé vérification tenant actif
- ✅ `get_user_from_token()` - supprimé vérification tenant
- ✅ `refresh_access_token()` - supprimé param `tenant_id`
- ✅ Ajouté `get_subscription_limits(tier)` - retourne limites par tier

#### services/tenant_service.py
- ❌ Renommé en `.OLD` (plus utilisé)

#### services/__init__.py
- ❌ Supprimé import `TenantService`

---

### 3. Database (shared/database.py)

**Changements:**
- ✅ Renommé `set_tenant_schema()` → `set_user_schema(user_id)`
- ✅ Renommé `create_tenant_schema()` → `create_user_schema(user_id)`
- ✅ Schema name: `client_{id}` → `user_{id}`

---

### 4. API Routes (api/auth.py)

#### POST /auth/register
**Avant:**
```json
{
  "company_name": "Ma Boutique",
  "email": "user@example.com",
  "password": "SecurePass123!",
  "full_name": "John Doe"
}
```

**Après:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "full_name": "John Doe"
}
```

**Comportement:**
1. Crée directement le User (pas de Tenant)
2. Applique tier `starter` par défaut
3. Crée schema PostgreSQL `user_{id}`
4. Retourne tokens JWT

#### POST /auth/login
**Avant:**
```json
{
  "access_token": "...",
  "user_id": 1,
  "tenant_id": 1,
  "role": "admin"
}
```

**Après:**
```json
{
  "access_token": "...",
  "user_id": 1,
  "role": "user",
  "subscription_tier": "starter"
}
```

---

### 5. Schemas (schemas/auth_schemas.py)

**Changements:**
- ❌ Supprimé champ `company_name` dans `RegisterRequest`
- ❌ Supprimé champ `tenant_id` dans `TokenResponse`
- ✅ Ajouté champ `subscription_tier` dans `TokenResponse`

---

## 🔧 À FAIRE pour terminer

### 1. Recréer la base de données

```bash
# Se connecter à PostgreSQL
docker exec -it stoflow_postgres psql -U stoflow_user -d stoflow_db

# Supprimer TOUTES les tables (ATTENTION: perte de données!)
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;

# Quitter psql
\q
```

### 2. Créer nouvelle migration Alembic

```bash
# Supprimer anciennes migrations
rm migrations/versions/*.py

# Créer nouvelle migration avec nouveau modèle
alembic revision --autogenerate -m "simplified user model without tenant"

# Appliquer la migration
alembic upgrade head
```

### 3. Tester l'API

```bash
# Démarrer l'API
uvicorn main:app --reload --port 8000

# Test 1: Register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!",
    "full_name": "Test User"
  }'

# Devrait retourner:
# {
#   "access_token": "...",
#   "refresh_token": "...",
#   "user_id": 1,
#   "role": "user",
#   "subscription_tier": "starter"
# }

# Test 2: Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!"
  }'

# Test 3: Vérifier schema créé
docker exec -it stoflow_postgres psql -U stoflow_user -d stoflow_db \
  -c "\dn" # Devrait voir "user_1"
```

---

## 📊 Architecture finale

```
PostgreSQL: stoflow_db
├── public (tables communes)
│   ├── users (id, email, password, subscription_tier, max_products, vinted_cookies...)
│   ├── platform_mappings (partagé)
│   ├── brands, categories, colors, etc. (partagé)
│
├── user_1 (isolation user ID 1)
│   ├── products
│   ├── vinted_products
│   ├── publications_history
│   └── ai_generations_log
│
├── user_2 (isolation user ID 2)
│   └── ...
```

---

## 🔐 Sécurité

**Isolation:**
- Chaque user a son propre schema PostgreSQL (`user_{id}`)
- `search_path` configuré automatiquement via middleware (à implémenter)
- Impossible pour user_1 d'accéder aux données de user_2

**Limites d'abonnement:**
- Starter: 50 produits, 2 plateformes, 0 crédits IA
- Standard: 200 produits, 5 plateformes, 100 crédits IA
- Premium: Illimité produits/plateformes, 500 crédits IA
- Business/Enterprise: Illimité + crédits IA élevés

---

## 📝 Fichiers modifiés

| Fichier | Statut | Changements |
|---------|--------|-------------|
| `models/public/user.py` | ✅ Modifié | Supprimé tenant_id, ajouté subscription fields |
| `models/public/tenant.py` | ❌ Renommé .OLD | Plus utilisé |
| `models/public/subscription.py` | ❌ Renommé .OLD | Plus utilisé |
| `services/auth_service.py` | ✅ Modifié | Simplifié tokens JWT, ajouté get_subscription_limits() |
| `services/tenant_service.py` | ❌ Renommé .OLD | Plus utilisé |
| `services/__init__.py` | ✅ Modifié | Supprimé import TenantService |
| `shared/database.py` | ✅ Modifié | Renommé fonctions tenant → user |
| `api/auth.py` | ✅ Modifié | Simplifié register/login |
| `schemas/auth_schemas.py` | ✅ Modifié | Supprimé company_name, tenant_id |

**Total fichiers modifiés:** 8
**Total fichiers supprimés:** 3

---

## 🚀 Prochaines étapes

1. ✅ DROP database et recréer
2. ✅ Tester register + login
3. ⏭️ Modifier middleware pour utiliser `user_id` au lieu de `tenant_id`
4. ⏭️ Modifier API produits pour utiliser `user_id`
5. ⏭️ Mettre à jour tests unitaires

---

**Temps estimé pour terminer:** 1 heure
**Complexité:** Moyenne (principalement DB reset et tests)
