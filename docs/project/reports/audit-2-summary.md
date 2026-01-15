# Security Audit 2 - Summary of Changes

**Date:** 2026-01-08
**Worktree:** `~/StoFlow-fix-audit-2`
**Branch:** `hotfix/fix-audit-2`

---

## 🎯 Objectifs

Corriger les problèmes critiques de sécurité identifiés lors de l'audit :

1. **Isolation multi-tenant** : Prévenir la pollution du `search_path` PostgreSQL
2. **Double publication** : Éviter les publications en double via idempotence
3. **Architecture générique** : Unifier le système de jobs pour toutes les marketplaces

---

## ✅ Modifications Effectuées

### 1. Isolation Multi-Tenant (🔴 CRITIQUE)

**Fichier:** `backend/api/dependencies/__init__.py`

**Changements:**
- ✅ Ligne 418 : `SET search_path` → `SET LOCAL search_path`
- ✅ Lignes 427-437 : Warning → **Exception critique** si mismatch détecté

**Impact:**
- `SET LOCAL` reset automatique au COMMIT/ROLLBACK
- Empêche pollution du pool de connexions
- Force client retry avec connexion propre si isolation compromise

**Code:**
```python
# AVANT
db.execute(text(f"SET search_path TO {schema_name}, public"))
if schema_name not in actual_path:
    logger.warning(...)
    db.execute(text(f"SET search_path TO {schema_name}, public"))

# APRÈS
db.execute(text(f"SET LOCAL search_path TO {schema_name}, public"))
if schema_name not in actual_path:
    logger.critical(...)
    db.close()
    raise HTTPException(status_code=500, ...)
```

---

### 2. Modèle MarketplaceJob - Idempotency Key (🔴 CRITIQUE)

**Fichier:** `backend/models/user/marketplace_job.py`

**Changement:**
```python
idempotency_key: Mapped[str | None] = mapped_column(
    String(64),
    nullable=True,
    unique=True,  # ← UNIQUE constraint
    index=True,
    comment="Unique key to prevent duplicate publications"
)
```

**Impact:**
- Évite publications en double
- Clé générée par client (format: `pub_{product_id}_{uuid}`)
- Index unique partiel (WHERE idempotency_key IS NOT NULL)

---

### 3. Migration Alembic

**Fichier:** `backend/migrations/versions/20260108_1640_add_idempotency_key_to_marketplace_jobs.py`

**Fonctionnalités:**
- ✅ Itère sur tous les schemas `user_*`
- ✅ Ajoute colonne `idempotency_key VARCHAR(64)`
- ✅ Crée index unique partiel
- ✅ Met à jour `template_tenant` pour nouveaux users
- ✅ Downgrade fonctionnel

**Schemas impactés:**
- Tous les `user_X` existants
- `template_tenant` (pour nouveaux users)

---

### 4. BasePublishHandler - Classe Abstraite (🟡 IMPORTANT)

**Fichier:** `backend/services/marketplace/handlers/base_publish_handler.py` (NOUVEAU)

**Responsabilités:**
1. **Idempotence** : Vérification via `idempotency_key`
2. **Validation produit** : Titre, prix, stock
3. **Upload photos** : Avec tracking des IDs
4. **Cleanup** : Logging photos orphelines en cas d'échec
5. **Gestion erreurs** : Exceptions typées (ConflictError, ValidationError)

**Méthodes abstraites:**
```python
@abstractmethod
def marketplace_name(self) -> str: ...

@abstractmethod
async def _upload_photos(self, product: Product) -> list[int]: ...

@abstractmethod
async def _create_listing(self, product: Product, photo_ids: list[int]) -> dict: ...
```

---

### 5. Handlers de Publication (🟡 IMPORTANT)

#### VintedPublishHandler

**Fichier:** `backend/services/marketplace/handlers/vinted/publish_handler.py` (NOUVEAU)

**Spécificités:**
- Upload photos via **plugin browser**
- Réutilise services existants (mapping, pricing, title, description)
- Sauvegarde `VintedProduct`

#### EbayPublishHandler

**Fichier:** `backend/services/marketplace/handlers/ebay/publish_handler.py` (NOUVEAU)

