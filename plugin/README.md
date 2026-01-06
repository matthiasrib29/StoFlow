# 🔌 StoFlow Plugin - Proxy HTTP Générique pour Vinted

Plugin Firefox (Manifest V3) qui sert de **proxy HTTP générique** entre votre backend et Vinted.

## 🎯 Concept

Le plugin agit comme un **intermédiaire transparent** :

```
Backend (FastAPI)
    ↓ Crée une tâche HTTP dans la DB
Plugin Firefox (polling toutes les 5s)
    ↓ Récupère la tâche
Plugin exécute sur Vinted via content script
    ↓ Injecte automatiquement : Cookies + X-CSRF-Token + X-Anon-Id
    ↓ Renvoie la réponse brute
Backend traite la réponse
```

## ✨ Fonctionnalités

### 🔐 Auto-injection des credentials Vinted

Le plugin injecte **automatiquement** dans toutes les requêtes :
- ✅ **Cookies** de session Vinted (via `credentials: 'include'`)
- ✅ **X-CSRF-Token** (extrait dynamiquement du HTML)
- ✅ **X-Anon-Id** (extrait dynamiquement du HTML)
- ✅ **Content-Type** approprié (JSON ou multipart)

### 🌐 Proxy HTTP totalement générique

Le backend envoie **n'importe quelle requête HTTP** :
- Tous les verbes HTTP : `GET`, `POST`, `PUT`, `DELETE`, `PATCH`
- Body JSON ou FormData (multipart)
- Headers personnalisés (avec possibilité de surcharge)
- Upload de fichiers (base64 → Blob)

### 🔄 Polling automatique

- Interroge le backend toutes les **5 secondes**
- Authentification JWT automatique
- Gestion des erreurs 401 (token expiré)
- Une seule tâche exécutée à la fois

### 📊 Réponse brute complète

Renvoie toutes les informations au backend :
- `status` : Code HTTP (200, 404, 500...)
- `headers` : Headers de réponse
- `data` : Body de la réponse
- `execution_time_ms` : Temps d'exécution
- `executed_at` : Timestamp ISO

---

## 🚀 Installation

### Prérequis
- Node.js 18+
- Firefox Developer Edition

### 1. Installer les dépendances
```bash
npm install
```

### 2. Build le plugin
```bash
npm run build
```

### 3. Charger dans Firefox
1. Ouvrir `about:debugging`
2. Cliquer "This Firefox"
3. Cliquer "Load Temporary Add-on"
4. Sélectionner `dist/manifest.json`

---

## 📝 Utilisation

### 1. Connexion au backend

Le plugin se connecte à votre backend via JWT :

```typescript
POST http://localhost:8000/api/auth/login?source=plugin
Body: {
  "email": "user@example.com",
  "password": "password"
}

Response: {
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "user_id": 1,
  "role": "user",
  "subscription_tier": "starter"
}
```

Le plugin stocke les tokens et démarre automatiquement le polling.

### 2. Créer une tâche HTTP

Le backend crée une tâche dans la table `plugin_tasks` :

```python
# Exemple 1 : GET simple
{
    "task_type": "HTTP_REQUEST",
    "status": "PENDING",
    "payload": {
        "url": "https://www.vinted.fr/api/v2/items/123456",
        "method": "GET"
    }
}

# Exemple 2 : POST avec body JSON
{
    "task_type": "HTTP_REQUEST",
    "status": "PENDING",
    "payload": {
        "url": "https://www.vinted.fr/api/v2/items/123",
        "method": "PUT",
        "body": {"price": 15.99}
    }
}

# Exemple 3 : Headers custom
{
    "task_type": "HTTP_REQUEST",
    "status": "PENDING",
    "payload": {
        "url": "https://www.vinted.fr/api/v2/items",
        "method": "GET",
        "headers": {
            "X-Custom-Header": "value"
        }
    }
}

# Exemple 4 : Upload de photo
{
    "task_type": "HTTP_REQUEST",
    "status": "PENDING",
    "payload": {
        "url": "https://www.vinted.fr/api/v2/photos",
        "method": "POST",
        "content_type": "multipart",
        "files": [{
            "field": "photo",
            "filename": "product.jpg",
            "content": "base64_encoded_image_data",
            "mime_type": "image/jpeg"
        }],
        "body": {
            "product_id": 123
        }
    }
}
```

### 3. Récupérer le résultat

Le plugin renvoie la réponse complète au backend :

