# Migration Guide: Job System Unification

**Date**: 2026-01-09
**Status**: Implementation Complete
**Migration Timeline**: January 2026 - February 2026

---

## 📋 Overview

This guide documents the migration from marketplace-specific job systems to a unified `MarketplaceJobProcessor` that supports Vinted, eBay, and Etsy.

### What Changed

**Before (Old System)**:
```python
# Vinted only
from services.vinted.vinted_job_processor import VintedJobProcessor
from services.vinted.vinted_job_service import VintedJobService

processor = VintedJobProcessor(db, user_id=1, shop_id=123)
result = await processor.process_next_job()
```

**After (Unified System)**:
```python
# All marketplaces (Vinted, eBay, Etsy)
from services.marketplace import MarketplaceJobProcessor, MarketplaceJobService

# For Vinted jobs
processor = MarketplaceJobProcessor(db, user_id=1, shop_id=123, marketplace="vinted")
result = await processor.process_next_job()

# For eBay jobs
processor = MarketplaceJobProcessor(db, user_id=1, marketplace="ebay")
result = await processor.process_next_job()

# For Etsy jobs
processor = MarketplaceJobProcessor(db, user_id=1, marketplace="etsy")
result = await processor.process_next_job()
```

---

## 🎯 Key Improvements

1. **Unified Handler Pattern**: All marketplaces use the same orchestration system
2. **Dual Communication**: WebSocket (Vinted) + Direct HTTP (eBay/Etsy) in one codebase
3. **Centralized Action Types**: Single `public.marketplace_action_types` table
4. **Consistent API**: Same methods across all marketplaces
5. **Backward Compatible**: `VintedJobProcessor` still works with deprecation warning

---

## 🏗️ Architecture Changes

### Action Types (Database)

**Before**:
```
vinted.action_types (Vinted only)
├── publish
├── update
├── delete
├── sync
└── orders
```

**After**:
```
public.marketplace_action_types (All marketplaces)
├── (vinted, publish)
├── (vinted, update)
├── (vinted, delete)
├── (vinted, sync)
├── (vinted, orders)
├── (ebay, publish)
├── (ebay, update)
├── (ebay, delete)
├── (ebay, sync)
├── (ebay, sync_orders)
├── (etsy, publish)
├── (etsy, update)
├── (etsy, delete)
├── (etsy, sync)
└── (etsy, sync_orders)
```

**Migration SQL**:
```sql
-- Already applied via migration 20260109_0200_unify_action_types.py
-- Migrates vinted.action_types → public.marketplace_action_types
-- Adds marketplace column, migrates data, drops old table
```

### Handler Registry

**Before**:
```python
# services/vinted/jobs/__init__.py
HANDLERS = {
    "publish": PublishJobHandler,
    "update": UpdateJobHandler,
    # ... Vinted only
}
```

**After**:
```python
# services/vinted/jobs/__init__.py
HANDLERS = {
    "publish_vinted": PublishJobHandler,
    "update_vinted": UpdateJobHandler,
    # ...
}

# services/ebay/jobs/__init__.py
EBAY_HANDLERS = {
    "publish_ebay": EbayPublishJobHandler,
    "update_ebay": EbayUpdateJobHandler,
    # ...
}

# services/etsy/jobs/__init__.py
ETSY_HANDLERS = {
    "publish_etsy": EtsyPublishJobHandler,
    "update_etsy": EtsyUpdateJobHandler,
    # ...
}

# services/marketplace/marketplace_job_processor.py
ALL_HANDLERS = {
    **HANDLERS,
    **EBAY_HANDLERS,
    **ETSY_HANDLERS,
}
```

**Action Code Format**: `{action}_{marketplace}`
- Examples: `publish_vinted`, `publish_ebay`, `sync_etsy`

---

## 📝 Migration Steps

### Step 1: Database Migrations

Run the following migrations (in order):

```bash
# 1. Unify action_types table
alembic upgrade 20260109_0200  # unify_action_types

# 2. Add eBay action types
alembic upgrade 20260109_0300  # create_ebay_action_types

# 3. Add Etsy action types
alembic upgrade 20260109_0400  # create_etsy_action_types
```

**Verify**:
```sql
-- Check action types
SELECT marketplace, code, name FROM public.marketplace_action_types ORDER BY marketplace, code;

-- Should see 17 rows (7 vinted + 5 ebay + 5 etsy)
```

### Step 2: Code Migration (Optional, Backward Compatible)

**VintedJobProcessor → MarketplaceJobProcessor**

The old `VintedJobProcessor` is deprecated but still functional. You can migrate progressively:

**Option A - Keep existing code (recommended for now)**:
```python
# Works, but shows deprecation warning
from services.vinted.vinted_job_processor import VintedJobProcessor

processor = VintedJobProcessor(db, user_id=1, shop_id=123)
result = await processor.process_next_job()
```

**Option B - Migrate to unified processor**:
```python
# New unified approach
from services.marketplace import MarketplaceJobProcessor

processor = MarketplaceJobProcessor(
    db=db,
    user_id=1,
    shop_id=123,
    marketplace="vinted"  # Optional filter
)
result = await processor.process_next_job()
```

**Option C - Process all marketplaces**:
```python
# Process jobs from all marketplaces
processor = MarketplaceJobProcessor(db=db, user_id=1)
result = await processor.process_next_job()  # Gets highest priority job regardless of marketplace
```

### Step 3: Job Creation

**VintedJobService → MarketplaceJobService**

**Before**:
```python
from services.vinted.vinted_job_service import VintedJobService

service = VintedJobService(db)
job = service.create_job(
    action_code="publish",
    product_id=123
)
```

