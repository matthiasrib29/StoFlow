# Directory Structure

## Repository Layout

```
StoFlow/ (monorepo)
├── backend/              # FastAPI REST API
├── frontend/             # Nuxt.js web application
├── plugin/               # Browser extension
├── CLAUDE.md             # Project AI guidelines
├── README.md             # Project documentation
└── .gitignore
```

## Backend Structure

```
backend/
├── main.py                      # FastAPI application entry point
├── api/                         # FastAPI routes
│   ├── admin*.py                # Admin endpoints
│   ├── auth.py                  # Authentication & registration
│   ├── attributes.py            # Shared product attributes API
│   ├── products.py              # Product CRUD
│   ├── subscription.py          # Subscription management
│   ├── stripe_routes.py         # Stripe webhooks
│   ├── vinted/                  # Vinted API module
│   │   ├── __init__.py          # Main router
│   │   ├── connection.py        # Vinted account connection
│   │   ├── products.py          # Vinted product operations
│   │   ├── publishing.py        # Publishing logic
│   │   ├── orders.py            # Order synchronization
│   │   ├── messages.py          # Message handling
│   │   └── jobs.py              # Job management
│   ├── ebay/                    # eBay API module
│   ├── etsy/                    # Etsy API module
│   └── dependencies/            # FastAPI dependency injection
│
├── services/                    # Business logic layer
│   ├── product_service.py       # Product CRUD & rules (713 lines)
│   ├── pricing_service.py       # Pricing algorithms
│   ├── auth_service.py          # JWT & authentication (622 lines)
│   ├── validators.py            # Business validators (628 lines)
│   ├── vinted/                  # Vinted services
│   │   ├── vinted_adapter.py
│   │   ├── vinted_importer.py
│   │   ├── vinted_publisher.py
│   │   ├── vinted_job_service.py (636 lines)
│   │   └── jobs/                # Job handlers
│   ├── ebay/                    # eBay services
│   ├── etsy/                    # Etsy services
│   ├── marketplace/             # Unified marketplace framework
│   │   ├── marketplace_job_processor.py  # Unified processor (784 lines)
│   │   ├── marketplace_job_service.py
│   │   └── batch_job_service.py
│   └── ai/                      # AI/ML services
│       ├── openai_service.py
│       └── gemini_service.py
│
├── models/                      # SQLAlchemy ORM models
│   ├── public/                  # Shared models (all users)
│   │   ├── user.py
│   │   ├── subscription_quota.py
│   │   ├── ai_credit.py
│   │   └── marketplace_action_type.py
│   └── user/                    # Tenant-specific models
│       ├── product.py           # Core product model
│       ├── vinted_product.py
│       ├── ebay_credentials.py
│       ├── marketplace_job.py   # Unified job model
│       └── publication_history.py
│
├── repositories/                # Data access layer
│   ├── product_repository.py
│   ├── user_repository.py
│   └── [other repositories]
│
├── schemas/                     # Pydantic request/response models
│   ├── auth_schemas.py
│   ├── product_schemas.py
│   ├── vinted_schemas.py
│   ├── ebay_schemas.py
│   └── pricing.py
│
├── middleware/                  # HTTP middleware
│   ├── error_handler.py
│   ├── rate_limit.py
│   └── security_headers.py
│
├── shared/                      # Shared utilities & config
│   ├── config.py                # Settings (Pydantic)
│   ├── database.py              # SQLAlchemy setup
│   ├── exceptions.py            # Custom exceptions
│   ├── security_utils.py        # Password, encryption
│   ├── logging_setup.py
│   └── [other utils]
│
├── migrations/                  # Alembic migrations
│   ├── env.py
│   ├── alembic.ini
│   └── versions/                # 86 migration files
│
├── tests/                       # Pytest test suite
│   ├── conftest.py              # Global fixtures
│   ├── unit/                    # Unit tests
│   │   ├── services/
│   │   ├── repositories/
│   │   └── schemas/
│   └── integration/             # API endpoint tests
│       ├── api/
│       ├── database/
│       └── security/
│
├── requirements.txt             # Python dependencies
├── docker-compose.yml           # PostgreSQL + Redis for dev
├── Dockerfile                   # Production image
└── CLAUDE.md                    # Backend-specific AI guidelines
```

