# 🔐 Flow de Connexion Frontend ↔ Plugin

## 📋 Vue d'ensemble

Le plugin Stoflow se synchronise automatiquement avec le frontend via SSO (Single Sign-On).

---

## 🔄 Flow Complet

```
┌─────────────────────────────────────────────────────────────────┐
│                    1. CONNEXION FRONTEND                         │
│                                                                  │
│  User se connecte sur http://localhost:3000/login               │
│          ↓                                                       │
│  authStore.login(email, password)                               │
│          ↓                                                       │
│  Backend API → /api/auth/login                                  │
│          ↓                                                       │
│  Response: { access_token, refresh_token, user }                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                 2. STOCKAGE TOKEN FRONTEND                       │
│                                                                  │
│  localStorage.setItem('token', access_token)                    │
│  localStorage.setItem('refresh_token', refresh_token)           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              3. DÉTECTION PAR CONTENT SCRIPT                     │
│                                                                  │
│  Content Script: stoflow-web.ts (actif sur localhost:3000)      │
│          ↓                                                       │
│  Détecte changement localStorage via:                           │
│    - window.addEventListener('storage')                         │
│    - Override localStorage.setItem()                            │
│    - Polling toutes les 30s                                     │
│          ↓                                                       │
│  Méthodes de détection:                                          │
│    1. getTokenFromLocalStorage() cherche:                       │
│       - 'token' ✅                                              │
│       - 'stoflow_access_token'                                  │
│       - 'access_token'                                          │
│       - 'auth_token'                                            │
│    2. getRefreshTokenFromLocalStorage() cherche:                │
│       - 'refresh_token' ✅                                      │
│       - 'stoflow_refresh_token'                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│               4. SYNCHRONISATION VERS BACKGROUND                 │
│                                                                  │
│  chrome.runtime.sendMessage({                                   │
│    action: 'SYNC_TOKEN_FROM_WEBSITE',                           │
│    access_token: token,                                         │
│    refresh_token: refreshToken                                  │
│  })                                                             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│            5. RÉCEPTION PAR BACKGROUND SCRIPT                    │
│                                                                  │
│  BackgroundService.handleMessage()                              │
│          ↓                                                       │
│  case 'SYNC_TOKEN_FROM_WEBSITE':                                │
│    syncTokenFromWebsite(message)                                │
│          ↓                                                       │
│  chrome.storage.local.set({                                     │
│    'stoflow_access_token': access_token,                        │
│    'stoflow_refresh_token': refresh_token                       │
│  })                                                             │
│          ↓                                                       │
│  pollingManager.start() // Démarre le polling automatique       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                 6. PLUGIN AUTHENTIFIÉ                            │
│                                                                  │
│  Popup.vue → useAuth.checkAuth()                                │
│          ↓                                                       │
│  Lit chrome.storage.local.get('stoflow_access_token')           │
│          ↓                                                       │
│  isAuthenticated = true ✅                                       │
│          ↓                                                       │
│  Affiche: "Connexion Stoflow: Authentifié"                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔍 Points de Vérification

### ✅ Frontend (localhost:3000)

**Fichier**: `stores/auth.ts`

```typescript
// Après login réussi:
localStorage.setItem('token', data.access_token)
localStorage.setItem('refresh_token', data.refresh_token)
```

**Clés utilisées**:
- ✅ `token` → access token
- ✅ `refresh_token` → refresh token

### ✅ Plugin Content Script

**Fichier**: `src/content/stoflow-web.ts`

**Détection automatique**:
1. ✅ Au chargement (500ms delay)
2. ✅ Sur changement localStorage
3. ✅ Polling toutes les 30 secondes
4. ✅ Via postMessage `STOFLOW_SYNC_TOKEN`

**Logs à surveiller** (Console frontend):
```
📡 [CONTENT SCRIPT] CHARGÉ SUR: http://localhost:3000/...
[Stoflow Web SSO] ✅ Token trouvé dans localStorage.token
💌 [CONTENT] ENVOI TOKEN AU BACKGROUND
💌 ✅✅✅ SUCCÈS - Token synchronisé ✅✅✅
```

### ✅ Plugin Background

**Fichier**: `src/background/index.ts`

**Réception du token**:
```typescript
case 'SYNC_TOKEN_FROM_WEBSITE':
  syncTokenFromWebsite(message)
  // Stocke dans chrome.storage
  // Démarre le polling
