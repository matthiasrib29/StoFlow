# Code Structure

## Directory Layout

```
backend/
├── main.py                         # FastAPI app + WebSocket setup
├── requirements.txt                # Python dependencies (pinned)
├── .env.example                    # Environment template
├── alembic.ini                     # Alembic configuration
├── docker-compose.yml              # PostgreSQL + Redis
├── docker-compose.test.yml         # Test database
│
├── api/                            # FastAPI routes (10+ routers)
│   ├── auth.py                     # Authentication endpoints
│   ├── products/                   # Product management
│   │   ├── crud.py                 # Create, Read, Update, Delete
│   │   ├── ai.py                   # AI generation endpoints
│   │   └── images.py               # Image upload/delete/reorder
│   ├── vinted/                     # Vinted-specific routes
│   │   ├── products.py
│   │   ├── connection.py
│   │   ├── publishing.py
│   │   ├── jobs.py
│   │   ├── orders.py
│   │   ├── messages.py
│   │   └── shared.py
│   ├── ebay/                       # eBay-specific routes
│   │   ├── products.py
│   │   ├── jobs.py
│   │   ├── orders.py
│   │   ├── dashboard.py
│   │   ├── returns.py
│   │   ├── refunds.py
│   │   ├── cancellations.py
│   │   ├── inquiries.py
│   │   ├── payment_disputes.py
│   │   └── main.py
│   ├── etsy/                       # Etsy (disabled 2026-01-09)
│   ├── batches.py                  # Batch job processing
│   ├── pricing.py                  # Pricing algorithm
│   ├── text_generator.py           # AI text generation
│   └── admin.py                    # Admin endpoints
│
├── services/                       # Business logic layer
│   ├── marketplace/                # Unified job system
│   │   ├── marketplace_job_processor.py    # Job orchestrator
│   │   ├── marketplace_job_service.py      # Job CRUD
│   │   └── batch_job_service.py            # Batch processing
│   ├── vinted/                     # Vinted business logic
│   │   ├── vinted_adapter.py               # High-level operations
│   │   ├── vinted_mapper.py                # Attribute mapping
│   │   ├── vinted_product_converter.py     # Product → Vinted payload
│   │   ├── vinted_importer.py              # Import from Vinted
│   │   ├── vinted_publisher.py             # Publishing orchestration
│   │   ├── vinted_description_service.py   # Description generation
│   │   ├── vinted_title_service.py         # Title generation
│   │   ├── vinted_pricing_service.py       # Price calculation
│   │   ├── vinted_link_service.py          # Product linking
│   │   ├── vinted_stats_service.py         # Seller statistics
│   │   ├── vinted_image_downloader.py      # Image handling
│   │   ├── vinted_image_sync_service.py    # Image synchronization
│   │   └── jobs/                           # Job handlers
│   │       ├── base_job_handler.py         # Base handler (WebSocket)
│   │       ├── publish_handler.py
│   │       ├── update_handler.py
│   │       ├── delete_handler.py
│   │       ├── sync_handler.py
│   │       ├── orders_handler.py
│   │       ├── message_handler.py
│   │       └── link_product_handler.py
│   ├── ebay/                       # eBay business logic
│   │   ├── ebay_adapter.py                 # High-level operations
│   │   ├── ebay_mapper.py                  # Attribute mapping
│   │   ├── ebay_product_conversion_service.py  # Product → eBay payload
│   │   ├── ebay_base_client.py             # OAuth 2.0 client
│   │   ├── ebay_inventory_client.py        # Inventory API
│   │   ├── ebay_offer_client.py            # Offer API
│   │   ├── ebay_taxonomy_client.py         # Taxonomy API
│   │   ├── ebay_marketing_client.py        # Marketing API
│   │   ├── ebay_analytics_client.py        # Analytics API
│   │   ├── ebay_account_client.py          # Account API
│   │   ├── ebay_publication_service.py     # Publishing orchestration
│   │   ├── ebay_aspect_value_service.py    # Aspect mapping
│   │   ├── ebay_gpsr_compliance.py         # GPSR compliance
│   │   └── jobs/                           # Job handlers
│   │       ├── publish_handler.py
│   │       ├── update_handler.py
│   │       ├── delete_handler.py
│   │       ├── sync_handler.py
│   │       └── sync_orders_handler.py
│   ├── etsy/                       # Etsy business logic
│   │   ├── etsy_adapter.py                 # High-level operations
│   │   ├── etsy_mapper.py                  # Attribute mapping
│   │   ├── etsy_product_conversion_service.py  # Product → Etsy payload
│   │   ├── etsy_base_client.py             # OAuth 2.0 client
│   │   ├── etsy_shop_client.py             # Shop API
│   │   ├── etsy_listing_client.py          # Listing API
│   │   ├── etsy_receipt_client.py          # Receipt (order) API
│   │   ├── etsy_polling_service.py         # Event polling
│   │   └── jobs/                           # Job handlers (partial)
│   ├── auth_service.py             # JWT authentication
│   ├── product_service.py          # Product CRUD + business logic
│   ├── product_image_service.py    # JSONB image operations
│   ├── file_service.py             # R2 upload/download/optimize
│   ├── r2_service.py               # Cloudflare R2 config
│   ├── websocket_service.py        # Socket.IO server
│   ├── plugin_websocket_helper.py  # Async HTTP via WebSocket
│   └── pricing/                    # Pricing algorithms
│
├── repositories/                   # Data access layer
│   ├── product_repository.py
│   ├── vinted_product_repository.py
│   ├── vinted_mapping_repository.py
│   ├── vinted_conversation_repository.py
│   ├── ebay_order_repository.py
│   ├── ebay_return_repository.py
│   ├── ebay_refund_repository.py
│   ├── ebay_cancellation_repository.py
│   ├── ebay_inquiry_repository.py
│   ├── ebay_payment_dispute_repository.py
│   └── user_repository.py
│
├── models/                         # SQLAlchemy entities
│   ├── public/                     # Shared entities (global)
│   │   ├── user.py                 # Users
│   │   ├── subscription_quota.py   # Subscription plans
│   │   ├── ai_credit_pack.py       # AI pricing
│   │   ├── marketplace_action_type.py  # Unified action types
│   │   ├── revoked_token.py        # JWT blacklist
│   │   └── product_attributes/     # Shared reference data
│   │       ├── brand.py
│   │       ├── category.py
│   │       ├── color.py
│   │       ├── condition.py
│   │       ├── material.py
│   │       ├── size_normalized.py
│   │       ├── size_original.py
│   │       └── ... (20+ attribute tables)
│   ├── user/                       # Tenant-specific entities
│   │   ├── product.py              # Core product model
│   │   ├── marketplace_job.py      # Unified job model
│   │   ├── batch_job.py            # Batch job orchestration
│   │   ├── vinted_connection.py    # Vinted account link
│   │   ├── vinted_product.py       # Vinted product mapping
│   │   ├── vinted_order.py         # Vinted orders
│   │   ├── vinted_conversation.py  # Vinted messages
│   │   ├── ebay_credentials.py     # eBay OAuth tokens
│   │   ├── ebay_product.py         # eBay product mapping
│   │   ├── ebay_order.py           # eBay orders
│   │   ├── ebay_return.py          # eBay returns
│   │   ├── ebay_refund.py          # eBay refunds
│   │   ├── ebay_cancellation.py    # eBay cancellations
│   │   ├── ebay_inquiry.py         # eBay buyer messages
│   │   ├── ebay_payment_dispute.py # eBay payment disputes
│   │   ├── ai_generation_log.py    # AI usage tracking
│   │   └── publication_history.py  # Audit log
│   └── vinted/                     # Deprecated (moved to user/)
│
├── schemas/                        # Pydantic validation schemas
│   ├── product.py                  # Product Create/Update/Response
│   ├── vinted.py                   # Vinted schemas
│   ├── ebay.py                     # eBay schemas
│   ├── etsy.py                     # Etsy schemas
│   ├── auth.py                     # Auth schemas (login, register)
│   ├── marketplace_job.py          # Job schemas
│   └── batch_job.py                # Batch job schemas
│
├── middleware/                     # FastAPI middleware
│   ├── cors.py                     # CORS configuration
│   ├── security_headers.py         # Security headers
│   └── rate_limiting.py            # Rate limiting
│
├── shared/                         # Utilities & config
│   ├── database.py                 # Multi-tenant session setup
│   ├── config.py                   # Pydantic Settings
│   ├── exceptions.py               # Custom exceptions
│   ├── logging_setup.py            # Structured logging
│   └── utils.py                    # Helper functions
│
├── migrations/                     # Alembic migrations
│   ├── versions/                   # Migration files (~120 files)
│   │   ├── 20260114_*.py           # Latest migrations
│   │   └── ...
│   ├── archive_20260105/           # Historical migrations
│   └── env.py                      # Alembic environment
│
├── tests/                          # Test suite
│   ├── conftest.py                 # Shared fixtures (session scope)
│   ├── unit/                       # Unit tests (mocked)
│   │   ├── conftest.py             # Unit-specific fixtures
│   │   ├── services/
│   │   │   ├── test_product_service.py
│   │   │   ├── test_auth_service.py
│   │   │   └── test_pricing_service.py
│   │   ├── schemas/
│   │   │   └── test_product_schemas.py
│   │   └── models/
│   │       └── test_product_models.py
│   └── integration/                # Integration tests (real DB)
│       ├── api/
│       │   ├── test_products.py    # API endpoint tests
│       │   ├── test_auth.py
│       │   └── test_batches.py
│       └── database/
│           ├── test_migrations.py
│           └── test_validators.py
│
├── docs/                           # Architecture documentation
│   ├── architecture.md             # System design
│   ├── migration_guides/           # Refactoring guides
│   └── job_unification.md          # Job system migration
│
├── scripts/                        # Data migration scripts
│   ├── migrate_from_pythonapiwoo.py    # Initial data import
│   ├── repair_lost_brands.py           # Brand data repair
│   ├── find_lost_brands.py             # Data integrity check
│   ├── compare_brands_detail.py        # Brand comparison
│   └── compare_databases.py            # DB diff analysis
│
└── logs/                           # Application logs (gitignored)
```

