# CLAUDE.md - StoFlow Browser Extension

> Pour les règles globales (commits, sécurité, etc.), voir [CLAUDE.md](../CLAUDE.md)
> Pour Vue.js 3, TypeScript et Vitest, voir [frontend/CLAUDE.md](../frontend/CLAUDE.md) (mêmes pratiques)

---

## Project Overview

Browser extension (Firefox/Chrome) that acts as a proxy between the StoFlow backend and Vinted API.
Handles authentication, API requests, and synchronization tasks.

### Loading in Browser
- **Firefox**: about:debugging -> Load Temporary Add-on -> select `dist/manifest.json`
- **Chrome**: chrome://extensions -> Load unpacked -> select `dist/` folder

---

## Architecture

### Key Directories
```
plugin/
├── src/
│   ├── background/      # Service worker (index.ts, VintedActionHandler.ts)
│   ├── popup/           # Extension popup UI (Vue)
│   ├── content/         # Content scripts (vinted.ts, stoflow-web.ts)
│   ├── api/             # Backend API client (StoflowAPI.ts)
│   ├── composables/     # Vue composables (useAuth.ts)
│   ├── components/      # Vue components
│   ├── types/           # TypeScript interfaces
│   ├── config/          # Environment configuration
│   └── utils/           # Shared utilities (logger, errors)
├── manifest.json        # Chrome Manifest V3
└── manifest.firefox.json # Firefox specific manifest
```

### Communication Flow (externally_connectable)
```
stoflow.io ---> chrome.runtime.sendMessage(EXTENSION_ID) ---> Plugin Background
                                                                     |
                                                                     v
                                                               Vinted Tab
                                                               (content script)
                                                                     |
                                                                     v
                                                               Vinted API

Firefox fallback (no externally_connectable support):
stoflow.io ---> postMessage ---> stoflow-web.ts ---> background ---> Vinted
```

---

## Development Rules

### Main Rule
**NEVER test Vinted API directly with curl or raw requests.**

All Vinted interactions must go through the extension's services.

---

## Chrome Extension Manifest V3

### Bonnes pratiques

**Structure du manifest**
```json
{
  "manifest_version": 3,
  "background": {
    "service_worker": "src/background/index.ts",
    "type": "module"
  },
  "permissions": ["storage", "cookies", "alarms"],
  "host_permissions": ["https://www.vinted.fr/*"]
}
```

**Service Worker - Listeners synchrones**
```typescript
// TOUJOURS enregistrer les listeners au top-level (synchrone)
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  handleMessage(msg).then(sendResponse);
  return true; // Keep channel open for async response
});
```

**Persistance de l'état**
```typescript
// Le SW peut être terminé à tout moment - ne jamais utiliser de variables globales
// Toujours persister l'état important
await chrome.storage.local.set({ lastSync: Date.now() });
```

### Mauvaises pratiques

- **Variables globales pour l'état** : Le SW se termine, utiliser `chrome.storage`
- **Code distant** : Interdit en MV3, tout doit être dans le package
- **Accès DOM dans SW** : Impossible, utiliser Offscreen Documents si nécessaire
- **Listeners async au top-level** : Les enregistrer de façon synchrone
- **Ne pas retourner `true`** dans onMessage pour les réponses async

### Pieges courants

- Le SW peut mettre du temps à démarrer (délai perceptible)
- `chrome.browserAction` → `chrome.action` en MV3
- `webRequest` pour bloquer → `declarativeNetRequest`
- Pas de `XMLHttpRequest` dans SW → utiliser `fetch()`
- Les permissions host doivent être dans `host_permissions`, pas `permissions`

### Sources
- [Migrate to Service Workers](https://developer.chrome.com/docs/extensions/develop/migrate/to-service-workers)
- [Service Worker Basics](https://developer.chrome.com/docs/extensions/develop/concepts/service-workers/basics)

---

## @crxjs/vite-plugin (v2.0.x)

### Bonnes pratiques

**Configuration manifest**
```typescript
// vite.config.ts
import { crx, ManifestV3Export } from '@crxjs/vite-plugin';
import manifest from './manifest.json';

export default defineConfig({
  plugins: [
    vue(),
    crx({ manifest: manifest as ManifestV3Export })
  ]
});
```

**HMR pour extensions**
```typescript
server: {
  port: 5173,
  strictPort: true,
  hmr: { clientPort: 5173 }
}
```

### Mauvaises pratiques

- **Manifest V2** : Toujours utiliser V3 (requis pour le Chrome Web Store)
- **Oublier le type "module"** pour le service worker

### Pieges courants

- Erreur "vite manifest is missing" en prod → vérifier la config rollupOptions
- Type errors avec le manifest → utiliser `ManifestV3Export` ou `defineManifest`
- Le service worker doit être déclaré comme string, pas array

### Sources
- [CRXJS Documentation](https://crxjs.dev/vite-plugin/)

---

## Security Rules (Extension-Specific)

> Les règles générales de sécurité sont dans [CLAUDE.md](../CLAUDE.md)

**Règles spécifiques aux extensions browser :**
- Store auth tokens in `chrome.storage.local` (encrypted by browser)
- Never execute remote code (Manifest V3 restriction)
- Verify message origins in `onMessageExternal` before processing
- Use `chrome.runtime.getURL()` for internal resources

---

## Environment Variables

```bash
# .env.development
VITE_API_URL=http://localhost:8000

# .env.production
VITE_API_URL=https://api.stoflow.com
```

---

## Important Files

| Fichier | Description |
|---------|-------------|
| `src/background/index.ts` | Main service worker |
| `src/background/VintedActionHandler.ts` | External message handler for Vinted actions |
| `src/api/StoflowAPI.ts` | Backend communication |
| `src/composables/useAuth.ts` | Authentication composable |
| `src/content/vinted.ts` | Vinted content script |
| `src/content/stoflow-web.ts` | StoFlow website integration (Firefox fallback) |

---

## Contexte Projet

- **Vue** : 3 composants simples (Popup, LoginForm, VintedSessionInfo)
- **TypeScript** : Mode strict (`tsconfig.json`)
- **Tests** : Vitest avec happy-dom (`vitest.config.ts`)
- **Build** : CRXJS gère Vite automatiquement

---

*Last updated: 2026-01-06*
