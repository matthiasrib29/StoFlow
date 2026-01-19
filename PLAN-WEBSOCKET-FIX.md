# Plan: Fix WebSocket Disconnect Loop

## Worktree de Travail

```
/home/maribeiro/StoFlow-fiw-websocket/
```

Branche: `hotfix/fiw-websocket`

---

## Probleme Identifie

Les logs backend montrent:
- **18 connexions Engine.IO** pour un seul utilisateur en 6 minutes
- Seulement **4 authentifiees** au niveau Socket.IO
- **Connexions en rafale** (4 simultanées) lors des hot-reload Vite
- **Pattern disconnect → reconnect immediat** en boucle

### Causes Racines

1. **Vite HMR** - Recharge les modules sans fermer l'ancien socket
2. **Watchers multiples** - Le plugin websocket.client.ts declenche connect() plusieurs fois
3. **Pas de singleton** - Chaque appel useWebSocket() peut creer une nouvelle instance

---

## Solution

### Architecture Cible

```
Auth Store (auth.ts)
├── login()          → ws.connect()    [explicite]
├── logout()         → ws.disconnect() [explicite]
├── loadFromStorage()→ ws.connect()    [session restore]
└── refreshToken()   → update socket.auth [pas de reconnect]

useWebSocket.ts
├── import.meta.hot.data → Preserve socket entre HMR
├── autoConnect: false   → Pas de connexion auto
├── Singleton pattern    → Une seule instance
└── connect()/disconnect()→ Appels explicites

websocket.client.ts
└── SUPPRIME ou simplifie (plus de watcher)
```

---

## Fichiers a Modifier

| Fichier | Action |
|---------|--------|
| `frontend/composables/useWebSocket.ts` | Refactoring HMR + singleton |
| `frontend/stores/auth.ts` | Ajouter connect/disconnect explicites |
| `frontend/plugins/websocket.client.ts` | Supprimer watcher, simplifier |

---

## Implementation

### Phase 1: useWebSocket.ts

1. Utiliser `import.meta.hot.data` pour preserver le socket entre HMR
2. Pattern singleton strict
3. `autoConnect: false` dans la config Socket.IO
4. Nettoyer les listeners avant disconnect

### Phase 2: auth.ts

1. Importer useWebSocket de facon lazy (eviter import circulaire)
2. Appeler `ws.connect()` apres login/loadFromStorage reussi
3. Appeler `ws.disconnect()` AVANT logout/clear

### Phase 3: websocket.client.ts

1. Supprimer le watcher sur isAuthenticated
2. Garder uniquement un log de debug si necessaire

---

## Tests de Validation

1. **Login frais** - WebSocket se connecte une seule fois
2. **Logout** - WebSocket se deconnecte proprement
3. **Session restore** - WebSocket se reconnecte au refresh page
4. **Vite HMR** - Socket ID reste le MEME apres modification de code
5. **Pas de boucle** - Une seule connexion dans les logs backend

---

## Rollback

Si probleme:
1. `git checkout develop -- frontend/composables/useWebSocket.ts`
2. `git checkout develop -- frontend/stores/auth.ts`
3. `git checkout develop -- frontend/plugins/websocket.client.ts`