```json
{
    "success": true,
    "status": 200,
    "headers": {
        "content-type": "application/json",
        "x-request-id": "abc123"
    },
    "data": {
        "id": 123456,
        "title": "T-shirt Nike",
        "price": "15.00",
        "description": "..."
    },
    "execution_time_ms": 450,
    "executed_at": "2025-12-08T09:41:00Z"
}
```

En cas d'erreur :

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

## 🔧 Configuration

### Backend URL

Modifier dans `src/background/task-poller.ts` :
```typescript
const BACKEND_URL = 'http://localhost:8000';
```

### Intervalle de polling

Modifier dans `src/background/task-poller.ts` :
```typescript
const POLL_INTERVAL = 5000; // 5 secondes
```

---

## 🏗️ Architecture

### Structure des fichiers

```
src/
├── background/
│   ├── index.ts          # Background service worker
│   └── task-poller.ts    # Polling + exécution des tâches
├── content/
│   ├── vinted.ts         # Content script Vinted
│   └── proxy.ts          # Proxy HTTP générique
├── composables/
│   └── useAuth.ts        # Authentification JWT
├── popup/
│   └── Popup.vue         # Interface utilisateur
└── manifest.json         # Configuration du plugin
```

### Flow d'exécution

1. **Polling** (`task-poller.ts`)
   - Interroge `GET /api/plugin/tasks` toutes les 5s
   - Authentification JWT (Bearer token)

2. **Extraction tokens** (`vinted.ts`)
   - Extrait `X-CSRF-Token` du HTML
   - Extrait `X-Anon-Id` du HTML

3. **Exécution** (`proxy.ts`)
   - Merge tokens auto + headers custom
   - Exécute la requête avec `fetch()`
   - Inclut automatiquement les cookies

4. **Réponse** (`task-poller.ts`)
   - Parse la réponse (JSON/text/blob)
   - Envoie à `POST /api/plugin/tasks/{id}/result`

---

## 🔐 Sécurité

### Tokens JWT

- `access_token` : Expire après 1h
- `refresh_token` : Expire après 7 jours
- Stockés dans `chrome.storage.local` (chiffré par Firefox)
- Refresh automatique en cas de 401

### Headers Vinted

- CSRF Token et Anon-Id extraits **dynamiquement** à chaque requête
- Jamais stockés (toujours frais)
- Impossible de faire une requête sans onglet Vinted ouvert

### Isolation

- Exécution dans le contexte de vinted.fr uniquement
- Cookies Vinted jamais exposés au backend
- Le backend ne voit que les réponses API

---

## 📊 Endpoints Backend Requis

Le backend doit implémenter :

### 1. Authentification
```
POST /api/auth/login?source=plugin
POST /api/auth/refresh
```

### 2. Tâches
```
GET  /api/plugin/tasks                 # Liste des tâches PENDING
POST /api/plugin/tasks/{id}/result     # Soumettre un résultat
```

### 3. Base de données

Table `plugin_tasks` dans chaque schéma utilisateur :

```sql
CREATE TABLE plugin_tasks (
    id SERIAL PRIMARY KEY,
    task_type VARCHAR NOT NULL,
    status VARCHAR NOT NULL DEFAULT 'PENDING',
    payload JSONB,
    result JSONB,
    error_message TEXT,
    product_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3
);
```

---

## 🐛 Debug

### Console du Popup

```javascript
[Auth] ✅ Connexion réussie: {userId: 1, role: "user"}
[Popup] Polling démarré pour user_id: 1
```

### Console du Background (`about:debugging` → Inspect)

```javascript
[Task Poller] ✅ Démarrage polling (intervalle: 5000ms)
[Task Poller] ✅ Nouvelle tâche: HTTP_REQUEST 1
[Task Poller] 🚀 Exécution tâche 1: HTTP_REQUEST
[Stoflow Proxy] 🌐 Exécution requête: GET https://www.vinted.fr/api/v2/users/me
[Stoflow Proxy] ✅ Réponse: 200 OK
[Task Poller] ✅ Résultat envoyé pour tâche 1
```

---

## 📚 Documentation

See the [CLAUDE.md](./CLAUDE.md) file for development guidelines and architecture overview.

---

## 🤝 Contribution

Key files for modifications:

1. **Background service** : `src/background/index.ts` and `src/background/VintedActionHandler.ts`
2. **API client** : `src/api/StoflowAPI.ts`
3. **Vinted API hook** : `src/content/stoflow-vinted-api.js`

---

## 📄 Licence

MIT

---

**Version** : 2.0.0
**Dernière mise à jour** : 2025-12-08
