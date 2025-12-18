# 🏗️ Architecture des Requêtes HTTP - Plugin Stoflow

## 📊 Vue d'Ensemble

Le plugin utilise une architecture **Background Script → Content Script → Vinted API** pour exécuter des requêtes HTTP authentifiées vers l'API Vinted.

```
┌─────────────────────────────────────────────────────────────────┐
│                         BACKEND STOFLOW                          │
│                    (http://localhost:8000)                       │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           │ PluginTask (http_method + path)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      BACKGROUND SCRIPT                           │
│                   (src/background/index.ts)                      │
│                                                                   │
│  • Polling toutes les 5 secondes                                │
│  • Récupère les tâches en attente via /api/plugin/tasks/pending│
│  • Exécute les tâches (PollingManager.ts)                       │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           │ chrome.tabs.sendMessage()
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                       CONTENT SCRIPT                             │
│                    (src/content/vinted.ts)                       │
│                                                                   │
│  • Injecté dans les pages www.vinted.fr/*                       │
│  • Extrait csrf_token + anon_id depuis le HTML                  │
│  • Reçoit les messages du background                            │
│  • Exécute les requêtes HTTP via fetch()                        │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           │ fetch() avec headers Vinted
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                         API VINTED                               │
│                   (https://www.vinted.fr/api/*)                  │
│                                                                   │
│  • Requêtes authentifiées avec X-CSRF-Token + X-Anon-Id        │
│  • Retourne les données JSON                                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Flux Complet d'une Requête HTTP

### 1️⃣ Backend Créé une Tâche

**Fichier**: `backend/api/plugin.py`

```python
# Créer une tâche HTTP
task = PluginTask(
    task_type="HTTP",
    platform="vinted",
    http_method="POST",            # GET, POST, PUT, DELETE
    path="/api/v2/items/123/photos",  # Path API Vinted
    payload={
        "headers": {"Content-Type": "application/json"},
        "body": {"photo_id": 456}
    },
    status=TaskStatus.PENDING
)
```

**Format de la tâche stockée** :
```json
{
  "id": 25,
  "task_type": "HTTP",
  "platform": "vinted",
  "http_method": "POST",
  "path": "/api/v2/items/123/photos",
  "payload": {
    "headers": {"Content-Type": "application/json"},
    "body": {"photo_id": 456}
  },
  "status": "PENDING"
}
```

---

### 2️⃣ Background Récupère la Tâche

**Fichier**: `src/background/PollingManager.ts:sendHeartbeat()`

```typescript
// Polling toutes les 5 secondes
const tasks = await StoflowAPI.getPendingTasks();
// Retourne: [
//   { id: 25, task_type: "HTTP", http_method: "POST", path: "/api/v2/items/123/photos", ... }
// ]
```

---

### 3️⃣ Background Envoie Message au Content Script

**Fichier**: `src/background/PollingManager.ts:executeTask()`

```typescript
// Trouver un onglet Vinted ouvert
const vintedTabs = await chrome.tabs.query({
  url: 'https://www.vinted.fr/*'
});

// Envoyer la tâche au content script
const response = await chrome.tabs.sendMessage(vintedTabs[0].id!, {
  action: 'EXECUTE_HTTP_REQUEST',
  request: {
    url: `https://www.vinted.fr${task.path}`,  // URL complète
    method: task.http_method,
    headers: task.payload?.headers || {},
    body: task.payload?.body || null
  }
});
```

**Format du message** :
```json
{
  "action": "EXECUTE_HTTP_REQUEST",
  "request": {
    "url": "https://www.vinted.fr/api/v2/items/123/photos",
    "method": "POST",
    "headers": {"Content-Type": "application/json"},
    "body": {"photo_id": 456}
  }
}
```

---

### 4️⃣ Content Script Reçoit et Traite le Message

**Fichier**: `src/content/vinted.ts:chrome.runtime.onMessage`

```typescript
if (action === 'EXECUTE_HTTP_REQUEST') {
  const req = message.request;

  // 1. Attendre que les headers soient disponibles
  await waitForHeaders();

  // 2. Récupérer les headers Vinted (csrf + anon_id)
  const vintedHeaders = getVintedHeaders();
  // Retourne: {
  //   'X-CSRF-Token': '5kE3tY8pL...',
  //   'X-Anon-Id': 'anon-123456...',
  //   'User-Agent': '...',
  //   'Accept': 'application/json'
  // }

  // 3. Merger avec les headers de la requête
  const mergedHeaders = { ...vintedHeaders, ...(req.headers || {}) };

  // 4. Construire les options fetch
  const fetchOptions: RequestInit = {
    method: req.method,
    headers: mergedHeaders,
    credentials: 'include',  // Important pour les cookies
    body: req.body ? JSON.stringify(req.body) : undefined
  };

  // 5. Exécuter la requête
  const response = await fetch(req.url, fetchOptions);
  const data = await response.json();

  // 6. Retourner le résultat au background
  sendResponse({
    success: true,
    data: data
  });
}
```

---

### 5️⃣ Content Script Exécute la Requête HTTP

**Requête HTTP réelle envoyée** :
```http
POST https://www.vinted.fr/api/v2/items/123/photos HTTP/1.1
Host: www.vinted.fr
X-CSRF-Token: 5kE3tY8pL...
X-Anon-Id: anon-123456...
Content-Type: application/json
Accept: application/json
Cookie: _vinted_fr_session=...

