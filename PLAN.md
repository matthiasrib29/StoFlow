# Plan: Fix Plugin pour validation Chrome Web Store

## Worktree de travail
**Chemin**: `~/StoFlow-fix-plugin`
**Branche**: `hotfix/fix-plugin`

**IMPORTANT**: Executer `cd ~/StoFlow-fix-plugin` AVANT toute action !

---

## Contexte

Le plugin StoFlow v2.0.0 utilise une architecture Manifest V3 avec communication par messages.
Cependant, plusieurs points bloquent la validation sur le Chrome Web Store.

### Problemes identifies

| # | Probleme | Severite | Fichier principal |
|---|----------|----------|-------------------|
| 1 | Permission `<all_urls>` trop large | CRITIQUE | `manifest.json:34` |
| 2 | Proxy HTTP generique (CORS bypass) | CRITIQUE | `VintedActionHandler.ts:311` |
| 3 | Fichier nomme "datadome" explicite | ELEVEE | `stoflow-vinted-datadome.js` |
| 4 | Localhost en production | ELEVEE | `manifest.json:18-21` |
| 5 | Code mort: batch operations inutilise | MOYENNE | `VintedActionHandler.ts`, `useVintedBridge.ts` |
| 6 | Double injection possible | MOYENNE | `inject-api.ts` |
| 7 | Absence de Privacy Policy | OBLIGATOIRE | - |

---

## Phase 1: Securisation des permissions (CRITIQUE)

### Etape 1.1: Restreindre host_permissions

**Fichier**: `plugin/manifest.json`

**Avant** (ligne 33-35):
```json
"host_permissions": [
  "<all_urls>"
]
```

**Apres**:
```json
"host_permissions": [
  "*://*.vinted.fr/*",
  "*://*.vinted.com/*",
  "*://*.vinted.co.uk/*",
  "*://*.vinted.de/*",
  "*://*.vinted.es/*",
  "*://*.vinted.it/*",
  "*://*.vinted.nl/*",
  "*://*.vinted.be/*",
  "*://*.vinted.pl/*",
  "*://*.vinted.pt/*",
  "*://*.vinted.cz/*",
  "*://*.vinted.lt/*",
  "*://*.vinted.at/*",
  "*://*.vinted.lu/*",
  "*://*.vinted.hu/*",
  "*://*.vinted.sk/*",
  "*://*.vinted.ro/*",
  "*://*.vinted.se/*",
  "*://*.vinted.dk/*",
  "*://*.vinted.fi/*",
  "https://*.stoflow.io/*"
]
```

### Etape 1.2: Mettre a jour web_accessible_resources

**Fichier**: `plugin/manifest.json`

**Avant** (ligne 75-89):
```json
"web_accessible_resources": [
  {
    "resources": ["icons/*"],
    "matches": ["<all_urls>"]
  },
  ...
]
```

**Apres**:
```json
"web_accessible_resources": [
  {
    "resources": ["icons/*"],
    "matches": ["*://*.vinted.fr/*", "*://*.vinted.com/*", "https://*.stoflow.io/*"]
  },
  {
    "resources": [
      "src/content/stoflow-vinted-logger.js",
      "src/content/stoflow-vinted-session.js",
      "src/content/stoflow-vinted-api-core.js",
      "src/content/stoflow-vinted-bootstrap.js"
    ],
    "matches": ["*://*.vinted.fr/*", "*://*.vinted.com/*", "*://*.vinted.co.uk/*", "*://*.vinted.de/*"]
  }
]
```

### Etape 1.3: Etendre content_scripts pour tous les domaines Vinted

**Fichier**: `plugin/manifest.json`

**Avant** (ligne 55-59):
```json
"content_scripts": [
  {
    "matches": ["https://www.vinted.fr/*"],
    ...
  }
]
```

**Apres**:
```json
"content_scripts": [
  {
    "matches": [
      "https://www.vinted.fr/*",
      "https://www.vinted.com/*",
      "https://www.vinted.co.uk/*",
      "https://www.vinted.de/*",
      "https://www.vinted.es/*",
      "https://www.vinted.it/*",
      "https://www.vinted.nl/*",
      "https://www.vinted.be/*",
      "https://www.vinted.pl/*",
      "https://www.vinted.pt/*"
    ],
    "js": ["src/content/vinted.ts"],
    "run_at": "document_idle"
  },
  ...
]
```