**Spécificités:**
- Photos gérées lors de création listing (pas d'upload séparé)
- API directe eBay (pas de plugin)
- Requiert `marketplace_id` (EBAY_FR, EBAY_GB, etc.)

#### EtsyPublishHandler

**Fichier:** `backend/services/marketplace/handlers/etsy/publish_handler.py` (NOUVEAU)

**Spécificités:**
- Photos gérées lors de création listing
- API directe Etsy (pas de plugin)
- Requiert `taxonomy_id`, `shipping_profile_id`

---

## 📊 Résumé des Fichiers

| Type | Action | Fichier |
|------|--------|---------|
| 🔴 **Critique** | Modifié | `backend/api/dependencies/__init__.py` |
| 🔴 **Critique** | Modifié | `backend/models/user/marketplace_job.py` |
| 🔴 **Critique** | Créé | `backend/migrations/versions/20260108_1640_*.py` |
| 🟡 **Important** | Créé | `backend/services/marketplace/handlers/base_publish_handler.py` |
| 🟡 **Important** | Créé | `backend/services/marketplace/handlers/vinted/publish_handler.py` |
| 🟡 **Important** | Créé | `backend/services/marketplace/handlers/ebay/publish_handler.py` |
| 🟡 **Important** | Créé | `backend/services/marketplace/handlers/etsy/publish_handler.py` |
| 📚 **Doc** | Créé | `backend/services/marketplace/handlers/README.md` |

**Total:** 8 fichiers (2 modifiés, 6 créés)

---

## 🧪 Tests à Effectuer

### Test 1: Isolation Multi-Tenant
```bash
# Créer 2 users via API
# User 1 : créer produit A
# User 2 : créer produit B
# ✅ Vérifier User 1 ne voit que produit A
# ✅ Vérifier User 2 ne voit que produit B
```

### Test 2: Idempotence
```python
# Publier avec idempotency_key = "pub_123_abc"
handler1 = VintedPublishHandler(db, job_id=job1.id, user_id=1)
result1 = await handler1.execute()

# Republier avec MÊME key
handler2 = VintedPublishHandler(db, job_id=job2.id, user_id=1)
result2 = await handler2.execute()

# ✅ Vérifier result2["cached"] == True
# ✅ Vérifier 1 SEUL listing créé sur Vinted
```

### Test 3: Photos Orphelines
```python
# Mocker échec après upload photo 2
with patch("handler._create_listing", side_effect=Exception("API Error")):
    try:
        await handler.execute()
    except Exception:
        pass

# ✅ Vérifier logs contiennent "PARTIAL FAILURE"
# ✅ Vérifier logs contiennent "photo_ids=[111, 222]"
```

---

## ⚠️ Actions Requises

### 1. Migration Alembic (BLOQUÉ)

**Problème:** Base de données référence révision du worktree `develop` qui n'existe pas dans `fix-audit-2`.

**Options:**
1. **Utiliser DB de test** : `docker-compose -f docker-compose.test.yml up -d`
2. **Reset Alembic** : Stopper tous les envs et `alembic stamp head`
3. **Attendre merge** : Merger dans develop avant d'exécuter migration

**Commande (une fois résolu):**
```bash
cd backend
source venv/bin/activate
alembic upgrade head
```

### 2. Mise à Jour des Routes (OPTIONNEL)

**Ancien code (VintedJob):**
```python
from services.vinted.vinted_job_service import VintedJobService

job_service = VintedJobService(db)
job = job_service.create_job(action_code="publish", product_id=product_id)
# ...
```

**Nouveau code (MarketplaceJob):**
```python
from services.marketplace.handlers.vinted.publish_handler import VintedPublishHandler

job = MarketplaceJob(
    marketplace="vinted",
    product_id=product_id,
    action_type_id=1,
    idempotency_key=f"pub_{product_id}_{uuid4().hex[:16]}",
    status=JobStatus.PENDING
)
db.add(job)
db.commit()

handler = VintedPublishHandler(db, job_id=job.id, user_id=user_id)
result = await handler.execute()
```

---

## 📈 Impact et Bénéfices

| Aspect | Avant | Après |
|--------|-------|-------|
| **Isolation multi-tenant** | ⚠️ Risk de pollution | ✅ SET LOCAL + exception |
| **Double publication** | ❌ Possible | ✅ Idempotency key |
| **Architecture jobs** | ❌ Spécifique Vinted | ✅ Générique (Vinted, eBay, Etsy) |
| **Photos orphelines** | ❌ Silencieux | ✅ Loggées pour cleanup |
| **Handlers** | ❌ Duplication logique | ✅ BasePublishHandler réutilisable |

---

## 🚀 Déploiement

### Ordre recommandé

1. **Merger dans develop**
   ```bash
   cd ~/StoFlow
   git checkout develop
   git pull origin develop
   ```

2. **Merger hotfix**
   ```bash
   git merge hotfix/fix-audit-2
   ```

3. **Exécuter migration**
   ```bash
   cd backend
   source venv/bin/activate
   alembic upgrade head
   ```

4. **Vérifier**
   ```bash
   # Vérifier colonne existe
   psql -c "\d user_1.marketplace_jobs" stoflow_dev

   # Vérifier index
   psql -c "\di user_1.idx_*_marketplace_jobs_idempotency_key" stoflow_dev
   ```

5. **Tests end-to-end**
   - Test isolation multi-tenant
   - Test idempotence
   - Test handlers Vinted/eBay/Etsy

---

## 📚 Documentation

- **README handlers** : `backend/services/marketplace/handlers/README.md`
- **Migration** : `backend/migrations/versions/20260108_1640_*.py`
- **Plan audit** : `/home/maribeiro/.claude/plans/bright-bubbling-hammock.md`

---

**Statut:** ✅ Implémentation terminée, migration en attente de résolution DB

**Prochaines étapes:**
1. Résoudre conflit révision Alembic
2. Exécuter migration
3. Tests end-to-end
4. Merge dans develop
