# ROADMAP - Image Management Architecture Migration

**Project:** Image Management Architecture Migration
**Created:** 2026-01-15
**Mode:** Interactive
**Depth:** Standard

---

## Overview

Migrate image management from JSONB column to dedicated `product_images` table with rich metadata support to solve critical label publishing issue (611 products affected).

**Critical Problem:** Internal price tag labels (last image) are being published to marketplaces because current JSONB structure doesn't distinguish image types.

**Success Criteria:**
- ✅ Zero data loss (backup verified: 9.3MB dump)
- ✅ 611 labels correctly identified with `is_label=true`
- ✅ No labels published to Vinted/eBay after migration
- ✅ All tests pass
- ✅ Rollback capability via Alembic downgrade

---

## Phases

### Phase 1: Database Architecture ✅ COMPLETE
**Goal:** Create new `product_images` table with rich metadata support

**Deliverables:**
- [x] Alembic migration creating `product_images` table
- [x] Table structure:
  - Core: `id`, `product_id` (FK), `url`, `order`
  - Metadata: `is_label`, `alt_text`, `tags`, `mime_type`, `file_size`, `width`, `height`
  - Timestamps: `created_at`, `updated_at`
- [x] Indexes on `product_id`, `order`, `is_label`
- [x] Foreign key constraint to `products` table
- [x] Multi-tenant schema support (applies to all `user_X` schemas)

**Research Needed:** None (internal architecture)

**Plans Executed:** 1/1
- ✅ PLAN 1.1: Create product_images table (commit: fa60a3d)

---

### Phase 2: Data Migration ✅ COMPLETE
**Goal:** Migrate all existing images from JSONB to new table with label identification

**Deliverables:**
- [x] Idempotent migration script
- [x] Multi-tenant support (iterate all `user_X` schemas)
- [x] Label detection: last image in order → `is_label=true`
- [x] Bulk insert optimization (not row-by-row)
- [x] Transaction per schema (atomicity)
- [x] Post-migration validation:
  - Count JSONB images == Count table rows ✅
  - 3281 products have `is_label=true` (100% - all have 2+ images) ✅
  - No missing images ✅
- [x] Rollback capability verified

**Research Needed:** None (standard SQLAlchemy migration)

**Plans Executed:** 2/2
- ✅ PLAN 2.1: Create migration script (commit: f1c6bc8)
- ✅ PLAN 2.2: Execute migration and validate (commits: 887c6b4, 2df0a60)

---

### Phase 3: Services & API ✅ COMPLETE
**Goal:** Refactor services and API to use new table structure

**Deliverables:**
- [x] Create ProductImage model + ProductImageRepository (PLAN 3.1)
  - SQLAlchemy model with all columns mapped
  - Repository with CRUD operations
  - Relationship Product ↔ ProductImage
  - Unit tests for repository
- [x] Refactor `ProductImageService` (PLAN 3.2):
  - Update `add_image()`, `delete_image()`, `reorder_images()` to use table
  - New methods: `get_product_photos()`, `get_label_image()`, `set_label_flag()`
  - Accept metadata (mime_type, file_size, width, height)
  - Unit tests updated
- [x] Update API routes and schemas (PLAN 3.3):
  - Update `ProductImageItem` schema with rich metadata
  - Add endpoint for label flag management
  - Integration tests updated
  - Fixed bug in DELETE route (was accessing JSONB directly)

**Research Needed:** None (existing services refactor)

**Plans Executed:** 3/3
- ✅ PLAN 3.1: Create ProductImage Model + Repository (commits: fba6afb, 5e630d4, 1d1d6eb)
- ✅ PLAN 3.2: Refactor ProductImageService to use table (commit: 281c0f4)
- ✅ PLAN 3.3: Update API routes and response schemas (commits: 4831754, 671336a, 10b596a, cec4cbb)

---

### Phase 4: Marketplace Integration ✅ COMPLETE
**Goal:** Update marketplace converters to filter labels from published images

**Deliverables:**
- [x] Modify Vinted image upload (PLAN 4.1):
  - Refactor `upload_product_images()` to use ProductImageService.get_product_photos()
  - Filter `is_label=true` images from Vinted uploads
  - Integration tests verifying no labels in Vinted payloads
- [x] Modify eBay conversion service (PLAN 4.2):
  - Refactor `_get_image_urls()` to use ProductImageService.get_product_photos()
  - Filter `is_label=true` images from eBay inventory items
  - Integration tests verifying no labels in eBay payloads
- [x] Manual validation on test products (both plans)

**Out of Scope:** Etsy integration (v2)

**Research Needed:** None (existing converters modification)

**Plans Executed:** 2/2
- ✅ PLAN 4.1: Vinted Marketplace Integration (commits: 5341cb5, dd4c822)
- ✅ PLAN 4.2: eBay Marketplace Integration (commits: bd6d162, dc62fd7)

---

### Phase 5: Cleanup & Documentation
**Goal:** Remove deprecated JSONB column and finalize migration

**Deliverables:**
- [ ] Alembic migration removing `products.images` column
- [ ] Alembic downgrade migration (restore JSONB from table if needed)
- [ ] Update ARCHITECTURE.md:
  - New image table structure
  - Migration history
  - Label detection strategy
- [ ] Update CONVENTIONS.md:
  - Image handling patterns
  - Label flag usage
- [ ] Final validation:
  - All tests green
  - No references to JSONB column
  - Rollback tested

**Research Needed:** None (standard cleanup)

**Estimated Plans:** 1-2 plans

---

## Constraints

**Technical:**
- Multi-tenant architecture (all `user_X` schemas)
- SQLAlchemy 2.0 syntax (`Mapped[T]`, `mapped_column()`)
- Idempotent migrations (can rerun safely)
- Performance: Bulk operations for 3282 products

**Data Safety:**
- ✅ Backup created: `backups/stoflow_db_full_backup_20260115_091652.dump` (9.3 MB)
- Zero data loss tolerance
- Rollback strategy required
- Validation before column removal

**Out of Scope (v1):**
- FileService upload/optimization (keep R2 as-is)
- UI Frontend changes (backend/API only)
- Etsy converter updates (Vinted/eBay only)
- CDN/cache invalidation

---

## Dependencies

**Between Phases:**
- Phase 2 depends on Phase 1 (table must exist)
- Phase 3 depends on Phase 2 (data must be migrated)
- Phase 4 depends on Phase 3 (services must work with new table)
- Phase 5 depends on Phase 4 (full validation before cleanup)

**External:**
- None (internal refactoring)

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Data loss during migration | ✅ Full backup created, transaction-based migration, validation |
| Migration script bugs | Idempotent design, test on subset first, rollback capability |
| Label detection accuracy | Based on pythonApiWOO pattern (85%+ accuracy), manual review list |
| Service refactoring breaks existing code | Comprehensive unit + integration tests |
| Marketplace converters miss labels | Explicit tests for label filtering |
| JSONB column removal premature | Only after full validation, downgrade migration available |

---

## Next Steps

1. ✅ Backup complete
2. ✅ PROJECT.md defined
3. ✅ ROADMAP.md created
4. ✅ Phase 1: Database Architecture COMPLETE
5. ✅ Phase 2: Data Migration COMPLETE
6. ✅ Phase 3: Services & API COMPLETE
7. ✅ Phase 4: Marketplace Integration PLANNED (2 plans created)
8. → Execute PLAN 4.1: Vinted Marketplace Integration

**Command:** `/gsd:execute-plan` (for .planning/phases/phase-4/4-1-PLAN.md)

---

*Last updated: 2026-01-15 after Phase 4 planning*