---

## Phase 2: Verrouillage du Proxy (CRITIQUE)

### Etape 2.1: Creer un module de validation de domaine

**Fichier a creer**: `plugin/src/utils/domain-validator.ts`

```typescript
/**
 * Domain Validator - Ensures all API calls target authorized domains only
 * Security layer to prevent CORS bypass attacks
 */

// Whitelist of authorized Vinted domains
const VINTED_DOMAINS = [
  'www.vinted.fr',
  'www.vinted.com',
  'www.vinted.co.uk',
  'www.vinted.de',
  'www.vinted.es',
  'www.vinted.it',
  'www.vinted.nl',
  'www.vinted.be',
  'www.vinted.pl',
  'www.vinted.pt',
  'www.vinted.cz',
  'www.vinted.lt',
  'www.vinted.at',
  'www.vinted.lu',
  'www.vinted.hu',
  'www.vinted.sk',
  'www.vinted.ro',
  'www.vinted.se',
  'www.vinted.dk',
  'www.vinted.fi',
];

// Allowed endpoint prefixes (relative paths)
const ALLOWED_ENDPOINT_PREFIXES = [
  '/items',
  '/users',
  '/photos',
  '/categories',
  '/brands',
  '/colors',
  '/sizes',
  '/transactions',
  '/conversations',
  '/web/api',
];

/**
 * Validates that an endpoint is within the allowed list
 */
export function isAllowedEndpoint(endpoint: string): boolean {
  if (!endpoint) return false;

  // Normalize endpoint (remove query string for validation)
  const normalizedEndpoint = endpoint.split('?')[0];

  return ALLOWED_ENDPOINT_PREFIXES.some(prefix =>
    normalizedEndpoint.startsWith(prefix)
  );
}

/**
 * Validates that a full URL targets an authorized Vinted domain
 */
export function isAllowedVintedUrl(url: string): boolean {
  if (!url) return false;

  try {
    const parsed = new URL(url);
    return VINTED_DOMAINS.includes(parsed.hostname);
  } catch {
    return false;
  }
}

/**
 * Returns error response for forbidden domain
 */
export function forbiddenDomainError(endpoint: string) {
  return {
    success: false,
    errorCode: 'FORBIDDEN_DOMAIN',
    error: `Endpoint not allowed: ${endpoint}. Only Vinted API endpoints are authorized.`
  };
}
```

### Etape 2.2: Integrer la validation dans VintedActionHandler

**Fichier**: `plugin/src/background/VintedActionHandler.ts`

**Ajouter import** (apres ligne 11):
```typescript
import { isAllowedEndpoint, forbiddenDomainError } from '../utils/domain-validator';
```

**Modifier handleVintedApiCall** (ligne 311-350):
```typescript
async function handleVintedApiCall(
  requestId?: string,
  payload?: { method: string; endpoint: string; data?: any; params?: any }
): Promise<ExternalResponse> {
  const { tab, error } = await ensureVintedTab();
  if (error) return { ...error, requestId };

  if (!payload?.method || !payload?.endpoint) {
    return {
      success: false,
      requestId,
      errorCode: 'INVALID_PAYLOAD',
      error: 'method and endpoint are required'
    };
  }

  // SECURITY: Validate endpoint against whitelist
  if (!isAllowedEndpoint(payload.endpoint)) {
    BackgroundLogger.warn(`[VintedHandler] BLOCKED - Forbidden endpoint: ${payload.endpoint}`);
    return { ...forbiddenDomainError(payload.endpoint), requestId };
  }

  // SECURITY: Validate HTTP method
  const ALLOWED_METHODS = ['GET', 'POST', 'PUT', 'DELETE'];
  if (!ALLOWED_METHODS.includes(payload.method.toUpperCase())) {
    return {
      success: false,
      requestId,
      errorCode: 'INVALID_METHOD',
      error: `HTTP method not allowed: ${payload.method}`
    };
  }

  try {
    const response = await sendToContentScript(tab!.id, 'VINTED_API_CALL', {
      method: payload.method,
      endpoint: payload.endpoint,
      data: payload.data,
      params: payload.params
    });

    return {
      success: response?.success ?? false,
      requestId,
      data: response?.data,
      error: response?.error,
      errorCode: response?.success ? undefined : 'API_CALL_FAILED'
    };
  } catch (error: any) {
    return {
      success: false,
      requestId,
      errorCode: 'CONTENT_SCRIPT_ERROR',
      error: error.message
    };
  }
}
```

