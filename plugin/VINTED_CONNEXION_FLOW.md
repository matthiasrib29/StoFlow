# 🛍️ Flow de Connexion Vinted (Simplifié)

## 📋 Vue d'ensemble

Le plugin détecte si l'utilisateur est connecté à Vinted **uniquement via l'extraction de userId + login depuis le HTML**.

**✅ NOUVELLES RÈGLES:**
- ✅ **Connexion = userId ET login extraits avec succès**
- ❌ **Aucune vérification de cookies** (v_sid supprimé)
- ❌ **Aucune sync automatique** de csrf_token, anon_id, email, etc.
- ✅ **Sync uniquement quand:**
  - Le popup est ouvert (manuellement)
  - Le backend demande via une tâche

---

## 🔄 Flow Complet Simplifié

```
┌─────────────────────────────────────────────────────────────────┐
│              1. USER SE CONNECTE SUR VINTED.FR                   │
│                                                                  │
│  https://www.vinted.fr/auth/login                               │
│         ↓                                                        │
│  User entre email + password                                    │
│         ↓                                                        │
│  Vinted injecte userId + login dans le HTML de la page          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│             2. DÉTECTION PAR CONTENT SCRIPT                      │
│                                                                  │
│  Content Script: vinted.ts (actif sur vinted.fr/*)             │
│         ↓                                                        │
│  Attends message 'GET_VINTED_USER_INFO' depuis le popup        │
│         ↓                                                        │
│  Extrait userId + login depuis HTML via regex                   │
│  vinted-detector.ts:getVintedUserInfo()                        │
│         ↓                                                        │
│  const html = document.documentElement.innerHTML                │
│  const userIdMatch = html.match(/\\"userId\\":\\"(\\d+)\\\"/)        │
│  const loginMatch = html.match(/\\"login\\":\\"([^"]+)\\\"/)        │
│         ↓                                                        │
│  Résultat: { userId: "29535217", login: "shop.ton.outfit" }   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              3. USER OUVRE LE POPUP                              │
│                                                                  │
│  VintedSessionInfo.vue (composant popup)                        │
│         ↓                                                        │
│  Cherche un onglet Vinted ouvert                                │
│         ↓                                                        │
│  Envoie message au content script                               │
│  chrome.tabs.sendMessage(tabId, {                              │
│    action: 'GET_VINTED_USER_INFO'                              │
│  })                                                            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│           4. CONTENT SCRIPT RÉPOND                               │
│                                                                  │
│  vinted.ts reçoit 'GET_VINTED_USER_INFO'                       │
│         ↓                                                        │
│  Appelle getVintedUserInfo()                                    │
│         ↓                                                        │
│  Retourne:                                                       │
│  {                                                              │
│    success: true,                                              │
│    data: {                                                     │
│      userId: "29535217",                                       │
│      login: "shop.ton.outfit"                                  │
│    }                                                           │
│  }                                                             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              5. POPUP DÉTECTE LA CONNEXION                       │
│                                                                  │
│  VintedSessionInfo.vue vérifie:                                │
│         ↓                                                        │
│  session.isConnected = !!(userId && login)                     │
│         ↓                                                        │
│  SI les deux sont présents:                                     │
│    - ✅ session.isConnected = true                             │
│    - Affiche: "🟢 Vinted - Connecté"                           │
│    - Affiche userId + login                                     │
│  SINON:                                                          │
│    - ❌ session.isConnected = false                             │
│    - Affiche: "🔴 Vinted - Non connecté"                       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│          6. SYNCHRONISATION AVEC BACKEND (OPTIONNEL)             │
│                                                                  │
│  StoflowAPI.syncVintedUser(userId, login)                      │
│         ↓                                                        │
│  POST /api/vinted/user/sync                                     │
│  Body: {                                                        │
│    vinted_user_id: 29535217,                                   │
│    login: "shop.ton.outfit"                                    │
│  }                                                             │
│         ↓                                                        │
│  Backend stocke dans DB:                                        │
│  table vinted_connection (vinted_user_id, login, last_sync)   │
│  table users (vinted_user_id, vinted_username)                │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📂 Fichiers Concernés

### 1. Content Script: vinted.ts
**Localisation**: `/home/maribeiro/Stoflow/StoFlow_Plugin/src/content/vinted.ts`

**Rôle**: Script injecté sur toutes les pages vinted.fr

**Handler de message**:
```typescript
if (action === 'GET_VINTED_USER_INFO') {
  VintedLogger.debug('📨 [VINTED] Message reçu: GET_VINTED_USER_INFO');
  try {
    const userInfo = getVintedUserInfo();
    sendResponse({
      success: true,
      data: {
        userId: userInfo.userId,
        login: userInfo.login
      }
    });
  } catch (error) {
    sendResponse({ success: false, error: error.message });
  }
  return true;
}
```

**Logs attendus** (Console vinted.fr):
```
📨 [VINTED] Message reçu: GET_VINTED_USER_INFO
🔍 [VINTED DETECTOR] Extraction userId + login...
🔍 Taille HTML: 250000 caractères
🔍 userId trouvé: 29535217
🔍 ✅ Login final: shop.ton.outfit
```

### 2. Détecteur: vinted-detector.ts
**Localisation**: `/home/maribeiro/Stoflow/StoFlow_Plugin/src/content/vinted-detector.ts`

**Fonction**: `getVintedUserInfo()`

**Regex utilisées**:
```typescript
// Extraction userId
const userIdMatch = html.match(/\\"userId\\":\\"(\\d+)\\"/)
// Exemple match: "userId":"29535217"

