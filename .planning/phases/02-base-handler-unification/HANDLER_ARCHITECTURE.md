# Handler Architecture Documentation

> **Status**: Phase 2 - Before unification
> **Date**: 2026-01-15

## Overview

StoFlow currently has **two incompatible base handler classes** serving the same purpose. This document captures the current state before Phase 2 unification.

---

## 1. BaseJobHandler (Modern, Active)

**Location**: `backend/services/vinted/jobs/base_job_handler.py`

**Status**: ✅ **Used by ALL active handlers (15 handlers)**

**Lines of Code**: 186 lines

### Interface

```python
class BaseJobHandler(ABC):
    """Base class for all marketplace job handlers."""

    # Class attribute
    ACTION_CODE: str = "base"

    # Constructor
    def __init__(
        self,
        db: Session,
        shop_id: int | None = None,
        job_id: int | None = None
    ):
        self.db = db
        self.shop_id = shop_id
        self.job_id = job_id
        self.user_id: Optional[int] = None  # Must be set before execute()

    # Abstract method - must be implemented by subclasses
    @abstractmethod
    async def execute(self, job: MarketplaceJob) -> dict[str, Any]:
        """Execute the action."""
        pass

    # Helper methods
    async def call_plugin(...) -> dict[str, Any]:
        """Helper for calling plugin via WebSocket (Vinted only)."""

    async def call_http(...) -> dict[str, Any]:
        """Helper for calling API marketplace directly (eBay, Etsy)."""

    def log_start(self, message: str):
        """Log start of operation."""

    def log_success(self, message: str):
        """Log successful operation."""

    def log_error(self, message: str, exc_info: bool = False):
        """Log error."""

    def log_debug(self, message: str):
        """Log debug info."""
```

### Active Handlers Using BaseJobHandler

**Vinted (7 handlers)**:
- `backend/services/vinted/jobs/publish_job_handler.py` - PublishJobHandler
- `backend/services/vinted/jobs/update_job_handler.py` - UpdateJobHandler
- `backend/services/vinted/jobs/delete_job_handler.py` - DeleteJobHandler
- `backend/services/vinted/jobs/link_product_job_handler.py` - LinkProductJobHandler
- `backend/services/vinted/jobs/sync_job_handler.py` - SyncJobHandler
- `backend/services/vinted/jobs/orders_job_handler.py` - OrdersJobHandler
- `backend/services/vinted/jobs/message_job_handler.py` - MessageJobHandler

**eBay (5 handlers)**:
- `backend/services/ebay/jobs/ebay_publish_job_handler.py` - EbayPublishJobHandler
- `backend/services/ebay/jobs/ebay_update_job_handler.py` - EbayUpdateJobHandler
- `backend/services/ebay/jobs/ebay_delete_job_handler.py` - EbayDeleteJobHandler
- `backend/services/ebay/jobs/ebay_sync_job_handler.py` - EbaySyncJobHandler
- `backend/services/ebay/jobs/ebay_orders_sync_job_handler.py` - EbayOrdersSyncJobHandler

**Etsy (3 handlers)**:
- `backend/services/etsy/jobs/etsy_publish_job_handler.py` - EtsyPublishJobHandler
- `backend/services/etsy/jobs/etsy_update_job_handler.py` - EtsyUpdateJobHandler
- `backend/services/etsy/jobs/etsy_delete_job_handler.py` - EtsyDeleteJobHandler
- `backend/services/etsy/jobs/etsy_sync_job_handler.py` - EtsySyncJobHandler
- `backend/services/etsy/jobs/etsy_orders_sync_job_handler.py` - EtsyOrdersSyncJobHandler

**Total**: 15 active handlers

### Key Characteristics

✅ **Modern async architecture** with `async def execute(job: MarketplaceJob)`
✅ **WebSocket support** for Vinted plugin via `call_plugin()`
✅ **Direct HTTP support** for eBay/Etsy via `call_http()`
✅ **Clean interface** with minimal methods
✅ **Logging helpers** for consistent log formatting
⚠️ **Missing**: TaskOrchestrator integration (to be added in Phase 2)

---

## 2. BaseMarketplaceHandler (Legacy, Dead)

**Location**: `backend/services/marketplace/handlers/base_handler.py`

**Status**: ❌ **Dead code - only used by 4 obsolete handlers**

**Lines of Code**: 343 lines (bloated)

### Interface

```python
class BaseMarketplaceHandler(ABC):
    """Base class for all marketplace job handlers (legacy)."""

    # Class attribute
    ACTION_CODE: str = "base"

    # Constructor
    def __init__(self, db: Session, job_id: int):
        self.db = db
        self.job_id = job_id
        self.user_id = None  # Set by MarketplaceJobProcessor

        # Load the job automatically (couples handler to job existence)
        self.job = self.db.query(MarketplaceJob).filter(...).first()
        if not self.job:
            raise ValueError(f"MarketplaceJob with id={job_id} not found")

        # Extract fields for convenience (tight coupling)
        self.marketplace = self.job.marketplace
        self.product_id = self.job.product_id

    # Abstract method
    @abstractmethod
    async def execute(self) -> dict[str, Any]:
        """Execute the job (no job parameter - uses self.job)."""
        pass

    # Legacy task creation (pre-TaskOrchestrator)
    async def create_task(...) -> MarketplaceTask:
        """Create a child task for this job."""

    # Legacy task execution (complex, no longer used)
    async def execute_plugin_task(...) -> dict[str, Any]:
        """Execute a plugin HTTP task."""

    async def execute_direct_http(...) -> dict[str, Any]:
        """Execute a direct HTTP request."""

    # Compatibility layer (redundant with BaseJobHandler)
    async def call_plugin(...) -> dict[str, Any]:
        """Helper for calling the plugin (backward compatibility)."""

    # Logging helpers (same as BaseJobHandler)
    def log_start(self, message: str):
    def log_success(self, message: str):
    def log_error(self, message: str, exc_info: bool = False):
    def log_debug(self, message: str):
    def log_warning(self, message: str):
```