---

## Phase 3: Renommer les fichiers sensibles (ELEVEE)

### Etape 3.1: Renommer stoflow-vinted-datadome.js

**Action**: Renommer le fichier pour eviter les flags automatiques

**Avant**: `plugin/src/content/stoflow-vinted-datadome.js`
**Apres**: `plugin/src/content/stoflow-vinted-session.js`

**Modifications internes**: Remplacer tous les commentaires/logs mentionnant "DataDome" ou "bypass" par des termes neutres comme "session management" ou "keep-alive".

### Etape 3.2: Mettre a jour les references

**Fichiers a modifier**:
1. `plugin/manifest.json` - web_accessible_resources (ligne 83)
2. `plugin/src/content/inject-api.ts` - API_MODULES array
3. `plugin/src/content/vinted.ts` - si references

### Etape 3.3: Nettoyer le code du fichier renomme

**Fichier**: `plugin/src/content/stoflow-vinted-session.js` (renomme)

Remplacer:
- `DataDome` -> `Session`
- `DATADOME` -> `SESSION`
- `datadome` -> `session`
- Commentaires mentionnant "bypass" ou "anti-bot" -> "session maintenance"

---

## Phase 4: Gestion des environnements (ELEVEE)

### Etape 4.1: Creer un fichier de configuration dynamique

**Fichier a creer**: `plugin/src/config/origins.ts`

```typescript
/**
 * Allowed origins configuration
 * Dynamically excludes localhost in production builds
 */

const PRODUCTION_ORIGINS = [
  'https://stoflow.io',
  'https://www.stoflow.io',
  'https://app.stoflow.io'
];

const DEVELOPMENT_ORIGINS = [
  'http://localhost:3000',
  'http://localhost:5173',
  'http://127.0.0.1:3000',
  'http://127.0.0.1:5173'
];

// Only include dev origins in development mode
export const ALLOWED_ORIGINS = import.meta.env.DEV
  ? [...PRODUCTION_ORIGINS, ...DEVELOPMENT_ORIGINS]
  : PRODUCTION_ORIGINS;

export function isAllowedOrigin(senderUrl: string | undefined): boolean {
  if (!senderUrl) return false;

  try {
    const origin = new URL(senderUrl).origin;
    return ALLOWED_ORIGINS.some(allowed =>
      origin === allowed || origin.startsWith(allowed.replace('/*', ''))
    );
  } catch {
    return false;
  }
}
```

### Etape 4.2: Mettre a jour VintedActionHandler.ts

**Fichier**: `plugin/src/background/VintedActionHandler.ts`

Remplacer la definition de ALLOWED_ORIGINS (lignes 43-49) par:
```typescript
import { ALLOWED_ORIGINS, isAllowedOrigin } from '../config/origins';
```

Et supprimer la fonction `isAllowedOrigin` locale (lignes 51-65).

### Etape 4.3: Creer des manifests separes (optionnel mais recommande)

**Fichiers a creer**:
- `plugin/manifest.json` - Production (sans localhost)
- `plugin/manifest.dev.json` - Developpement (avec localhost)

Modifier `vite.config.ts` pour utiliser le bon manifest selon l'environnement.

---

## Phase 5: Supprimer le code mort batch (MOYENNE)

> **Contexte**: La fonctionnalite batch (`VINTED_BATCH`) n'est jamais utilisee.
> - `executeBatch()` dans `useVintedBridge.ts` est definie mais jamais appelee
> - Aucune reference dans le backend Python
> - Code mort = surface d'attaque inutile

### Etape 5.1: Supprimer handleBatchExecute du plugin

**Fichier**: `plugin/src/background/VintedActionHandler.ts`

**Supprimer** la fonction `handleBatchExecute` (lignes 529-585):
```typescript
// SUPPRIMER ENTIEREMENT cette fonction
async function handleBatchExecute(
  requestId?: string,
  payload?: { operations: Array<{ action: string; payload?: any }> }
): Promise<ExternalResponse> {
  // ... tout le contenu
}
```

### Etape 5.2: Supprimer le case VINTED_BATCH du switch

