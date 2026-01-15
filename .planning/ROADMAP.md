# StoFlow - Task System Unified Architecture - Roadmap

## 📋 Overview

**Goal:** Refactor the task/job/batch orchestration system to create a unified, powerful architecture shared across all marketplaces (Vinted, eBay, Etsy).

**Core Value:** One unified task orchestration system that eliminates duplication, enables granular tracking, and provides consistent patterns.

**Timeline:** ~2 weeks (10 phases foundation + 2 phases finalization)

**Strategy:**
- Priority: **Foundation first** (Phase 1 critical)
- Testing: **Hybrid** (TDD for foundation, pragmatic for handlers)
- Migration: **Cleanup first** (fresh start, no backward compat with old jobs)
- Commit model: **1 commit per task** (for monitoring, with idempotent retry)

---

## 🏗️ Target Architecture

```
BatchJob (parent orchestrator)
├── MarketplaceJob (operation: publish, update, delete, sync)
│   ├── MarketplaceTask (validate product data)
│   ├── MarketplaceTask (map data to marketplace format)
│   ├── MarketplaceTask (upload image 1)
│   ├── MarketplaceTask (upload image 2)
│   ├── MarketplaceTask (upload image N)
│   ├── MarketplaceTask (create listing on marketplace)
│   └── MarketplaceTask (save result to database)
```

### Key Principles

1. **Granularity:** 1 task = 1 functional step (max visibility)
2. **Commit:** 1 task = 1 commit (monitoring + partial persistence)
3. **Idempotence:** Each task checks its side-effects before execution
4. **Retry:** Skip COMPLETED tasks, retry only FAILED task
5. **Progress:** BatchJob.progress = completed jobs / total jobs
6. **Status:** Job stays RUNNING until all tasks complete
7. **Cascade:** Job → BatchJob auto-update (not Task → Job)

### Example: Publish 50 Products on Vinted

```
1 BatchJob "Publish 50 products to Vinted"
├── 50 MarketplaceJobs (1 per product)
│   └── Each job: ~7-10 MarketplaceTasks
│       - validate
│       - map_data
│       - upload_image_1
│       - upload_image_2
│       - upload_image_3
│       - create_listing
│       - save_result

Total: 1 BatchJob, 50 Jobs, ~400 Tasks
```

---

## 🎯 12 Phases Breakdown

### Phase 1: Foundation - Task Orchestration Core ⭐ (Priority)

**Goal:** Implement the MarketplaceTask system properly with granular tracking, idempotent retry, and 1-commit-per-task model.

**Deliverables:**
- `MarketplaceTask` model enhancement (add `step_type`, `step_order`, `is_idempotent`, `side_effects`)
- `TaskOrchestrator` service (create, execute, skip completed, retry logic)
- Migration to activate `marketplace_tasks` table
- **TDD:** Write tests FIRST for task orchestration (test-first strict)

**Tasks:**
1. Design task lifecycle (PENDING → RUNNING → COMPLETED/FAILED)
2. Implement task creation with `step_type` enum (validate, map, upload_image, create, save)
3. Implement task execution with 1 commit per task
4. Implement skip logic (if task.status == COMPLETED, skip)
5. Implement idempotence check (before executing, verify side-effects)
6. Write unit tests for TaskOrchestrator (TDD)
7. Write integration tests for task retry scenarios

**Success Criteria:**
- ✅ MarketplaceTask table active and used
- ✅ 1 task = 1 commit (visible in DB during execution)
- ✅ Retry skips COMPLETED tasks
- ✅ Idempotence prevents duplicate side-effects
- ✅ Test coverage: >90% for TaskOrchestrator

**Duration:** ~3 days

---

### Phase 2: Base Handler Unification

**Goal:** Clean up the dual BaseHandler situation (BaseJobHandler vs BaseMarketplaceHandler).

**Deliverables:**
- Remove dead `BaseMarketplaceHandler` code
- Standardize all handlers on `BaseJobHandler`
- Add `create_tasks()` abstract method to BaseJobHandler

**Tasks:**
1. Audit all handlers to confirm they use BaseJobHandler
2. Delete `services/marketplace/handlers/base_handler.py` (unused)
3. Add `create_tasks()` method to BaseJobHandler (returns list of task specs)
4. Update BaseJobHandler to use TaskOrchestrator from Phase 1
5. Write tests for BaseJobHandler (test-after pragmatic)

**Success Criteria:**
- ✅ Only one BaseHandler implementation exists
- ✅ All handlers inherit from BaseJobHandler
- ✅ `create_tasks()` method defined in base

