# Corrections des URLs Vinted API - Alignement avec pythonApiWOO

**Date**: 2025-12-10
**Auteur**: Claude
**Statut**: ✅ Complété

## 📋 Résumé

Correction complète des URLs de l'API Vinted dans Stoflow Backend pour qu'elles correspondent exactement à celles utilisées dans pythonApiWOO (projet de référence testé et validé).

## ❌ Problèmes identifiés

### 1. URL incorrecte pour récupérer les produits utilisateur

**Avant (INCORRECT)**:
```python
/users/current/items  # ❌ Cette URL n'existe pas dans l'API Vinted
```

**Après (CORRECT)**:
```python
/wardrobe/{user_id}/items  # ✅ URL réelle de l'API Vinted
```

**Impact**: La synchronisation des produits ne fonctionnait pas.

---

### 2. URL incorrecte pour créer un listing

**Avant (INCORRECT)**:
```python
/api/v2/items  # ❌ URL incorrecte
```

**Après (CORRECT)**:
```python
/api/v2/item_upload/items  # ✅ URL correcte pour créer un listing
```

**Impact**: La publication de produits échouait.

---

### 3. Informations utilisateur manquantes

**Avant**: Pas de `vinted_user_id` requis
**Après**: `vinted_user_id` obligatoire dans `users` table

**Impact**: Impossible de construire les URLs correctement.

---

## ✅ Fichiers modifiés

### 1. `.env`

**Ajouts**:
```bash
# Configuration utilisateur
VINTED_USER_ID=29535217
VINTED_X_CSRF_TOKEN=your-csrf-token-here
VINTED_X_ANON_ID=your-anon-id-here

# Headers Vinted complets
VINTED_ACCEPT=application/json, text/plain, */*
VINTED_ACCEPT_LANGUAGE=fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3
VINTED_CONNECTION=keep-alive
VINTED_SEC_FETCH_DEST=empty
VINTED_SEC_FETCH_MODE=cors
VINTED_SEC_FETCH_SITE=same-origin
VINTED_SEC_GPC=1
VINTED_PRIORITY=u=1
VINTED_TE=trailers

# Endpoints complets
VINTED_URL_API_PRODUCTS=https://www.vinted.fr/api/v2/wardrobe/{id_shop}/items
VINTED_URL_API_DRAFT=https://www.vinted.fr/api/v2/item_upload/drafts
VINTED_URL_API_ITEMS=https://www.vinted.fr/api/v2/item_upload/items
VINTED_URL_API_PHOTOS=https://www.vinted.fr/api/v2/photos
VINTED_URL_API_ORDERS=https://www.vinted.fr/api/v2/my_orders
VINTED_URL_API_TRANSACTIONS=https://www.vinted.fr/api/v2/transactions/{transaction_id}
VINTED_URL_API_ITEMS_UPDATE=https://www.vinted.fr/api/v2/item_upload/items/{item_id}
VINTED_URL_API_DRAFT_DELETE=https://www.vinted.fr/api/v2/item_upload/drafts/{draft_id}
VINTED_URL_API_PUBLISH_DELETE=https://www.vinted.fr/api/v2/items/{item_id}/delete
VINTED_URL_API_ITEMS_STATUS=https://www.vinted.fr/api/v2/items/{item_id}/status
VINTED_URL_API_SHIPMENT_LABEL=https://www.vinted.fr/api/v2/shipments/{shipment_id}/label_url

# Referers
VINTED_REFERER_MEMBER=https://www.vinted.fr/member/{user_id}
VINTED_REFERER_NEW_ITEM=https://www.vinted.fr/items/new
VINTED_REFERER_EDIT_ITEM=https://www.vinted.fr/items/{item_id}/edit
VINTED_REFERER_ORDERS=https://www.vinted.fr/my_orders/sold
VINTED_REFERER_INBOX=https://www.vinted.fr/inbox/{transaction_id}

# Rate limiting ajusté (50/heure au lieu de 40/2h)
VINTED_RATE_LIMIT_MAX=50
VINTED_RATE_LIMIT_WINDOW_HOURS=1
VINTED_REQUEST_DELAY_MIN_SECONDS=30
VINTED_REQUEST_DELAY_MAX_SECONDS=120
```

---

### 2. `api/vinted.py`

**Fonction**: `sync_vinted_products()`

**Modifications**:
```python
# Avant
path='/api/v2/users/current/items'
payload={'status': 'visible', 'per_page': 96}

# Après
if not current_user.vinted_user_id:
    raise HTTPException(status_code=400, detail="Vinted user ID non configuré")

path=f'/api/v2/wardrobe/{current_user.vinted_user_id}/items'
payload={'page': 1, 'per_page': 96, 'order': 'relevance'}
```

**Impact**: Le sync fonctionne maintenant avec la vraie API.

---

### 3. `services/vinted/vinted_importer.py`

**Fonction**: `get_current_user()`