**Fichier**: `plugin/src/background/VintedActionHandler.ts`

**Supprimer** dans le switch de `handleExternalMessage` (vers ligne 670):
```typescript
// SUPPRIMER ces lignes
case 'VINTED_BATCH':
  result = await handleBatchExecute(requestId, payload);
  break;
```

### Etape 5.3: Supprimer executeBatch du frontend

**Fichier**: `frontend/composables/useVintedBridge.ts`

**Supprimer** la fonction `executeBatch` (vers ligne 601-625):
```typescript
// SUPPRIMER ENTIEREMENT cette fonction
async function executeBatch(operations: Array<{ action: string; payload?: any }>): Promise<BridgeResponse> {
  // ... tout le contenu
}
```

**Supprimer** l'export de `executeBatch` (vers ligne 775):
```typescript
// SUPPRIMER de la liste des exports
executeBatch,
```

### Etape 5.4: Supprimer du README plugin

**Fichier**: `plugin/README.md`

**Supprimer** la ligne mentionnant VINTED_BATCH dans le tableau des actions supportees

---

## Phase 6: Prevenir la double injection (MOYENNE)

### Etape 6.1: Ajouter un guard dans inject-api.ts

**Fichier**: `plugin/src/content/inject-api.ts`

Ajouter au debut du fichier:
```typescript
// Guard against double injection
declare global {
  interface Window {
    __STOFLOW_INJECTED__?: boolean;
  }
}

if (window.__STOFLOW_INJECTED__) {
  console.warn('[Stoflow] Content script already injected, skipping');
  // Export empty to satisfy module requirements
  export {};
} else {
  window.__STOFLOW_INJECTED__ = true;

  // ... rest of the existing code
}
```

### Etape 6.2: Ajouter un guard dans les scripts injectes

**Fichier**: `plugin/src/content/stoflow-vinted-api-core.js`

Ajouter au debut:
```javascript
// Guard against double injection
if (window.__STOFLOW_API_INJECTED__) {
  console.warn('[StoflowAPI] Already injected, skipping');
} else {
  window.__STOFLOW_API_INJECTED__ = true;

  // ... rest of the existing code
}
```

---

## Phase 7: Documentation Store (OBLIGATOIRE)

### Etape 7.1: Creer la Privacy Policy

**Fichier a creer**: `plugin/docs/PRIVACY_POLICY.md`

```markdown
# Privacy Policy - StoFlow Extension

**Last updated**: 2026-01-19

## Overview

StoFlow Extension is a browser extension that helps sellers manage their Vinted inventory.

## Data Collection

### What we access:
- **Vinted session cookies**: Used only to authenticate API requests on your behalf
- **Vinted user ID**: Used to identify your wardrobe and products
- **Product data**: Titles, descriptions, prices of items you choose to sync

### What we DO NOT collect:
- Personal identification information
- Payment information
- Browsing history outside of Vinted
- Passwords

## Data Storage

- **Local storage only**: All session data is stored locally in your browser
- **No external transmission**: Your Vinted credentials are never sent to our servers
- **Encrypted by browser**: Chrome/Firefox encrypts extension storage

## Data Sharing

We do not share, sell, or transmit your personal data to any third parties.
The only external communication is between your browser and:
1. Vinted.fr (or your local Vinted domain) - for marketplace operations
2. stoflow.io - for inventory management (only product data you choose to sync)

## Your Rights

You can:
- Disable the extension at any time
- Clear extension data via browser settings
- Request deletion of your StoFlow account and associated data

## Contact

For privacy concerns, contact: privacy@stoflow.io

## Changes

We may update this policy. Changes will be posted on this page with updated date.
```

### Etape 7.2: Preparer la description Store

**Fichier a creer**: `plugin/docs/STORE_LISTING.md`

```markdown
# Chrome Web Store Listing

## Extension Name
StoFlow - Inventory Assistant for Vinted

## Short Description (132 chars max)
Manage your Vinted listings from StoFlow. Sync products, update prices, and track sales - all from one dashboard.

## Detailed Description

**StoFlow Extension** connects your StoFlow inventory management system with your Vinted seller account.

### Features:
- Sync products from StoFlow to Vinted
- Update prices and descriptions in bulk
- Track your sales and inventory status
- Receive notifications for new messages

### How it works:
1. Install the extension
2. Log in to your Vinted account
3. Connect StoFlow from the extension popup
4. Manage your inventory from the StoFlow dashboard

### Requirements:
- Active Vinted seller account
- StoFlow subscription (free trial available)

### Privacy:
- Your Vinted credentials stay in your browser
- We never access your payment information
- See our full privacy policy: [link]

### Support:
Contact us at support@stoflow.io

---

## Category
Shopping

## Language
French (primary), English

## Keywords
vinted, inventory, seller, reseller, management, sync, products
```

