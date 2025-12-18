# 🔗 Guide SSO - Authentification automatique Frontend → Plugin

Ce guide explique comment configurer le SSO (Single Sign-On) pour que les utilisateurs connectés sur le site web Stoflow (localhost:3000) soient automatiquement authentifiés dans le plugin navigateur.

---

## 🎯 Concept

Quand un utilisateur se connecte sur **localhost:3000**, le frontend stocke le token JWT dans `localStorage`. Le plugin lit automatiquement ce token et s'authentifie sans que l'utilisateur ait besoin de re-saisir ses identifiants.

```
User se connecte sur localhost:3000
    ↓
Frontend Nuxt stocke token dans localStorage
    ↓
Plugin content script lit localStorage
    ↓
Plugin envoie token au background
    ↓
Plugin est authentifié ✅
```

---

## 📝 Côté Frontend (Nuxt.js)

### Option 1 : Utiliser localStorage (Déjà fait ?)

Si ton frontend Nuxt stocke déjà le token dans localStorage après login, **ça marche automatiquement** !

Le plugin cherche automatiquement ces clés :
- `stoflow_access_token`
- `stoflow_token`
- `access_token`
- `auth_token`
- `token`
- `auth` (objet JSON avec `access_token`)

**Exemple dans ton store Pinia ou composable :**

```typescript
// stores/auth.ts ou composables/useAuth.ts
export const useAuth = () => {
  const login = async (credentials) => {
    const response = await $fetch('/api/auth/login', {
      method: 'POST',
      body: credentials
    });

    const { access_token, refresh_token } = response;

    // ✅ Stocker dans localStorage (le plugin va le détecter)
    localStorage.setItem('stoflow_access_token', access_token);
    localStorage.setItem('stoflow_refresh_token', refresh_token);

    // Le plugin va automatiquement détecter ce changement et synchroniser
  };
};
```

### Option 2 : Message direct au plugin (Optionnel)

Si tu veux contrôler exactement quand le token est envoyé au plugin :

```typescript
// Après le login réussi
const syncTokenWithPlugin = async (accessToken: string, refreshToken: string) => {
  try {
    // Envoyer directement au plugin via message
    await chrome.runtime.sendMessage('YOUR_PLUGIN_ID', {
      action: 'SYNC_TOKEN_FROM_WEBSITE',
      access_token: accessToken,
      refresh_token: refreshToken
    });

    console.log('✅ Token synchronisé avec le plugin');
  } catch (error) {
    console.log('⚠️ Plugin non installé ou désactivé');
  }
};
```

---

## 🔧 Côté Plugin (Déjà fait ✅)

Le plugin a déjà tout ce qu'il faut :

### 1. Content Script sur localhost:3000 ✅

**Fichier : `src/content/stoflow-web.ts`**

Ce script :
- ✅ Lit automatiquement `localStorage` quand la page charge
- ✅ Détecte les changements de token (login/logout)
- ✅ Envoie le token au background script
- ✅ Affiche une notification "Plugin connecté"

### 2. Background Script ✅

**Fichier : `src/background/index.ts`**

Handler `SYNC_TOKEN_FROM_WEBSITE` qui :
- ✅ Reçoit le token depuis le content script
- ✅ Stocke dans `chrome.storage.local`
- ✅ Démarre automatiquement le polling
- ✅ Le plugin est maintenant authentifié

### 3. Manifest ✅

Permissions ajoutées :
- ✅ `http://localhost:3000/*` (host_permissions)
- ✅ Content script injecté sur localhost:3000

---

## 🚀 Test du SSO

### 1. Build le plugin

```bash
cd /home/maribeiro/Stoflow/StoFlow_Plugin
npm run build
```

### 2. Charger dans Firefox

1. Ouvrir Firefox
2. Taper `about:debugging` dans l'URL
3. Cliquer "This Firefox"
4. Cliquer "Load Temporary Add-on"
5. Sélectionner `dist/manifest.json`

### 3. Tester le flow

**Scénario 1 : Login sur le site web**
1. Ouvrir `http://localhost:3000`
2. Se connecter avec email/password
3. Ouvrir la console (F12) → Tu devrais voir :
   ```
   [Stoflow Web SSO] ✅ Token trouvé dans localStorage.stoflow_access_token
   [Stoflow Web SSO] ✅ Token synchronisé avec le plugin
   ```