**Duration:** ~1 day

---

### Phase 3: DirectAPI Handler Base

**Goal:** Create `DirectAPIJobHandler` base class to factorize eBay/Etsy duplication (80% identical code).

**Deliverables:**
- `DirectAPIJobHandler` class (extends BaseJobHandler)
- Common patterns extracted: product fetch, service call, result handling
- OAuth token refresh logic factorized

**Tasks:**
1. Analyze eBay/Etsy handlers to identify common patterns
2. Create `DirectAPIJobHandler` with:
   - `get_product()` (fetch product from DB)
   - `get_service()` (abstract, returns marketplace-specific service)
   - `execute()` (delegates to service via create_tasks)
3. Implement task creation pattern for direct API handlers
4. Write tests for DirectAPIJobHandler (test-after)

**Success Criteria:**
- ✅ DirectAPIJobHandler base class exists
- ✅ Common logic factorized (product fetch, service delegation)
- ✅ eBay/Etsy handlers ready to migrate (next phases)

**Duration:** ~2 days

---

### Phase 4: eBay Handlers Refactoring

**Goal:** Refactor 5 eBay handlers to use DirectAPIJobHandler and task orchestration.

**Deliverables:**
- `EbayPublishJobHandler` migrated to DirectAPIJobHandler
- `EbayUpdateJobHandler` migrated
- `EbayDeleteJobHandler` migrated
- `EbaySyncJobHandler` migrated
- `EbayUnpublishJobHandler` migrated

**Tasks (per handler):**
1. Inherit from DirectAPIJobHandler
2. Implement `get_service()` (returns EbayPublicationService)
3. Implement `create_tasks()` (returns task specs: validate, map, create, save)
4. Update service to be task-aware (optional, if needed)
5. Write integration tests (test-after)

**Success Criteria:**
- ✅ All 5 eBay handlers use DirectAPIJobHandler
- ✅ All eBay handlers create MarketplaceTasks
- ✅ No code duplication between eBay handlers
- ✅ Tests pass (existing + new)

**Duration:** ~2 days (parallel refactoring possible)

---

### Phase 5: Etsy Handlers Refactoring ✅

**Goal:** Refactor 5 Etsy handlers to use DirectAPIJobHandler and task orchestration (identical to Phase 4).

**Status:** ✅ Complete (2026-01-15)

**Deliverables:**
- ✅ `EtsyPublishJobHandler` migrated to DirectAPIJobHandler
- ✅ `EtsyUpdateJobHandler` migrated
- ✅ `EtsyDeleteJobHandler` migrated
- ✅ `EtsySyncJobHandler` migrated
- ✅ `EtsyOrdersSyncJobHandler` migrated

**Accomplishments:**
- 5/5 handlers migrated successfully
- Code reduction: 206 lines (53%)
- Tests: 19/19 passing (100%)
- 2 stub services created (EtsySyncService, EtsyOrderSyncService)

**Duration:** ~6 min (actual)

---

### Phase 6: Vinted Services Extraction ✅

**Goal:** Extract Vinted handler logic (260 lines inline) to dedicated services (like eBay/Etsy pattern).

**Status:** ✅ Complete (2026-01-15)

**Deliverables:**
- ✅ `VintedPublicationService` (extracted from VintedPublishJobHandler)
- ✅ `VintedUpdateService` (extracted from VintedUpdateJobHandler)
- ✅ `VintedDeletionService` (extracted from VintedDeleteJobHandler)
- ✅ Services encapsulate complete business logic (not thin wrappers)

**Accomplishments:**
- 3/3 services created (748 lines total)
- 3/3 handlers migrated to delegate
- Code reduction: 343 lines (58%, handlers from 592 to 249 lines)
- Tests: 350/400 passing (87%, test debt to fix in Phase 7)
- WebSocket communication logic preserved in services

**Duration:** ~45 min (actual)

---

### Phase 7: Vinted Handlers Refactoring

**Goal:** Refactor 7 Vinted handlers to use BaseJobHandler + task orchestration + service delegation.

**Deliverables:**
- `VintedPublishJobHandler` (80 lines, delegates to VintedPublicationService)
- `VintedUpdateJobHandler` (80 lines, delegates to VintedUpdateService)
- `VintedDeleteJobHandler` (80 lines, delegates to VintedDeletionService)
- `VintedSyncJobHandler` migrated
- `VintedUnpublishJobHandler` migrated
- `VintedActivateJobHandler` migrated
- `VintedArchiveJobHandler` migrated

