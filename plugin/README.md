# StoFlow Plugin - Browser Extension for Vinted Integration

Browser extension (Firefox/Chrome, Manifest V3) that acts as a **proxy bridge** between the StoFlow frontend and Vinted.

**Version**: 2.0.0
**Last updated**: 2026-01-19

---

## Overview

The plugin enables secure communication between StoFlow and Vinted by:
- Executing API calls in the browser context (with Vinted session cookies)
- Extracting CSRF tokens and authentication data dynamically
- Providing a message-passing bridge for cross-origin communication

```
StoFlow Frontend (stoflow.io)
    |
    | chrome.runtime.sendMessage (Chrome)
    | postMessage fallback (Firefox)
    v
Plugin Background Service Worker
    |
    | chrome.tabs.sendMessage
    v
Content Script (vinted.fr)
    |
    | Injects scripts into MAIN world
    | Hooks Vinted's Webpack Axios instance
    v
Vinted API (www.vinted.fr/api/v2/*)
```

---

## Features

### Auto-injection of Vinted Credentials
- **Cookies**: Session cookies via `credentials: 'include'`
- **X-CSRF-Token**: Extracted dynamically from DOM
- **X-Anon-Id**: Extracted dynamically from DOM
- **Content-Type**: Automatic (JSON or multipart)

### Generic HTTP Proxy
- All HTTP methods: `GET`, `POST`, `PUT`, `DELETE`, `PATCH`
- JSON body or FormData (multipart)
- Custom headers support
- File uploads (base64 to Blob conversion)

### Supported Actions
| Action | Description |
|--------|-------------|
| `PING` | Health check, returns version |
| `CHECK_VINTED_TAB` | Check if Vinted tab exists |
| `OPEN_VINTED_TAB` | Open new Vinted tab |
| `VINTED_GET_USER_INFO` | Get userId + login from DOM |
| `VINTED_GET_USER_PROFILE` | Fetch full user profile |
| `VINTED_API_CALL` | Generic HTTP call |
| `VINTED_PUBLISH` | Publish new product |
| `VINTED_UPDATE` | Update existing product |
| `VINTED_DELETE` | Delete product |
| `VINTED_BATCH` | Execute multiple operations |

---

## Installation

### Prerequisites
- Node.js 18+
- Firefox Developer Edition or Chrome 109+

### Build
```bash
npm install
npm run build        # Production build
npm run dev          # Dev mode with HMR
```

### Load in Browser

**Firefox**:
1. Open `about:debugging`
2. Click "This Firefox"
3. Click "Load Temporary Add-on"
4. Select `dist/manifest.json`

**Chrome**:
1. Open `chrome://extensions`
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select the `dist/` folder

---

## Architecture

### Directory Structure
```
plugin/
src/
|-- background/
|   |-- index.ts                    # Main service worker entry point
|   |-- VintedActionHandler.ts      # All Vinted operations handler (705 lines)
|-- content/
|   |-- vinted.ts                   # Content script for vinted.fr
|   |-- stoflow-web.ts              # Content script for stoflow.io (Firefox fallback)
|   |-- vinted-api-bridge.ts        # Bridge between ISOLATED and MAIN worlds
|   |-- vinted-detector.ts          # Extract user info from Vinted DOM
|   |-- inject-api.ts               # Script injection orchestrator
|   |-- message-utils.ts            # postMessage helpers
|   |-- stoflow-vinted-logger.js    # Injected: logging utilities
|   |-- stoflow-vinted-datadome.js  # Injected: DataDome handling
|   |-- stoflow-vinted-api-core.js  # Injected: API implementation
|   |-- stoflow-vinted-bootstrap.js # Injected: Webpack module hooking
|-- popup/
|   |-- Popup.vue                   # Extension popup UI
|-- components/
|   |-- VintedSessionInfo.vue       # Vinted connection status
|   |-- DevModeBanner.vue           # Dev mode indicator
|   |-- PermissionRequest.vue       # Permission requests
|-- options/
|   |-- Options.vue                 # Extension settings
|-- config/
|   |-- environment.ts              # Centralized configuration
|-- utils/
|   |-- logger.ts                   # Centralized logger with sanitization
|   |-- errors.ts                   # Custom error classes
|-- types/
    |-- webextension.d.ts           # Type definitions
```

### Communication Patterns

**Chrome (externally_connectable)**:
```
stoflow.io --> chrome.runtime.sendMessage --> Background --> Content Script --> Vinted
```

**Firefox (postMessage fallback)**:
```
stoflow.io --> postMessage --> stoflow-web.ts --> chrome.runtime.sendMessage --> Background --> Content Script --> Vinted
```

### World Isolation
- **ISOLATED world**: Content scripts with Chrome APIs access
- **MAIN world**: Injected scripts with access to page's JavaScript (Webpack)

Communication via `window.postMessage` with request/response pattern.

---

## Configuration

### Environment Variables
```bash
# .env.development
VITE_BACKEND_URL=http://localhost:8000
VITE_ENABLE_DEBUG_LOGS=true

# .env.production
VITE_BACKEND_URL=https://api.stoflow.io
VITE_ENABLE_DEBUG_LOGS=false
```

### Key Configuration (environment.ts)
| Variable | Default | Description |
|----------|---------|-------------|
| `BACKEND_URL` | `https://api.stoflow.io` | Backend API URL |
| `VINTED_REQUEST_TIMEOUT` | `30000` | Request timeout (ms) |
| `VINTED_MIN_REQUEST_DELAY` | `1000` | Min delay between requests (ms) |
| `ENABLE_DEBUG_LOGS` | `false` | Debug logging toggle |