{"photo_id": 456}
```

**Réponse Vinted** :
```json
{
  "photo": {
    "id": 456,
    "url": "https://images.vinted.net/...",
    "is_main": false
  }
}
```

---

### 6️⃣ Background Reçoit la Réponse

**Fichier**: `src/background/PollingManager.ts:executeTask()`

```typescript
// Résultat reçu du content script
const result = await executeTask(task);
// result = { photo: { id: 456, url: "...", is_main: false } }

// Notifier le backend que la tâche est terminée
await StoflowAPI.reportTaskComplete(task.id, {
  success: true,
  result: result
});
```

---

### 7️⃣ Backend Reçoit le Résultat

**Fichier**: `backend/api/plugin.py:report_task_result()`

```python
# Mise à jour de la tâche
task.status = TaskStatus.SUCCESS
task.result = {
  "photo": {
    "id": 456,
    "url": "https://images.vinted.net/...",
    "is_main": false
  }
}
task.completed_at = datetime.utcnow()
```

---

## 🎯 Types de Messages Supportés

### 1. `GET_VINTED_USER_INFO` - Extraction d'infos utilisateur

**Usage**: Vérifier si l'utilisateur est connecté à Vinted

```typescript
// Background → Content
{
  action: 'GET_VINTED_USER_INFO'
}

// Content → Background
{
  success: true,
  data: {
    userId: "29535217",
    login: "shop.ton.outfit"
  }
}
```

**Fichiers impliqués** :
- `src/content/vinted-detector.ts` - Extraction simple userId + login
- `src/content/vinted.ts:574` - Handler du message

---

### 2. `EXECUTE_HTTP_REQUEST` - Requête HTTP générique

**Usage**: Exécuter n'importe quelle requête HTTP Vinted

```typescript
// Background → Content
{
  action: 'EXECUTE_HTTP_REQUEST',
  request: {
    url: 'https://www.vinted.fr/api/v2/items',
    method: 'GET',
    headers: {},
    body: null
  }
}

// Content → Background
{
  success: true,
  data: {
    items: [...]
  }
}
```

**Fichiers impliqués** :
- `src/content/vinted.ts:622` - Handler du message
- `src/content/vinted.ts:getVintedHeaders()` - Injection automatique des headers

---

### 3. `FETCH_VINTED_DATA` - Récupération complète

**Usage**: Récupérer produits + ventes + user info en une fois

```typescript
// Background → Content
{
  action: 'FETCH_VINTED_DATA'
}