**Tasks (per handler):**
1. Inherit from BaseJobHandler (not DirectAPIJobHandler, WebSocket different)
2. Implement `create_tasks()` (task specs specific to Vinted)
3. Delegate to service from Phase 6
4. Handle WebSocket communication via PluginWebSocketHelper
5. Write integration tests (test-after)

**Success Criteria:**
- ✅ All 7 Vinted handlers thin (80 lines max)
- ✅ All Vinted handlers create MarketplaceTasks
- ✅ Business logic in services
- ✅ Tests pass

**Duration:** ~3 days (7 handlers, WebSocket complexity)

---

### Phase 8: Stats System Refactoring

**Goal:** Separate statistics tracking per marketplace (current: all mixed in `vinted_job_stats`).

**Deliverables:**
- `marketplace_job_stats` table (marketplace-agnostic)
- Stats service that logs to correct marketplace
- Migration to rename/refactor `vinted_job_stats`

**Tasks:**
1. Create migration to rename `vinted_job_stats` to `marketplace_job_stats`
2. Add `marketplace` column (vinted, ebay, etsy)
3. Update `MarketplaceJobService` to log stats per marketplace
4. Add indexes on (marketplace, created_at) for queries
5. Update stats queries in frontend/API
6. Write tests for stats service (test-after)

**Success Criteria:**
- ✅ Stats separated by marketplace
- ✅ Essential metrics only (performance, success rates)
- ✅ Frontend shows per-marketplace stats
- ✅ Tests pass

**Duration:** ~1 day

---

### Phase 9: Schema Cleanup

**Goal:** Remove deprecated columns and dead code from database schema.

**Deliverables:**
- Migration to remove `batch_id` column (replaced by `batch_job_id`)
- Cleanup unused FK constraints
- Remove dead `BaseMarketplaceHandler` references

**Tasks:**
1. Create migration to drop `marketplace_jobs.batch_id` (deprecated string FK)
2. Verify all code uses `batch_job_id` (int FK)
3. Remove any dead code referencing old `batch_id`
4. Run migration on test DB (multi-tenant check)
5. Write migration rollback (in case of issue)

**Success Criteria:**
- ✅ `batch_id` column removed
- ✅ Only `batch_job_id` FK exists
- ✅ No references to old schema in code
- ✅ Migration works on all tenant schemas

**Duration:** ~0.5 day

---

### Phase 10: Testing & Documentation

**Goal:** Complete test coverage and architecture documentation.

**Deliverables:**
- Unit tests for all new services (target: >80% coverage)
- Integration tests for task retry scenarios
- Architecture documentation (ARCHITECTURE.md)
- API documentation updates

**Tasks:**
1. Audit test coverage (pytest-cov)
2. Write missing unit tests for services
3. Write integration tests for full job + task flow
4. Document task orchestration system (ARCHITECTURE.md)
5. Update API docs (task status endpoints)
6. Add code comments for complex task logic

**Success Criteria:**
- ✅ Test coverage >80% for new code
- ✅ All retry scenarios covered by tests
- ✅ ARCHITECTURE.md complete
- ✅ API docs updated

**Duration:** ~2 days

---

### Phase 11: Data Cleanup & Migration

**Goal:** Clean up old jobs/batches in test/dev databases before launch.

**Deliverables:**
- Script to delete old jobs (pre-refactoring)
- Fresh test data for validation
- Migration verification on clean DB

**Tasks:**
1. Write script to delete all jobs/batches before cutoff date
2. Run script on dev DB (cleanup)
3. Verify migrations work on clean DB
4. Create fresh test batch jobs for validation
5. Run full integration test suite on clean data

**Success Criteria:**
- ✅ All old jobs deleted from test/dev DBs
- ✅ Fresh test data created
- ✅ Migrations verified on clean DB
- ✅ Integration tests pass

**Duration:** ~0.5 day

---

### Phase 12: Monitoring & Optimization

**Goal:** Add monitoring for task system and optimize performance if needed.

**Deliverables:**
- Metrics for task execution times
- Alerts for high failure rates
- Performance profiling (if bottleneck detected)

**Tasks:**
1. Add logging for task execution times
2. Add metrics to track task success/failure rates
3. Add alerts for >20% task failure rate
4. Profile task creation (if >1000 tasks per job)
5. Optimize DB queries if slow (batch inserts?)
6. Add dashboard for task monitoring (optional)