4. Une notification verte apparaît : "✓ Plugin Stoflow connecté"
5. Ouvrir le plugin (clic sur l'icône) → Status : "🟢 Connecté"

**Scénario 2 : Déjà connecté**
1. User déjà connecté sur localhost:3000
2. Installer le plugin
3. Ouvrir n'importe quelle page localhost:3000
4. Le plugin se synchronise automatiquement

---

## 🔍 Debug

### Console du site web (F12 sur localhost:3000)

Tu devrais voir :
```
[Stoflow Web SSO] 🔗 Content script chargé sur http://localhost:3000/
[Stoflow Web SSO] ✅ Token trouvé dans localStorage.stoflow_access_token
[Stoflow Web SSO] ✅ Token synchronisé avec le plugin
[Stoflow Web SSO] ✅ Surveillance active du token
```

### Console du Background Script (`about:debugging` → Inspect)

Tu devrais voir :
```
[Background SSO] 🔗 Réception token depuis site web
[Background SSO] ✅ Token synchronisé depuis le site web
[Background SSO] 🚀 Démarrage du polling...
```

### Si ça ne marche pas

**Problème : Aucun log dans la console**
- Vérifier que le plugin est bien chargé dans `about:debugging`
- Vérifier que tu es bien sur `http://localhost:3000/*`
- Vérifier que le build a été fait (`npm run build`)

**Problème : "Aucun token trouvé"**
- Vérifier que le frontend stocke bien le token dans localStorage
- Ouvrir la console → Storage → Local Storage → Vérifier les clés
- Ajuster les noms de clés dans `stoflow-web.ts:17-24` si nécessaire

**Problème : "Erreur envoi au plugin"**
- Vérifier que le background script est actif
- Voir les logs dans `about:debugging` → Inspect

---

## 📊 Architecture Complète

```
┌─────────────────────────────────────────────────────────┐
│           FRONTEND NUXT (localhost:3000)                │
│                                                         │
│  1. User login                                          │
│  2. Store token in localStorage                         │
│      localStorage.setItem('stoflow_access_token', ...)  │
│                                                         │
└────────────────────┬────────────────────────────────────┘
                     │
                     │ Auto-détection
                     ▼
┌─────────────────────────────────────────────────────────┐
│      PLUGIN CONTENT SCRIPT (stoflow-web.ts)             │
│                                                         │
│  1. Lit localStorage toutes les 30s                     │
│  2. Détecte changements (login/logout)                  │
│  3. Envoie message au background                        │
│                                                         │
└────────────────────┬────────────────────────────────────┘
                     │
                     │ chrome.runtime.sendMessage()
                     ▼
┌─────────────────────────────────────────────────────────┐
│       PLUGIN BACKGROUND (background/index.ts)           │
│                                                         │
│  1. Reçoit token via message SYNC_TOKEN_FROM_WEBSITE    │
│  2. Stocke dans chrome.storage.local                    │
│  3. Démarre polling automatique                         │
│                                                         │
└────────────────────┬────────────────────────────────────┘
                     │
                     │ Polling toutes les 5s
                     ▼
┌─────────────────────────────────────────────────────────┐
│            BACKEND API (localhost:8000)                 │
│                                                         │
│  GET /api/plugin/tasks                                  │
│  Authorization: Bearer {token}                          │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## ✅ Checklist Implémentation

### Frontend Nuxt
- [ ] Stocker `access_token` dans localStorage après login
- [ ] Stocker `refresh_token` dans localStorage (optionnel)
- [ ] Supprimer tokens au logout
- [ ] Tester que les tokens sont bien dans localStorage (F12 → Storage)

### Plugin (Déjà fait ✅)
- [x] Content script sur localhost:3000
- [x] Lecture automatique de localStorage
- [x] Synchronisation avec background
- [x] Permissions manifest
- [x] Build et test

---

## 🎉 Résultat Final

Après implémentation, l'expérience utilisateur est :

1. **User se connecte sur localhost:3000** → Login normal
2. **Notification discrète** : "✓ Plugin Stoflow connecté"
3. **User ouvre le plugin** → Déjà connecté, pas besoin de re-login
4. **User peut synchroniser Vinted** → Immédiatement opérationnel

**Plus besoin de login dans le plugin !** 🎊

---

## 📞 Support

Si tu as des questions ou problèmes :
- Vérifier les logs console (F12)
- Vérifier `about:debugging` → Inspect
- Ajuster les noms de clés localStorage si besoin
- Vérifier que le backend accepte bien le token

---

**Version** : 1.0
**Dernière mise à jour** : 2025-12-09
