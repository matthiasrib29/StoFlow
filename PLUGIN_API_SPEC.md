# API Plugin Browser - Spécification Complète

**Date:** 2025-12-06  
**Backend:** Stoflow FastAPI  
**Plugin:** Chrome/Firefox Extension

---

## 🎯 Vue d'ensemble

L'API Plugin permet au plugin browser de:
1. S'authentifier avec les credentials Stoflow
2. Envoyer les cookies des plateformes (Vinted, eBay, Etsy) pour test de connexion
3. Tester la connexion aux plateformes
4. **IMPORTANT**: Les cookies restent UNIQUEMENT sur la machine de l'utilisateur (chrome.storage)
5. Le backend NE STOCKE JAMAIS les cookies (test uniquement)

---

## 📡 Endpoints Disponibles

### 1. **POST** `/api/plugin/auth`

Authentifie le plugin avec credentials utilisateur.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "your_password"
}
```

**Response 200:**
```json
{
  "success": true,
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "tenant_id": 1
  },
  "error": null
}
```

**Response 200 (échec):**
```json
{
  "success": false,
  "access_token": null,
  "user": null,
  "error": "Invalid credentials"
}
```

**Usage Plugin:**
```typescript
// Dans le plugin
async function authenticatePlugin(email: string, password: string) {
  const response = await fetch('http://localhost:8000/api/plugin/auth', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  
  const data = await response.json();
  
  if (data.success) {
    // Stocker le token dans chrome.storage
    await chrome.storage.local.set({ 
      stoflowToken: data.access_token,
      user: data.user 
    });
    return data.access_token;
  }
  
  throw new Error(data.error);
}
```

---

### 2. **POST** `/api/plugin/sync`

Synchronise les cookies des plateformes.

**Request Body:**
```json
{
  "platforms": [
    {
      "platform": "vinted",
      "cookies": {
        "v_sid": "abc123...",
        "anon_id": "xyz789..."
      },
      "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
  ],
  "plugin_version": "1.0.0",
  "browser": "chrome"
}
```

**Response 200:**
```json
{
  "success": true,
  "platforms_synced": 1,
  "platforms_status": [
    {
      "platform": "vinted",
      "connected": true,
      "user": {
        "id": 12345,
        "login": "john_doe",
        "email": "john@example.com"
      },
      "error": null,
      "last_sync": "2025-12-06T19:30:00Z"
    }
  ],
  "message": "1/1 platforms synced successfully",
  "new_access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Note:** Le champ `new_access_token` contient un nouveau JWT token (valide 1h). Le plugin doit automatiquement remplacer l'ancien token par celui-ci pour éviter l'expiration.

**Usage Plugin:**
```typescript
// Dans le plugin
async function syncPlatformCookies(token: string) {
  // Récupérer cookies Vinted depuis le browser
  const vintedCookies = await chrome.cookies.getAll({
    domain: '.vinted.fr'
  });

  // Convertir en dict
  const cookiesDict: Record<string, string> = {};
  vintedCookies.forEach(cookie => {
    cookiesDict[cookie.name] = cookie.value;
  });

  // Envoyer au backend
  const response = await fetch('http://localhost:8000/api/plugin/sync', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      platforms: [{
        platform: 'vinted',
        cookies: cookiesDict,
        user_agent: navigator.userAgent
      }],
      plugin_version: '1.0.0',
      browser: 'chrome'
    })
  });

  const data = await response.json();

  // ===== AUTO-REFRESH TOKEN =====
  // Le backend retourne automatiquement un nouveau token
  if (data.new_access_token) {
    await chrome.storage.local.set({
      stoflowToken: data.new_access_token
    });
    console.log('Token refreshed automatically');
  }

  // Afficher status dans popup
  data.platforms_status.forEach(status => {
    console.log(`${status.platform}: ${status.connected ? '✅' : '❌'}`);
  });

  return data;
}
```

---

### 3. **GET** `/api/plugin/platforms`

Liste des plateformes supportées.

**Response 200:**
```json
{
  "platforms": [
    {
      "name": "vinted",
      "display_name": "Vinted",
      "auth_method": "cookies",
      "supported": true,
      "features": ["import", "publish", "sync", "delete"]
    },
    {
      "name": "ebay",
      "display_name": "eBay",
      "auth_method": "oauth2",
      "supported": false,
      "features": [],
      "note": "OAuth2 integration not implemented in V1"
    },
    {
      "name": "etsy",
      "display_name": "Etsy",
      "auth_method": "oauth2",
      "supported": false,
      "features": [],
      "note": "OAuth2 integration not implemented in V1"
    }
  ]
}
```

**Usage Plugin:**
```typescript
// Récupérer plateformes disponibles au démarrage
async function loadSupportedPlatforms() {
  const response = await fetch('http://localhost:8000/api/plugin/platforms');
  const data = await response.json();
  
  // Afficher seulement les plateformes supportées
  const supported = data.platforms.filter(p => p.supported);
  
  // Render dans popup
  supported.forEach(platform => {
    renderPlatformButton(platform.name, platform.display_name);
  });
}
```

---

### 4. **GET** `/api/plugin/health`

Health check de l'API.

**Response 200:**
```json
{
  "status": "healthy",
  "api_version": "1.0.0",
  "plugin_compatible": ["1.0.0", "1.0.1"]
}
```

**Usage Plugin:**
```typescript
// Vérifier compatibilité au démarrage
async function checkApiCompatibility() {
  const response = await fetch('http://localhost:8000/api/plugin/health');
  const data = await response.json();
  
  const pluginVersion = chrome.runtime.getManifest().version;
  
  if (!data.plugin_compatible.includes(pluginVersion)) {
    showWarning('Plugin version not compatible. Please update.');
  }
}
```

---

## 🔐 Authentification

**Toutes les routes (sauf `/auth`, `/platforms`, et `/health`) nécessitent un JWT token:**

```typescript
headers: {
  'Authorization': `Bearer ${token}`
}
```

**Token access:** Valide 1h
**Token refresh:** Valide 7 jours
**Auto-refresh:** Automatique à chaque `/sync` (nouveau token retourné)

### Stratégie d'authentification

1. **Première connexion** : `/api/plugin/auth` avec email/password → reçoit `access_token`
2. **Utilisation** : Toutes les requêtes avec header `Authorization: Bearer <token>`
3. **Auto-refresh** : À chaque `/sync`, un nouveau token est retourné dans `new_access_token`
4. **Expiration** : Si token expiré (> 1h), re-login avec `/api/plugin/auth`

**Exemple workflow:**
```typescript
class StoflowPlugin {
  private token: string | null = null;

  async init() {
    const stored = await chrome.storage.local.get(['stoflowToken']);
    this.token = stored.stoflowToken;

    if (!this.token) {
      this.showLoginForm();
    } else {
      // Tester si le token est encore valide
      try {
        await this.syncPlatforms();
      } catch (error) {
        if (error.status === 401) {
          // Token expiré, demander re-login
          this.showLoginForm();
        }
      }
    }
  }

  async syncPlatforms() {
    const response = await fetch('http://localhost:8000/api/plugin/sync', {
      headers: {
        'Authorization': `Bearer ${this.token}`
      },
      // ... body
    });

    if (!response.ok) {
      throw { status: response.status };
    }

    const data = await response.json();

    // Auto-refresh automatique
    if (data.new_access_token) {
      this.token = data.new_access_token;
      await chrome.storage.local.set({
        stoflowToken: this.token
      });
    }

    return data;
  }
}
```

---

## 🔄 Workflow Plugin

### Au démarrage du plugin:

1. **Vérifier si token existe** dans `chrome.storage.local`
2. **Si non:** Afficher formulaire login
3. **Si oui:** Vérifier health check
4. **Charger** liste des plateformes supportées
5. **Auto-sync** toutes les 5 minutes (configurable)

### Lors du clic "Sync":

1. **Récupérer cookies** de toutes les plateformes (vinted.fr, ebay.com, etc.)
2. **Appeler** `/api/plugin/sync` avec tous les cookies
3. **Afficher résultat** dans popup (✅ connecté / ❌ erreur)
4. **Stocker** last_sync timestamp

### Exemple flux complet:

```typescript
class StoflowPlugin {
  private token: string | null = null;
  
  async init() {
    // Load token from storage
    const stored = await chrome.storage.local.get(['stoflowToken']);
    this.token = stored.stoflowToken;
    
    if (!this.token) {
      this.showLoginForm();
    } else {
      await this.checkHealth();
      await this.loadPlatforms();
      this.startAutoSync(5 * 60 * 1000); // 5 min
    }
  }
  
  async login(email: string, password: string) {
    const response = await fetch('http://localhost:8000/api/plugin/auth', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    
    const data = await response.json();
    
    if (data.success) {
      this.token = data.access_token;
      await chrome.storage.local.set({ stoflowToken: this.token });
      this.hideLoginForm();
      this.init();
    }
  }
  
  async syncPlatforms() {
    const platforms = [];
    
    // Vinted cookies
    const vintedCookies = await this.getCookies('.vinted.fr');
    if (vintedCookies) {
      platforms.push({
        platform: 'vinted',
        cookies: vintedCookies,
        user_agent: navigator.userAgent
      });
    }
    
    const response = await fetch('http://localhost:8000/api/plugin/sync', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.token}`
      },
      body: JSON.stringify({
        platforms,
        plugin_version: '1.0.0',
        browser: 'chrome'
      })
    });
    
    const data = await response.json();
    this.displaySyncResults(data);
  }
  
  async getCookies(domain: string): Promise<Record<string, string> | null> {
    const cookies = await chrome.cookies.getAll({ domain });
    
    if (cookies.length === 0) return null;
    
    const dict: Record<string, string> = {};
    cookies.forEach(c => dict[c.name] = c.value);
    
    return dict;
  }
  
  startAutoSync(interval: number) {
    setInterval(() => this.syncPlatforms(), interval);
  }
}
```

---

## 📊 Status Codes

| Code | Description |
|------|-------------|
| 200  | Success |
| 400  | Bad Request (invalid data) |
| 401  | Unauthorized (invalid token) |
| 500  | Internal Server Error |

---

## 🔒 Sécurité

1. **CORS:** Autoriser uniquement `chrome-extension://...` en production
2. **Rate Limiting:** Max 10 requêtes /auth par IP/5min
3. **Token Storage:** `chrome.storage.local` (encrypted by Chrome)
4. **Cookies Storage:** Les cookies NE SONT JAMAIS stockés côté backend
   - Ils restent UNIQUEMENT dans `chrome.storage.local` sur la machine utilisateur
   - Le backend les utilise seulement pour tester la connexion (appel API direct)
