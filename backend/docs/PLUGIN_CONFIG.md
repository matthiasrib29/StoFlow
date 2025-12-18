# Configuration du Plugin Stoflow

**Version:** 1.0
**Dernière mise à jour:** 2025-12-08

---

## 🔧 URL Backend

### Configuration Principale

**URL Backend:** `http://localhost:8000`

Cette URL doit être configurée dans tous les fichiers du plugin qui communiquent avec le backend.

---

## 📝 Fichiers à Configurer

### 1. background.js

```javascript
// Configuration Backend
const BACKEND_URL = 'http://localhost:8000';
const POLL_INTERVAL = 5000; // 5 secondes

// Exemple d'utilisation
const response = await fetch(
  `${BACKEND_URL}/api/plugin/tasks?user_id=${userId}`,
  {
    headers: {
      "Authorization": `Bearer ${token}`
    }
  }
);
```

**Endpoints utilisés:**
- `GET ${BACKEND_URL}/api/plugin/tasks?user_id=X` - Polling tâches
- `POST ${BACKEND_URL}/api/plugin/tasks/{id}/result` - Envoi résultats

---

### 2. popup.js

```javascript
// Configuration Backend
const BACKEND_URL = 'http://localhost:8000';

// Authentification
const response = await fetch(
  `${BACKEND_URL}/api/auth/login?source=plugin`,
  {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password })
  }
);
```

**Endpoints utilisés:**
- `POST ${BACKEND_URL}/api/auth/login?source=plugin` - Connexion

---

### 3. content.js

Le content script n'a généralement pas besoin de l'URL backend directement, car il communique avec le background script.

---

## 🌐 Environnements

### Développement Local

```javascript
const BACKEND_URL = 'http://localhost:8000';
```

### Production (exemple)

```javascript
const BACKEND_URL = 'https://api.stoflow.com';
```

---

## 📡 Endpoints Backend Disponibles

### Authentification

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `POST` | `/api/auth/register` | Créer un compte |
| `POST` | `/api/auth/login?source=plugin` | Connexion plugin |
| `POST` | `/api/auth/refresh` | Rafraîchir token |

### Plugin Tasks (Polling)

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/api/plugin/tasks?user_id=X` | Récupérer tâches en attente |
| `POST` | `/api/plugin/tasks/{id}/result` | Envoyer résultat de tâche |
| `GET` | `/api/plugin/health` | Health check plugin |
| `POST` | `/api/plugin/sync` | Synchronisation |

### Intégrations Vinted

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `POST` | `/api/integrations/vinted/import` | Importer produits Vinted |
| `POST` | `/api/integrations/vinted/publish` | Publier vers Vinted |
| `GET` | `/api/integrations/vinted/stats` | Stats Vinted |

---

## ✅ Checklist Configuration

### Plugin Navigateur

- [ ] `background.js` - Constante `BACKEND_URL` définie
- [ ] `popup.js` - Constante `BACKEND_URL` définie
- [ ] Manifest v2/v3 configuré selon le navigateur
- [ ] Permissions correctes dans manifest.json

### Backend Python

- [ ] Backend lancé sur `http://localhost:8000` ✅
- [ ] Endpoints `/api/plugin/*` fonctionnels ✅
- [ ] CORS configuré pour accepter les requêtes du plugin ✅
- [ ] JWT authentication active ✅

### Base de Données

- [ ] PostgreSQL actif (port 5433) ✅
- [ ] Redis actif (port 6379) ✅
- [ ] Migrations appliquées ✅

---

## 🔍 Vérification

### Test Backend

```bash
# Health check
curl http://localhost:8000/health

# Test endpoint plugin
curl http://localhost:8000/api/plugin/health
```

**Résultat attendu:**
```json
{
  "status": "healthy",
  "app_name": "Stoflow",
  "environment": "development"
}
```

### Test Plugin

1. Ouvrir Firefox/Chrome
2. Charger l'extension
3. Ouvrir la popup
4. Tenter connexion
5. Vérifier Console (F12) → Pas d'erreur CORS

---

## 🐛 Problèmes Courants

### ❌ CORS Error

**Erreur:**
```
Access to fetch at 'http://localhost:8000/api/auth/login' from origin 'chrome-extension://...' has been blocked by CORS policy
```

**Solution:**
- Vérifier que `CORS_ORIGINS=*` dans `.env` backend
- Redémarrer le backend après modification

### ❌ Connection Refused

**Erreur:**
```
Failed to fetch: net::ERR_CONNECTION_REFUSED
```

**Solution:**
- Vérifier que le backend tourne : `curl http://localhost:8000/health`
- Lancer le backend : `uvicorn main:app --reload --host 0.0.0.0 --port 8000`

### ❌ 401 Unauthorized

**Erreur:**
```
401 Unauthorized
```

**Solution:**
- Token JWT expiré ou invalide
- Se reconnecter via la popup
- Vérifier que le token est bien stocké : `chrome.storage.local.get(['access_token'])`

---

## 📚 Références

- **Backend API:** `docs/README.md`
- **Plugin Integration:** `docs/PLUGIN_INTEGRATION.md`
- **Architecture:** `docs/ARCHITECTURE.md`

---

**Dernière mise à jour:** 2025-12-08