// Content → Background
{
  success: true,
  data: {
    products: [...],
    sales: [...],
    userInfo: {...}
  }
}
```

---

## 🔐 Extraction des Headers Vinted

### Cache des Headers

**Fichier**: `src/content/vinted.ts:headersCache`

```typescript
const headersCache: VintedHeadersCache = {
  csrfToken: '',      // X-CSRF-Token
  anonId: '',         // X-Anon-Id
  lastUpdated: 0,     // Timestamp du dernier refresh
  isReady: false      // Headers disponibles ?
};
```

**Durée de cache** : 5 minutes

---

### Extraction depuis le HTML

**Fichier**: `src/content/vinted.ts:extractVintedData()`

```typescript
function extractVintedData() {
  // Parcourir tous les <script> de la page
  const scripts = document.querySelectorAll('script');

  for (const script of scripts) {
    const content = script.textContent || '';

    // 1. Extraire CSRF token
    const csrfMatch = content.match(/"csrf-token":\s*"([^"]+)"/);
    if (csrfMatch) csrfToken = csrfMatch[1];

    // 2. Extraire Anon ID
    const anonMatch = content.match(/"anon-id":\s*"([^"]+)"/);
    if (anonMatch) anonId = anonMatch[1];

    // 3. Extraire userId
    const userIdMatch = content.match(/"userId":\s*(\d+)/);
    if (userIdMatch) userId = parseInt(userIdMatch[1]);

    // 4. Extraire login
    const loginMatch = content.match(/"login":\s*"([^"]+)"/);
    if (loginMatch) login = loginMatch[1];
  }

  return { csrfToken, anonId, userId, login };
}
```

**Où chercher dans le HTML** :
- Balises `<script>` contenant `window.vinted` ou `vinted = {`
- JSON inline dans le HTML généré par le serveur Vinted

---

### Construction des Headers

**Fichier**: `src/content/vinted.ts:getVintedHeaders()`

```typescript
function getVintedHeaders(): HeadersInit {
  refreshHeadersCache();  // Refresh si nécessaire

  return {
    'X-CSRF-Token': headersCache.csrfToken,
    'X-Anon-Id': headersCache.anonId,
    'User-Agent': navigator.userAgent,
    'Accept': 'application/json',
    'Accept-Language': 'fr-FR,fr;q=0.9',
    'Content-Type': 'application/json'
  };
}
```

---

## 📝 Format des Tâches Backend

### Structure PluginTask

**Fichier**: `backend/models/user/plugin_task.py`

```python
class PluginTask(BaseUserModel):
    __tablename__ = "plugin_tasks"

    id: int
    task_type: str              # "HTTP" | "CHECK_VINTED_CONNECTION"
    platform: str               # "vinted"
    http_method: str | None     # "GET" | "POST" | "PUT" | "DELETE"
    path: str | None            # "/api/v2/items/123"
    payload: dict | None        # { headers: {...}, body: {...} }
    result: dict | None         # Résultat retourné par le plugin
    status: TaskStatus          # PENDING | SUCCESS | FAILED
    created_at: datetime
    completed_at: datetime | None
```

### Exemple de Tâche HTTP

```python
# Supprimer une photo
task = PluginTask(
    task_type="HTTP",
    platform="vinted",
    http_method="DELETE",
    path="/api/v2/photos/456",
    payload={
        "headers": {},
        "body": None
    },
    status=TaskStatus.PENDING
)
```

### Exemple de Tâche Spéciale

```python
# Vérifier connexion Vinted
task = PluginTask(
    task_type="CHECK_VINTED_CONNECTION",
    platform="vinted",
    http_method=None,  # Pas de requête HTTP
    path=None,
    payload=None,
    status=TaskStatus.PENDING
)
```

---

## 🚀 Performance et Optimisations

### 1. Polling Intelligent

**Fichier**: `src/background/PollingManager.ts`

- **Intervalle par défaut** : 5 secondes
- **Backoff** : Augmente à 60s si aucune tâche pendant longtemps
- **Immédiat** : Redescend à 5s dès qu'une tâche arrive

### 2. Cache des Headers

- **Durée** : 5 minutes
- **Refresh automatique** : Si headers expirés ou manquants
- **Lazy loading** : Extrait seulement quand nécessaire

### 3. Gestion d'Erreurs

```typescript
// Timeout de 10 secondes
if (!(await waitForHeaders(10000))) {
  throw new Error('Headers not available after 10s');
}

// Retry automatique si 401
if (response.status === 401) {
  // Le système de refresh token du StoflowAPI gère ça
  const refreshed = await refreshAccessToken();
  if (refreshed) {
    // Réessayer avec nouveau token
  }
}
```

---

## 📊 Diagramme de Séquence

```
Frontend           Backend           Background         Content Script      Vinted API
   │                  │                   │                    │                │
   │   Create Task    │                   │                    │                │
   ├─────────────────>│                   │                    │                │
   │                  │                   │                    │                │
   │                  │  getPendingTasks  │                    │                │
   │                  │<──────────────────┤                    │                │
   │                  ├──────────────────>│                    │                │
   │                  │  [Task 25]        │                    │                │
   │                  │                   │                    │                │
   │                  │                   │ sendMessage(EXECUTE_HTTP_REQUEST) │
   │                  │                   ├───────────────────>│                │
   │                  │                   │                    │                │
   │                  │                   │                    │ getHeaders()   │
   │                  │                   │                    ├────┐           │
   │                  │                   │                    │<───┘           │
   │                  │                   │                    │                │
   │                  │                   │                    │  fetch(POST)   │
   │                  │                   │                    ├───────────────>│
   │                  │                   │                    │                │
   │                  │                   │                    │  {photo:{...}} │
   │                  │                   │                    │<───────────────┤
   │                  │                   │                    │                │
   │                  │                   │  {success, data}   │                │
   │                  │                   │<───────────────────┤                │
   │                  │                   │                    │                │
   │                  │  reportComplete   │                    │                │
   │                  │<──────────────────┤                    │                │
   │                  ├──────────────────>│                    │                │
   │                  │                   │                    │                │
```

---

## 🔧 Fichiers Clés

| Fichier | Rôle |
|---------|------|
| `backend/api/plugin.py` | Endpoints `/api/plugin/tasks/*` |
| `backend/models/user/plugin_task.py` | Modèle PluginTask |
| `src/background/PollingManager.ts` | Polling + exécution des tâches |
| `src/background/index.ts` | Service worker principal |
| `src/content/vinted.ts` | Content script + extraction headers |
| `src/content/vinted-detector.ts` | Extraction simple userId+login |
| `src/api/StoflowAPI.ts` | Helper requêtes backend |

---

## 💡 Points Clés

1. ✅ **Injection automatique des headers** : Le content script ajoute automatiquement `X-CSRF-Token` et `X-Anon-Id`
2. ✅ **Authentification transparente** : Les cookies de session Vinted sont automatiquement inclus
3. ✅ **Refresh token automatique** : `StoflowAPI.fetchWithAuth()` gère les 401
4. ✅ **Cache intelligent** : Headers cachés 5 minutes pour performance
5. ✅ **Isolation** : Chaque tâche backend est isolée dans un schema PostgreSQL user-specific

---

**Dernière mise à jour** : 11 décembre 2025
