# Technical Concerns & Issues

## Critical Issues

### 1. Image Label Data Loss (Critical - Business Impact)

**Severity**: 🔴 **CRITICAL**
**Impact**: 611 products affected, customers see internal price tags

**Problem**:
- Original system (pythonApiWOO) had "label" images (internal price tags)
- Migration to StoFlow (2026-01-03) converted images from table → JSONB
- Label identification lost - no `image_type` field in JSONB structure
- Result: Internal labels being published to customers on Vinted/eBay/Etsy

**Current JSONB Structure**:
```json
[
  {"url": "...", "order": 0, "created_at": "..."}
]
```

**Missing**:
```json
[
  {"url": "...", "order": 0, "created_at": "...", "image_type": "product_photo" | "label"}
]
```

**Files Affected**:
- `models/user/product.py` (lines 386-394) - JSONB column definition
- `services/product_image_service.py` - Image CRUD operations
- `services/vinted/vinted_product_converter.py` - Vinted payload builder
- `services/ebay/ebay_product_conversion_service.py` - eBay payload builder
- `services/etsy/etsy_product_conversion_service.py` - Etsy payload builder

**Workaround Options**:
1. Add `image_type` field to JSONB structure
2. Assume last image is label (heuristic, 85% accuracy)
3. Store label order in Product model (`label_image_order: int | None`)

**Recommended**: Option 1 (add `image_type` field) - most flexible for future needs

---

### 2. Transaction Handling Race Condition (Critical - Data Integrity)

**Severity**: 🔴 **CRITICAL**
**Impact**: Orphaned R2 files, storage cost leak

**Problem**:
`ProductImageService.add_image()` does NOT commit transaction, but API route deletes R2 file on error

**File**: `services/product_image_service.py` (lines 32-101)
```python
def add_image(db: Session, product_id: int, image_url: str, ...):
    # ... validation ...
    product.images = images
    # NOTE: Transaction is NOT committed here (line 94)
    # Caller is responsible for db.commit()
    return new_image
```

**File**: `api/products/images.py` (lines 82-95)
```python
try:
    new_image = ProductImageService.add_image(...)  # No commit!
except ValueError as e:
    FileService.delete_product_image(image_url)  # Deletes R2 file
    raise HTTPException(...)  # Database rolls back
```

**Race Condition Scenario**:
1. File uploaded to R2 successfully
2. `ProductImageService.add_image()` called
3. ValueError raised (e.g., product locked)
4. `FileService.delete_product_image()` deletes R2 file
5. **Database transaction rolls back (auto-commit failed)**
6. **R2 file is deleted, but database never committed**
7. **Orphaned/leaked file on R2**

**Inconsistent Commit Strategy**:
- `add_image()` - Does NOT commit
- `delete_image()` (line 138) - DOES commit
- `reorder_images()` (line 195) - DOES commit

**Recommended Fix**: Either commit in service OR remove R2 delete from error handler

---

### 3. Migration Downgrade Data Loss (Critical - Deployment Risk)

**Severity**: 🔴 **CRITICAL**
**Impact**: Permanent data loss if rollback needed

**Problem**:
Migration `20260103_1759_drop_product_images_table.py` has downgrade path that:
- Recreates table structure
- **Does NOT restore data from JSONB**
- No backup mechanism

**File**: `migrations/versions/20260103_1759_drop_product_images_table.py` (lines 79-114)
```python
def downgrade() -> None:
    # Recreate table structure
    op.create_table(
        'product_images',
        sa.Column('id', ...),
        sa.Column('product_id', ...),
        sa.Column('url', ...),
        # ...
    )
    # ⚠️ NO data restoration from Product.images JSONB
```

**Risk**:
- Production deployment fails
- Need to rollback
- Downgrade recreates empty table
- **All image metadata lost**

**Multi-Tenant Complexity**:
- Migration iterates over all `user_*` schemas
- If one schema fails, others still proceed
- Partial failure = inconsistent state
- No rollback atomicity across schemas

**Recommended**: Add migration verification script + JSONB → table data recovery logic

---

## High Severity Issues

### 4. Inconsistent Image Handling Across Marketplaces (High - Maintainability)

**Severity**: 🟠 **HIGH**
**Impact**: Silent failures on eBay, defensive code in Vinted