```

**Logs à surveiller** (Console background):
```
🔐 [BACKGROUND SSO] DÉBUT SYNCHRONISATION TOKEN
🔐 [BACKGROUND SSO] access_token: ✅ Présent (...)
🔐 [BACKGROUND SSO] ✅✅✅ TOKEN STOCKÉ AVEC SUCCÈS ✅✅✅
```

### ✅ Plugin Popup

**Fichier**: `src/popup/Popup.vue` + `src/composables/useAuth.ts`

**Vérification auth**:
```typescript
const checkAuth = async () => {
  const result = await chrome.storage.local.get('stoflow_access_token')
  if (result.stoflow_access_token) {
    return true // ✅ Authentifié
  }
  return false // ❌ Non authentifié
}
```

---

## 🧪 Test du Flow

### Scénario 1: Connexion depuis Frontend

1. **Ouvrir** http://localhost:3000/login
2. **Se connecter** avec email/password
3. **Vérifier Console** (F12):
   ```
   ✅ [Stoflow Web SSO] Token trouvé dans localStorage.token
   ✅ [Stoflow Web SSO] Token synchronisé avec le plugin
   ```
4. **Voir Notification**: "✓ Plugin Stoflow connecté"
5. **Ouvrir popup** plugin
6. **Vérifier**: "Connexion Stoflow: Authentifié ✅"

### Scénario 2: Popup avant connexion

1. **Ouvrir popup** plugin (avant login)
2. **Voir**: Formulaire de connexion
3. **Se connecter** via popup
4. **Vérifier**: Plugin authentifié

### Scénario 3: Déconnexion

1. **Frontend**: Se déconnecter
2. **Plugin**: Détecte automatiquement
3. **Popup**: Affiche formulaire de connexion

---

## 🐛 Débogage

### Console Frontend (localhost:3000)
```javascript
// Voir le token
localStorage.getItem('token')

// Forcer la sync
window.postMessage({
  type: 'STOFLOW_SYNC_TOKEN',
  access_token: localStorage.getItem('token'),
  refresh_token: localStorage.getItem('refresh_token')
}, '*')
```

### Console Background Plugin
```javascript
// Voir le token stocké
chrome.storage.local.get(['stoflow_access_token'], console.log)

// Vérifier l'expiration
const token = '...' // copier le token
const payload = JSON.parse(atob(token.split('.')[1]))
console.log('Expire:', new Date(payload.exp * 1000))
```

### Console Popup Plugin
```javascript
// Forcer re-check auth
chrome.runtime.sendMessage({ action: 'CHECK_AUTH_STATUS' }, console.log)
```

---

## ⚙️ Configuration

### Clés localStorage (Frontend)
- ✅ `token` → Access token JWT
- ✅ `refresh_token` → Refresh token

### Clés chrome.storage (Plugin)
- ✅ `stoflow_access_token`
- ✅ `stoflow_refresh_token`
- ✅ `stoflow_user_data`

### URLs
- Frontend: `http://localhost:3000/*`
- Backend: `http://localhost:8000/api/*`

---

## 🔄 Refresh Token Flow

```
Token expire dans 5 min
        ↓
checkAndRefreshTokenOnStartup()
        ↓
Appelle /api/auth/refresh
        ↓
Reçoit nouveau access_token
        ↓
Met à jour chrome.storage
        ↓
Continue le polling ✅
```

---

*Dernière mise à jour: 11 décembre 2025*