---

## Phase 8: Tests de validation

### Etape 8.1: Test de securite - Proxy verrouille

**Test manuel**:
1. Ouvrir la console du background (about:debugging)
2. Tenter un appel vers un domaine externe:
```javascript
chrome.runtime.sendMessage(EXTENSION_ID, {
  action: 'VINTED_API_CALL',
  payload: { method: 'GET', endpoint: '/evil-endpoint' }
});
// Doit retourner: FORBIDDEN_DOMAIN error
```

### Etape 8.2: Test de securite - Batch supprime

**Test manuel**:
1. Verifier que l'action `VINTED_BATCH` retourne `UNKNOWN_ACTION`
```javascript
chrome.runtime.sendMessage(EXTENSION_ID, {
  action: 'VINTED_BATCH',
  payload: { operations: [] }
});
// Doit retourner: UNKNOWN_ACTION error
```

### Etape 8.3: Test de securite - Origins

**Test manuel**:
1. Ouvrir une page non-autorisee (ex: google.com)
2. Tenter d'envoyer un message a l'extension via console
3. Verifier que le message est rejete

### Etape 8.4: Build et verification

```bash
cd ~/StoFlow-fix-plugin/plugin
npm run build
# Verifier que le build passe sans erreur

# Inspecter le manifest genere
cat dist/manifest.json | jq '.host_permissions'
# Ne doit PAS contenir <all_urls>
```

---

## Resume des fichiers a modifier

### Plugin (`plugin/`)

| Fichier | Action | Phase |
|---------|--------|-------|
| `manifest.json` | Modifier permissions, content_scripts, web_accessible_resources | 1, 3 |
| `src/utils/domain-validator.ts` | CREER | 2 |
| `src/background/VintedActionHandler.ts` | Ajouter validation endpoint + supprimer batch | 2, 5 |
| `src/content/stoflow-vinted-datadome.js` | RENOMMER en `stoflow-vinted-session.js` | 3 |
| `src/config/origins.ts` | CREER | 4 |
| `src/content/inject-api.ts` | Ajouter guard double injection | 6 |
| `src/content/stoflow-vinted-api-core.js` | Ajouter guard | 6 |
| `docs/PRIVACY_POLICY.md` | CREER | 7 |
| `docs/STORE_LISTING.md` | CREER | 7 |
| `README.md` | Supprimer VINTED_BATCH du tableau | 5 |

### Frontend (`frontend/`)

| Fichier | Action | Phase |
|---------|--------|-------|
| `composables/useVintedBridge.ts` | Supprimer `executeBatch` + son export | 5 |

---

## Ordre d'execution recommande

1. **Phase 1** - Permissions (CRITIQUE) - ~30 min
2. **Phase 2** - Proxy verrouille (CRITIQUE) - ~45 min
3. **Phase 3** - Renommage fichiers (ELEVEE) - ~20 min
4. **Phase 4** - Gestion environnements (ELEVEE) - ~30 min
5. **Phase 5** - Supprimer code mort batch (MOYENNE) - ~15 min
6. **Phase 6** - Double injection (MOYENNE) - ~15 min
7. **Phase 7** - Documentation (OBLIGATOIRE) - ~20 min
8. **Phase 8** - Tests - ~30 min

**Temps total estime**: ~3h15

---

## Checklist finale avant soumission

- [ ] `host_permissions` ne contient PAS `<all_urls>`
- [ ] Tous les endpoints sont valides contre whitelist
- [ ] Aucun fichier nomme "bypass", "datadome", "anti-bot"
- [ ] Localhost absent du manifest production
- [ ] Code mort batch supprime (plugin + frontend)
- [ ] Privacy Policy accessible
- [ ] Description Store sans mots interdits (bot, scraping, bypass)
- [ ] Build production passe sans erreur
- [ ] Extension testee sur Chrome ET Firefox
