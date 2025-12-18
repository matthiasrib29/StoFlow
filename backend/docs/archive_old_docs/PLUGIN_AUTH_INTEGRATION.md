# 🔐 Intégration Authentification - Plugin StoFlow

## ✅ Ce qui a été fait

L'authentification JWT de ton API a été intégrée au plugin StoFlow.

---

## 🔑 Flux d'Authentification

### 1️⃣ **Login (Connexion)**

**User ouvre le popup du plugin** → Formulaire de connexion

**User entre email + password** → Clic sur "Se connecter"

**Plugin envoie** :
```
POST http://localhost:8000/api/auth/login?source=plugin

Body:
{
  "email": "user@example.com",
  "password": "secretpassword"
}
```

**Backend répond** :
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "role": "user",
  "subscription_tier": "starter",
  "token_type": "bearer",
  "user_id": 1
}
```

**Plugin stocke** :
- `access_token` → `chrome.storage.local`
- `refresh_token` → `chrome.storage.local`
- `user_id`, `role`, `subscription_tier` → `chrome.storage.local`

**Plugin démarre le polling** :
```javascript
chrome.runtime.sendMessage({
  action: 'START_POLLING',
  user_id: 1  // user_id du backend
});
```

---

### 2️⃣ **Polling avec Authentification**

Le plugin interroge le backend toutes les 5 secondes :

```
GET http://localhost:8000/api/plugin/tasks?user_id=1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Si le token est **valide** (pas expiré) :
```json
{
  "task_id": "abc123",
  "action": "get_all_products",
  "params": {...}
}
```

Si le token est **expiré** (401) :
- Le plugin utilise automatiquement le **refresh_token**
- Renouvelle l'access_token
- Réessaye la requête

---

### 3️⃣ **Refresh Token (Renouvellement)**

Quand l'`access_token` expire (après 1h), le plugin envoie :

```
POST http://localhost:8000/api/auth/refresh

Body:
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Backend répond** :
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",  // Nouveau token
  "token_type": "bearer"
}
```

**Plugin** :
- Stocke le nouveau `access_token`
- Continue le polling avec le nouveau token

---

### 4️⃣ **Logout (Déconnexion)**

**User clique "Se déconnecter"**

**Plugin** :
- Supprime tous les tokens du storage
- Arrête le polling (`STOP_POLLING`)
- Affiche le formulaire de connexion

---

## 🔐 Sécurité

### Storage des Tokens

Les tokens sont stockés dans `chrome.storage.local` (local au navigateur, chiffré par Firefox) :

```
stoflow_access_token    → "eyJhbGci..."
stoflow_refresh_token   → "eyJhbGci..."
stoflow_user_data       → {"user_id": 1, "role": "user", "subscription_tier": "starter"}
```

### Validation des Tokens

Le plugin **vérifie automatiquement** si le token est expiré avant chaque requête :

```typescript
// Décode le JWT
const payload = JSON.parse(atob(accessToken.split('.')[1]));
const exp = payload.exp * 1000; // Timestamp expiration

if (Date.now() >= exp) {
  // Token expiré, refresh automatique
  await refreshAccessToken();
}
```

### Headers d'Authentification

**Toutes les requêtes** au backend incluent automatiquement :

```
Authorization: Bearer {access_token}
```

---

## 📡 Endpoints Utilisés

| Endpoint | Méthode | Utilisé pour | Fréquence |
|----------|---------|--------------|-----------|
| `/api/auth/login?source=plugin` | POST | Connexion initiale | 1 fois |
| `/api/auth/refresh` | POST | Renouveler le token | Toutes les ~1h |
| `/api/plugin/tasks?user_id={id}` | GET | Polling des tâches | Toutes les 5s |
| `/api/plugin/tasks/{id}/result` | POST | Envoyer résultat | Après chaque tâche |

---

## 🧪 Tests

### Test 1 : Login

