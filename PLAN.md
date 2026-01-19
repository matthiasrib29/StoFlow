# Plan: Socket.IO Acknowledgement Pattern

## Objectif
Implémenter le pattern d'acknowledgement Socket.IO pour garantir la livraison des messages `plugin_response` du frontend vers le backend, même en cas de déconnexion.

## Problème Actuel
1. Le frontend émet `plugin_response` mais le socket peut être en état "zombie" (connected=true côté client mais déjà fermé côté serveur)
2. Le message est perdu et le backend timeout après 60s
3. Cela affecte systématiquement la première requête après connexion

## Solution: Pattern ACK avec Retry

### Principe
```
Frontend                          Backend
   |                                 |
   |-- emit('plugin_response') ---->|
   |                                 |-- traite la réponse
   |<-------- ACK callback ---------|
   |                                 |
   | Si pas d'ACK après timeout:     |
   |-- retry emit ----------------->|
```

---

## Phase 1: Backend - Ajouter le support ACK

### Fichier: `backend/services/websocket_service.py`

**Modification du handler `plugin_response`:**

```python
@sio.on('plugin_response')
async def plugin_response(sid, data):
    """Handle response from frontend plugin bridge."""
    request_id = data.get('request_id')

    logger.info(f"[WebSocket] ═══ RESPONSE RECEIVED ═══")
    logger.info(f"[WebSocket] SID: {sid}")
    logger.info(f"[WebSocket] Request ID: {request_id}")

    # ... existing processing logic ...

    # NOUVEAU: Retourner un ACK pour confirmer la réception
    # Socket.IO appelle automatiquement le callback client avec cette valeur
    return {"status": "ok", "request_id": request_id}
```

**Points clés:**
- Le `return` dans un handler Socket.IO envoie automatiquement l'ACK au client
- Le client reçoit cette valeur dans son callback

---

## Phase 2: Frontend - Utiliser emit avec ACK et retry

### Fichier: `frontend/composables/useWebSocket.ts`

**2.1 Supprimer le hack `pendingResponses`:**
- Supprimer la Map `pendingResponses`
- Supprimer la logique de re-emit dans `reconnect`
- Supprimer le `setTimeout` après emit

**2.2 Créer une fonction `emitWithRetry`:**

```typescript
/**
 * Emit with acknowledgement and automatic retry
 * Uses Socket.IO's built-in timeout and callback mechanism
 */
async function emitWithRetry(
  event: string,
  data: any,
  maxRetries = 3,
  timeout = 10000
): Promise<any> {
  let lastError: Error | null = null

  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      wsLog.info(`Emitting ${event} (attempt ${attempt}/${maxRetries})...`)

      const ack = await new Promise((resolve, reject) => {
        socket.value?.timeout(timeout).emit(event, data, (err: any, response: any) => {
          if (err) {
            // Timeout or socket error
            reject(new Error(err.message || 'Emit timeout'))
          } else {
            resolve(response)
          }
        })
      })

      wsLog.success(`${event} acknowledged by server`)
      return ack

    } catch (err: any) {
      lastError = err
      wsLog.warn(`${event} attempt ${attempt} failed: ${err.message}`)

      if (attempt < maxRetries) {
        // Wait before retry (exponential backoff)
        const delay = Math.min(1000 * Math.pow(2, attempt - 1), 5000)
        wsLog.info(`Retrying in ${delay}ms...`)
        await new Promise(r => setTimeout(r, delay))
      }
    }
  }

  throw lastError || new Error(`Failed to emit ${event} after ${maxRetries} attempts`)
}
```

**2.3 Modifier `handlePluginCommand` pour utiliser `emitWithRetry`:**

```typescript
// Au lieu de:
socket.value?.emit('plugin_response', responsePayload)

// Utiliser:
try {
  await emitWithRetry('plugin_response', responsePayload, 3, 10000)
  wsLog.success(`plugin_response confirmed for ${data.request_id}`)
} catch (err: any) {
  wsLog.error(`Failed to deliver plugin_response: ${err.message}`)
  // La réponse est perdue, le backend va timeout
  // Mais au moins on a essayé 3 fois
}
```

---

## Phase 3: Configuration Socket.IO Client

### Fichier: `frontend/composables/useWebSocket.ts`

**Option alternative: Utiliser la config built-in (Socket.IO v4.6+):**

```typescript
socket.value = io(backendUrl, {
  auth: {
    user_id: authStore.user.id,
    token: authStore.token
  },
  transports: ['websocket'],
  reconnection: true,
  reconnectionDelay: 1000,
  reconnectionDelayMax: 5000,
  reconnectionAttempts: 10,
  // NOUVEAU: Config ACK built-in
  ackTimeout: 10000,  // 10s timeout pour ACK
  retries: 3          // 3 retries automatiques
})
```

**Note:** Avec cette config, tous les `emit()` seront automatiquement retried si le serveur ne répond pas. Mais cela nécessite que TOUS les handlers serveur retournent un ACK.

---

## Phase 4: Tests et Validation

### 4.1 Test manuel
1. Lancer `/dev`
2. Ouvrir la console browser
3. Lancer une sync Vinted
4. Vérifier les logs:
   - `plugin_response acknowledged by server` doit apparaître
   - Pas de timeout côté backend

### 4.2 Test de résilience
1. Simuler une déconnexion pendant le traitement:
   - Dans les DevTools > Network > Offline (pendant 2s)
2. Vérifier que le retry fonctionne:
   - Logs: `attempt 1 failed`, `Retrying...`, `attempt 2`, `acknowledged`

### 4.3 Vérifier les logs backend
```
[WebSocket] ✓ Response received
[WebSocket] ✓ ACK sent to client
```

---

## Fichiers à Modifier

| Fichier | Modification |
|---------|--------------|
| `backend/services/websocket_service.py` | Ajouter `return` dans `plugin_response` handler |
| `frontend/composables/useWebSocket.ts` | Ajouter `emitWithRetry`, modifier `handlePluginCommand` |

---

## Risques et Mitigations

| Risque | Mitigation |
|--------|------------|
| Backend ne supporte pas ACK | Tester avec python-socketio - le `return` devrait fonctionner |
| Retry cause des duplicates | Le backend utilise `request_id` pour déduplication (déjà en place) |
| Timeout trop court | Configurer 10s (suffisant pour traitement + latence) |
| Trop de retries | Limiter à 3 avec exponential backoff |

---

## Ordre d'Implémentation

1. **Backend d'abord** - Ajouter le `return` ACK (1 ligne)
2. **Frontend** - Créer `emitWithRetry`
3. **Frontend** - Modifier `handlePluginCommand`
4. **Frontend** - Cleanup du hack `pendingResponses`
5. **Test** - Valider le flow complet

---

## Estimation

- Phase 1 (Backend ACK): ~5 min
- Phase 2 (Frontend retry): ~15 min
- Phase 3 (Config optionnelle): ~5 min
- Phase 4 (Tests): ~10 min

**Total: ~35 min**
