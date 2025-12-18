# 🧪 Test du Flow de Connexion

## ✅ Checklist de Test

### Préparation

- [ ] Backend API en cours d'exécution (`http://localhost:8000`)
- [ ] Frontend Nuxt en cours d'exécution (`http://localhost:3000`)
- [ ] Plugin chargé dans Firefox (`about:debugging` → "Ce Firefox")
- [ ] Console DevTools ouverte (F12) sur localhost:3000
- [ ] Console Background du plugin ouverte

---

## Test 1: Connexion depuis Frontend

### Étapes

1. **Ouvrir** http://localhost:3000/login dans Firefox
2. **Ouvrir Console** (F12) et vérifier:
   ```
   ✅ 📡 [CONTENT SCRIPT] CHARGÉ SUR: http://localhost:3000/login
   ```

3. **Se connecter** avec:
   - Email: `test@example.com`
   - Password: `password`

### Logs Frontend à surveiller

```javascript
// Console Frontend (localhost:3000)
🚀🚀🚀 [NUXT → PLUGIN] DÉBUT SYNC TOKEN 🚀🚀🚀
🚀 Access Token: eyJhbGciOiJIUzI1NiIsInR5cCI6...
🚀 Refresh Token: Présent
🚀 Méthode 1: Tentative chrome.runtime...
🚀 ⚠️ chrome.runtime échec: (normal depuis page web)
🚀 Méthode 2: Envoi via postMessage...
🚀 ✅ Token envoyé via postMessage
```

### Logs Content Script à surveiller

```javascript
// Console Frontend (localhost:3000) - partie content script
📬📬📬 [CONTENT SCRIPT] TOKEN REÇU VIA POSTMESSAGE 📬📬📬
📬 Access Token: Présent (eyJhbGciOiJIUzI1NiIsInR5cC...)
📬 Refresh Token: Présent
📬 Envoi au background script...

💌💌💌 [CONTENT] ENVOI TOKEN AU BACKGROUND 💌💌💌
💌 Appel chrome.runtime.sendMessage...
💌 Action: SYNC_TOKEN_FROM_WEBSITE
💌 Token: eyJhbGciOiJIUzI1NiIsInR5cC...
💌 ✅✅✅ SUCCÈS - Token synchronisé ✅✅✅
```

### Logs Background à surveiller

```javascript
// Console Background Plugin (about:debugging → Inspecter)
═══════════════════════════════════════════════════
🔔 [BACKGROUND] MESSAGE REÇU
Action: SYNC_TOKEN_FROM_WEBSITE
═══════════════════════════════════════════════════

🔐🔐🔐 [BACKGROUND SSO] DÉBUT SYNCHRONISATION TOKEN 🔐🔐🔐
🔐 access_token: ✅ Présent (eyJhbGciOiJIUzI1NiIsInR5...)
🔐 refresh_token: ✅ Présent
🔐 Stockage dans chrome.storage.local...
🔐 ✅✅✅ TOKEN STOCKÉ AVEC SUCCÈS ✅✅✅
🔐 Vérification stockage: { stoflow_access_token: "..." }
🔐 🚀 Démarrage du polling...
🔐 ✅ SYNCHRONISATION TERMINÉE
```

### Notification visuelle

- [ ] Toast apparaît en bas à droite: "✓ Plugin Stoflow connecté"

### Vérification Popup

4. **Cliquer** sur l'icône du plugin dans la barre d'outils
5. **Vérifier**:
   - [ ] Section "Connexion Stoflow" affiche "🟢 Connecté"
   - [ ] Email utilisateur affiché
   - [ ] Section "Vinted" visible

---

## Test 2: Vérification Token Stocké

### Console Background

```javascript
// Vérifier le token stocké
chrome.storage.local.get(['stoflow_access_token', 'stoflow_refresh_token'], console.log)

// Expected output:
{
  stoflow_access_token: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  stoflow_refresh_token: "def50200..."
}
```

### Console Frontend

```javascript
// Vérifier le token dans localStorage
localStorage.getItem('token')
// Expected: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

localStorage.getItem('refresh_token')
// Expected: "def50200..."
```

---

## Test 3: Polling Automatique

### Logs Background à surveiller

```javascript
// Toutes les 5 secondes (intervalle configurable)
[Polling] 📋 Récupération des tâches...
[Polling] ✅ Tâches récupérées
[Polling] Aucune tâche
```

---

## Test 4: Déconnexion

### Étapes

1. **Sur Frontend**: Cliquer "Se déconnecter"
2. **Vérifier Console**:

```javascript
// Console Frontend
🔴🔴🔴 [NUXT → PLUGIN] LOGOUT - DÉCONNEXION 🔴🔴🔴
🔴 Tentative chrome.runtime...
🔴 ⚠️ chrome.runtime échec (normal)
🔴 Envoi via postMessage...
🔴 ✅ Logout envoyé via postMessage
```