5. **HTTPS Only:** En production, forcer HTTPS

---

## 🚀 Prochaines Étapes

### Backend:
- [ ] Ajouter endpoint `/api/plugin/disconnect` pour déconnecter le plugin
- [ ] Ajouter webhook pour notifications (ventes, messages)
- [ ] OAuth2 pour eBay et Etsy (V2)

### Plugin:
- [ ] Implémenter auto-refresh token avant expiration
- [ ] Ajouter notifications desktop (vente détectée)
- [ ] Créer page options pour configurer auto-sync interval
- [ ] Ajouter badge icon avec nombre de plateformes connectées

---

## 📚 Exemples Complets

### Structure fichiers plugin recommandée:

```
plugin/
├── manifest.json
├── background.js      # Service worker (sync auto)
├── popup/
│   ├── popup.html     # UI principale
│   ├── popup.js       # Logique popup
│   └── popup.css
├── composables/
│   ├── useAuth.ts     # Hook auth
│   └── usePlatforms.ts # Hook platforms
└── utils/
    ├── api.ts         # Client API
    └── cookies.ts     # Gestion cookies
```

### api.ts:
```typescript
export class StoflowAPI {
  private baseURL = 'http://localhost:8000/api';
  
  async post(endpoint: string, data: any, token?: string) {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json'
    };
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      method: 'POST',
      headers,
      body: JSON.stringify(data)
    });
    
    return response.json();
  }
  
  async get(endpoint: string, token?: string) {
    const headers: Record<string, string> = {};
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      method: 'GET',
      headers
    });
    
    return response.json();
  }
}
```

---

**Fin de la spécification** ✅