**Success Criteria:**
- ✅ Task execution times logged
- ✅ Alerts configured for failures
- ✅ Performance acceptable (<100ms per task)
- ✅ No bottlenecks detected

**Duration:** ~1 day

---

## 📊 Dependencies Between Phases

```
Phase 1 (Foundation) ← CRITICAL PATH
    ↓
Phase 2 (Base Handler) ← Depends on Phase 1
    ↓
Phase 3 (DirectAPI Handler) ← Depends on Phase 2
    ├─→ Phase 4 (eBay) ← Can run in parallel
    └─→ Phase 5 (Etsy) ← Can run in parallel

Phase 6 (Vinted Services) ← Independent, can start early
    ↓
Phase 7 (Vinted Handlers) ← Depends on Phase 1, 2, 6

Phase 8 (Stats) ← Independent, can run anytime
Phase 9 (Schema Cleanup) ← After Phases 4, 5, 7 done
Phase 10 (Tests) ← After all implementation phases
Phase 11 (Cleanup) ← Before launch
Phase 12 (Monitoring) ← After launch
```

**Critical Path:** Phase 1 → Phase 2 → Phase 7 (Vinted is most complex)

**Parallelization opportunities:**
- Phase 4 + Phase 5 (eBay + Etsy handlers)
- Phase 6 can start while Phase 3-5 run
- Phase 8 can run anytime

---

## 🧪 Testing Strategy

### Phase 1: Test-First (TDD Strict)
- Write tests BEFORE implementing TaskOrchestrator
- Focus: task lifecycle, retry logic, idempotence
- Coverage target: >90%

### Phases 2-9: Test-After (Pragmatic)
- Implement handlers first (faster iteration)
- Write tests after to validate behavior
- Coverage target: >80%

### Phase 10: Comprehensive Testing
- Integration tests for full job + task flows
- Retry scenario tests (partial failure, skip completed)
- Performance tests (1000+ tasks)

### Test Environments
- **Unit tests:** In-memory or test DB (fast)
- **Integration tests:** Docker PostgreSQL (realistic)
- **E2E tests:** Full stack (backend + DB + WebSocket)

---

## ✅ Overall Success Criteria

### Functional
- ✅ MarketplaceTask system active and used by all handlers
- ✅ Granular tracking (1 task = 1 step)
- ✅ Idempotent retry (skip COMPLETED tasks)
- ✅ No code duplication between eBay/Etsy handlers
- ✅ Vinted handlers match eBay/Etsy pattern (delegation)
- ✅ Stats separated by marketplace

### Quality
- ✅ Test coverage >80% for new code
- ✅ All integration tests pass
- ✅ No regressions (existing features still work)

### Performance
- ✅ Task creation <100ms per task
- ✅ No DB bottlenecks (even with 1000+ tasks)
- ✅ Progress tracking real-time (1 commit per task)

### Maintainability
- ✅ Architecture documented (ARCHITECTURE.md)
- ✅ Code follows consistent patterns (base classes)
- ✅ Easy to add new marketplace (extend DirectAPIJobHandler)

---

## 📅 Timeline Summary

| Phase | Duration | Cumulative |
|-------|----------|------------|
| Phase 1: Foundation | 3 days | 3 days |
| Phase 2: Base Handler | 1 day | 4 days |
| Phase 3: DirectAPI Handler | 2 days | 6 days |
| Phase 4: eBay Handlers | 2 days | 8 days (parallel with 5) |
| Phase 5: Etsy Handlers | 2 days | 8 days (parallel with 4) |
| Phase 6: Vinted Services | 2 days | 10 days (can overlap) |
| Phase 7: Vinted Handlers | 3 days | 13 days |
| Phase 8: Stats Refactoring | 1 day | 14 days |
| Phase 9: Schema Cleanup | 0.5 day | 14.5 days |
| Phase 10: Tests & Docs | 2 days | 16.5 days |
| Phase 11: Data Cleanup | 0.5 day | 17 days |
| Phase 12: Monitoring | 1 day | 18 days |

**Total: ~3.5 weeks** (with parallelization, can be reduced to ~2.5 weeks)

---

## 🚀 Next Steps

1. Review and approve this roadmap
2. Create Phase 1 detailed plan (PLAN.md)
3. Start implementation of TaskOrchestrator
4. TDD: Write tests first for Phase 1

---

*Created: 2026-01-15*
*Mode: Interactive, Comprehensive depth*
*Priority: MarketplaceTask foundation first*
