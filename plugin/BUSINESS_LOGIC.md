# 💼 Logique Métier - StoFlow Plugin (Proxy HTTP Générique)

## 🎯 Vue d'ensemble

Le plugin StoFlow est un **proxy HTTP générique** qui permet au backend d'exécuter n'importe quelle requête HTTP sur Vinted en utilisant la session authentifiée de l'utilisateur.

### Principe clé

```
Backend ──(tâche HTTP)──> Plugin ──(cookies + tokens)──> Vinted API
Backend <─(réponse)────── Plugin <─(JSON/data)────────── Vinted API
```

Le plugin est un **intermédiaire transparent** : il n'a aucune logique métier Vinted, il exécute simplement ce que le backend lui demande.

---

## 🔄 Architecture de Communication

### 1. Polling (Interrogation régulière)

Le plugin interroge le backend **toutes les 5 secondes** :

```
┌─────────────────────────────────────────────────────────────┐
│                     BACKEND (FastAPI)                       │
│                                                             │
│  Table: plugin_tasks                                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ id | task_type    | status  | payload (JSONB)      │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │ 1  | HTTP_REQUEST | PENDING | {"url": "...", ...}  │  │
│  │ 2  | HTTP_REQUEST | PENDING | {"url": "...", ...}  │  │
│  └──────────────────────────────────────────────────────┘  │
│                            ▲                                │
│                            │ GET /api/plugin/tasks          │
│                            │ Bearer: JWT token              │
│                            │ (toutes les 5s)                │
└────────────────────────────┼────────────────────────────────┘
                             │
                             │
┌────────────────────────────┼────────────────────────────────┐
│                     PLUGIN FIREFOX                          │
│                            │                                │
│  Background Script (task-poller.ts)                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Polling Loop:                                        │  │
│  │  1. Récupère JWT token du storage                    │  │
│  │  2. GET /api/plugin/tasks (Authorization: Bearer)    │  │
│  │  3. Si tâche → execute()                             │  │
│  │  4. Sinon → attendre 5s                              │  │
│  └──────────────────────────────────────────────────────┘  │
│                            │                                │
│  Content Script (proxy.ts)                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  1. Extrait X-CSRF-Token du HTML                     │  │
│  │  2. Extrait X-Anon-Id du HTML                        │  │
│  │  3. Merge avec headers custom                        │  │
│  │  4. fetch() avec credentials: 'include'              │  │
│  │  5. Renvoie la réponse brute                         │  │
│  └──────────────────────────────────────────────────────┘  │
│                            │                                │
│                            │ POST /api/plugin/tasks/1/result│
│                            ▼                                │
└────────────────────────────┼────────────────────────────────┘
                             │
                             │
┌────────────────────────────┼────────────────────────────────┐
│                     BACKEND (FastAPI)                       │
│                            │                                │
│  POST /api/plugin/tasks/{id}/result                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  {                                                    │  │
│  │    "success": true,                                   │  │
│  │    "status": 200,                                     │  │
│  │    "headers": {...},                                  │  │
│  │    "data": {...},                                     │  │
│  │    "execution_time_ms": 450                           │  │
│  │  }                                                    │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  → UPDATE plugin_tasks SET status='SUCCESS', result=...    │
│  → Traite la réponse selon la logique métier               │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 Structure d'une tâche HTTP

### Format de base

```json
{
  "task_type": "HTTP_REQUEST",
  "status": "PENDING",
  "payload": {
    "url": "https://www.vinted.fr/api/v2/users/me",
    "method": "GET",
    "headers": {},
    "body": null,
    "content_type": "json"
  }
}
```

### Champs du payload

| Champ | Type | Requis | Description |
|-------|------|--------|-------------|
| `url` | string | ✅ | URL complète de l'API Vinted |
| `method` | string | ✅ | GET, POST, PUT, DELETE, PATCH |
| `headers` | object | ❌ | Headers custom (surcharge possible) |
| `body` | any | ❌ | Body de la requête (JSON) |
| `content_type` | string | ❌ | "json" (défaut) ou "multipart" |
| `files` | array | ❌ | Fichiers pour multipart (voir section upload) |

---

## 🔐 Injection automatique des credentials

Le plugin injecte automatiquement dans **TOUTES** les requêtes :

### 1. Cookies (automatique via fetch)

```typescript
fetch(url, {
  credentials: 'include'  // ← Cookies Vinted automatiques
})
```

### 2. Headers Vinted

```typescript
const autoHeaders = {
  'X-CSRF-Token': userData.csrf_token,  // Extrait du HTML
  'X-Anon-Id': userData.anon_id,        // Extrait du HTML
  'Accept': 'application/json',
  'Content-Type': 'application/json'    // Si body JSON
};
```

### 3. Merge avec headers custom

Le backend peut surcharger les headers auto :

```json
{
  "payload": {
    "url": "...",
    "headers": {
      "X-CSRF-Token": "custom-token",  // ← Surcharge le token auto
      "X-Custom-Header": "value"        // ← Header additionnel
    }
  }
}
```

Résultat final :
```typescript
const finalHeaders = {
  ...autoHeaders,           // Headers automatiques
  ...payload.headers        // Headers custom (surcharge possible)
};
```

---

## 📝 Exemples de tâches

### 1. GET simple (récupérer un produit)

```json
{
  "task_type": "HTTP_REQUEST",
  "payload": {
    "url": "https://www.vinted.fr/api/v2/items/123456",
    "method": "GET"
  }
}
```

**Résultat :**
```json
{
  "success": true,
  "status": 200,
  "data": {
    "id": 123456,
    "title": "T-shirt Nike",
    "price": "15.00",
    "description": "..."
  }
}
```

### 2. GET avec pagination (liste des produits)

```json
{
  "task_type": "HTTP_REQUEST",
  "payload": {
    "url": "https://www.vinted.fr/api/v2/wardrobe/29535217/items?page=1&per_page=20",
    "method": "GET"
  }
}
```

**Résultat :**
```json
{
  "success": true,
  "status": 200,
  "data": {
    "items": [...],
    "pagination": {
      "current_page": 1,
      "total_pages": 80,
      "total_entries": 1595
    }
  }
}
```

### 3. PUT (modifier un produit)

```json
{
  "task_type": "HTTP_REQUEST",
  "payload": {
    "url": "https://www.vinted.fr/api/v2/items/123456",
    "method": "PUT",
    "body": {
      "price": "15.99",
      "description": "Nouveau texte"
    }
  }
}
```

**Résultat :**
```json
{
  "success": true,
  "status": 200,
  "data": {
    "id": 123456,
    "price": "15.99",
    "description": "Nouveau texte"
  }
}
```

### 4. DELETE (supprimer un produit)

```json
{
  "task_type": "HTTP_REQUEST",
  "payload": {
    "url": "https://www.vinted.fr/api/v2/items/123456",
    "method": "DELETE"
  }
}
```

**Résultat :**
```json
{
  "success": true,
  "status": 204,
  "data": null
}
```

### 5. POST multipart (upload photo)

```json
{
  "task_type": "HTTP_REQUEST",
  "payload": {
    "url": "https://www.vinted.fr/api/v2/photos",
    "method": "POST",
    "content_type": "multipart",
    "files": [{
      "field": "photo",
      "filename": "product.jpg",
      "content": "iVBORw0KGgoAAAANSUhEUgAA...",  // Base64
      "mime_type": "image/jpeg"
    }],
    "body": {
      "product_id": 123456
    }
  }
}
```

**Résultat :**
```json
{
  "success": true,
  "status": 201,
  "data": {
    "id": 789,
    "url": "https://images.vinted.net/...",
    "thumbnail_url": "https://images.vinted.net/..."
  }
}
```

---

## 🔄 Gestion de la pagination

Le backend gère la pagination en créant **plusieurs tâches** :

### Backend crée N tâches

```python
total_pages = 80  # Récupéré lors de la première requête