## Frontend Structure

```
frontend/
├── app.vue                      # Root component
├── nuxt.config.ts               # Nuxt configuration
├── tailwind.config.js           # Tailwind customization
├── tsconfig.json                # TypeScript config
│
├── components/                  # Vue components (auto-imported)
│   ├── layout/
│   │   ├── DashboardSidebar.vue
│   │   ├── DashboardHeader.vue
│   │   └── DashboardFooter.vue
│   ├── ui/                      # Generic UI
│   │   ├── form/
│   │   ├── Modal.vue
│   │   └── Card.vue
│   ├── products/                # Product components
│   │   ├── ProductList.vue
│   │   ├── ProductCard.vue
│   │   └── forms/
│   ├── vinted/                  # Vinted-specific
│   ├── ebay/                    # eBay-specific
│   ├── etsy/                    # Etsy-specific
│   └── admin/                   # Admin components
│
├── composables/                 # Vue 3 composables (30+)
│   ├── useApi.ts                # API client with JWT
│   ├── useAuth.ts               # Authentication state
│   ├── useWebSocket.ts          # WebSocket management
│   ├── useVintedBridge.ts       # Vinted WebSocket bridge (671 lines)
│   ├── useProducts.ts
│   ├── useAttributes.ts
│   ├── useVinted*.ts            # Vinted operations
│   ├── useEbay*.ts              # eBay operations
│   ├── useEtsy*.ts              # Etsy operations
│   └── useAdmin*.ts             # Admin operations
│
├── pages/                       # Nuxt routes (auto-generated)
│   ├── index.vue                # Landing page
│   ├── auth/                    # Auth pages
│   │   ├── login.vue
│   │   └── register.vue
│   └── dashboard/               # Dashboard pages
│       ├── index.vue
│       ├── products/
│       │   ├── index.vue        # Product list
│       │   ├── [id].vue         # Product detail
│       │   └── create.vue       # Create product (637 lines)
│       ├── platforms/
│       │   ├── vinted.vue
│       │   ├── ebay.vue
│       │   └── etsy.vue
│       ├── settings/
│       └── admin/
│
├── stores/                      # Pinia stores (8 stores)
│   ├── auth.ts
│   ├── products.ts
│   ├── vinted.ts
│   ├── ebay.ts
│   └── etsy.ts
│
├── types/                       # TypeScript definitions
│   ├── api.ts
│   ├── models.ts
│   ├── vinted.ts
│   └── marketplace.ts
│
├── middleware/                  # Nuxt middleware
│   ├── auth.ts                  # Auth guard
│   └── admin.ts                 # Admin-only
│
├── layouts/                     # Nuxt layouts
│   ├── default.vue
│   └── dashboard.vue
│
├── assets/                      # Static assets
│   ├── css/
│   │   ├── tailwind.css
│   │   └── dashboard.css
│   └── images/
│
├── plugins/                     # Nuxt plugins
│   ├── primevue.ts
│   └── chartjs.ts
│
├── utils/                       # Utility functions
│   ├── logger.ts
│   ├── formatters.ts
│   └── validators.ts
│
├── public/                      # Public static files
│   ├── favicon.ico
│   └── images/
│
├── tests/                       # Vitest tests
│   ├── unit/
│   │   ├── composables/
│   │   ├── components/
│   │   └── utils/
│   └── security/
│
├── package.json
└── CLAUDE.md                    # Frontend-specific guidelines
```

## Plugin Structure