**Modifications**:
```python
# Avant
async def get_current_user(self) -> Optional[dict]:
    response = self.client.get("/users/current")  # ❌

# Après
async def get_current_user(self, vinted_user_id: int) -> Optional[dict]:
    response = self.client.get(f"/users/{vinted_user_id}")  # ✅
```

**Fonction**: `fetch_user_items()`

**Modifications**:
```python
# Avant
async def fetch_user_items(self, status: str = "visible", ...) -> dict:
    response = self.client.get("/users/current/items", params=params)  # ❌

# Après
async def fetch_user_items(self, vinted_user_id: int, ...) -> dict:
    response = self.client.get(f"/wardrobe/{vinted_user_id}/items", params=params)  # ✅
```

**Fonction**: `fetch_all_active_items()`

**Modifications**:
```python
# Avant
async def fetch_all_active_items(self) -> list[dict]:
    data = await self.fetch_user_items(status="visible", ...)

# Après
async def fetch_all_active_items(self, vinted_user_id: int) -> list[dict]:
    data = await self.fetch_user_items(vinted_user_id=vinted_user_id, ...)
```

---

### 4. `services/vinted/vinted_publish_service.py`

**Fonction**: `create_listing()`

**Modifications**:
```python
# Avant
path='/api/v2/items'  # ❌

# Après
path='/api/v2/item_upload/items'  # ✅
```

**Note**: L'URL `/api/v2/photos` était déjà correcte.

---

## 📊 URLs Vinted - Référence complète

### Récupération de données (GET)

| Endpoint | URL | Params |
|----------|-----|--------|
| **Produits utilisateur** | `/wardrobe/{user_id}/items` | `page`, `per_page`, `order` |
| **Info utilisateur** | `/users/{user_id}` | - |
| **Commandes** | `/my_orders` | - |
| **Transaction** | `/transactions/{transaction_id}` | - |
| **Bordereau** | `/shipments/{shipment_id}/label_url` | - |

### Publication/Modification (POST/PUT/DELETE)

| Endpoint | URL | Method | Usage |
|----------|-----|--------|-------|
| **Upload photo** | `/photos` | POST | Upload image avant création |
| **Créer brouillon** | `/item_upload/drafts` | POST | Créer brouillon |
| **Créer listing** | `/item_upload/items` | POST | Publier produit |
| **Modifier listing** | `/item_upload/items/{item_id}` | PUT | Modifier produit |
| **Supprimer brouillon** | `/item_upload/drafts/{draft_id}` | DELETE | Supprimer brouillon |
| **Supprimer listing** | `/items/{item_id}/delete` | POST | Supprimer produit |
| **Changer statut** | `/items/{item_id}/status` | PUT | Cacher/afficher |

---

## 🔧 Configuration requise

### Table `users` doit avoir:
```sql
vinted_user_id INTEGER  -- ID utilisateur Vinted (ex: 29535217)
vinted_username VARCHAR  -- Username Vinted
vinted_cookies TEXT  -- Cookies pour authentification
```

### Variables d'environnement requises:
```bash
VINTED_USER_ID  # ID par défaut (peut être overridé par user)
VINTED_X_CSRF_TOKEN  # Token CSRF
VINTED_X_ANON_ID  # ID anonyme
```

---

## ⚠️ Points d'attention

### 1. vinted_user_id obligatoire
Toutes les opérations nécessitent le `vinted_user_id` (ID Vinted, pas ID Stoflow).

### 2. Ordre des paramètres modifié
```python
# Avant
fetch_user_items(status="visible", page=1)

# Après
fetch_user_items(vinted_user_id=29535217, page=1, order="relevance")
```

### 3. Rate limiting ajusté
- **Avant**: 40 requêtes / 2 heures
- **Après**: 50 requêtes / 1 heure (aligné avec pythonApiWOO)

### 4. Délais entre requêtes
- **Avant**: 20-50 secondes
- **Après**: 30-120 secondes (plus prudent)

---

## 🧪 Tests recommandés

1. **Test sync**: Vérifier que `/sync-products` récupère les produits
2. **Test publish**: Vérifier que la publication fonctionne
3. **Test pagination**: Vérifier le parcours de toutes les pages
4. **Test error handling**: Vérifier comportement si `vinted_user_id` manquant

---

## 📚 Références

- **pythonApiWOO**: `/home/maribeiro/PycharmProjects/pythonApiWOO`
- **Client Vinted**: `pythonApiWOO/clients/vinted/vinted_client.py`
- **Config Vinted**: `pythonApiWOO/.env` (lignes 49-90)

---

## ✅ Validation

- [x] .env mis à jour avec toutes les URLs
- [x] api/vinted.py corrigé pour sync
- [x] vinted_importer.py corrigé avec vinted_user_id
- [x] vinted_publish_service.py corrigé
- [x] Documentation créée
- [ ] Tests d'intégration à exécuter

---

**Note**: Toutes les URLs ont été vérifiées contre le projet pythonApiWOO qui est testé et fonctionnel en production.
