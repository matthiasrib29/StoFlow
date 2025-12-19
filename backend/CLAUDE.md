# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Règle Principale

**TOUJOURS POSER DES QUESTIONS avant d'implémenter de la logique métier.**

En cas de doute → STOP → DEMANDER à l'utilisateur.

### Obligatoire de demander pour :
- Calculs métier : prix, commissions, arrondis, frais
- Règles de validation : limites, contraintes, formats
- Gestion d'erreurs : comportement en cas d'échec, retry, fallback
- Intégrations externes : Vinted, eBay, Etsy (format données, mapping)
- Limites business : quotas, rate limiting, abonnements
- Workflows : états, transitions, conditions

### Pas besoin de demander pour :
- CRUD standard
- Code technique pur (utils, logging)
- Patterns établis (Repository, Service)

## Commands

### Development Server
```bash
# Start FastAPI server (auto-reload)
uvicorn main:app --reload

# Start with debug logs
uvicorn main:app --reload --log-level debug
```

### Database & Migrations
```bash
# Start PostgreSQL and Redis (Docker)
docker-compose up -d

# With pgAdmin (optional)
docker-compose --profile tools up -d

# Apply migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"

# Rollback one migration
alembic downgrade -1
```

### Testing
```bash
# Start test database (Docker)
docker-compose -f docker-compose.test.yml up -d

# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/unit/services/test_auth_service.py -v

# Run single test
pytest tests/unit/services/test_auth_service.py::test_function_name -v
```

### Code Quality
```bash
# Format code
black .

# Sort imports
isort .

# Lint
flake8

# Type check
mypy .
```

## Architecture

### Multi-Tenant (PostgreSQL Schemas)
Each user has an isolated PostgreSQL schema (`user_{user_id}`) for their data:
- `public` schema: shared tables (users, subscription_quotas, categories, brands, colors, etc.)
- `product_attributes` schema: shared product attributes
- `user_X` schema: user-specific data (products, product_images, plugin_tasks, etc.)
- `template_tenant` schema: template for cloning new user schemas

Schema isolation via `SET search_path TO user_{user_id}, public` in `shared/database.py:set_user_schema()`.

### Key Directories
- `api/` - FastAPI routers (auth, products, vinted, ebay, etsy, plugin)
- `services/` - Business logic (auth_service, product_service, validators)
- `services/vinted/` - Vinted integration (adapter, mapper, importer, publisher)
- `services/ebay/` - eBay integration (inventory, offers, taxonomy clients)
- `services/etsy/` - Etsy integration (listings, polling, shop clients)
- `models/public/` - SQLAlchemy models for shared tables
- `models/user/` - SQLAlchemy models for user-specific tables
- `schemas/` - Pydantic schemas for request/response validation
- `middleware/` - Rate limiting, security headers
- `shared/` - Config, database session, utilities

### Marketplace Integrations
The plugin (Firefox extension) acts as a proxy for Vinted API:
```
Backend → API Bridge → Plugin → Vinted API
```

eBay and Etsy use direct OAuth2 API integration.

### Vinted Job System

The Vinted integration uses a two-level task orchestration system:

```
┌─────────────────────────────────────────────────────────────────┐
│                         VintedJob                                │
│  (Business operation: publish, update, delete, sync, message)   │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  PluginTask  │  │  PluginTask  │  │  PluginTask  │   ...    │
│  │  (HTTP #1)   │  │  (HTTP #2)   │  │  (HTTP #3)   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

#### VintedJob (High-level - Business)
- **Definition**: A complete business operation on Vinted
- **Examples**: Publish a product, sync orders, fetch messages
- **Table**: `user_X.vinted_jobs`
- **Status**: pending → running → completed/failed/cancelled/expired
- **Contains**: Multiple PluginTasks (HTTP requests)
- **Handlers**: One handler per action type in `services/vinted/jobs/`

| Action Code | Handler | Description |
|-------------|---------|-------------|
| `publish` | `PublishJobHandler` | Create new listing |
| `update` | `UpdateJobHandler` | Modify existing listing |
| `delete` | `DeleteJobHandler` | Remove listing |
| `sync` | `SyncJobHandler` | Sync products from Vinted |
| `orders` | `OrdersJobHandler` | Fetch orders/sales |
| `message` | `MessageJobHandler` | Sync conversations/messages |

#### PluginTask (Low-level - Technical)
- **Definition**: A single HTTP request sent via the browser plugin
- **Examples**: GET /api/v2/items, POST /api/v2/items, PUT /api/v2/items/{id}
- **Table**: `user_X.plugin_tasks`
- **Status**: pending → processing → completed/failed/timeout
- **Linked to**: Parent VintedJob via `job_id` FK

#### Flow Example: Publishing a Product
```
1. API receives POST /vinted/publishing/{product_id}
2. VintedJobService.create_job(action_code="publish") → VintedJob created
3. VintedJobProcessor._execute_job() dispatches to PublishJobHandler
4. PublishJobHandler.execute():
   a. Validates product
   b. Maps attributes
   c. PluginTask #1: Upload images (POST /api/v2/photos)
   d. PluginTask #2: Create listing (POST /api/v2/items)
5. VintedJob marked as completed
```

#### Key Files
- `models/user/vinted_job.py` - VintedJob model
- `models/user/plugin_task.py` - PluginTask model
- `services/vinted/vinted_job_service.py` - Job CRUD operations
- `services/vinted/vinted_job_processor.py` - Job orchestrator
- `services/vinted/jobs/` - Handler implementations (one per action)

### Product Status Flow
```
DRAFT → PUBLISHED → SOLD → ARCHIVED
              ↘ ARCHIVED
```
- Cannot publish with `stock_quantity = 0`
- `deleted_at IS NOT NULL` = soft deleted

## Code Style

- **Python**: PEP 8, type hints obligatoires
- **Docstrings**: Format Google pour fonctions publiques
- **Naming**: snake_case pour fonctions/variables, PascalCase pour classes
- **Imports**: Groupés (stdlib, third-party, local) avec ligne vide entre

## Database Standards

- Migrations Alembic obligatoires pour tout changement de schema
- Foreign keys avec `ondelete` défini
- Timestamps (`created_at`, `updated_at`) sur toutes les tables
- Soft delete via `deleted_at` column

## Testing Standards

- Tests use PostgreSQL via Docker (`docker-compose.test.yml`)
- Test database URL: `postgresql://stoflow_test:test_password_123@localhost:5434/stoflow_test`
- Fixtures in `tests/conftest.py`: `db_session`, `client`, `test_user`, `auth_headers`
- User schemas (user_1, user_2, user_3) cloned from `template_tenant`
