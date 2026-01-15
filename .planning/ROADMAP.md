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

### Phase 3: Services & API
**Goal:** Refactor services and API to use new table structure

**Deliverables:**
- [ ] Refactor `ProductImageService`:
  - Update `add_image()`, `delete_image()`, `reorder_images()`
  - New methods: `get_product_photos()`, `get_label_image()`, `set_label_flag()`
  - Validation logic (mime_type, file_size)
  - Auto-reorder on delete
- [ ] Update API routes (`api/products/images.py`)
- [ ] Update response schemas to include new metadata
- [ ] Unit tests for service methods
- [ ] Integration tests for API endpoints
- [ ] Test label flag validation

**Research Needed:** None (existing services refactor)

**Estimated Plans:** 3-4 plans

---

### Phase 4: Marketplace Integration
**Goal:** Update marketplace converters to filter labels from published images

**Deliverables:**
- [ ] Modify `VintedProductConverter`:
  - Filter `is_label=true` images
  - Only send product photos to Vinted
- [ ] Modify `EbayProductConversionService`:
  - Filter `is_label=true` images
  - Only send product photos to eBay
- [ ] Integration tests:
  - Verify no labels in Vinted payload
  - Verify no labels in eBay payload
- [ ] Manual validation on test products

**Out of Scope:** Etsy integration (v2)

**Research Needed:** None (existing converters modification)

**Estimated Plans:** 2-3 plans

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
6. → Plan Phase 3: Services & API Refactoring

---

*Last updated: 2026-01-15 after Phase 2 completion*
