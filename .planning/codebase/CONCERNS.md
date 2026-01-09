# Technical Concerns & Debt

## Priority Legend
- 🔴 **CRITICAL** - Security/data loss risk, must fix ASAP
- 🟠 **HIGH** - Functionality blocked, performance issues
- 🟡 **MEDIUM** - Quality/maintainability, technical debt
- 🟢 **LOW** - Nice-to-have, minor improvements

---

## 🔴 CRITICAL Issues

### Security

**JWT Algorithm Migration (TODO)**
- **Status**: Planned but not yet implemented
- **Current**: Using RS256 (good), but migration from HS256 incomplete
- **Risk**: Old HS256 algorithm more vulnerable to attacks
- **Action**: Complete migration, remove HS256 support
- **Location**: `services/auth_service.py`

**Token Expiry Configuration**
- **Status**: Access tokens last 15 minutes (good), but refresh handling incomplete
- **Risk**: Refresh token rotation not implemented
- **Action**: Implement refresh token rotation to prevent token replay attacks
- **Location**: `services/auth_service.py:create_refresh_token()`

**Irreversible Database Migration**
- **File**: `migrations/versions/20260107_1817_drop_deprecated_columns.py`
- **Risk**: Drops columns IRREVERSIBLY (`color`, `material`, `condition_sup`)
- **Issue**: No safe rollback if migration causes problems
- **Action**: Add data backup step or make reversible
- **Impact**: Potential data loss if rollback needed

**Hardcoded Development Origins in Production Code**
- **File**: `plugin/src/background/VintedActionHandler.ts:40-45`
- **Issue**: Development URLs (`http://localhost:3000`, `http://localhost:5173`) in production
- **Risk**: Security risk if shipped to production
- **Action**: Move to environment configuration, filter by NODE_ENV

### Data Integrity

**Missing Category Mapping**
- **Status**: Hardcoded category IDs in multiple places
- **Files**: `vinted_product_validator.py:135`, `etsy_mapper.py:164`
- **Risk**: Publishing products with incorrect categories
- **Action**: Implement dynamic category mapping system (blocked by PlatformMapping model)
- **Impact**: HIGH - Affects all marketplace integrations

---

## 🟠 HIGH Priority Issues

### Incomplete Implementations

**eBay Webhook Handlers** (6 TODOs)
- **Files**: `api/ebay_webhook.py` (lines 118, 140, 162, 186, 308, 339)
- **Missing**:
  - Order creation processing
  - Payment status updates
  - Product status synchronization
- **Impact**: Orders not automatically synced from eBay
- **Action**: Implement webhook handlers

**Etsy Polling Notifications** (3 TODOs)
- **File**: `services/etsy_polling_cron.py` (lines 143, 197, 251)
- **Missing**:
  - Notification system for new orders
  - Database synchronization
  - Stock level alerts
- **Impact**: Manual order checking required
- **Action**: Complete polling job with notifications

**Image Persistence Layer**
- **File**: `services/vinted/vinted_importer.py:317`
- **Status**: TODO - "Upload to Cloudinary/S3 via FileService"
- **Impact**: Images not persisted, lost on re-import
- **Action**: Implement R2 upload integration

**Pricing Configuration**
- **File**: `services/ebay/ebay_product_conversion_service.py:540`
- **Status**: TODO - "Load from user settings"
- **Issue**: All users use default pricing coefficients
- **Impact**: No user customization for pricing algorithms
- **Action**: Create user pricing settings model + UI

### Performance

**Large Files (>500 lines)**
| File | Lines | Impact | Action |
|------|-------|--------|--------|
| `marketplace_job_service.py` | 784 | Maintenance | Split into sub-modules |
| `product_service.py` | 713 | Complexity | Extract sub-services |
| `useVintedBridge.ts` | 671 | Hard to test | Refactor into smaller composables |
| `validators.py` | 628 | Monolithic | Split by domain (product, user, marketplace) |
| `create.vue` | 637 | Component bloat | Extract child components |

**Potential N+1 Queries**
- **Location**: Product model relationships (colors, materials, conditions, images)
- **Risk**: Lazy loading causing multiple queries
- **Action**: Add explicit `selectinload()` or `joinedload()` in repositories
- **File**: `models/user/product.py:451` - TODO comment present

---

## 🟡 MEDIUM Priority Issues

### Technical Debt

**Deprecated Code Still Active**
- **VintedJobProcessor** - Marked DEPRECATED (removal planned Feb 2026)
- **Dual-write phase**: `product_service.py` maintains old + new columns
- **Backward compatibility fields**: `product_schemas.py:87-108`
- **Action**: Complete migration cleanup after column drop

