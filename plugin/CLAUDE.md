# CLAUDE.md - StoFlow Browser Extension

This file provides guidance to Claude Code when working with the browser extension.

## Project Overview

Browser extension (Firefox/Chrome) that acts as a proxy between the StoFlow backend and Vinted API.
Handles authentication, API requests, and synchronization tasks.

## Commands

### Development
```bash
npm install          # Install dependencies
npm run dev          # Start dev build with watch mode
npm run build        # Production build to dist/
npm run test         # Run tests with Vitest
```

### Loading in Browser
- **Firefox**: about:debugging -> Load Temporary Add-on -> select `dist/manifest.json`
- **Chrome**: chrome://extensions -> Load unpacked -> select `dist/` folder

## Architecture

### Key Directories
```
plugin/
├── src/
│   ├── background/      # Service worker (background.ts)
│   ├── popup/           # Extension popup UI
│   ├── services/        # API clients and business logic
│   │   ├── api/         # Backend API client
│   │   └── vinted/      # Vinted API client
│   ├── types/           # TypeScript interfaces
│   └── utils/           # Shared utilities
├── public/              # Static assets
├── dist/                # Build output
└── manifest.json        # Extension manifest
```

### Communication Flow
```
Backend API <-> Plugin Background <-> Vinted API
                    ^
                    |
              Popup UI
```

### Key Components
- **Background Service Worker**: Handles all API requests and task processing
- **Vinted Service**: Manages Vinted authentication and API calls
- **API Bridge**: Receives tasks from backend, executes on Vinted
- **Popup**: Simple status UI for connection/auth state

## Development Rules

### Main Rule
**NEVER test Vinted API directly with curl or raw requests.**

All Vinted interactions must go through the extension's VintedService.

### Code Style
- TypeScript strict mode
- No `any` types (use proper interfaces)
- Async/await for all async operations
- Error handling with try/catch

### Security
- Never log tokens or credentials
- Store auth tokens in browser.storage.local
- Validate all data from external sources
- Use HTTPS for all API calls

### Testing
- Unit tests with Vitest
- Test services in isolation with mocks
- No real API calls in tests

## Environment Variables

Development (`.env.development`):
```
VITE_API_URL=http://localhost:8000
```

Production (`.env.production`):
```
VITE_API_URL=https://api.stoflow.com
```

## Manifest Versions
- `manifest.json` - Chrome Manifest V3
- `manifest.firefox.json` - Firefox specific manifest

## Important Files
- `src/background/background.ts` - Main service worker
- `src/services/vinted/` - Vinted integration
- `src/services/api/` - Backend communication

---

*Last updated: 2024-12-18*