// Extraction login (associé au userId)
const pattern = new RegExp(`\\"userId\\":\\"${userId}\\"[^}]*\\"login\\":\\"([^"\\\\]+)\\"`)
// Exemple match: "userId":"29535217"..."login":"shop.ton.outfit"

// Fallback login
const fallbackLogin = html.match(/\\"login\\":\\"([^"\\\\]+)\\"/)
```

### 3. Composant Popup: VintedSessionInfo.vue
**Localisation**: `/home/maribeiro/Stoflow/StoFlow_Plugin/src/components/VintedSessionInfo.vue`

**Méthode**: `loadVintedSession()`

**Code simplifié**:
```typescript
// 1. Chercher un onglet Vinted
const [tab] = await chrome.tabs.query({ url: 'https://*.vinted.fr/*' });

// 2. Envoyer message au content script
const response = await chrome.tabs.sendMessage(tab.id, {
  action: 'GET_VINTED_USER_INFO'
});

// 3. Détection de connexion
if (response?.success) {
  session.value.userId = response.data.userId || null;
  session.value.login = response.data.login || null;

  // ✅ Connecté = userId ET login présents
  session.value.isConnected = !!(response.data.userId && response.data.login);
}
```

**Logs attendus** (Console popup):
```
🎯 [POPUP] Envoi de GET_VINTED_USER_INFO au tab 123
🎯 Réponse reçue: { success: true, data: { userId: "29535217", login: "shop.ton.outfit" } }
🎯 ✅ Connecté à Vinted (userId + login extraits)
```

### 4. API Backend: StoflowAPI.ts
**Localisation**: `/home/maribeiro/Stoflow/StoFlow_Plugin/src/api/StoflowAPI.ts`

**Méthode**: `syncVintedUser(userId, login)`

```typescript
static async syncVintedUser(userId: string, login: string): Promise<any> {
  const token = await this.getToken();

  const response = await fetch(`${this.baseUrl}/api/vinted/user/sync`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      vinted_user_id: parseInt(userId),
      login: login
    })
  });

  return await response.json();
}
```

**Méthode**: `getVintedConnectionStatus()`

```typescript
static async getVintedConnectionStatus(): Promise<any> {
  const token = await this.getToken();

  const response = await fetch(`${this.baseUrl}/api/vinted/user/status`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });

  return await response.json();
}
```

---

## 🧪 Test du Flow

### Préparation
1. ✅ Plugin chargé dans Firefox
2. ✅ Ouvrir https://www.vinted.fr
3. ✅ Se connecter à Vinted

### Test 1: Extraction userId + login

```javascript
// Console vinted.fr - Simuler extraction
const html = document.documentElement.innerHTML;
const userIdMatch = html.match(/\\"userId\\":\\"(\\d+)\\"/);
const userId = userIdMatch ? userIdMatch[1] : null;
console.log('userId:', userId);
// Expected: "29535217"

const loginMatch = html.match(/\\"login\\":\\"([^"\\\\]+)\\"/);
const login = loginMatch ? loginMatch[1] : null;
console.log('login:', login);
// Expected: "shop.ton.outfit"
```

### Test 2: Message Popup → Content Script

```javascript
// Console popup (clic droit sur popup → Inspecter)
chrome.tabs.query({ url: 'https://*.vinted.fr/*' }, tabs => {
  if (tabs[0]) {
    chrome.tabs.sendMessage(tabs[0].id, {
      action: 'GET_VINTED_USER_INFO'
    }, response => {
      console.log('Réponse:', response);
    });
  }
});