**eBay Issue** (`services/ebay/ebay_product_conversion_service.py:500-519`):
```python
def _get_image_urls(self, product: Product) -> List[str]:
    # TODO: Récupérer depuis product_images table (removed!)
    import json

    if product.images:
        try:
            images = json.loads(product.images)  # ⚠️ Parses already-parsed JSONB
            if isinstance(images, list):
                return images[:12]  # eBay limit: 12 images
        except (json.JSONDecodeError, TypeError):
            pass  # ⚠️ Silent failure, returns []
    return []
```

**Issues**:
- **Type Confusion**: `Product.images` is already JSONB (dict/list), but code tries `json.loads()` again
- **Silent Failures**: Catches all exceptions, returns empty list without logging
- **TODO Comment**: Still references removed `product_images table`
- **No Validation**: Returns list without checking elements have "url" key

**Vinted Defensive Code** (`services/vinted/vinted_product_helpers.py:52-62`):
```python
if hasattr(product, 'images') and product.images:
    if isinstance(product.images, list):
        for img in product.images:
            if isinstance(img, dict) and img.get('url'):
                image_urls.append(img['url'])
            elif hasattr(img, 'url'):  # ⚠️ Handles ORM objects?
                image_urls.append(img.url)
    elif isinstance(product.images, str):
        image_urls = [url.strip() for url in product.images.split(',')]
```

**Issues**:
- Handles list, dict, string, ORM objects - masks schema issues
- String fallback suggests legacy format still supported

**Etsy**: No image handling implementation (`etsy_product_conversion_service.py` - marked TODO)

**Recommended**: Standardize image extraction logic in shared utility

---

### 5. Poor Error Handling & Logging (High - Debugging)

**Severity**: 🟠 **HIGH**
**Impact**: Debugging difficult, silent failures

**Silent Failures**:
- `ebay_product_conversion_service.py:516` - JSON exceptions silently caught
- `vinted_product_helpers.py:92-93` - Logs warning but continues with empty photo_ids
- `ProductImageService:62, 75` - Raises ValueError but no logger.error()

**Missing Logging**:
- `file_service.py` - No logs on image validation failures
- `ebay_product_conversion_service.py:500-519` - JSON parsing failure not logged
- API error responses don't include context (user_id, product_id)

**No Metrics/Monitoring**:
- No counters for failed image uploads
- No timing metrics for image operations
- No alerts for orphaned R2 files
- No dashboard for job failure rates

**Recommended**: Add structured logging + metrics (Prometheus/Datadog)

---

## Medium Severity Issues

### 6. Security Concerns (Medium - Validation)

**Severity**: 🟡 **MEDIUM**
**Impact**: Potential XSS, malicious URLs

**Image URL Validation**:
- No URL validation in `ProductImageService.add_image()`
- Can store arbitrary URLs (malicious, external, etc.)
- No domain whitelist for R2 URLs

**File Upload Security**:
- `FileService._detect_image_format()` (line 48-75) - Magic byte validation ✓
- **BUT**: `_validate_and_optimize()` (line 132-150) - Filename only checked for extension
- Filename parsing: `file.filename.split(".")[-1].lower()` - can be spoofed

**Access Control**:
- Image URLs stored in plain JSONB
- No per-image permission checks
- API allows listing all images via product.images

**Recommended**: Add URL validation, domain whitelist, per-image access control

---

### 7. Performance & Scalability Issues (Medium - Performance)

**Severity**: 🟡 **MEDIUM**
**Impact**: Slow queries, high memory usage

**JSONB Array Operations**:
- `ProductImageService.reorder_images()` - Full list copy and rewrite
- No pagination support (max 20 hardcoded)
- `list()` conversion creates new Python list every operation
- **N+1 Risk**: Loading many products loads all images in memory

**Large File Service Issues**:
- `FileService.download_and_upload_from_url()` - Downloads entire image to memory
- No streaming/chunked upload for large images
- 10MB limit (before optimization) means retry = significant bandwidth

**Missing Indexes**:
- No index on `products.images` (JSONB columns rarely indexed)
- Product queries load full JSONB even when images not needed
- Could use `SELECT products.id, title, price` (without images column)

**Recommended**: Add pagination, streaming upload, JSONB indexing

