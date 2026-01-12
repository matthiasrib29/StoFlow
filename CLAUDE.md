# CLAUDE.md - StoFlow Monorepo

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> **Note**: General rules (language, security, git, debugging) are defined in `~/.claude/CLAUDE.md` (global config).
> This file contains **StoFlow-specific** rules and architecture details.

---

## 🛡️ Git Worktree Safety Rules (CRITIQUE - 2026-01-12)

> **Contexte** : Ces règles ont été ajoutées après une perte de ~8000 lignes de code
> causée par un `git reset --hard origin/develop` accidentel lors de sessions parallèles.

### Règle Principale

**`~/StoFlow` (repo principal) est READ-ONLY pour le développement.**

Tout le travail doit se faire dans des **worktrees** (`~/StoFlow-*`).

### Commandes Interdites sur develop

| Commande | Danger | Alternative |
|----------|--------|-------------|
| `git reset --hard` | Perte de commits locaux | `git pull --no-rebase` |
| `git checkout -- .` | Perte de modifications | Commit d'abord |
| `git clean -fd` | Suppression fichiers | Vérifier avant |

### Workflow Obligatoire

```
1. Créer worktree    : /1-new-feature ou /2-new-feature
2. Travailler dans   : ~/StoFlow-[nom]/
3. Terminer avec     : /finish (depuis le worktree)
4. NE JAMAIS         : Committer directement sur develop dans ~/StoFlow
```

### Vérifications Automatiques (skills /finish et /sync)

Avant toute opération sur `~/StoFlow`, les skills vérifient :
1. ✅ Pas de changements non commités
2. ✅ Pas de commits locaux non poussés
3. ✅ Confirmation utilisateur si problème détecté

### En cas de doute

```
⛔ ARRÊTER et DEMANDER à l'utilisateur
```

---

## Project Overview

**StoFlow** is an e-commerce management application for multi-channel selling:
- **Backend**: FastAPI REST API with PostgreSQL multi-tenant architecture
- **Frontend**: Nuxt.js web application (Vue 3 + Composition API)
- **Plugin**: Browser extension (Firefox/Chrome) for marketplace integrations

---

## Repository Structure

```
StoFlow/
├── backend/         # FastAPI API server
├── frontend/        # Nuxt.js web application
├── plugin/          # Browser extension (Vinted integration)
├── CLAUDE.md        # This file (project guidelines)
├── README.md        # Project documentation
└── .gitignore       # Git ignore rules
```

---

## Module-Specific Guidelines

Each module has its own CLAUDE.md with detailed instructions:
- [backend/CLAUDE.md](backend/CLAUDE.md) - Backend API development
- [frontend/CLAUDE.md](frontend/CLAUDE.md) - Frontend development
- [plugin/CLAUDE.md](plugin/CLAUDE.md) - Browser extension development

---

## Quick Start Commands

### Backend (FastAPI)
```bash
cd backend
source .venv/bin/activate        # Activate virtual env
docker-compose up -d             # Start PostgreSQL + Redis
alembic upgrade head             # Apply migrations
uvicorn main:app --reload        # Start dev server (port 8000)
```

### Frontend (Nuxt.js)
```bash
cd frontend
npm install                      # Install dependencies
npm run dev                      # Start dev server (port 3000)
```

### Plugin (Browser Extension)
```bash
cd plugin
npm install                      # Install dependencies
npm run dev                      # Start dev build with watch
npm run build                    # Production build
```

---

## 💻 Stack Technique

### Backend (Python)
- **Framework**: FastAPI
- **ORM**: SQLAlchemy
- **Database**: PostgreSQL
- **Migrations**: Alembic
- **Tests**: Pytest (unit + integration)
- **Architecture**: Clean Architecture (Services, Repositories, Entities)

### Frontend (JavaScript/TypeScript)
- **Framework**: Vue.js / Nuxt.js
- **Style**: Composition API (`setup()`, `ref()`, `computed()`)
- **CSS**: Tailwind CSS
- **Package manager**: npm
- **Structure**: By type (`components/`, `services/`, `stores/`)

### Plugin (Browser Extension)
- **Framework**: Vue.js (Composition API)
- **Build**: Vite
- **Target**: Firefox & Chrome (Manifest V3)

---

## 📝 Standards de Code Python

### Naming Conventions
```python
# Variables et fonctions : snake_case
user_name = "John"
def get_user_by_id(user_id: int): ...

# Classes : PascalCase
class UserService: ...
class ProductRepository: ...

# Constantes : UPPER_SNAKE_CASE
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30
```

### Type Hints
- **Flexible**: Use when it helps understanding
- Required on public service functions
- Optional on simple internal functions