3. **Vérifier Background**:

```javascript
// Console Background
🔴🔴🔴 [BACKGROUND SSO] DÉCONNEXION DEPUIS SITE WEB 🔴🔴🔴
🔴 Suppression des tokens...
🔴 ✅✅✅ TOKENS SUPPRIMÉS ✅✅✅
🔴 🛑 Arrêt du polling...
🔴 ✅ DÉCONNEXION TERMINÉE
```

4. **Vérifier Popup**:
   - [ ] Formulaire de connexion affiché
   - [ ] Plus d'email utilisateur

---

## Test 5: Reconnexion Automatique (Refresh Page)

### Étapes

1. **Avec utilisateur déjà connecté** sur localhost:3000
2. **Recharger la page** (F5)
3. **Vérifier**: Token automatiquement récupéré depuis localStorage

```javascript
// Console après refresh
📡 [CONTENT SCRIPT] CHARGÉ SUR: http://localhost:3000/...
[Stoflow Web SSO] ✅ Token trouvé dans localStorage.token
[Stoflow Web SSO] ✅ Token synchronisé avec le plugin
```

---

## Test 6: Content Script Fallback (Polling)

### Si postMessage échoue

Le content script fait aussi :
- Vérification toutes les 30 secondes
- Détection automatique des changements localStorage

```javascript
// Logs toutes les 30s
[Stoflow Web SSO] 🔄 Token modifié, re-synchronisation...
```

---

## 🐛 Problèmes Courants

### Problème 1: Content Script non chargé

**Symptômes**:
- Aucun log `📡 [CONTENT SCRIPT] CHARGÉ SUR`
- Token non synchronisé

**Solution**:
1. Recharger la page localhost:3000
2. Vérifier le manifest.json :
   ```json
   "content_scripts": [{
     "matches": ["http://localhost:3000/*"],
     "js": ["src/content/stoflow-web.ts"],
     "run_at": "document_idle"
   }]
   ```
3. Rebuild le plugin : `npm run build`
4. Recharger dans Firefox (`about:debugging` → Recharger)

### Problème 2: Token non reçu par Background

**Symptômes**:
- postMessage envoyé ✅
- Mais aucun log dans Background

**Solution**:
1. Vérifier Background script actif :
   ```javascript
   // Console Background
   console.log('Background active:', new Date())
   ```
2. Vérifier listener installé :
   ```javascript
   // Devrait voir au démarrage:
   [Background] Message listener configuré
   ```

### Problème 3: Popup affiche "Non connecté"

**Symptômes**:
- Token stocké ✅
- Mais popup dit "Non connecté"

**Solution**:
1. Forcer re-check dans popup :
   ```javascript
   // Console Popup
   chrome.storage.local.get(['stoflow_access_token'], console.log)
   ```
2. Vérifier expiration token :
   ```javascript
   const token = '...' // copier depuis storage
   const payload = JSON.parse(atob(token.split('.')[1]))
   console.log('Expire:', new Date(payload.exp * 1000))
   ```

### Problème 4: localStorage vide après login

**Symptômes**:
- Login réussi
- Mais `localStorage.getItem('token')` → null

**Solution**:
1. Vérifier stores/auth.ts ligne 160 :
   ```typescript
   localStorage.setItem('token', data.access_token)
   ```
2. Vérifier process.client :
   ```typescript
   if (process.client) {
     // Code localStorage
   }
   ```

---

## ✅ Résultat Attendu

Après tous les tests :

- [x] Login Frontend → Token dans localStorage
- [x] postMessage → Content Script reçoit
- [x] Content Script → Background reçoit
- [x] Background → Token stocké dans chrome.storage
- [x] Popup → Affiche "Connecté"
- [x] Polling → Démarre automatiquement
- [x] Logout → Tokens supprimés
- [x] Refresh page → Re-sync automatique

---

## 🔍 Commandes de Debug Utiles

### Console Frontend

```javascript
// Forcer sync manuelle
window.postMessage({
  type: 'STOFLOW_SYNC_TOKEN',
  access_token: localStorage.getItem('token'),
  refresh_token: localStorage.getItem('refresh_token')
}, '*')

// Vérifier tokens
console.log('Access:', localStorage.getItem('token'))
console.log('Refresh:', localStorage.getItem('refresh_token'))
```

### Console Background

```javascript
// Vérifier storage
chrome.storage.local.get(null, console.log)

// Forcer check auth
await checkAuthStatus()

// Tester refresh token
await refreshAccessToken()
```

### Console Popup

```javascript
// Re-check auth
const result = await chrome.storage.local.get('stoflow_access_token')
console.log('Token:', result.stoflow_access_token)
```

---

*Dernière mise à jour: 11 décembre 2025*