---

### 8. Technical Debt & Code Quality (Medium - Maintainability)

**Severity**: 🟡 **MEDIUM**
**Impact**: Maintenance burden

**Large Files (>500 lines)**:
| File | Lines | Recommendation |
|------|-------|----------------|
| `vinted_order_sync.py` | 920 | Split order fetching, parsing, persistence |
| `ebay_fulfillment_client.py` | 836 | Split shipping, returns, cancellations |
| `marketplace_job_service.py` | 784 | Split job CRUD, query builder, batch logic |
| `product_service.py` | 713 | Split CRUD, validation, AI logic |

**Deprecated Code Still Active**:
- Migration file has DEPRECATED comment (line 130) - old images column reference
- `ebay_product_conversion_service.py:507` - TODO comment references removed table
- `vinted_job_processor.py` - Marked DEPRECATED (2026-01-09) but still imported

**Loose Type Handling**:
- `vinted_product_helpers.py:52-62` - Handles multiple types (suggests schema uncertainty)
- Mixed handling of JSONB (parsed) and JSON strings
- No type hints on JSONB columns in models

**Recommended**: Refactor large files, remove deprecated code, add type hints

---

### 9. Incomplete Marketplace Implementations (Medium - Feature Completeness)

**Severity**: 🟡 **MEDIUM**
**Impact**: Features not functional

**Etsy Missing Image Handling**:
- `etsy_product_conversion_service.py` - No image method implementation
- Line 83: TODO: "Upload images (TODO)"
- Uses images from product.images but no format conversion

**eBay Silent Failures**:
- Missing images causes empty list (line 519)
- Validation at line 279-282 checks for images but message vague
- No specific error about which images missing

**Vinted Complex Retry Logic**:
- `vinted_image_downloader.py:92-115` - Exponential backoff (3 retries)
- Works but lacks observability
- **Risk**: Silent image loss if all retries fail

**Recommended**: Complete Etsy implementation, add retry metrics

---

## Low Severity Issues

### 10. Migration Archiving Strategy (Low - Organization)

**Severity**: 🟢 **LOW**
**Impact**: Codebase organization

**Current State**:
- ~120 migrations (2025-12-07 to 2026-01-14)
- Archived: `migrations/archive_20260105/` (historical)
- No automated squashing

**CLAUDE.md Recommendation**:
- Squash at 200+ migrations
- Currently at 120 (60% of threshold)

**Recommended**: Monitor migration count, plan squash at 200

---

## Summary Table

| Concern | Severity | Impact | Affected Components | Estimated Fix |
|---------|----------|--------|---------------------|---------------|
| Label image data loss | 🔴 Critical | 611 products | Image services, converters | 2-3 days |
| Transaction race condition | 🔴 Critical | R2 storage leak | API images, ProductImageService | 1 day |
| Downgrade data loss | 🔴 Critical | Deployment risk | Migrations | 2 days |
| Inconsistent image handling | 🟠 High | Silent failures | eBay/Vinted/Etsy converters | 1-2 days |
| Poor error handling | 🟠 High | Debugging difficult | All image services | 2-3 days |
| Security concerns | 🟡 Medium | XSS, malicious URLs | FileService, API | 1-2 days |
| Performance issues | 🟡 Medium | Slow queries | JSONB operations | 2-3 days |
| Technical debt (file size) | 🟡 Medium | Maintenance | 4 large files | 3-5 days |
| Incomplete Etsy | 🟡 Medium | Missing features | Etsy services | 1 day |
| Migration count | 🟢 Low | Organization | Migrations | N/A (monitor) |

---

## Recommended Priority Order

1. **Immediate** (Critical):
   - Add `image_type` field to JSONB structure
   - Fix transaction handling race condition
   - Add migration verification + JSONB recovery

2. **Short-term** (High):
   - Standardize image handling across marketplaces
   - Add structured logging + error context
   - Complete Etsy image implementation

3. **Medium-term** (Medium):
   - Refactor large files (>700 lines)
   - Add image upload metrics/monitoring
   - Implement URL validation + domain whitelist
   - Add JSONB indexes for performance

4. **Long-term** (Low):
   - Monitor migration count
   - Plan migration squashing at 200+

---

*Last analyzed: 2026-01-14*