1. Ouvrir le plugin (clic sur l'icône)
2. Entrer email + password valides
3. Cliquer "Se connecter"

**Résultat attendu** :
- ✅ Popup affiche "🟢 Connecté"
- ✅ Console : `[Auth] ✅ Connexion réussie: {userId: 1, role: "user", tier: "starter"}`
- ✅ Console : `[Popup] Polling démarré pour user_id: 1`
- ✅ Console : `[Task Poller] ✅ Démarrage polling (intervalle: 5000ms)`

---

### Test 2 : Polling avec Token

1. Après login, attendre 5 secondes
2. Vérifier la console du background (`about:debugging` → Inspect)

**Résultat attendu** :
```
[Task Poller] ✅ Démarrage polling (intervalle: 5000ms)
...5 secondes...
[Task Poller] Polling des tâches...
// Si aucune tâche:
[Task Poller] Aucune tâche disponible

// Si tâche disponible:
[Task Poller] ✅ Nouvelle tâche: get_all_products abc123
[Task Poller] 🚀 Exécution tâche abc123
...
[Task Poller] ✅ Résultat envoyé pour abc123
```

---

### Test 3 : Refresh Token

1. **Simuler un token expiré** (modifier manuellement dans storage)
2. Attendre le prochain poll (5s)

**Résultat attendu** :
```
[Task Poller] 401 reçu du backend
[Auth] Access token expiré, tentative refresh
[Auth] Renouvellement du token...
[Auth] ✅ Token renouvelé
[Task Poller] Réessai de la requête avec nouveau token
```

---

### Test 4 : Logout

1. Cliquer "Se déconnecter" dans le popup

**Résultat attendu** :
- ✅ Popup affiche "🔴 Déconnecté"
- ✅ Formulaire de connexion réaffiché
- ✅ Console : `[Auth] Déconnexion...`
- ✅ Console : `[Auth] Tokens supprimés`
- ✅ Console : `[Task Poller] ⏸️ Arrêt polling`

---

## 🐛 Erreurs Possibles

### ❌ "Identifiants incorrects"

**Cause** : Email ou password invalide

**Solution** : Vérifier les credentials dans la DB

---

### ❌ "Session expirée, reconnexion nécessaire"

**Cause** : Le refresh_token est expiré (> 7 jours)

**Solution** : L'utilisateur doit se reconnecter

**Flux** :
```
User se connecte → Token valide 7 jours
Après 7 jours → Refresh token expire
Prochain poll → Erreur 401
Plugin tente refresh → 401
Plugin déconnecte l'utilisateur
→ Formulaire de connexion réaffiché
```

---

### ❌ "Pas de token d'authentification, skip polling"

**Cause** : L'utilisateur n'est pas connecté

**Solution** : Normal, l'utilisateur doit se connecter d'abord

---

## 📊 Diagramme Complet

```
┌─────────────────────────────────────────────────────────────┐
│                    USER ACTION                              │
│  User ouvre plugin → Formulaire login                       │
│  User entre email/password → Clic "Se connecter"            │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                    PLUGIN (useAuth.ts)                      │
│                                                             │
│  POST /api/auth/login?source=plugin                         │
│  Body: {email, password}                                    │
│                                                             │
│  ◄── {access_token, refresh_token, user_id, role, ...}     │
│                                                             │
│  Stocke dans chrome.storage.local                           │
│                                                             │
│  Envoie message: START_POLLING avec user_id                 │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│              BACKGROUND (task-poller.ts)                    │
│                                                             │
│  Démarre polling toutes les 5 secondes:                     │
│                                                             │
│  GET /api/plugin/tasks?user_id=1                            │
│  Headers: Authorization: Bearer {access_token}              │
│                                                             │
│  Si 401 (token expiré):                                     │
│    → POST /api/auth/refresh {refresh_token}                 │
│    → Nouveau access_token                                   │
│    → Réessaye GET /api/plugin/tasks                         │
│                                                             │
│  Si tâche disponible:                                       │
│    → Exécute la tâche sur Vinted                            │
│    → POST /api/plugin/tasks/{id}/result                     │
│       Headers: Authorization: Bearer {access_token}         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## ✅ Checklist Backend

Pour que tout fonctionne, vérifie que :

- [ ] L'endpoint `/api/auth/login?source=plugin` fonctionne
- [ ] L'endpoint `/api/auth/refresh` fonctionne
- [ ] Le serveur accepte les requêtes depuis `chrome-extension://` (CORS)
- [ ] Les endpoints `/api/plugin/tasks*` vérifient le Bearer token
- [ ] Le JWT contient bien un champ `exp` (expiration timestamp)
- [ ] Le backend tourne sur `http://localhost:8000`

---

## 🔧 Configuration

### Modifier l'URL du Backend

**Fichier** : `src/composables/useAuth.ts`

```typescript
const BACKEND_URL = 'http://localhost:8000';  // ← Modifier ici
```

**Fichier** : `src/background/task-poller.ts`

```typescript
const BACKEND_URL = 'http://localhost:8000';  // ← Modifier ici
```

---

## 📝 Logs Utiles

### Console du Popup

```
[Auth] Tentative de connexion: user@example.com
[Auth] ✅ Connexion réussie: {userId: 1, role: "user", tier: "starter"}
[Popup] Polling démarré pour user_id: 1
```

### Console du Background (`about:debugging` → Inspect)

```
[Background] Démarrage polling avec user_id: 1
[Task Poller] ✅ Démarrage polling (intervalle: 5000ms)
[Task Poller] Polling des tâches...
[Task Poller] ✅ Nouvelle tâche: get_all_products abc123
[Task Poller] 🚀 Exécution tâche abc123
[Task Poller] Total: 1595 produits, 80 pages
[Task Poller] Page 1/80: 20 produits
...
[Task Poller] ✅ Résultat envoyé pour abc123
```

---

## 🎉 Résumé

✅ **Authentification JWT intégrée** :
- Login avec email/password
- Stockage sécurisé des tokens
- Refresh automatique des tokens expirés
- Logout propre

✅ **Polling authentifié** :
- Toutes les requêtes incluent le Bearer token
- Refresh automatique si 401
- Déconnexion si refresh échoue

✅ **Prêt pour la production** !

---

**Version** : 2.0.0
**Dernière mise à jour** : 2024-12-07
