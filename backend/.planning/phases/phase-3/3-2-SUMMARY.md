# PLAN 3.2 SUMMARY - Refactor ProductImageService to Use Table

**Phase:** 3 - Services & API
**Plan:** 3.2 - Refactor ProductImageService to Use Table
**Status:** ✅ Complete
**Completed:** 2026-01-15

---

## Objective

Refactor ProductImageService to use the new `product_images` table instead of JSONB, while maintaining backward compatibility and adding new methods for label handling.

---

## Tasks Completed

### ✅ Task 1: Refactored `add_image()` Method
- **Commit:** 281c0f4
- **Changes:**
  - Uses ProductImageRepository.create() instead of JSONB manipulation
  - Accepts `**kwargs` for metadata (mime_type, file_size, width, height, alt_text, tags)
  - Returns dict with rich metadata (backward compatible with old API format)
  - db.flush() instead of db.commit() (caller controls transaction)

### ✅ Task 2: Refactored `delete_image()` Method
- **Commit:** 281c0f4
- **Changes:**
  - Uses ProductImageRepository.delete() to remove image from table
  - Auto-reorders remaining images after deletion (gap filling)
  - Commits at service level

### ✅ Task 3: Refactored `reorder_images()` Method
- **Commit:** 281c0f4
- **Changes:**
  - Uses ProductImageRepository.update_order() for each image
  - Validates all URLs belong to product
  - Returns list of dicts (API format) with updated orders

### ✅ Task 4: Refactored `get_images()` and `get_image_count()`
- **Commit:** 281c0f4
- **Changes:**
  - get_images() uses ProductImageRepository.get_by_product()
  - get_image_count() counts table rows instead of JSONB array length
  - Both methods return same format as before (backward compatible)

### ✅ Task 5: Added New Methods for Photo/Label Distinction
- **Commit:** 281c0f4
- **New Methods:**
  1. `get_product_photos()` - Returns only photos (is_label=False), for marketplace publishing
  2. `get_label_image()` - Returns label image (is_label=True), or None if not exists
  3. `set_label_flag()` - Toggle is_label flag with business rule: only one label per product

### ✅ Task 6: Added Helper Function `_image_to_dict()`
- **Commit:** 281c0f4
- **Changes:**
  - Converts ProductImage model to dict for API responses
  - Includes all fields: id, url, order, is_label, alt_text, tags, mime_type, file_size, width, height, created_at, updated_at

### ✅ Task 7: Updated Unit Tests
- **Commit:** 281c0f4
- **Changes:**
  - Refactored all existing tests to use ProductImageRepository mocks
  - Added fixtures for ProductImage instances (mock_product_images, mock_product_images_with_label)
  - Added new test cases:
    - `test_add_image_with_metadata()` - Metadata fields saved
    - `test_get_product_photos_filters_labels()` - Only photos returned
    - `test_get_label_image_returns_single()` - Label returned or None
    - `test_set_label_flag_unsets_previous()` - Only one label per product
    - `test_set_label_flag_image_not_found()` - Error handling
    - `test_set_label_flag_wrong_product()` - Error handling

---

## Technical Details

### Architecture Changes

**Before (JSONB-based):**
```python
# Read product.images JSONB
images = product.images or []
# Append/modify JSONB dict
images.append({"url": url, "order": 0})
product.images = images
db.commit()
```

**After (Table-based):**
```python
# Use repository for CRUD operations
image = ProductImageRepository.create(db, product_id, url, order)
db.flush()
# Return dict for backward compatibility
return _image_to_dict(image)
```

### Backward Compatibility

- ✅ All methods return dicts (same format as before)
- ✅ API routes don't need changes yet (Phase 3.3)
- ✅ JSONB column (`product.images`) still intact until Phase 5

### Business Rules Enforced

1. **Maximum 20 images per product** (Vinted limit)
2. **Cannot add images to SOLD products**
3. **Auto-calculate display_order** when not provided
4. **Auto-reorder after deletion** (gap filling)
5. **Only one label per product** (set_label_flag unsets previous label)

---

## Success Validation

**Checklist:**
- ✅ All existing methods work with new table
- ✅ New methods (get_product_photos, get_label_image, set_label_flag) implemented
- ✅ Unit tests updated and passing (17 tests)
- ✅ Backward compatibility maintained (returns same dict format)
- ✅ JSONB column untouched (still contains old data)

**Ready for Phase 3.3:**
- ProductImageService fully refactored to use table
- API routes can be updated to use new service methods
- Marketplace converters can use `get_product_photos()` to filter labels

---

## Files Modified

1. `backend/services/product_image_service.py` - Service refactored (344 lines)
2. `backend/tests/unit/services/test_product_image_service.py` - Tests updated (676 lines)

---

## Next Steps

**Phase 3.3** - Update API routes and response schemas:
1. Update `/products/{id}/images` endpoints to use new service methods
2. Add `/products/{id}/images/photos` endpoint (marketplace publishing)
3. Add `/products/{id}/images/label` endpoint (label management)
4. Update response schemas to include new metadata fields

---

*Summary created: 2026-01-15*
