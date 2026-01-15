# StoFlow - Task System Unified Architecture

## What This Is

A comprehensive refactoring of StoFlow's task/job/batch orchestration system to create a unified, powerful architecture shared across all marketplaces (Vinted, eBay, Etsy). This project eliminates code duplication, implements granular task tracking, and establishes consistent patterns for marketplace operations.

## Core Value

**One unified task orchestration system that works consistently across all marketplaces**, eliminating duplication and enabling advanced features like partial retry, granular monitoring, and parallel execution.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] **Granular Task System** — Implement MarketplaceTask as functional sub-operations within jobs (validate, map, upload, create, save) with tracking, retry, and resume capabilities
- [ ] **Unified Handler Pattern** — Establish consistent delegation pattern where handlers are thin orchestrators that delegate business logic to specialized services (like eBay/Etsy, unlike current Vinted)
- [ ] **Factorized Base Classes** — Create shared DirectAPIJobHandler base class eliminating eBay/Etsy duplication (currently ~80% identical code across 10+ handlers)
- [ ] **Service Layer Migration** — Refactor Vinted handlers (260 lines inline logic) to match eBay/Etsy pattern (80 lines delegation to services)
- [ ] **Per-Marketplace Stats** — Separate statistics tracking for each marketplace (current: all mixed in `vinted_job_stats`)
- [ ] **Clean Schema** — Remove deprecated `batch_id` column (replaced by `batch_job_id`), remove dead `BaseMarketplaceHandler` code
- [ ] **Documentation & Tests** — Complete architecture documentation and test coverage for new task orchestration system

### Out of Scope

- **UI/UX changes** — Focus is backend architecture only, no frontend refactoring
- **Performance optimization** — Current system performs adequately, not a bottleneck (focus on maintainability)
- **New marketplace integrations** — Refactor existing three (Vinted, eBay, Etsy) only, new marketplaces come later
- **Real-time progress updates** — WebSocket progress tracking exists and works, no changes needed
- **Batch system rewrite** — `BatchJob` architecture is clean and working, keep as-is
- **Database schema migrations** — Minimize schema changes, work with existing tables where possible (marketplace_tasks table already exists)

## Context

### Current State (Discovered via Codebase Exploration)

**Architecture:**
```
BatchJob (parent orchestrator)
├── MarketplaceJob (operation: publish, update, delete, sync)
└── MarketplaceTask (granular: validate, map, upload) ← DEAD CODE (table exists, never used)
```

**7 Critical Problems Identified:**

1. **eBay/Etsy Duplication (Critical)** — 10+ handlers are 80% identical copy-paste code
2. **Two BaseHandler Classes (Critical)** — `BaseJobHandler` (used) vs `BaseMarketplaceHandler` (unused) causing confusion
3. **Dead MarketplaceTask System (High)** — Table + model exist but NEVER created by any handler (WebSocket architecture bypassed it)
4. **Dual Batch FK (High)** — `batch_id` (deprecated string) + `batch_job_id` (new int FK) both present
5. **Mixed Stats (Medium)** — `vinted_job_stats` receives ALL marketplace jobs (eBay, Etsy included)
6. **Inconsistent Handlers (Medium)** — Vinted (260 lines inline), eBay/Etsy (80 lines delegation), no unified pattern
7. **Confusing Nomenclature (Medium)** — "Task" in code/docs refers to dead concept

**What Works Well:**
- Unified `MarketplaceJobProcessor` orchestrator (2026-01-09 refactoring)
- BatchJob progress tracking auto-updated
- WebSocket communication for Vinted plugin
- Direct HTTP for eBay/Etsy OAuth
- Retry logic and priority queue

### Technology Stack

- **Backend:** FastAPI + SQLAlchemy 2.0 + PostgreSQL (multi-tenant schemas)
- **Async:** Full async/await architecture
- **Communication:** WebSocket (Vinted plugin) + Direct HTTP (eBay/Etsy OAuth)
- **Job Storage:** PostgreSQL tables per tenant (`user_X.marketplace_jobs`, `user_X.marketplace_tasks`, `user_X.batch_jobs`)

### Codebase Size

- **Handlers:** 17 total (7 Vinted, 5 eBay, 5 Etsy) = ~2200 lines
- **Services:** VintedJobService, MarketplaceJobService, BatchJobService = ~1500 lines
- **Models:** MarketplaceJob, BatchJob, MarketplaceTask = ~400 lines

## Constraints

- **Backward Compatibility:** Existing jobs/batches in production must continue working during migration
- **Zero Downtime:** Phased rollout required, no "big bang" cutover
- **Multi-Tenant:** All changes must respect schema-per-tenant architecture (user_X schemas)
- **Test Coverage:** Must maintain/improve test coverage (currently pytest + Docker test DB)
- **Timeline:** ~2 weeks estimated (1 week foundation + 1 week migration + 2-3 days polish)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Implement MarketplaceTask granular system | Enables partial retry, granular monitoring, resume after crash | — Pending |
| Adopt eBay/Etsy delegation pattern everywhere | Handlers thin (80 lines), Services testable, consistent across marketplaces | — Pending |
| Factorize via DirectAPIJobHandler base class | Eliminates 80% duplication between eBay/Etsy handlers | — Pending |
| Refactor Vinted to match eBay/Etsy | Move 260-line handler logic to VintedPublicationService | — Pending |
| Keep BatchJob architecture unchanged | Current design is clean and working, no issues found | — Pending |
| Minimize schema migrations | Work with existing marketplace_tasks table, avoid new tables | — Pending |

---
*Last updated: 2026-01-15 after initialization*