### Dead Handlers Using BaseMarketplaceHandler

**Obsolete handlers (4 files + 1 parent)**:
1. `backend/services/marketplace/handlers/base_publish_handler.py` - BasePublishHandler (extends BaseMarketplaceHandler)
2. `backend/services/marketplace/handlers/vinted/publish_handler.py` - VintedPublishHandler
3. `backend/services/marketplace/handlers/ebay/publish_handler.py` - EbayPublishHandler
4. `backend/services/marketplace/handlers/etsy/publish_handler.py` - EtsyPublishHandler
5. `backend/services/marketplace/handlers/vinted/link_product_handler.py` - LinkProductHandler

**Why Dead**:
- Replaced by modern `*_job_handler.py` equivalents in Phase 1
- No active code references these files
- Not imported by any active modules
- **To be deleted in Task 2**

### Key Characteristics

❌ **Bloated** with 343 lines (vs 186 for BaseJobHandler)
❌ **Tight coupling** - loads job in constructor, raises if not found
❌ **Legacy task methods** - `create_task()`, `execute_plugin_task()` (pre-TaskOrchestrator)
❌ **No parameter on execute()** - uses `self.job` instead of `execute(job)`
❌ **Complex** - many methods no longer used

---

## 3. Key Differences

| Aspect | BaseJobHandler (Modern) | BaseMarketplaceHandler (Legacy) |
|--------|-------------------------|----------------------------------|
| **Status** | ✅ Active (15 handlers) | ❌ Dead (4 handlers) |
| **Lines of code** | 186 | 343 |
| **Constructor** | `__init__(db, shop_id, job_id)` | `__init__(db, job_id)` |
| **Job handling** | Parameter: `execute(job)` | Attribute: `execute()` uses `self.job` |
| **Job loading** | Caller's responsibility | Loads in constructor (tight coupling) |
| **Task creation** | No built-in (ready for TaskOrchestrator) | Legacy `create_task()` method |
| **Task execution** | No built-in (clean separation) | Legacy `execute_plugin_task()`, `execute_direct_http()` |
| **Vinted plugin** | `call_plugin()` via WebSocket | `call_plugin()` via WebSocket (same) |
| **eBay/Etsy API** | `call_http()` direct | `execute_direct_http()` (more complex) |
| **Logging** | 4 methods (start, success, error, debug) | 5 methods (+ warning) |
| **Flexibility** | High - clean interface | Low - tight coupling |
| **Maintainability** | High - minimal surface | Low - bloated codebase |

---

## 4. Phase 2 Unification Plan

### What Will Be Removed

**Files to delete** (~843 lines total):
- `backend/services/marketplace/handlers/base_handler.py` (343 lines)
- `backend/services/marketplace/handlers/base_publish_handler.py` (~100 lines)
- `backend/services/marketplace/handlers/vinted/publish_handler.py` (~100 lines)
- `backend/services/marketplace/handlers/ebay/publish_handler.py` (~100 lines)
- `backend/services/marketplace/handlers/etsy/publish_handler.py` (~100 lines)
- `backend/services/marketplace/handlers/vinted/link_product_handler.py` (~100 lines)

**Empty directories to remove**:
- `backend/services/marketplace/handlers/vinted/`
- `backend/services/marketplace/handlers/ebay/`
- `backend/services/marketplace/handlers/etsy/`

### What Will Be Added to BaseJobHandler

**1. Abstract method for task definition**:
```python
@abstractmethod
def create_tasks(self, job: MarketplaceJob) -> List[str]:
    """Define task names for this job type."""
    pass
```

**2. TaskOrchestrator integration**:
```python
def __init__(self, db: Session, shop_id: int | None = None, job_id: int | None = None):
    # ... existing code ...
    self.orchestrator = TaskOrchestrator(db)
```

**3. Helper method for task-based execution**:
```python
async def execute_with_tasks(
    self,
    job: MarketplaceJob,
    handlers: dict[str, Callable[[MarketplaceTask], dict]]
) -> dict[str, Any]:
    """Execute job using TaskOrchestrator with retry intelligence."""
    # ... implementation ...
```

**Net change**: ~700 lines removed, ~50 lines added → **~650 lines net reduction**

### Why This is Safe

✅ **Only deleting dead code** - No active handlers affected
✅ **Adding optional helper** - Handlers not required to use `execute_with_tasks()` yet
✅ **Abstract method won't break** - `create_tasks()` only enforced at instantiation (handlers still work without it for now)
✅ **Incremental migration** - Handlers will adopt TaskOrchestrator in future phases

---

## 5. Post-Unification State

After Phase 2 completion:

**Single base handler**: `BaseJobHandler` only
**All 15 handlers**: Inherit from `BaseJobHandler`
**TaskOrchestrator ready**: Handlers can opt-in to task-based execution
**Migration path**: Future phases will update handlers to implement `create_tasks()` and use `execute_with_tasks()`

---

*Documented: 2026-01-15*
*Phase: 02 Base Handler Unification*
*This document will be updated after Task 6 with final state*
