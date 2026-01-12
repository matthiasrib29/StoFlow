# Technology Stack

## Languages

### Backend
- **Python 3.11+** - Primary backend language
  - Modern async/await support
  - Type hints (PEP 484)
  - Pattern matching (3.10+)

### Frontend
- **TypeScript 5.9.3** - Primary frontend language
  - Strict mode enabled
  - Vue 3 Composition API
  - Type-safe props/emits

### Browser Extension
- **TypeScript 5.3.0** - Extension development
  - Chrome Manifest V3
  - Firefox compatibility

## Frameworks

### Backend (Python)
- **FastAPI 0.115.0** - Modern async web framework
  - Auto-generated OpenAPI docs
  - Dependency injection
  - WebSocket support via Socket.IO
- **SQLAlchemy 2.0.35** - ORM with async support
- **Alembic 1.14.0** - Database migrations
- **Pydantic 2.10.1** - Data validation

### Frontend (JavaScript/TypeScript)
- **Nuxt.js 4.2.1** - Vue meta-framework
  - SSR/SSG capable
  - File-based routing
  - Auto-imports
- **Vue.js 3.5.25** - Reactive UI framework
  - Composition API (`<script setup>`)
  - TypeScript-first
- **PrimeVue 4.5.1** - Enterprise UI components
- **Pinia 0.11.3** - State management

### Browser Extension
- **Vue.js 3.4.0** - Popup UI
- **Vite 5.0.0** - Build tool
- **CRXJS 2.0.0** - Extension build plugin

## Key Dependencies

### Backend
| Library | Version | Purpose |
|---------|---------|---------|
| uvicorn | 0.32.0 | ASGI server |
| python-jose | 3.3.0 | JWT authentication (RS256) |
| passlib | 1.7.4 | Password hashing (bcrypt) |
| python-socketio | 5.11.0 | WebSocket server |
| httpx | 0.27.2 | Async HTTP client |
| boto3 | 1.35.0 | Cloudflare R2 (S3-compatible) |
| stripe | 11.3.0 | Payment processing |
| APScheduler | 3.10.4 | Task scheduling (Etsy polling) |
| pytest | 8.3.2 | Testing framework |

### Frontend
| Library | Version | Purpose |
|---------|---------|---------|
| @nuxt/ui | 4.2.1 | UI component system |
| tailwindcss | 6.14.0 | Utility-first CSS |
| @vueuse/core | 14.1.0 | Composition utilities |
| chart.js | 4.5.1 | Data visualization |
| vue-chartjs | 5.3.3 | Vue Chart.js wrapper |
| socket.io-client | 4.8.3 | WebSocket client |
| vitest | 4.0.16 | Unit/component testing |
| dompurify | 3.0.6 | XSS sanitization |

## Build Tools

### Backend
- **pip** - Package manager
- **Docker Compose** - Local PostgreSQL + Redis
- **Alembic** - Schema migrations

### Frontend
- **npm** - Package manager
- **Nuxt CLI** - Development server
- **Vite** - Underlying bundler (via Nuxt)

### Browser Extension
- **npm** - Package manager
- **Vite** - Build tool with HMR
- **CRXJS** - Extension-specific bundling

## Databases

### Primary Database
- **PostgreSQL 15** (Docker)
  - Multi-tenant via schemas (`public`, `product_attributes`, `user_X`)
  - Connection pooling via SQLAlchemy
  - Port: 5433 (dev), 5434 (test)

### Development Tools
- **pgAdmin 4** (optional, port 5050)
- Docker volumes for persistence

## External Services

### Cloud Infrastructure
- **Cloudflare R2** - Object storage (S3-compatible)
  - Product images
  - CDN distribution

### AI/ML Services
- **OpenAI GPT-4 Turbo** - Description generation
- **Google Gemini Flash** - Image analysis

### Payment Processing
- **Stripe** - Subscriptions & AI credit packs

### Email
- **Brevo** (formerly Sendinblue) - Transactional emails

### Marketplace APIs
- **Vinted API** - Via browser extension plugin
- **eBay Commerce APIs** - Direct OAuth2
- **Etsy API v3** - Direct OAuth2

## Development Tools

### Linting & Formatting
- **Black** - Python formatter (88 char line length)
- **isort** - Python import sorting
- **ESLint 9.39.2** - JavaScript/TypeScript linting (flat config)
- **Prettier** - Frontend formatting (2 spaces, no semi)

### Testing
- **pytest** - Backend testing
  - pytest-asyncio for async tests
  - pytest-cov for coverage
- **Vitest** - Frontend testing
  - @vue/test-utils for component tests
  - happy-dom for DOM simulation

### Version Control
- **Git** - Version control
- **GitHub** - Repository hosting
- **Git worktrees** - Multi-environment development (dev 1-4)

## Runtime Environments

### Development
| Component | Port | Environment |
|-----------|------|-------------|
| Backend | 8000-8003 | Uvicorn dev server |
| Frontend | 3000-3003 | Nuxt dev server |
| Plugin | 5173 | Vite HMR server |
| PostgreSQL | 5433 | Docker container |
| Test DB | 5434 | Docker container |

### Production
| Component | Platform | URL |
|-----------|----------|-----|
| Backend | Railway | api.stoflow.com |
| Frontend | Vercel | stoflow.io |
| Database | Railway PostgreSQL | (managed) |
| Storage | Cloudflare R2 | CDN URLs |
| Extension | Chrome Web Store | (extension ID) |

## Package Managers

- **Backend**: pip with requirements.txt
- **Frontend**: npm with package-lock.json
- **Plugin**: npm with package-lock.json

## Architecture Summary

```
┌─────────────────────────────────────────────────────┐
│ Frontend (Nuxt.js 4 + Vue 3 + TypeScript)          │
│ - Tailwind CSS + PrimeVue                          │
│ - Pinia state management                           │
│ - Socket.IO client                                 │
└────────────┬────────────────────────────────────────┘
             │ HTTP/WebSocket
┌────────────┴────────────────────────────────────────┐
│ Backend (FastAPI + SQLAlchemy + Python 3.11)       │
│ - Multi-tenant PostgreSQL schemas                  │
│ - JWT RS256 authentication                         │
│ - Unified marketplace job processor                │
└────────────┬────────────────────────────────────────┘
             │ WebSocket relay
┌────────────┴────────────────────────────────────────┐
│ Plugin (Vue 3 + Vite + Manifest V3)                │
│ - Browser extension (Chrome/Firefox)               │
│ - Vinted API interception                          │
│ - Content script injection                         │
└─────────────────────────────────────────────────────┘
```

---
*Last updated: 2026-01-09 after codebase mapping*
