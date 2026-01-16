# StoFlow Backend Architecture

**Comprehensive documentation of the task orchestration system and multi-marketplace architecture**

---

## Table of Contents

1. [Overview](#overview)
2. [Task Orchestration System](#task-orchestration-system)
3. [Key Models](#key-models)
4. [Service Layer](#service-layer)
5. [Handler Architecture](#handler-architecture)
6. [State Machine](#state-machine)
7. [Retry Logic & Idempotence](#retry-logic--idempotence)
8. [Multi-Tenant Architecture](#multi-tenant-architecture)
9. [API Design](#api-design)
10. [Database Schema](#database-schema)
11. [Design Patterns](#design-patterns)
12. [Extension Guide](#extension-guide)
13. [Testing Strategy](#testing-strategy)
14. [Performance Considerations](#performance-considerations)
15. [Security](#security)
16. [Troubleshooting](#troubleshooting)

---

## Overview

StoFlow Backend is a multi-marketplace e-commerce management system built with **FastAPI**, **PostgreSQL**, and **SQLAlchemy 2.0**. It provides a unified orchestration layer for managing product listings, orders, and synchronization across multiple marketplaces (Vinted, eBay, Etsy).

### Core Features

- **Multi-Marketplace Support**: Unified API for Vinted, eBay, and Etsy
- **Task Orchestration**: Three-level hierarchy (BatchJob → MarketplaceJob → MarketplaceTask)
- **Multi-Tenant Isolation**: PostgreSQL schema-based tenant separation
- **Retry Intelligence**: Idempotent task execution with granular retry logic
- **Real-Time Communication**: WebSocket integration for browser plugin (Vinted)
- **Direct API Integration**: OAuth 2.0 for eBay and Etsy

### Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Framework** | FastAPI | REST API server |
| **Database** | PostgreSQL 15+ | Multi-tenant data storage |
| **ORM** | SQLAlchemy 2.0 | Database access layer |
| **Migrations** | Alembic | Schema version control |
| **Authentication** | JWT | Token-based auth with refresh rotation |
| **WebSocket** | Socket.IO | Real-time plugin communication |
| **Testing** | Pytest | Unit and integration tests |

---

## Task Orchestration System

The task orchestration system provides a unified way to execute marketplace operations with granular progress tracking, retry logic, and idempotence guarantees.

### Three-Level Hierarchy

```
BatchJob (Parent Orchestrator)
├── MarketplaceJob #1 (operation: publish product A)
│   ├── MarketplaceTask #1 (validate product data)
│   ├── MarketplaceTask #2 (map data to marketplace format)
│   ├── MarketplaceTask #3 (upload image 1/3)
│   ├── MarketplaceTask #4 (upload image 2/3)
│   ├── MarketplaceTask #5 (upload image 3/3)
│   ├── MarketplaceTask #6 (create listing)
│   └── MarketplaceTask #7 (save listing ID)
├── MarketplaceJob #2 (operation: publish product B)
│   └── ... (similar tasks)
└── MarketplaceJob #3 (operation: publish product C)
    └── ... (similar tasks)
```

**Level 1: BatchJob**
- Groups multiple jobs from a single bulk operation
- Tracks overall progress (e.g., "200/500 products published")
- Provides batch-level status (pending, running, completed, partially_failed)

**Level 2: MarketplaceJob**
- Represents a single marketplace operation (publish, update, delete, sync)
- Executes via marketplace-specific handlers
- Manages retry logic and expiration (1 hour for pending jobs)

**Level 3: MarketplaceTask**
- Atomic execution unit (1 task = 1 functional step)
- Types: plugin_http (Vinted), direct_http (eBay/Etsy), db_operation, file_operation
- Idempotent: checks for side-effects before execution
- Positioned: enables intelligent retry (skip completed, retry only failed)

### Key Principles

1. **Granularity**: Each task represents a single, atomic operation
2. **Idempotence**: Tasks check for existing side-effects before executing
3. **Retry Intelligence**: Skip tasks with status='success', retry only 'failed'
4. **Progress Tracking**: Real-time visibility at all three levels
5. **Fault Isolation**: Failed task doesn't block others in the job
6. **Auditability**: Full history of task attempts and results

---

## Key Models

### BatchJob

**Location**: `backend/models/user/batch_job.py`

**Purpose**: Groups multiple MarketplaceJobs from a single bulk operation.

**Key Fields**:
- `batch_id`: Unique string identifier (format: `{action}_{timestamp}_{uuid}`)
- `marketplace`: Target marketplace (vinted, ebay, etsy)
- `action_code`: Operation type (publish, update, delete, sync)
- `status`: BatchJobStatus enum (pending, running, completed, partially_failed, failed, cancelled)
- `total_count`, `completed_count`, `failed_count`, `cancelled_count`: Progress counters
- `priority`: 1=CRITICAL, 2=HIGH, 3=NORMAL, 4=LOW

**Relationships**:
- `jobs`: One-to-many relationship with MarketplaceJob

**Properties**:
- `progress_percent`: Calculated percentage (completed / total * 100)
- `is_active`: True if pending or running
- `is_terminal`: True if completed, failed, partially_failed, or cancelled
- `pending_count`: Number of jobs not yet processed

### MarketplaceJob

**Location**: `backend/models/user/marketplace_job.py`

**Purpose**: Represents a single marketplace operation on a product.

**Key Fields**:
- `marketplace`: Target marketplace (vinted, ebay, etsy)
- `action_type_id`: Foreign key to marketplace_action_types table
- `product_id`: Product being processed (optional, can be null for non-product operations)
- `batch_job_id`: Foreign key to parent BatchJob (optional)
- `status`: JobStatus enum (pending, running, paused, completed, failed, cancelled, expired)
- `priority`: Can override action_type default priority
- `retry_count`, `max_retries`: Retry tracking (default: max 3 retries)
- `expires_at`: Expiration timestamp (created_at + 1 hour)
- `input_data`, `result_data`: JSONB fields for job parameters and results

**Relationships**:
- `batch_job`: Many-to-one with BatchJob
- `product`: Many-to-one with Product (optional)

**Properties**:
- `is_active`: True if pending, running, or paused
- `is_terminal`: True if completed, failed, cancelled, or expired
- `is_vinted`, `is_ebay`, `is_etsy`: Marketplace type checks

### MarketplaceTask

**Location**: `backend/models/user/marketplace_task.py`

**Purpose**: Atomic execution unit within a MarketplaceJob.

**Key Fields**:
- `task_type`: MarketplaceTaskType enum (plugin_http, direct_http, db_operation, file_operation)
- `description`: Human-readable description (e.g., "Upload image 1/5")
- `position`: Integer for ordered execution (enables intelligent retry)
- `status`: TaskStatus enum (pending, processing, success, failed, timeout, cancelled)
- `job_id`: Foreign key to parent MarketplaceJob
- `payload`: JSONB with task execution parameters
- `result`: JSONB with task output after execution
- `http_method`, `path`, `platform`: HTTP request details (for HTTP tasks)

**Indexes**:
- `(job_id, position)`: For ordered task retrieval
- `(job_id, status)`: For querying failed/pending tasks to retry

**Properties**:
- `is_plugin_task`: True if task_type is plugin_http
- `is_active`: True if pending or processing
- `is_terminal`: True if success, failed, timeout, or cancelled

### MarketplaceActionType

**Location**: `backend/models/public/marketplace_action_type.py`

**Purpose**: Defines available operation types per marketplace.

**Key Fields**:
- `marketplace`: Target marketplace (vinted, ebay, etsy)
- `code`: Action identifier (publish, update, delete, sync, orders, message, link_product)
- `name`: Human-readable name
- `priority`: Default priority for jobs of this type
- `max_retries`: Default retry limit
- `description`: Operation description

**Scope**: Shared across all tenants (stored in `public` schema)

---

## Service Layer

### MarketplaceJobService

**Location**: `backend/services/marketplace/marketplace_job_service.py`

**Purpose**: CRUD operations and orchestration for MarketplaceJobs.

**Key Methods**:

| Method | Purpose |
|--------|---------|
| `create_job()` | Create a new MarketplaceJob with validation |
| `start_job()` | Mark job as running, set started_at timestamp |
| `complete_job()` | Mark job as completed, update parent batch progress |
| `fail_job()` | Mark job as failed, update parent batch progress |
| `pause_job()`, `resume_job()` | Pause/resume job execution |
| `cancel_job()` | Cancel job and all pending tasks |
| `increment_retry()` | Increment retry count, check if max retries reached |
| `get_next_pending_job()` | Get highest priority pending job |
| `expire_old_jobs()` | Mark jobs pending > 1 hour as expired |
| `get_job_tasks()` | Get all tasks for a job |
| `get_job_progress()` | Calculate job progress based on task statuses |

**Features**:
- Action type caching for performance
- Automatic parent BatchJob progress updates
- Statistics tracking (daily stats per action type)
- Retry logic with configurable max attempts

### MarketplaceJobProcessor

**Location**: `backend/services/marketplace/marketplace_job_processor.py`

**Purpose**: Main orchestrator for job execution across all marketplaces.

**Key Methods**:

| Method | Purpose |
|--------|---------|
| `process_next_job()` | Get and execute next pending job |
| `_execute_job()` | Dispatch job to appropriate handler |
| `_handle_job_failure()` | Handle job failure with retry logic |

**Handler Dispatch Logic**:
```python
# Full action code format: "{action_code}_{marketplace}"
# Examples: "publish_vinted", "publish_ebay", "sync_etsy"

handler_class = ALL_HANDLERS.get(full_action_code)
if not handler_class:
    raise ValueError(f"Unknown action: {full_action_code}")

handler = handler_class(db=db, shop_id=shop_id, job_id=job_id)
handler.user_id = user_id  # For WebSocket (Vinted only)

result = await handler.execute(job)
```

**Global Handler Registry**:
- Combines handlers from all marketplaces
- Format: `{action_code}_{marketplace}` → Handler class
- Loaded from `VINTED_HANDLERS`, `EBAY_HANDLERS`, `ETSY_HANDLERS`

### BatchJobService

**Location**: `backend/services/marketplace/batch_job_service.py`

**Purpose**: CRUD operations and progress tracking for BatchJobs.

**Key Methods**:

| Method | Purpose |
|--------|---------|
| `create_batch_job()` | Create batch with N MarketplaceJobs |
| `update_batch_progress()` | Recalculate progress counters from jobs |
| `get_batch_summary()` | Get batch status and progress |
| `cancel_batch()` | Cancel all pending jobs in batch |

**Batch Status Calculation**:
- `pending`: No jobs started yet
- `running`: At least one job is running
- `completed`: All jobs completed successfully
- `partially_failed`: Some jobs succeeded, some failed
- `failed`: All jobs failed
- `cancelled`: Batch was cancelled by user

---

## Handler Architecture

### BaseMarketplaceHandler

**Location**: `backend/services/marketplace/handlers/base_handler.py`

**Purpose**: Abstract base class for all marketplace-specific handlers.

**Key Methods**:

| Method | Purpose | Abstract |
|--------|---------|----------|
| `execute()` | Execute the job (must be implemented by subclasses) | ✅ Yes |
| `create_task()` | Create a child MarketplaceTask | No |
| `execute_plugin_task()` | Execute plugin_http task via WebSocket | No |
| `execute_direct_http()` | Execute direct_http task via httpx | No |
| `call_plugin()` | Helper for Vinted WebSocket calls (backward compat) | No |
| `log_start()`, `log_success()`, `log_error()`, `log_debug()` | Logging helpers | No |

**Task Creation Pattern**:
```python
# Create a task
task = await self.create_task(
    task_type=MarketplaceTaskType.PLUGIN_HTTP,
    description="Upload image 1/3",
    product_id=self.product_id,
    http_method="POST",
    path="/api/v2/photos",
    payload={"photo_data": "..."},
    platform="vinted"
)

# Execute the task
result = await self.execute_plugin_task(task, timeout=60)
```

### Communication Patterns by Marketplace

| Marketplace | Pattern | Implementation |
|-------------|---------|----------------|
| **Vinted** | WebSocket → Frontend → Plugin | `execute_plugin_task()` via PluginWebSocketHelper |
| **eBay** | Direct HTTP OAuth 2.0 | `execute_direct_http()` via httpx |
| **Etsy** | Direct HTTP OAuth 2.0 | `execute_direct_http()` via httpx |

**WebSocket Architecture (Vinted)**:
```
Backend (Handler) → PluginWebSocketHelper
                  → WebSocketService (Socket.IO server)
                  → Frontend (useVintedBridge composable)
                  → Plugin (Browser Extension)
                  → Vinted API (with DataDome bypass)
```

**Direct HTTP Architecture (eBay/Etsy)**:
```
Backend (Handler) → httpx.AsyncClient
                  → eBay/Etsy API (OAuth 2.0 Bearer token)
```

### Handler Implementation Example

**VintedPublishHandler** (`services/vinted/jobs/publish_handler.py`):
- Inherits from `BaseMarketplaceHandler`
- Creates 5-7 tasks: validate → map → upload images → create listing → save
- Uses WebSocket for all Vinted API calls
- Implements idempotence checks (skip if listing already exists)

**EbayPublishHandler** (`services/ebay/jobs/publish_handler.py`):
- Inherits from `BaseMarketplaceHandler`
- Creates 3-5 tasks: validate → create inventory item → create offer → publish
- Uses direct HTTP with eBay OAuth 2.0 token
- Implements eBay-specific inventory model

---

## State Machine

### Job Status Flow

```
PENDING → RUNNING → COMPLETED
   ↓         ↓           ↑
   ↓         ↓           |
   ↓    (retry logic)    |
   ↓         ↓           |
   ↓    RUNNING ─────────┘
   ↓         ↓
   ↓    FAILED (max retries reached)
   ↓
PAUSED ⇄ (user action: resume)
   ↓
CANCELLED (user action)
   ↓
EXPIRED (pending > 1 hour)
```

**Status Transitions**:

| From | To | Trigger |
|------|----|----- |
| PENDING | RUNNING | Job processor starts execution |
| RUNNING | COMPLETED | All tasks succeeded |
| RUNNING | FAILED | Task failed and max retries reached |
| RUNNING | PENDING | Task failed, retry available |
| PENDING/RUNNING | PAUSED | User pauses job |
| PAUSED | PENDING | User resumes job |
| Any non-terminal | CANCELLED | User cancels job |
| PENDING | EXPIRED | Job pending for > 1 hour |

**Terminal States**: COMPLETED, FAILED, CANCELLED, EXPIRED
- Jobs in terminal states cannot transition to other states
- Terminal jobs are excluded from queue queries

### Task Status Flow

```
PENDING → PROCESSING → SUCCESS
   ↓          ↓            ↑
   ↓      (idempotent)     |
   ↓          ↓            |
   ↓     PROCESSING ───────┘
   ↓          ↓
   ↓      FAILED (task error)
   ↓          ↓
   ↓      TIMEOUT (execution timeout)
   ↓
CANCELLED (parent job cancelled)
```

**Task Retry Behavior**:
- Tasks with status='success': **SKIPPED** on retry
- Tasks with status='failed': **RE-EXECUTED** on retry
- Tasks with status='pending': **EXECUTED** on retry

---

## Retry Logic & Idempotence

### Retry Logic

**Job-Level Retry**:
1. Job fails during execution
2. `MarketplaceJobService.increment_retry()` is called
3. If `retry_count < max_retries` (default: 3):
   - Job status set to PENDING
   - Job returns to queue
4. If max retries reached:
   - Job status set to FAILED
   - Error message: "Max retries (3) exceeded"
   - Parent BatchJob progress updated

**Task-Level Retry Intelligence**:
```python
# When retrying a job, processor checks each task status
for task in job.tasks:
    if task.status == TaskStatus.SUCCESS:
        # Skip completed tasks - idempotence guarantee
        logger.info(f"Skipping completed task {task.id}")
        continue

    # Only execute pending or failed tasks
    if task.status in (TaskStatus.PENDING, TaskStatus.FAILED):
        try:
            handler.execute_task(task)
            task.status = TaskStatus.SUCCESS
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error_message = str(e)

        # Commit after each task for granular progress tracking
        db.commit()
```

### Idempotence Guarantees

**Definition**: An operation is idempotent if executing it multiple times has the same effect as executing it once.

**Implementation Strategies**:

| Task Type | Idempotence Check |
|-----------|-------------------|
| Create Listing | Check if listing_id exists in database before API call |
| Upload Image | Check if image_url exists in database before upload |
| Update Listing | Check if current data matches desired state |
| Delete Listing | Check if listing still exists before deletion |
| Sync Operation | Compare timestamps to avoid re-syncing unchanged data |

**Example: Vinted Publish Handler**
```python
# Check if product already published to Vinted
existing_listing = get_vinted_listing(product_id)
if existing_listing and existing_listing.vinted_id:
    # Skip API call, return existing listing
    return {"success": True, "vinted_id": existing_listing.vinted_id}

# Proceed with publication only if not already published
result = await call_vinted_api(...)
```

**Benefits**:
1. **Safety**: Retrying a job multiple times doesn't create duplicate listings
2. **Efficiency**: Skip unnecessary API calls for already-completed work
3. **Consistency**: Database state remains consistent across retries
4. **Auditability**: Task status accurately reflects completion state

---

## Multi-Tenant Architecture

### Schema-Based Isolation

Each user has their own PostgreSQL schema for complete data isolation:

```
┌─────────────────────┐
│  public schema      │  ← Shared data (users, subscriptions)
├─────────────────────┤
│  product_attributes │  ← Shared data (brands, colors, categories)
├─────────────────────┤
│  user_1 schema      │  ← User 1 data (products, jobs, tasks)
├─────────────────────┤
│  user_2 schema      │  ← User 2 data (products, jobs, tasks)
├─────────────────────┤
│  user_3 schema      │  ← User 3 data (products, jobs, tasks)
├─────────────────────┤
│  template_tenant    │  ← Template for creating new user schemas
└─────────────────────┘
```

**Schema Contents**:

| Schema | Tables | Purpose |
|--------|--------|---------|
| `public` | users, marketplace_action_types | Authentication and shared configuration |
| `product_attributes` | brands, colors, conditions, materials, sizes, categories | Shared product metadata |
| `user_X` | products, marketplace_jobs, marketplace_tasks, batch_jobs, vinted_products, ebay_listings, etsy_listings | User-specific data |
| `template_tenant` | Same as user_X | Template cloned for new users |

### Schema Context Switching

**Automatic Context Switching**:
```python
# In shared/database.py
def set_user_schema(db: Session, user_id: int):
    """Set search_path for multi-tenant isolation."""
    db.execute(text(f"SET search_path TO user_{user_id}, public"))
    db.commit()

# In API dependencies
def get_user_db(current_user: User = Depends(get_current_user)):
    """Get DB session with user schema context."""
    db = SessionLocal()
    try:
        set_user_schema(db, current_user.id)
        yield db, current_user
    finally:
        db.close()
```

**Schema Translate Map** (SQLAlchemy):
```python
# Models use placeholder schema 'tenant'
class MarketplaceJob(Base):
    __tablename__ = "marketplace_jobs"
    __table_args__ = {"schema": "tenant"}

# At runtime, 'tenant' is mapped to 'user_X'
execution_options = {
    "schema_translate_map": {"tenant": f"user_{user_id}"}
}
```

### Multi-Tenant Migrations

**Fan-Out Pattern**:
```python
def upgrade():
    conn = op.get_bind()

    # Get all user schemas
    result = conn.execute(text("""
        SELECT schema_name FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%'
    """))
    user_schemas = [row[0] for row in result]

    # Apply migration to each user schema
    for schema in user_schemas:
        op.execute(f"SET search_path TO {schema}, public")
        op.add_column('marketplace_jobs',
                     sa.Column('new_field', sa.String(50)))
```

**Template Tenant Cloning**:
```python
# When creating a new user
def create_user_schema(user_id: int):
    # Clone template_tenant schema
    conn.execute(text(f"""
        CREATE SCHEMA user_{user_id}
        AUTHORIZATION stoflow_backend
    """))

    # Clone all tables from template_tenant
    conn.execute(text(f"""
        CREATE TABLE user_{user_id}.products
        (LIKE template_tenant.products INCLUDING ALL)
    """))
    # ... repeat for all tables
```

### Security & Isolation

**Guarantees**:
1. **No Cross-Tenant Queries**: Search path ensures queries only access current user's schema
2. **Explicit FK Validation**: Foreign keys to shared tables use full schema names
3. **Row-Level Security**: Not needed - schema isolation is sufficient
4. **Connection Pooling**: Each connection has its own search_path (set per request)

**Trade-offs**:
- ✅ Pros: Strong isolation, simple queries, easy to backup/restore per tenant
- ❌ Cons: Schema proliferation (max ~1000 tenants), migrations take longer

---

## API Design

### REST API Principles

**URL Structure**:
```
/api/{domain}/{resource}
/api/{domain}/{resource}/{id}
/api/{domain}/{resource}/{id}/{action}
```

**Examples**:
- `POST /api/marketplace/jobs` - Create a job
- `GET /api/marketplace/jobs/{id}` - Get job status
- `POST /api/marketplace/jobs/{id}/retry` - Retry a failed job
- `GET /api/marketplace/tasks?job_id={id}` - List tasks for a job

### Job Endpoints

**POST /api/marketplace/jobs**
- **Purpose**: Create a new marketplace job
- **Auth**: Required
- **Body**: `{marketplace, action_code, product_id, priority?}`
- **Returns**: `201 Created` with job object

**GET /api/marketplace/jobs/{id}**
- **Purpose**: Get job status and details
- **Auth**: Required
- **Returns**: `200 OK` with job object including tasks

**GET /api/marketplace/jobs**
- **Purpose**: List jobs with filters
- **Auth**: Required
- **Query Params**: `marketplace, status, batch_job_id, limit, offset`
- **Returns**: `200 OK` with paginated job list

**POST /api/marketplace/jobs/{id}/retry**
- **Purpose**: Retry a failed job
- **Auth**: Required
- **Validation**: Job must be in FAILED status
- **Returns**: `200 OK` with updated job

**POST /api/marketplace/jobs/{id}/pause**
- **Purpose**: Pause a running job
- **Auth**: Required
- **Returns**: `200 OK` with updated job

**POST /api/marketplace/jobs/{id}/resume**
- **Purpose**: Resume a paused job
- **Auth**: Required
- **Returns**: `200 OK` with updated job

**POST /api/marketplace/jobs/{id}/cancel**
- **Purpose**: Cancel a job
- **Auth**: Required
- **Returns**: `200 OK` with updated job

### Task Endpoints

**GET /api/marketplace/tasks**
- **Purpose**: List tasks with filters
- **Auth**: Required
- **Query Params**: `job_id, status, limit, offset`
- **Returns**: `200 OK` with task list

**GET /api/marketplace/tasks/{id}**
- **Purpose**: Get task details
- **Auth**: Required
- **Returns**: `200 OK` with task object

### BatchJob Endpoints

**POST /api/batch-jobs**
- **Purpose**: Create a batch job
- **Auth**: Required
- **Body**: `{marketplace, action_code, product_ids[]}`
- **Returns**: `201 Created` with batch object

**GET /api/batch-jobs/{id}**
- **Purpose**: Get batch progress and status
- **Auth**: Required
- **Returns**: `200 OK` with batch object including jobs

**GET /api/batch-jobs**
- **Purpose**: List batch jobs
- **Auth**: Required
- **Query Params**: `marketplace, status, limit, offset`
- **Returns**: `200 OK` with batch list

**POST /api/batch-jobs/{id}/cancel**
- **Purpose**: Cancel all pending jobs in batch
- **Auth**: Required
- **Returns**: `200 OK` with updated batch

### Response Format

**Success Response**:
```json
{
  "id": 123,
  "marketplace": "vinted",
  "action_code": "publish",
  "status": "completed",
  "product_id": 456,
  "created_at": "2026-01-16T10:00:00Z",
  "completed_at": "2026-01-16T10:05:30Z",
  "result_data": {
    "vinted_id": 789,
    "url": "https://www.vinted.fr/items/789"
  }
}
```

**Error Response**:
```json
{
  "detail": "Job not found",
  "status_code": 404,
  "error_code": "JOB_NOT_FOUND"
}
```

---

## Database Schema

### Tables Overview

| Table | Schema | Purpose |
|-------|--------|---------|
| `marketplace_action_types` | public | Action type definitions per marketplace |
| `batch_jobs` | user_X | Batch operation orchestration |
| `marketplace_jobs` | user_X | Individual marketplace operations |
| `marketplace_tasks` | user_X | Atomic execution units |
| `products` | user_X | Product catalog |
| `vinted_products` | user_X | Vinted-specific metadata |
| `ebay_listings` | user_X | eBay listing data |
| `etsy_listings` | user_X | Etsy listing data |

### Relationships

```
BatchJob (1) ─┬─ (N) MarketplaceJob
              │
              └─ (N) MarketplaceJob ─┬─ (N) MarketplaceTask
                                      │
                                      └─ (1) Product
                                      │
                                      └─ (1) MarketplaceActionType (public schema)
```

### Key Constraints

**Foreign Keys**:
- `marketplace_jobs.batch_job_id` → `batch_jobs.id` (ondelete: SET NULL)
- `marketplace_jobs.product_id` → `products.id` (ondelete: SET NULL)
- `marketplace_jobs.action_type_id` → `public.marketplace_action_types.id` (ondelete: RESTRICT)
- `marketplace_tasks.job_id` → `marketplace_jobs.id` (ondelete: SET NULL)
- `marketplace_tasks.product_id` → `products.id` (ondelete: CASCADE)

**Unique Constraints**:
- `marketplace_jobs.idempotency_key` (unique, index) - Prevents duplicate publications

**Indexes**:
- `(job_id, position)` on marketplace_tasks - For ordered task retrieval
- `(job_id, status)` on marketplace_tasks - For querying failed/pending tasks
- `status` on marketplace_jobs - For queue queries
- `(status, priority, created_at)` on marketplace_jobs - For priority queue
- `marketplace` on marketplace_jobs - For marketplace-specific queries

### JSONB Fields

**marketplace_jobs.input_data**:
```json
{
  "source_product_id": 123,
  "target_marketplace": "vinted",
  "override_price": 29.99,
  "custom_description": "Special description for Vinted"
}
```

**marketplace_jobs.result_data**:
```json
{
  "vinted_id": 789,
  "url": "https://www.vinted.fr/items/789",
  "published_at": "2026-01-16T10:05:30Z"
}
```

**marketplace_tasks.payload**:
```json
{
  "photo_url": "https://r2.stoflow.com/user1/photo1.jpg",
  "photo_order": 1
}
```

**marketplace_tasks.result**:
```json
{
  "vinted_photo_id": 456,
  "url": "https://images.vinted.net/...",
  "uploaded_at": "2026-01-16T10:03:15Z"
}
```

---

## Design Patterns

### Handler Pattern

**Problem**: Different marketplaces require different execution logic.

**Solution**: Abstract base class `BaseMarketplaceHandler` with marketplace-specific implementations.

**Structure**:
```
BaseMarketplaceHandler (Abstract)
├── VintedPublishHandler
├── VintedUpdateHandler
├── VintedDeleteHandler
├── EbayPublishHandler
├── EbayUpdateHandler
├── EtsyPublishHandler
└── ...
```

**Benefits**:
- Consistent interface across all handlers
- Easy to add new marketplaces or actions
- Shared utilities (task creation, logging, HTTP helpers)
- Testable in isolation

### Factory Pattern

**Problem**: Need to instantiate the correct handler based on marketplace and action.

**Solution**: Global handler registry with dynamic lookup.

**Implementation**:
```python
# Registry format: "{action_code}_{marketplace}" → Handler class
ALL_HANDLERS = {
    "publish_vinted": VintedPublishHandler,
    "publish_ebay": EbayPublishHandler,
    "publish_etsy": EtsyPublishHandler,
    "update_vinted": VintedUpdateHandler,
    # ...
}

# Usage
full_action_code = f"{action_code}_{marketplace}"
handler_class = ALL_HANDLERS.get(full_action_code)
handler = handler_class(db=db, job_id=job_id)
```

**Benefits**:
- Simple registration mechanism
- No complex if/elif chains
- Easy to discover available handlers

### Strategy Pattern

**Problem**: Vinted uses WebSocket, eBay/Etsy use direct HTTP.

**Solution**: Two execution strategies in `BaseMarketplaceHandler`.

**Implementation**:
```python
# Strategy 1: WebSocket (Vinted)
async def execute_plugin_task(task, timeout):
    result = await PluginWebSocketHelper.call_plugin_http(...)
    return result

# Strategy 2: Direct HTTP (eBay, Etsy)
async def execute_direct_http(task, headers, timeout):
    async with httpx.AsyncClient() as client:
        response = await client.request(...)
        return response.json()
```

**Benefits**:
- Handlers choose the appropriate strategy
- Unified task model regardless of communication method
- Easy to test each strategy independently

### Repository Pattern (Implicit)

**Problem**: Need to abstract database access from business logic.

**Solution**: Service layer acts as repositories.

**Implementation**:
- `MarketplaceJobService` encapsulates all job database operations
- `BatchJobService` encapsulates all batch database operations
- API routes never access SQLAlchemy models directly

**Benefits**:
- Business logic decoupled from ORM
- Easy to mock services for testing
- Consistent error handling

---

## Extension Guide

### Adding a New Marketplace

Follow these steps to add support for a new marketplace (e.g., "amazon"):

**1. Create Handler Directory**
```bash
mkdir backend/services/amazon
mkdir backend/services/amazon/jobs
```

**2. Define Action Types**
```sql
-- In migration file
INSERT INTO public.marketplace_action_types
  (marketplace, code, name, priority, max_retries)
VALUES
  ('amazon', 'publish', 'Publish to Amazon', 3, 3),
  ('amazon', 'update', 'Update Amazon Listing', 3, 3),
  ('amazon', 'delete', 'Delete from Amazon', 2, 1),
  ('amazon', 'sync', 'Sync Amazon Inventory', 4, 3);
```

**3. Create Base Handler**
```python
# services/amazon/jobs/base_handler.py
from services.marketplace.handlers.base_handler import BaseMarketplaceHandler

class AmazonBaseHandler(BaseMarketplaceHandler):
    """Base handler for Amazon operations."""

    def __init__(self, db, job_id):
        super().__init__(db, job_id)
        self.amazon_client = AmazonAPIClient(...)
```

**4. Implement Action Handlers**
```python
# services/amazon/jobs/publish_handler.py
class AmazonPublishHandler(AmazonBaseHandler):
    ACTION_CODE = "publish"

    async def execute(self) -> dict:
        # Create tasks
        task1 = await self.create_task(
            task_type=MarketplaceTaskType.DIRECT_HTTP,
            description="Create Amazon inventory item",
            http_method="POST",
            path="/v1/inventory/items",
            payload={...}
        )

        # Execute task
        result = await self.execute_direct_http(task1)

        return {"success": True, "amazon_asin": result["asin"]}
```

**5. Register Handlers**
```python
# services/amazon/jobs/__init__.py
from .publish_handler import AmazonPublishHandler
from .update_handler import AmazonUpdateHandler

AMAZON_HANDLERS = {
    "publish_amazon": AmazonPublishHandler,
    "update_amazon": AmazonUpdateHandler,
    # ...
}

# In marketplace_job_processor.py
from services.amazon.jobs import AMAZON_HANDLERS

ALL_HANDLERS = {
    **VINTED_HANDLERS,
    **EBAY_HANDLERS,
    **ETSY_HANDLERS,
    **AMAZON_HANDLERS,  # Add new handlers
}
```

**6. Create Marketplace-Specific Models (if needed)**
```python
# models/user/amazon_listing.py
class AmazonListing(Base):
    __tablename__ = "amazon_listings"
    __table_args__ = {"schema": "tenant"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("tenant.products.id"))
    asin: Mapped[str] = mapped_column(String(20), unique=True)
    # ...
```

**7. Add API Routes (optional)**
```python
# api/amazon.py
@router.post("/amazon/sync")
async def sync_amazon_inventory(db_user=Depends(get_user_db)):
    db, user = db_user

    # Create sync job
    job = job_service.create_job(
        marketplace="amazon",
        action_code="sync"
    )

    return job
```

### Adding a New Action Type

To add a new action to an existing marketplace:

**1. Define Action Type**
```sql
INSERT INTO public.marketplace_action_types
  (marketplace, code, name, priority, max_retries, description)
VALUES
  ('vinted', 'bump', 'Bump Listing', 3, 2, 'Move listing to top of search results');
```

**2. Create Handler**
```python
# services/vinted/jobs/bump_handler.py
class VintedBumpHandler(BaseMarketplaceHandler):
    ACTION_CODE = "bump"

    async def execute(self) -> dict:
        # Implementation
        pass
```

**3. Register Handler**
```python
# services/vinted/jobs/__init__.py
VINTED_HANDLERS = {
    # ...
    "bump_vinted": VintedBumpHandler,
}
```

**4. Add API Endpoint (if needed)**
```python
# api/vinted/bump.py
@router.post("/products/{product_id}/bump")
async def bump_vinted_listing(product_id: int, db_user=Depends(get_user_db)):
    # Create bump job
    pass
```

---

## Testing Strategy

### Test Levels

**1. Unit Tests** (`tests/unit/`):
- Test individual services, repositories, and utilities
- Mock database and external dependencies
- Fast execution (< 5 seconds for full suite)
- Coverage target: >80% for service layer

**2. Integration Tests** (`tests/integration/`):
- Test full workflows with real database (Docker)
- Test API endpoints end-to-end
- Test job processor with handlers
- Coverage target: >60% for critical paths

**3. Manual Testing**:
- Test WebSocket communication with real plugin
- Test OAuth flows with real marketplace accounts
- Test batch operations with large datasets

### Testing the Orchestration System

**Test BatchJob Creation**:
```python
def test_create_batch_job_with_multiple_jobs(db_session):
    service = BatchJobService(db_session)

    batch = service.create_batch_job(
        marketplace="vinted",
        action_code="publish",
        product_ids=[1, 2, 3],
        priority=2
    )

    assert batch.total_count == 3
    assert batch.status == BatchJobStatus.PENDING
    assert len(batch.jobs) == 3
```

**Test Job Execution**:
```python
@pytest.mark.asyncio
async def test_process_publish_job(db_session, mock_plugin_websocket):
    # Create job
    job = job_service.create_job(
        marketplace="vinted",
        action_code="publish",
        product_id=1
    )

    # Process job
    processor = MarketplaceJobProcessor(db_session, user_id=1)
    result = await processor.process_next_job()

    # Verify
    assert result["success"] is True
    assert job.status == JobStatus.COMPLETED
```

**Test Retry Logic**:
```python
@pytest.mark.asyncio
async def test_job_retry_after_failure(db_session, mock_failing_handler):
    job = create_test_job(db_session)

    # First attempt fails
    processor = MarketplaceJobProcessor(db_session, user_id=1)
    result1 = await processor.process_next_job()
    assert result1["will_retry"] is True
    assert job.retry_count == 1
    assert job.status == JobStatus.PENDING

    # Second attempt fails
    result2 = await processor.process_next_job()
    assert job.retry_count == 2

    # Third attempt fails - max retries reached
    result3 = await processor.process_next_job()
    assert result3["will_retry"] is False
    assert job.status == JobStatus.FAILED
```

**Test Task Idempotence**:
```python
@pytest.mark.asyncio
async def test_retry_skips_completed_tasks(db_session):
    # Create job with 3 tasks
    job = create_test_job_with_tasks(db_session, num_tasks=3)

    # First execution: task 1 and 2 succeed, task 3 fails
    job.tasks[0].status = TaskStatus.SUCCESS
    job.tasks[1].status = TaskStatus.SUCCESS
    job.tasks[2].status = TaskStatus.FAILED
    job.status = JobStatus.PENDING
    db_session.commit()

    # Retry job
    processor = MarketplaceJobProcessor(db_session, user_id=1)
    await processor.process_next_job()

    # Verify: tasks 1 and 2 were not re-executed
    assert job.tasks[0].retry_count == 0
    assert job.tasks[1].retry_count == 0
    assert job.tasks[2].retry_count == 1
```

### Test Database Setup

**Docker Compose for Testing**:
```yaml
# docker-compose.test.yml
services:
  postgres_test:
    image: postgres:15
    environment:
      POSTGRES_DB: stoflow_test
      POSTGRES_USER: stoflow_test
      POSTGRES_PASSWORD: test_password_123
    ports:
      - "5434:5432"
```

**Test Fixtures** (`tests/conftest.py`):
```python
@pytest.fixture(scope="session")
def db_engine():
    """Create test database engine."""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)

@pytest.fixture
def db_session(db_engine):
    """Create test database session with transaction rollback."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()
```

---

## Performance Considerations

### Task Commit Strategy

**Current Behavior**:
- Commit after each task completion
- Enables real-time progress tracking
- Frontend can poll for updates

**Trade-off**:
- ✅ Pros: Granular visibility, better UX, fault tolerance
- ❌ Cons: More DB roundtrips (1 commit per task vs 1 per job)

**Monitoring**:
```python
# Track commit duration
start = time.time()
db.commit()
commit_duration_ms = (time.time() - start) * 1000

if commit_duration_ms > 100:
    logger.warning(f"Slow commit: {commit_duration_ms}ms")
```

**Future Optimization**:
- Batch commits for non-interactive jobs
- Use `LISTEN/NOTIFY` for real-time updates instead of polling

### Query Optimization

**Eager Loading**:
```python
# BAD: N+1 queries
jobs = db.query(MarketplaceJob).all()
for job in jobs:
    print(job.tasks)  # Lazy load triggers 1 query per job

# GOOD: 1 query with join
jobs = db.query(MarketplaceJob)\
    .options(selectinload(MarketplaceJob.tasks))\
    .all()
```

**Pagination**:
```python
# Always use LIMIT/OFFSET for lists
jobs = db.query(MarketplaceJob)\
    .order_by(MarketplaceJob.created_at.desc())\
    .limit(50)\
    .offset(page * 50)\
    .all()
```

**Indexes**:
- Status-based queries: Index on `status` column
- Priority queue: Composite index on `(status, priority, created_at)`
- Task retrieval: Composite index on `(job_id, position)`

### Batch Processing

**Parallelization Opportunities**:
```python
# Sequential (current)
for job in batch.jobs:
    await processor._execute_job(job)

# Parallel (future)
import asyncio
tasks = [processor._execute_job(job) for job in batch.jobs]
results = await asyncio.gather(*tasks)
```

**Considerations**:
- Connection pool size limits
- Rate limiting per marketplace
- Database lock contention

### Caching

**Action Type Caching**:
```python
# MarketplaceJobService caches action types per (marketplace, code)
self._action_types_cache[(marketplace, code)] = action_type
```

**Future Caching Opportunities**:
- Product data (avoid repeated lookups)
- Marketplace credentials (OAuth tokens)
- Shared attributes (brands, colors)

---

## Security

### Multi-Tenant Isolation

**Schema-Based**:
- Each user has isolated PostgreSQL schema
- `SET search_path` ensures queries only access current user's data
- No cross-tenant queries without explicit schema qualification

**Validation**:
```python
# Always verify user owns the resource
job = db.query(MarketplaceJob).filter(MarketplaceJob.id == job_id).first()
if not job:
    raise HTTPException(status_code=404, detail="Job not found")

# Schema context is already set by get_user_db(), so this query
# automatically only searches in user's schema
```

### Input Validation

**Pydantic Schemas**:
- All API inputs validated by Pydantic models
- Type checking, constraints (min/max), regex patterns
- Custom validators for business rules

**SQL Injection Prevention**:
- Always use parameterized queries
- Never concatenate user input into SQL strings
- SQLAlchemy ORM provides automatic escaping

### Authentication & Authorization

**JWT Authentication**:
- Access tokens (60 min) + Refresh tokens (7 days)
- Signature verification with RS256
- Token rotation support (old + new secrets)

**RBAC** (Role-Based Access Control):
- Roles: admin, seller, viewer
- Permissions: create_product, publish_product, view_orders
- Enforced via `require_role()` and `require_permission()` dependencies

### Secrets Management

**Environment Variables**:
- All secrets in `.env` file (not committed)
- Loaded via `pydantic-settings`
- Separate `.env` per environment (dev, staging, prod)

**Marketplace Credentials**:
- OAuth tokens stored encrypted in database
- Refresh tokens rotated periodically
- Scope limitation (request only needed permissions)

---

## Troubleshooting

### Common Issues

**1. Job Stuck in PROCESSING**

**Symptom**: Job status is RUNNING but hasn't completed after expected time.

**Causes**:
- Plugin disconnected (Vinted)
- WebSocket timeout
- Handler exception not caught

**Resolution**:
```python
# Check job status
GET /api/marketplace/jobs/{id}

# Check logs
tail -f backend/logs/app.log | grep "job_id={id}"

# Manually retry
POST /api/marketplace/jobs/{id}/retry

# Or reset status via DB
UPDATE user_X.marketplace_jobs
SET status = 'pending', retry_count = 0
WHERE id = {id};
```

**2. Tasks Not Retrying**

**Symptom**: Job retries but same tasks fail again.

**Causes**:
- Idempotence check too strict
- External API issue persists
- Invalid payload data

**Resolution**:
```python
# Check task details
GET /api/marketplace/tasks?job_id={id}

# Review task error messages
SELECT id, description, status, error_message
FROM user_X.marketplace_tasks
WHERE job_id = {id};

# Verify idempotence logic in handler
# Review handler logs for skipped tasks
```

**3. Schema Errors**

**Symptom**: `relation "marketplace_jobs" does not exist` or `schema "user_X" does not exist`.

**Causes**:
- User schema not created
- Search path not set
- Migration not applied to user schema

**Resolution**:
```sql
-- Check if user schema exists
SELECT schema_name FROM information_schema.schemata
WHERE schema_name = 'user_{id}';

-- Check if table exists
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'user_{id}';

-- Manually set search path
SET search_path TO user_{id}, public;

-- Run migrations on user schema
cd backend && alembic upgrade head
```

**4. Batch Progress Not Updating**

**Symptom**: Batch progress shows 0% even though jobs are completing.

**Causes**:
- `update_batch_progress()` not called
- Transaction not committed
- Parent batch_job_id not set on jobs

**Resolution**:
```python
# Manually recalculate batch progress
batch_service = BatchJobService(db)
batch_service.update_batch_progress(batch_id)
db.commit()

# Verify jobs have correct batch_job_id
SELECT id, batch_job_id, status
FROM user_X.marketplace_jobs
WHERE batch_job_id = {batch_id};
```

### Debugging

**Enable Debug Logging**:
```bash
# In .env
LOG_LEVEL=DEBUG

# Or via CLI
uvicorn main:app --reload --log-level debug
```

**Check Logs**:
```bash
# Application logs
tail -f backend/logs/app.log

# Filter by job ID
grep "job_id=123" backend/logs/app.log

# Filter by marketplace
grep "marketplace=vinted" backend/logs/app.log
```

**Inspect Job Status**:
```bash
# Via API
curl -H "Authorization: Bearer {token}" \
  http://localhost:8000/api/marketplace/jobs/123

# Via Database
psql -U stoflow_backend -d stoflow
SET search_path TO user_1, public;
SELECT * FROM marketplace_jobs WHERE id = 123;
```

**View Task Details**:
```bash
# Via API
curl -H "Authorization: Bearer {token}" \
  "http://localhost:8000/api/marketplace/tasks?job_id=123"

# Via Database
SELECT id, description, status, error_message, started_at, completed_at
FROM marketplace_tasks
WHERE job_id = 123
ORDER BY position;
```

### Performance Debugging

**Slow Queries**:
```sql
-- Enable query logging in PostgreSQL
ALTER DATABASE stoflow SET log_statement = 'all';
ALTER DATABASE stoflow SET log_min_duration_statement = 100;

-- Check slow queries
tail -f /var/log/postgresql/postgresql-15-main.log | grep "duration:"
```

**Connection Pool Exhaustion**:
```python
# Check active connections
SELECT count(*) FROM pg_stat_activity
WHERE datname = 'stoflow';

# Check pool stats (in application)
from shared.database import engine
pool = engine.pool
print(f"Pool size: {pool.size()}")
print(f"Checked out: {pool.checkedout()}")
print(f"Overflow: {pool.overflow()}")
```

---

*Documentation Last Updated: 2026-01-16*
*System Version: Phase 10-03 (Testing & Documentation)*