---

## Module Organization Principles

### By Domain (Not by Type)

**API Layer**: Organized by marketplace/domain
- `api/products/` - Product management
- `api/vinted/` - Vinted-specific endpoints
- `api/ebay/` - eBay-specific endpoints
- `api/etsy/` - Etsy endpoints (disabled)

**Service Layer**: Mirrors API organization
- `services/vinted/` - Vinted business logic
- `services/ebay/` - eBay business logic
- `services/etsy/` - Etsy business logic
- `services/marketplace/` - Cross-marketplace logic

### Marketplace-Specific Structure

Each marketplace follows consistent structure:
```
services/{marketplace}/
├── {marketplace}_adapter.py              # High-level orchestration
├── {marketplace}_mapper.py               # Attribute mapping
├── {marketplace}_product_converter.py    # Format conversion
├── {marketplace}_base_client.py          # HTTP/OAuth client
├── {marketplace}_*_client.py             # API clients
└── jobs/                                 # Job handlers
    ├── base_job_handler.py (shared)
    ├── publish_handler.py
    ├── update_handler.py
    ├── delete_handler.py
    ├── sync_handler.py
    └── sync_orders_handler.py
```

---

## File Naming Conventions

| Type | Pattern | Example |
|------|---------|---------|
| Models | `{entity}.py` | `product.py`, `vinted_order.py` |
| Services | `{entity}_service.py` | `product_service.py`, `vinted_pricing_service.py` |
| Repositories | `{entity}_repository.py` | `product_repository.py` |
| Schemas | `{entity}.py` | `product.py`, `vinted.py` |
| API Routes | `{resource}.py` | `products.py`, `auth.py` |
| Clients | `{platform}_*_client.py` | `ebay_inventory_client.py` |
| Migrations | `YYYYMMDD_HHMM_description.py` | `20260114_1200_add_label_column.py` |
| Tests | `test_{subject}.py` | `test_product_service.py` |