// Expected output:
// Réponse: { success: true, data: { userId: "29535217", login: "shop.ton.outfit" } }
```

### Test 3: Vérification Popup

1. **Ouvrir popup** (clic sur icône plugin)
2. **Section Vinted** devrait afficher:
   - Si userId ET login extraits: 🟢 **Vinted** - Connecté
   - Si l'un des deux manque: 🔴 **Vinted** - Non connecté
   - **User ID**: 29535217 [📋 Copier]
   - **Login**: shop.ton.outfit [📋 Copier]
   - [🔄 Actualiser]

### Test 4: Sync Backend

```javascript
// Console background
const token = await chrome.storage.local.get('stoflow_access_token');
const response = await fetch('http://localhost:8000/api/vinted/user/sync', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token.stoflow_access_token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    vinted_user_id: 29535217,
    login: 'shop.ton.outfit'
  })
});
const data = await response.json();
console.log('Backend response:', data);
```

---

## 🐛 Problèmes Courants

### Problème 1: Popup dit "Non connecté"

**Symptômes**:
- Connecté sur vinted.fr
- Mais popup dit "🔴 Non connecté"

**Causes possibles**:
1. userId ou login non extrait du HTML
2. Content script non chargé
3. Onglet Vinted non trouvé

**Solution**:
```javascript
// Console vinted.fr - Vérifier extraction manuelle
const html = document.documentElement.innerHTML;
console.log('Test userId:', html.match(/\\"userId\\":\\"(\\d+)\\"/));
console.log('Test login:', html.match(/\\"login\\":\\"([^"\\\\]+)\\"/));

// Si null → HTML structure a changé ou pas connecté
// Si présents → Problème de communication popup ↔ content script
```

### Problème 2: userId / login non extraits

**Symptômes**:
- Popup dit "Connecté"
- Mais userId: N/A, login: N/A

**Causes possibles**:
1. HTML Vinted a changé de structure
2. Regex obsolètes
3. Pas vraiment connecté

**Solution**:
```javascript
// Console vinted.fr - Tester regex manuellement
const html = document.documentElement.innerHTML;

// Test userId
console.log('Test userId:', html.match(/\\"userId\\":\\"(\\d+)\\"/));

// Test login
console.log('Test login:', html.match(/\\"login\\":\\"([^"\\\\]+)\\"/));

// Si null → Chercher manuellement dans HTML:
console.log('Search userId:', html.includes('userId'));
console.log('Search login:', html.includes('login'));
```

### Problème 3: Content Script ne répond pas

**Symptômes**:
- Message "Rechargez la page Vinted pour activer l'extension"

**Solution**:
1. **Recharger** page Vinted (F5)
2. **Vérifier** console:
   ```
   🛍️ [VINTED] Content script chargé: https://www.vinted.fr/...
   ```
3. Si toujours rien → **Rebuild plugin**:
   ```bash
   cd /home/maribeiro/Stoflow/StoFlow_Plugin
   npm run build
   ```
4. **Recharger extension** dans Firefox (`about:debugging` → Recharger)

---

## ✅ Résultat Attendu

Après connexion Vinted + ouverture popup:

- [x] userId extrait: "29535217"
- [x] login extrait: "shop.ton.outfit"
- [x] Popup affiche: "🟢 Vinted - Connecté"
- [x] Boutons [📋 Copier] fonctionnels
- [x] Sync backend: POST /api/vinted/user/sync (uniquement userId + login)

---

## 🔧 Commandes Debug Utiles

### Console Vinted.fr

```javascript
// Forcer extraction
const userInfo = {
  userId: document.documentElement.innerHTML.match(/\\"userId\\":\\"(\\d+)\\"/)?.[1],
  login: document.documentElement.innerHTML.match(/\\"login\\":\\"([^"\\\\]+)\\"/)?.[1]
};
console.log('User Info:', userInfo);
console.log('Connecté:', !!(userInfo.userId && userInfo.login));
```

### Console Background

```javascript
// Forcer sync Vinted
await StoflowAPI.syncVintedUser('29535217', 'shop.ton.outfit');

// Vérifier statut connexion
const status = await StoflowAPI.getVintedConnectionStatus();
console.log('Status:', status);
```

### Console Popup

```javascript
// Re-load session
loadVintedSession();

// Copier userId dans clipboard
navigator.clipboard.writeText('29535217');
```

---

## 🔄 Endpoints Backend (Simplifié)

### ✅ À UTILISER:

**POST /api/vinted/user/sync**
- Sync uniquement userId + login
- Stocke dans `vinted_connection` table
- Pas de csrf_token, anon_id, email, etc.

**GET /api/vinted/user/status**
- Retourne: is_connected, vinted_user_id, login, last_sync
- Version simplifiée

### ❌ OBSOLÈTES (Supprimés):

~~POST /api/vinted/credentials/sync~~
- Supprimé (trop complexe, 15+ champs)

~~GET /api/vinted/credentials/status~~
- Supprimé (utilise /user/status à la place)

---

*Dernière mise à jour: 11 décembre 2025*
*Flow simplifié: Connexion = userId + login extraits*