for page in range(1, total_pages + 1):
    task = {
        "task_type": "HTTP_REQUEST",
        "payload": {
            "url": f"https://www.vinted.fr/api/v2/wardrobe/{user_id}/items?page={page}",
            "method": "GET"
        }
    }
    db.add(PluginTask(**task))

db.commit()
```

### Plugin exécute les tâches séquentiellement

```
Plugin poll → Tâche page 1 → Exécute → Renvoie résultat
    ↓ (5s)
Plugin poll → Tâche page 2 → Exécute → Renvoie résultat
    ↓ (5s)
Plugin poll → Tâche page 3 → Exécute → Renvoie résultat
    ...
```

---

## 📊 Format de réponse

### Succès (2xx)

```json
{
  "success": true,
  "status": 200,
  "headers": {
    "content-type": "application/json",
    "x-request-id": "abc-123"
  },
  "data": {
    "id": 123,
    "title": "T-shirt Nike"
  },
  "execution_time_ms": 450,
  "executed_at": "2025-12-08T09:41:00Z"
}
```

### Erreur HTTP (4xx, 5xx)

```json
{
  "success": false,
  "status": 404,
  "headers": {...},
  "data": {
    "error": "Item not found"
  },
  "execution_time_ms": 250,
  "executed_at": "2025-12-08T09:41:00Z"
}
```

### Erreur d'exécution

```json
{
  "success": false,
  "status": 0,
  "error": "EXECUTION_ERROR",
  "error_message": "Aucun onglet Vinted ouvert",
  "execution_time_ms": 50,
  "executed_at": "2025-12-08T09:41:00Z"
}
```

---

## 🔒 Sécurité

### 1. Isolation des données

- **Cookies** : Restent dans le navigateur, jamais exposés au backend
- **CSRF Token** : Extrait dynamiquement à chaque requête, jamais stocké
- **Anon-Id** : Extrait dynamiquement à chaque requête, jamais stocké

### 2. Validation

Le plugin valide :
- ✅ Présence d'un onglet Vinted ouvert
- ✅ Extraction réussie des tokens (CSRF, Anon-Id)
- ✅ JWT token valide pour communiquer avec le backend

### 3. Contexte d'exécution

- Le content script s'exécute **uniquement** sur `https://www.vinted.fr/*`
- Aucune requête possible vers d'autres domaines
- Le backend ne peut pas injecter de code JavaScript