---

## Import Conventions

**Absolute Imports** (no relative imports):
```python
from models.user.product import Product
from services.product_service import ProductService
from shared.database import get_db
```

**Group Imports**:
```python
# Standard library
from datetime import datetime
from decimal import Decimal
import os

# Third-party
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

# Local
from models.user.product import Product
from services.product_service import ProductService
from schemas.product import ProductCreate, ProductResponse
from shared.database import get_user_db
```

---

## Key File Sizes (Code Maintenance)

**Large Files (>500 lines) Requiring Refactoring**:
| File | Lines | Recommendation |
|------|-------|----------------|
| `vinted_order_sync.py` | 920 | Split order fetching, parsing, persistence |
| `ebay_fulfillment_client.py` | 836 | Split shipping, returns, cancellations |
| `marketplace_job_service.py` | 784 | Split job CRUD, query builder, batch logic |
| `product_service.py` | 713 | Split CRUD, validation, AI logic |

**Note**: CLAUDE.md recommends refactoring at >500 lines

---

## Configuration Files

| File | Purpose |
|------|---------|
| `alembic.ini` | Alembic migration config |
| `docker-compose.yml` | Development PostgreSQL + Redis |
| `docker-compose.test.yml` | Test database (port 5434) |
| `requirements.txt` | Pinned Python dependencies |
| `.env.example` | Environment template |
| `.gitignore` | Excludes .env, logs/, __pycache__ |

---

## Data Directory Structure (Not in Git)

```
backend/
├── logs/                           # Application logs
│   ├── app.log                     # Main application
│   ├── websocket.log               # WebSocket events
│   └── marketplace_jobs.log        # Job execution
│
└── .env                            # Environment variables (secret)
```

---

## Migration Archiving Strategy

**Active**: `migrations/versions/` (current migrations)
**Archived**: `migrations/archive_YYYYMMDD/` (historical migrations)

**Archiving Criteria**:
- When migration count exceeds 200
- When squashing migrations for performance
- When cleaning up old feature branches

**Current Count**: ~120 migrations (2025-12-07 to 2026-01-14)

---

*Last analyzed: 2026-01-14*