### Docstrings (Google Style)
```python
def create_user(name: str, email: str) -> User:
    """
    Creates a new user in the database.

    Args:
        name: The user's full name.
        email: The user's email address.

    Returns:
        The newly created User object.

    Raises:
        ValidationError: If email format is invalid.
        DuplicateError: If email already exists.
    """
```

### Function Length
- **Flexible** depending on context
- Split if function becomes hard to understand
- Favor readability over artificial brevity

---

## 🧪 Tests

### Backend (Pytest)
- **Unit tests**: For services and isolated functions
- **Integration tests**: For API endpoints
- Use PostgreSQL Docker container for tests

### Frontend (Vitest)
- Unit tests for components and composables
- E2E tests with Playwright (optional)

### Conventions
```python
# Files: test_*.py
# Functions: test_*
# Classes: Test*

def test_create_user_with_valid_data():
    ...

def test_create_user_raises_error_on_duplicate_email():
    ...
```

---

## 🛠️ Gestion des Erreurs (StoFlow)

### Exception Hierarchy
```python
# Use custom exceptions inheriting from StoflowError
class ServiceError(StoflowError): ...
class ValidationError(StoflowError): ...
class MarketplaceError(StoflowError): ...
class VintedError(MarketplaceError): ...
class EbayError(MarketplaceError): ...
```

### Logging
- Use `logger` (never `print()`)
- Levels: DEBUG for dev, INFO for prod, ERROR for exceptions
- Include context (user_id, product_id, etc.)

---

## 🗄️ Base de Données (PostgreSQL)

### Multi-Tenant Architecture (Schemas)
- `public` schema: shared data (users, categories, brands, colors, etc.)
- `user_X` schema: user-specific data (products, orders, listings)
- Isolation via `SET search_path` per request

### Migrations (Alembic)
- Claude can create migration files
- Claude can help execute them
- Always verify content before `upgrade`

### Conventions
- Tables in plural: `users`, `products`, `orders`
- Foreign keys with `ondelete` defined
- Timestamps on all tables (`created_at`, `updated_at`)
- Indexes on frequently queried columns

---

## 🏗️ Architecture Backend (Clean Architecture)

```
backend/
├── api/              # FastAPI routes
├── services/         # Business logic
├── repositories/     # Data access
├── models/           # SQLAlchemy entities
├── schemas/          # Pydantic schemas
├── shared/           # Utils, config, exceptions
└── tests/
    ├── unit/
    └── integration/
```

### Principles
- **Services**: Business logic
- **Repositories**: Database access
- **Schemas**: Input/output validation
- **Models**: SQLAlchemy entities

---

## 🎨 Frontend (Vue.js/Nuxt)

### Structure
```
frontend/
├── components/       # Reusable components
├── pages/           # Pages/routes
├── stores/          # Pinia stores
├── services/        # API calls
├── composables/     # Composition functions
└── assets/          # CSS, images
```

### Style
- Composition API with `<script setup>`
- Tailwind CSS for styling
- Pinia for state management

---

## 🏛️ Architecture Overview

### Multi-Tenant (PostgreSQL Schemas)
- `public` schema: shared data (users, categories, brands)
- `user_X` schema: user-specific data (products, orders)
- Isolation via `SET search_path` per request

### Marketplace Integration Flow
```
User -> Frontend -> Backend API -> Plugin -> Marketplace (Vinted)
                              -> Direct API (eBay, Etsy)
```

### Product Status Flow
```
DRAFT -> PUBLISHED -> SOLD -> ARCHIVED
             |
             v
         ARCHIVED
```

---

## 🔌 Intégrations Marketplaces (Vinted, eBay, Etsy)

### RÈGLE CRITIQUE

> **JAMAIS tester les APIs externes avec curl ou requêtes directes.**

### Comportement Attendu
1. **Toujours** passer par les fonctions du code (services, clients)
2. **Jamais** de `curl` vers les APIs Vinted/eBay/Etsy
3. Laisser l'utilisateur faire les tests d'intégration manuels
4. En cas de doute sur un endpoint → **DEMANDER**

### Structure des Clients
```python
# Use existing clients
from services.vinted import VintedAdapter
from services.ebay import EbayBaseClient
from services.etsy import EtsyBaseClient
```

### Vinted Integration
- Done via **Browser Extension Plugin** (not direct API)
- Plugin intercepts Vinted API calls in browser
- Backend communicates with plugin via WebSocket/HTTP

### eBay Integration
- Direct API access via OAuth 2.0
- Use `EbayBaseClient` for all API calls

### Etsy Integration
- Direct API access via OAuth 2.0
- Use `EtsyBaseClient` for all API calls

---

## 📋 Development Mode

**Assume POC/prototype mode** unless explicitly stated otherwise:
- Max 3 files per commit when possible
- Prioritize working functionality over perfect code
- Refactor later when requirements are stable

---

*Last updated: 2026-01-12*