**TODO Comments** (29 found)
- **Business Logic**: 7 TODOs (pricing, SEO, category mapping)
- **Webhooks/Integration**: 9 TODOs (eBay, Etsy)
- **Infrastructure**: 3 TODOs (heartbeat, image storage)
- **Action**: Prioritize and address in next sprint

**Migration Count Approaching Threshold**
- **Current**: 86 migration files
- **Threshold**: 200 recommended before squashing
- **Status**: On track but monitor growth
- **Action**: Consider squashing when reaching 150+

### Code Quality

**Empty Exception Blocks**
- **File**: `shared/encryption.py`
- **Issue**: Bare `except:` catches all exceptions silently
- **Risk**: Errors hidden, debugging difficult
- **Action**: Add logging, re-raise specific exceptions

**Generic Exception Handling**
- **Pattern**: `except Exception as e:` used instead of specific exceptions
- **Files**: Multiple service files
- **Action**: Catch specific exceptions where possible

**Inconsistent Validation**
- **Issue**: Some endpoints validate in routes, others in services
- **Action**: Standardize validation at service layer

### Testing

**Test Coverage Gaps**
| Module | Coverage | Missing |
|--------|----------|---------|
| eBay webhook handlers | 0% | All webhook endpoints |
| Etsy polling | 0% | Polling job handlers |
| Plugin communication | 10% | WebSocket integration |
| Image services | 20% | Upload/sync logic |
| Large components | 30% | ProductCreate.vue (637 lines) |

**Test-to-Production Ratio**: 80 test files vs 478 production files (16.7%)

---

## 🟢 LOW Priority Issues

### Documentation

**Missing Documentation**:
- API endpoint documentation (OpenAPI auto-generated, but lacking examples)
- WebSocket event documentation
- Plugin message protocol specification
- Deployment runbook

**Stale Documentation**:
- Some CLAUDE.md sections reference old patterns

### Dependency Management

**Flexible Version Constraints**
- `google-genai>=1.0.0` - Could allow breaking changes
- `fastapi>=0.115.0` - Pin to minor version recommended

**Unused Dependencies**:
- Potential cleanup needed (requires audit)

### Code Organization

**Module Coupling**
- Frontend directly dependent on backend WebSocket implementation
- Plugin relay pattern adds latency
- **Optimization**: Consider direct backend ↔ plugin WebSocket

**Naming Inconsistencies**:
- Some files use `kebab-case.ts`, others `snake_case.py`
- Consistent within each ecosystem but not cross-platform

---

## Trends & Observations

### Positive Trends ✅
- **Active refactoring** (2026-01-09 unified marketplace jobs)
- **Security awareness improving** (XSS fixes, JWT migration planned)
- **Clean Architecture** well-established
- **Multi-tenant isolation** fixed (SET LOCAL)

### Concerning Trends ⚠️
- **TODO accumulation** (29 total, increasing)
- **Incomplete marketplace integrations** (webhooks, polling)
- **Test coverage lagging behind features**
- **Large file growth** (10+ files >500 lines)

### Deprecation Management 🔄
- **Good**: Deprecated code clearly marked
- **Issue**: Removal timeline unclear
- **Action**: Set hard deadlines for deprecation cleanup

---

## Recommended Action Plan

### Immediate (This Sprint)
1. ✅ Complete JWT algorithm migration (RS256)
2. ✅ Implement refresh token rotation
3. ✅ Add safe rollback for irreversible migration
4. ✅ Fix hardcoded development origins

### Short-Term (Next 2 Sprints)
1. Complete eBay webhook handlers
2. Implement Etsy polling notifications
3. Add image persistence layer
4. Refactor large files (>700 lines)

### Medium-Term (Next Quarter)
1. Implement user pricing configuration
2. Remove deprecated code (VintedJobProcessor)
3. Improve test coverage to 70%+
4. Add N+1 query optimization

### Long-Term (Next 6 Months)
1. Migration squashing (when reaching 150+)
2. Plugin direct WebSocket connection
3. Redis caching layer
4. Distributed tracing implementation

---

## Risk Assessment

| Risk Category | Level | Mitigation |
|---------------|-------|------------|
| Security (JWT, auth) | 🔴 CRITICAL | Immediate fixes required |
| Data Loss (migration) | 🔴 CRITICAL | Add backup/rollback |
| Incomplete Features | 🟠 HIGH | Prioritize webhooks, polling |
| Performance (N+1) | 🟡 MEDIUM | Monitor, optimize on demand |
| Technical Debt | 🟡 MEDIUM | Allocate 20% sprint capacity |
| Documentation | 🟢 LOW | Update as features ship |

---
*Last updated: 2026-01-09 after codebase mapping*