---

## Security

### Permissions
```json
{
  "permissions": ["storage", "notifications", "scripting", "activeTab", "tabs"],
  "host_permissions": ["<all_urls>"]
}
```

### Security Features
- **Origin validation**: All external messages validated against whitelist
- **Content Security Policy**: `script-src 'self'; object-src 'self'`
- **Log sanitization**: Automatic masking of tokens, passwords, secrets
- **Timeout protection**: All async operations have 30s timeout

### Allowed Origins
```typescript
const ALLOWED_ORIGINS = [
  'https://stoflow.io',
  'https://www.stoflow.io',
  'https://app.stoflow.io',
  'http://localhost:3000',  // Dev only
  'http://localhost:5173'   // Dev only
];
```

---

## Code Quality Status

**Analysis Date**: 2026-01-19

### Technical Debt Score: MEDIUM (140 points)

| Severity | Count | Examples |
|----------|-------|----------|
| Critical | 3 | `any` type overuse (127 occurrences), untyped error handling |
| High | 12 | Files > 500 lines, no tests, JS/TS duplication |
| Medium | 18 | Magic numbers, inconsistent timeouts, exposed globals |
| Low | 14 | Naming inconsistencies, missing JSDoc |

### Critical Issues
1. **Excessive `any` type usage** (127 occurrences) - Loss of TypeScript benefits
2. **Files too long**: `VintedActionHandler.ts` (705 lines), `vinted.ts` (532 lines)
3. **No unit tests** - Vitest configured but no test files

### Recommended Refactoring
```
VintedActionHandler.ts (705 lines)
  --> handlers/UserHandlers.ts      (150 lines)
  --> handlers/ProductHandlers.ts   (200 lines)
  --> handlers/TabManager.ts        (100 lines)
  --> handlers/MessageSender.ts     (80 lines)
```

---

## Security Audit Status

**Security Score**: 6.5/10

### Critical Vulnerabilities

| Issue | Risk | Recommendation |
|-------|------|----------------|
| `<all_urls>` permission | HIGH | Restrict to specific domains |
| Batch operations unlimited | MEDIUM | Add `MAX_BATCH_SIZE = 100` |
| Double content script injection | MEDIUM | Add injection guard flag |
| localhost in production | MEDIUM | Remove dev origins in prod |

### Recommended Permission Fix
```json
{
  "host_permissions": [
    "https://www.vinted.fr/*",
    "https://www.vinted.com/*",
    "https://stoflow.io/*",
    "https://*.stoflow.io/*"
  ]
}
```

### Security Best Practices Implemented
- Origin validation with whitelist
- Log sanitization (tokens, passwords masked)
- CSP restrictive policy
- Request timeouts

---

## API Response Format

### Success Response
```typescript
interface ExternalResponse {
  success: true;
  requestId?: string;
  data?: any;
}
```

### Error Response
```typescript
interface ExternalResponse {
  success: false;
  requestId?: string;
  error: string;
  errorCode: string;
  status?: number;
}
```

### Error Codes
| Code | Description |
|------|-------------|
| `NO_VINTED_TAB` | No Vinted tab found |
| `CONTENT_SCRIPT_TIMEOUT` | Content script did not respond |
| `INVALID_PAYLOAD` | Missing required fields |
| `API_ERROR` | Vinted API returned error |
| `UNAUTHORIZED` | Not authenticated on Vinted |

---

## Debugging

### Browser DevTools

| Context | How to access |
|---------|---------------|
| Popup | Right-click popup > Inspect |
| Background | `about:debugging` (Firefox) / `chrome://extensions` > Inspect service worker |
| Content Script | Page DevTools console (look for `[Vinted]` prefix) |
| Injected Scripts | Page DevTools console (look for `[StoflowAPI]` prefix) |

### Log Prefixes
```
[Background]     - Service worker logs
[VintedHandler]  - Action handler logs
[Vinted]         - Content script logs
[StoflowAPI]     - Injected API logs
```

### Common Issues

| Symptom | Cause | Solution |
|---------|-------|----------|
| "No Vinted tab" | Tab not open | Open vinted.fr in a tab |
| "Content script timeout" | Injection failed | Reload Vinted tab |
| "Unauthorized origin" | Frontend not whitelisted | Check ALLOWED_ORIGINS |
| API returns HTML | Session expired | Re-login to Vinted |

---

## Development

### Scripts
```bash
npm run dev          # Dev server with HMR
npm run build        # Production build
npm run build:check  # Type check + build
npm test             # Run Vitest tests
```

### Tech Stack
| Layer | Technology |
|-------|------------|
| Framework | Vue 3 + Composition API |
| Language | TypeScript |
| Build | Vite + @crxjs/vite-plugin |
| Testing | Vitest |
| Styling | Scoped CSS |

### Key Files for Contributions
| File | Purpose |
|------|---------|
| `background/VintedActionHandler.ts` | Add new Vinted actions |
| `content/vinted.ts` | Modify content script behavior |
| `content/stoflow-vinted-api-core.js` | Modify Webpack hooking |
| `config/environment.ts` | Add configuration options |

---

## Documentation

- [CLAUDE.md](./CLAUDE.md) - Development guidelines and architecture details
- [Backend Plugin API](../backend/CLAUDE.md) - Backend integration docs

---

## Known Limitations

1. **Firefox**: No `externally_connectable` support - uses postMessage fallback
2. **Webpack hooking**: May break if Vinted updates their bundler
3. **DataDome**: Bot detection may require manual solving
4. **Rate limiting**: Handled by backend, no local fallback

---

## License

MIT