---

## 🚫 Ce que le plugin NE FAIT PAS

- ❌ Pas de logique métier Vinted (pas de "get_all_products", "update_price", etc.)
- ❌ Pas de gestion de pagination automatique
- ❌ Pas de retry automatique
- ❌ Pas de cache des réponses
- ❌ Pas de transformation des données

**Le plugin est un proxy "bête"** : il exécute ce qu'on lui demande et renvoie la réponse brute.

---

## 📈 Performance

### Temps d'exécution typiques

| Opération | Temps |
|-----------|-------|
| Polling (aucune tâche) | ~50-100ms |
| Extraction tokens | ~10-50ms |
| GET simple | ~200-500ms |
| POST avec body | ~300-700ms |
| Upload photo (multipart) | ~1-3s |

### Optimisations

1. **Polling intelligent** : Skip si une tâche est déjà en cours
2. **Cache des tokens** : Tokens extraits une fois par tâche, pas à chaque requête
3. **Pas de throttling** : Le backend gère le rate limiting

---

## 🐛 Gestion d'erreurs

### Erreurs possibles

| Erreur | Cause | Solution |
|--------|-------|----------|
| `Aucun onglet Vinted ouvert` | Pas d'onglet vinted.fr actif | User doit ouvrir Vinted |
| `Impossible de récupérer les tokens` | CSRF/Anon-Id non trouvés | Recharger la page Vinted |
| `Token expiré (401)` | JWT expired | Plugin refresh automatiquement |
| `Network error` | Timeout, connexion coupée | Retry côté backend |

### Retry logic (côté backend)

Le backend doit implémenter la logique de retry :

```python
task.retry_count += 1

if task.retry_count < task.max_retries:
    task.status = 'PENDING'  # Retry
else:
    task.status = 'FAILED'   # Abandon
```

---

## 📚 Cas d'usage typiques

### 1. Synchronisation initiale (tous les produits)

```
Backend → Crée 80 tâches (1 par page)
Plugin → Exécute séquentiellement (5s entre chaque)
Backend → Agrège les résultats en BDD
```

### 2. Modification de prix en masse

```
Backend → Crée N tâches PUT (1 par produit)
Plugin → Exécute séquentiellement
Backend → Met à jour le statut de chaque produit
```

### 3. Upload de photos

```
Backend → Encode l'image en base64
Backend → Crée 1 tâche multipart
Plugin → Convertit base64 → Blob → FormData
Plugin → Upload vers Vinted
Backend → Stocke l'URL de la photo
```

---

## 🔧 Configuration Backend

### Table plugin_tasks

```sql
CREATE TABLE plugin_tasks (
    id SERIAL PRIMARY KEY,
    task_type VARCHAR NOT NULL,           -- 'HTTP_REQUEST'
    status VARCHAR NOT NULL DEFAULT 'PENDING',  -- PENDING/SUCCESS/FAILED
    payload JSONB,                        -- {url, method, headers, body, ...}
    result JSONB,                         -- Réponse du plugin
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3
);
```

### Endpoints requis

```
GET  /api/plugin/tasks           # Retourne les tâches PENDING
POST /api/plugin/tasks/{id}/result  # Reçoit le résultat
POST /api/auth/login?source=plugin  # Authentification
POST /api/auth/refresh              # Renouvellement token
```

---

**Version** : 2.0.0
**Dernière mise à jour** : 2025-12-08