**After**:
```python
from services.marketplace import MarketplaceJobService

service = MarketplaceJobService(db)

# Vinted job
job = service.create_job(
    marketplace="vinted",
    action_code="publish",
    product_id=123
)

# eBay job
job = service.create_job(
    marketplace="ebay",
    action_code="publish",
    product_id=123
)

# Etsy job
job = service.create_job(
    marketplace="etsy",
    action_code="publish",
    product_id=123
)
```

---

## 🔄 Communication Patterns

### Vinted (WebSocket via Plugin)

**Pattern**: Backend → WebSocket → Frontend → Plugin → Vinted API

```python
# Handler uses call_plugin() (WebSocket)
class VintedPublishJobHandler(BaseJobHandler):
    async def execute(self, job):
        result = await self.call_plugin(
            action_name="vinted.item.publish",
            payload={"product_id": job.product_id}
        )
        return result
```

### eBay (Direct HTTP with OAuth 2.0)

**Pattern**: Backend → Direct HTTP → eBay API

```python
# Handler uses call_http() (Direct HTTP)
class EbayPublishJobHandler(BaseJobHandler):
    async def execute(self, job):
        service = EbayPublicationService(self.db)
        result = await service.publish_product(job.product_id)
        return result
```

### Etsy (Direct HTTP with OAuth 2.0)

**Pattern**: Backend → Direct HTTP → Etsy API

```python
# Handler uses call_http() (Direct HTTP)
class EtsyPublishJobHandler(BaseJobHandler):
    async def execute(self, job):
        service = EtsyPublicationService(self.db)
        result = await service.publish_product(job.product_id)
        return result
```

---

## ⚠️ Breaking Changes

### 1. Action Code Format Changed

**Before**: `"publish"` (Vinted only)
**After**: `"publish"` (for Vinted), but internally stored as `"publish_vinted"`

**Impact**: Minimal - The system handles the mapping automatically.

**If you create jobs programmatically**:
```python
# Old way (still works for Vinted)
service.create_job(action_code="publish", product_id=123)

# New way (explicit marketplace)
service.create_job(marketplace="vinted", action_code="publish", product_id=123)
```

### 2. VintedActionType Deprecated

**Before**:
```python
from models.vinted.vinted_action_type import VintedActionType

action_type = db.query(VintedActionType).filter_by(code="publish").first()
```

**After**:
```python
from models.public.marketplace_action_type import MarketplaceActionType

action_type = db.query(MarketplaceActionType).filter_by(
    marketplace="vinted",
    code="publish"
).first()
```

---

## 🧪 Testing

### Test Job Creation

```python
from services.marketplace import MarketplaceJobService

service = MarketplaceJobService(db)

# Test Vinted job
job = service.create_job(
    marketplace="vinted",
    action_code="publish",
    product_id=1
)
assert job.marketplace == "vinted"
assert job.status == JobStatus.PENDING

# Test eBay job
job = service.create_job(
    marketplace="ebay",
    action_code="publish",
    product_id=1
)
assert job.marketplace == "ebay"
```

### Test Job Processing

```python
from services.marketplace import MarketplaceJobProcessor

# Vinted processor
processor = MarketplaceJobProcessor(db, user_id=1, shop_id=123, marketplace="vinted")
result = await processor.process_next_job()
assert result["success"]

# eBay processor
processor = MarketplaceJobProcessor(db, user_id=1, marketplace="ebay")
result = await processor.process_next_job()
assert result["success"]

# Etsy processor
processor = MarketplaceJobProcessor(db, user_id=1, marketplace="etsy")
result = await processor.process_next_job()
assert result["success"]
```

---

## 📅 Deprecation Timeline

| Date | Event |
|------|-------|
| **2026-01-09** | Unified system introduced, VintedJobProcessor deprecated |
| **2026-02-01** | VintedJobProcessor will be removed |
| **2026-02-01** | All code must use MarketplaceJobProcessor |

---

## 🔍 Troubleshooting

### Issue: "Action type not found"

**Symptom**: `ValueError: Invalid action code: publish for marketplace: ebay`

**Cause**: Migrations not applied

**Solution**:
```bash
alembic upgrade head
```

### Issue: "Unknown action: publish_ebay"

**Symptom**: `ValueError: Unknown action: publish_ebay`

**Cause**: Handler not registered in EBAY_HANDLERS dict

**Solution**: Check `services/ebay/jobs/__init__.py` - handler should be in EBAY_HANDLERS dict

### Issue: Deprecation warning on VintedJobProcessor

**Symptom**: `DeprecationWarning: VintedJobProcessor is deprecated...`

**Cause**: Using deprecated class

**Solution**: Migrate to `MarketplaceJobProcessor` (see Step 2 above)

---

## 📚 Additional Resources

- **Plan Document**: `/home/maribeiro/.claude/plans/encapsulated-seeking-coral.md`
- **Migration Files**: `backend/migrations/versions/20260109_*.py`
- **Unified Processor**: `backend/services/marketplace/marketplace_job_processor.py`
- **Handler Examples**:
  - Vinted: `backend/services/vinted/jobs/`
  - eBay: `backend/services/ebay/jobs/`
  - Etsy: `backend/services/etsy/jobs/`

---

## ✅ Migration Checklist

- [ ] Run database migrations (`alembic upgrade head`)
- [ ] Verify action types in DB (17 total)
- [ ] Test job creation for each marketplace
- [ ] Test job processing for each marketplace
- [ ] Update API routes to use MarketplaceJobProcessor (optional, backward compatible)
- [ ] Update documentation/comments referencing VintedJobProcessor
- [ ] Schedule removal of VintedJobProcessor for February 2026

---

*Document created: 2026-01-09*
*Last updated: 2026-01-09*