```
plugin/
├── manifest.json                # Chrome Manifest V3
├── manifest.firefox.json        # Firefox manifest
│
├── src/
│   ├── background/              # Service Worker (MV3)
│   │   ├── index.ts             # Main entry point
│   │   └── VintedActionHandler.ts
│   │
│   ├── content/                 # Content scripts
│   │   ├── vinted.ts            # Vinted page interceptor
│   │   ├── stoflow-web.ts       # StoFlow integration
│   │   ├── stoflow-vinted-bootstrap.js
│   │   └── stoflow-vinted-api-core.js
│   │
│   ├── popup/                   # Extension popup UI
│   │   ├── index.html
│   │   ├── Popup.vue
│   │   └── LoginForm.vue
│   │
│   ├── api/                     # Backend API client
│   │   └── StoflowAPI.ts
│   │
│   ├── components/              # Vue components
│   ├── composables/             # Vue composables
│   ├── types/                   # TypeScript types
│   └── utils/                   # Utilities
│
├── public/                      # Static resources
│   └── icons/
│
├── dist/                        # Build output (generated)
├── package.json
├── vite.config.ts               # Vite + CRXJS config
└── CLAUDE.md                    # Plugin-specific guidelines
```

## Key Organization Patterns

### Backend (Python)

**Organization by layer**:
- `api/` - HTTP routes (thin, delegate to services)
- `services/` - Business logic (thick)
- `repositories/` - Data access
- `models/` - SQLAlchemy entities
- `schemas/` - Pydantic validation

**Organization by feature** (within services):
- `services/vinted/` - All Vinted logic
- `services/ebay/` - All eBay logic
- `services/marketplace/` - Unified framework

### Frontend (TypeScript)

**Organization by type**:
- `components/` - Vue components (organized by feature)
- `composables/` - Reusable logic
- `pages/` - Routes (file-based)
- `stores/` - Global state (Pinia)

**Auto-import naming**:
- File: `components/vinted/StatsCards.vue`
- Usage: `<VintedStatsCards>`
- Pattern: `FolderName + FileName`

### Shared Code

**Cross-module patterns**:
- Each module has its own `CLAUDE.md` with guidelines
- Shared types defined in backend (source of truth)
- Frontend imports TypeScript types generated from Pydantic

## File Naming Conventions

### Backend
- Models: `snake_case.py` (e.g., `vinted_product.py`)
- Services: `snake_case_service.py` (e.g., `product_service.py`)
- Tests: `test_*.py` (e.g., `test_product_service.py`)

### Frontend
- Components: `PascalCase.vue` (e.g., `ProductCard.vue`)
- Composables: `camelCase.ts` with `use` prefix (e.g., `useProducts.ts`)
- Pages: `kebab-case.vue` or `[dynamic].vue`

### Plugin
- Similar to frontend (Vue + TypeScript)
- Content scripts: `kebab-case.ts` (e.g., `vinted.ts`)

## Module Boundaries

### Backend → Frontend
- REST API (JSON)
- WebSocket (Socket.IO)
- JWT authentication

### Backend → Plugin
- WebSocket commands (via frontend relay)
- No direct communication

### Frontend → Plugin
- `chrome.runtime.sendMessage`
- `postMessage` (Firefox fallback)

## Large Files (>500 lines)

Files exceeding recommended size limits:

| File | Lines | Module |
|------|-------|--------|
| `product_service.py` | 713 | Backend |
| `marketplace_job_service.py` | 784 | Backend |
| `vinted_job_service.py` | 636 | Backend |
| `auth_service.py` | 622 | Backend |
| `validators.py` | 628 | Backend |
| `useVintedBridge.ts` | 671 | Frontend |
| `create.vue` | 637 | Frontend |
| `PhotoUploader.vue` | 515 | Frontend |

**Recommendation**: Consider refactoring files >500 lines into smaller modules.

---
*Last updated: 2026-01-09 after codebase mapping*
