# Vinted API Endpoints - Référence Validée

> **Documentation des endpoints Vinted API validés et fonctionnels**
>
> Date: 2026-01-15
>
> ⚠️ **IMPORTANT**: Tous ces endpoints doivent être appelés via le plugin (WebSocket) pour accéder à l'API Vinted avec les cookies de session utilisateur.

---

## 📋 Table des matières

- [Produits (Items)](#produits-items)
- [Utilisateurs (Users/Sellers)](#utilisateurs-userssellers)
- [Garde-robe (Wardrobe)](#garde-robe-wardrobe)
- [Transactions](#transactions)
- [Photos](#photos)

---

## Produits (Items)

### Détails d'un produit (item_upload)

**Endpoint le plus complet pour enrichir les produits**

```
GET /api/v2/item_upload/items/{vinted_id}
```

**Usage actuel**: `VintedProductEnricher` (backend/services/vinted/vinted_product_enricher.py:46)

**Données retournées**:
- Description complète
- IDs Vinted (brand_id, size_id, catalog_id, status_id, color1_id, color2_id)
- Dimensions (width, length, unit)
- Attributs (is_unisex, manufacturer_labelling, item_attributes)
- Photos (photos_data)
- Prix et devise
- Status (is_draft, etc.)

### Détails d'un produit (standard)

```
GET /api/v2/items/{item_id}
```

**Usage**: Alternative plus légère que item_upload

### Créer un produit

```
POST /api/v2/items
```

**Usage actuel**: Via plugin pour publier des produits

### Mettre à jour un produit

```
PUT /api/v2/items/{item_id}
```

### Supprimer un produit

```
DELETE /api/v2/items/{item_id}
```

---

## Utilisateurs (Users/Sellers)

### ✅ Informations vendeur (direct)

```
GET /api/v2/users/{user_id}
```

**Exemple**: `GET /api/v2/users/23099232`

**Testé**: ✅ Fonctionne (2026-01-15)

**Données probables**:
```json
{
  "user": {
    "id": 23099232,
    "login": "username",
    "real_name": "...",
    "feedback_reputation": 4.95,
    "feedback_count": 150,
    "positive_feedback_count": 148,
    "follower_count": 45,
    "verification": {...},
    "business": false
  }
}
```

### ✅ Informations vendeur (query param)

```
GET /api/v2/users?id={user_id}
```

**Exemple**: `GET /api/v2/users?id=23099232`

**Testé**: ✅ Fonctionne (2026-01-15)

### ✅ Liste des abonnés

```
GET /api/v2/users/{user_id}/followers
```

**Exemple**: `GET /api/v2/users/23099232/followers`

**Testé**: ✅ Fonctionne (2026-01-15)

**Paramètres**:
- `page` (int): Numéro de page
- `per_page` (int): Résultats par page (max 100)

### ✅ Recherche d'utilisateurs

```
GET /api/v2/users/search?query={username}
```

**Exemple**: `GET /api/v2/users/search?query=vintage_seller`

**Testé**: ✅ Fonctionne (2026-01-15)

### Abonnements (following)

```
GET /api/v2/users/{user_id}/following
```

**Testé**: ⏳ À tester

---

## Garde-robe (Wardrobe)

### Produits d'un vendeur

```
GET /api/v2/users/{user_id}/items
GET /wardrobe/{user_id}/items
```

**Paramètres**:
- `page` (int): Numéro de page
- `per_page` (int): Résultats par page (20-96)
- `order` (string): "relevance", "newest", etc.

**Usage actuel**: `VintedAPIBridge.getWardrobe()` (plugin/src/content/vinted-api-bridge.ts:159)

---

## Transactions

### Liste des transactions

```
GET /api/v2/transactions
```

**Usage actuel**: `VintedAPIBridge.getTransactions()` (plugin/src/content/vinted-api-bridge.ts:191)

---

## Photos

### Upload photo

```
POST /api/v2/item_upload/photos
```

**Body**: FormData
- `file`: File
- `temp_uuid`: string

**Usage actuel**: `VintedAPIBridge.uploadPhoto()` (plugin/src/content/vinted-api-bridge.ts:226)

---

## 🔒 Règles d'utilisation

### ⛔ INTERDIT

- ❌ Appeler ces URLs directement avec `curl` ou `requests` depuis le backend
- ❌ Bypasser le plugin pour accéder aux APIs Vinted
- ❌ Stocker ou logger les tokens/cookies Vinted

### ✅ OBLIGATOIRE

- ✅ Toujours passer par `PluginWebSocketHelper.call_plugin_http()`
- ✅ Le plugin exécute la requête dans le contexte du navigateur (cookies session)
- ✅ Respecter les délais entre requêtes (rate limiting côté plugin)
- ✅ Gérer les timeouts (60s par défaut)

### Exemple d'appel correct

```python
from services.plugin_websocket_helper import PluginWebSocketHelper

result = await PluginWebSocketHelper.call_plugin_http(
    db=db,
    user_id=user_id,
    http_method="GET",
    path="/api/v2/users/23099232",
    timeout=60,
    description="Get seller info"
)
```

---

## 📊 Endpoints à tester

**Ces endpoints n'ont pas encore été validés mais sont probables** :

### Statistiques vendeur

```
GET /api/v2/users/{user_id}/stats
```

### Reviews/Feedback

```
GET /api/v2/users/{user_id}/feedback
GET /api/v2/users/{user_id}/reviews
```

### Conversations/Messages

```
GET /api/v2/conversations
GET /api/v2/conversations/{conversation_id}
POST /api/v2/conversations/{conversation_id}/messages
```

### Recherche de produits

```
GET /api/v2/catalog/items
```

**Paramètres** (probables):
- `search_text`: Texte de recherche
- `catalog_ids[]`: IDs catégories
- `brand_ids[]`: IDs marques
- `size_ids[]`: IDs tailles
- `color_ids[]`: IDs couleurs
- `price_from`, `price_to`: Fourchette prix

---

## 🚀 Intégration dans StoFlow

### Service Backend

Les endpoints validés sont intégrés dans :

| Service | Fichier | Endpoints |
|---------|---------|-----------|
| VintedProductEnricher | `backend/services/vinted/vinted_product_enricher.py` | `/api/v2/item_upload/items/{id}` |
| VintedAPIBridge | `plugin/src/content/vinted-api-bridge.ts` | Wardrobe, transactions, photos |

### Nouveaux services à créer

Pour les endpoints users/sellers validés (2026-01-15), créer :

- `backend/services/vinted/vinted_user_service.py` - Service pour info vendeurs
- `backend/api/vinted/users.py` - Routes API vendeurs

---

## 📝 Notes de version

| Date | Endpoints validés | Note |
|------|-------------------|------|
| 2026-01-15 | `/api/v2/users/{id}`, `/api/v2/users?id={id}`, `/api/v2/users/{id}/followers`, `/api/v2/users/search?query=` | Validés manuellement dans le navigateur |
| 2026-01-05 | `/api/v2/item_upload/items/{id}` | Remplace le parsing HTML pour l'enrichissement |
| 2025-12-11 | Wardrobe, transactions, photos | Intégrés dans VintedAPIBridge |

---

**Dernière mise à jour**: 2026-01-15
