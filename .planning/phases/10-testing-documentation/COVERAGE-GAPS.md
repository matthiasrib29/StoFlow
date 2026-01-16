# Test Coverage Gaps Analysis

**Date:** 2026-01-16
**Phase:** 10-01 - Test Coverage Audit

## Overall Coverage

- **Total Coverage:** 51.1%
- **Total Statements:** 16,109
- **Total Covered:** 8,227
- **Total Missing:** 7,882

**Files Summary:**
- ✅ Files with >=80% coverage: 126
- ❌ Files needing work (<80%): 124

---

## 🔴 CRITICAL GAPS (<50% coverage)

### Priority 1: Zero Coverage (0%)

These files have **no test coverage** and should be prioritized:

#### Marketplace Handlers (New Pattern - Phase 7-9)
- `services/marketplace/handlers/base_handler.py` (93 lines)
- `services/marketplace/handlers/base_publish_handler.py` (92 lines)
- `services/marketplace/handlers/vinted/publish_handler.py` (71 lines)
- `services/marketplace/handlers/vinted/link_product_handler.py` (106 lines)

#### Job Services
- `services/vinted/vinted_job_stats_service.py` (57 lines) - Phase 8
- `services/vinted/vinted_job_status_manager.py` (89 lines)
- `services/marketplace/job_cleanup_service.py` (37 lines)
- `services/marketplace/job_cleanup_scheduler.py` (80 lines)

#### Repositories
- `repositories/category_mapping_repository.py` (113 lines)

#### Other Services
- `services/attribute_mapping_service.py` (66 lines)
- `services/marketplace_http_helper.py` (32 lines)
- `services/ebay/ebay_adapter.py` (17 lines)
- `services/ebay/ebay_identity_client.py` (38 lines)
- `services/etsy_polling_cron.py` (128 lines)

#### Models
- `models/user/pending_instruction.py` (18 lines)

### Priority 2: Very Low Coverage (< 20%)

#### Vinted Services (Phase 6)
- `services/vinted/vinted_order_sync.py` - 8.8% (333/365 missing)
- `services/vinted/vinted_bordereau_service.py` - 11.6% (114/129 missing)
- `services/vinted/vinted_api_sync.py` - 13.1% (139/160 missing)
- `services/vinted/vinted_product_enricher.py` - 13.6% (114/132 missing)
- `services/vinted/description/section_builder.py` - 15.6% (108/128 missing)
- `services/vinted/vinted_item_upload_parser.py` - 17.2% (72/87 missing)
- `services/vinted/vinted_inbox_sync_service.py` - 18.1% (68/83 missing)
- `services/vinted/vinted_conversation_service.py` - 18.8% (108/133 missing)

#### eBay Services
- `services/ebay/ebay_fulfillment_client.py` - 13.2% (118/136 missing)
- `services/ebay/ebay_dashboard_service.py` - 14.5% (141/165 missing)
- `services/ebay/ebay_inquiry_service.py` - 15.3% (161/190 missing)
- `services/ebay/ebay_account_parser.py` - 16.4% (56/67 missing)
- `services/ebay/ebay_cancellation_sync_service.py` - 17.2% (101/122 missing)
- `services/ebay/ebay_aspect_value_service.py` - 17.3% (86/104 missing)
- `services/ebay/ebay_payment_dispute_service.py` - 17.4% (147/178 missing)
- `services/ebay/ebay_gpsr_compliance.py` - 17.9% (32/39 missing)
- `services/ebay/ebay_refund_service.py` - 18.2% (121/148 missing)
- `services/ebay/ebay_oauth_service.py` - 19.3% (92/114 missing)
- `services/ebay/ebay_inquiry_client.py` - 19.3% (71/88 missing)

#### Etsy Services
- `services/etsy/etsy_product_conversion_service.py` - 14.3% (102/119 missing)
- `services/etsy/etsy_polling_service.py` - 18.7% (61/75 missing)
- `services/etsy/etsy_base_client.py` - 19.8% (97/121 missing)

#### Other Services
- `services/product_text_generator.py` - 16.3% (175/209 missing)
- `services/ai/vision_service.py` - 17.8% (198/241 missing)

### Priority 3: Low Coverage (20-50%)

#### Vinted Services (Phase 6-7)
- `services/vinted/vinted_job_service.py` - 21.4% (143/182 missing)
- `services/vinted/vinted_sync_service.py` - 21.9% (146/187 missing) - Phase 7
- `services/vinted/vinted_data_extractor.py` - 21.6% (109/139 missing)
- `services/vinted/vinted_link_service.py` - 22.7% (58/75 missing)
- `services/vinted/vinted_image_downloader.py` - 21.6% (40/51 missing)
- `services/vinted/vinted_image_sync_service.py` - 23.6% (55/72 missing)
- `services/vinted/vinted_importer.py` - 23.7% (74/97 missing)
- `services/vinted/vinted_adapter.py` - 26.4% (53/72 missing)
- `services/vinted/vinted_stats_service.py` - 28.2% (28/39 missing)
- `services/vinted/vinted_product_helpers.py` - 28.8% (37/52 missing)
- `services/vinted/vinted_description_service.py` - 44.2% (24/42 missing)

#### Vinted Job Handlers (Phase 7)
- `services/vinted/jobs/message_job_handler.py` - 26.5% (36/49 missing)
- `services/vinted/jobs/orders_job_handler.py` - 30.2% (30/43 missing)
- `services/vinted/jobs/sync_job_handler.py` - 33.3% (24/36 missing)
- `services/vinted/jobs/link_product_job_handler.py` - 35.3% (22/34 missing)

#### eBay Services
- `services/ebay/ebay_publication_service.py` - 20.0% (64/80 missing)
- `services/ebay/ebay_marketing_client.py` - 20.3% (47/59 missing)
- `services/ebay/ebay_analytics_client.py` - 21.1% (30/38 missing)
- `services/ebay/ebay_cancellation_service.py` - 21.8% (79/101 missing)
- `services/ebay/ebay_order_fulfillment_service.py` - 26.0% (57/77 missing)
- `services/ebay/ebay_product_conversion_service.py` - 30.8% (101/146 missing)
- `services/ebay/ebay_taxonomy_client.py` - 35.5% (20/31 missing)
- `services/ebay/ebay_account_client.py` - 40.7% (35/59 missing)
- `services/ebay/ebay_offer_client.py` - 42.1% (24/43 missing)
- `services/ebay/ebay_oauth_config.py` - 47.2% (19/36 missing)

#### eBay Job Handlers (Phase 4)
- `services/ebay/jobs/ebay_publish_job_handler.py` - 34.5% (19/29 missing)
- `services/ebay/jobs/ebay_update_job_handler.py` - 34.5% (19/29 missing)
- `services/ebay/jobs/ebay_delete_job_handler.py` - 35.7% (18/28 missing)
- `services/ebay/jobs/ebay_sync_job_handler.py` - 38.5% (16/26 missing)

#### Etsy Services
- `services/etsy/etsy_publication_service.py` - 21.2% (52/66 missing)
- `services/etsy/etsy_receipt_client.py` - 26.9% (19/26 missing)
- `services/etsy/etsy_taxonomy_client.py` - 35.0% (13/20 missing)
- `services/etsy/etsy_listing_client.py` - 35.9% (41/64 missing)

#### Etsy Job Handlers (Phase 5)
- `services/etsy/jobs/etsy_publish_job_handler.py` - 35.7% (18/28 missing)
- `services/etsy/jobs/etsy_update_job_handler.py` - 34.5% (19/29 missing)
- `services/etsy/jobs/etsy_delete_job_handler.py` - 35.7% (18/28 missing)
- `services/etsy/jobs/etsy_sync_job_handler.py` - 38.5% (16/26 missing)
- `services/etsy/jobs/etsy_orders_sync_job_handler.py` - 40.0% (15/25 missing)

#### Marketplace Unified System (Phase 9)
- `services/marketplace/marketplace_job_processor.py` - 23.5% (55/72 missing)
- `services/marketplace/marketplace_job_service.py` - 38.2% (134/217 missing)

#### Other Services
- `services/validators.py` - 21.3% (137/174 missing)
- `services/user_schema_service.py` - 22.7% (51/66 missing)
- `services/websocket_service.py` - 25.3% (65/87 missing)
- `services/r2_service.py` - 26.5% (75/102 missing)
- `services/category_service.py` - 25.0% (33/44 missing)
- `services/ai_credit_pack_service.py` - 34.7% (32/49 missing)
- `services/product_status_manager.py` - 39.0% (36/59 missing)
- `services/product_utils.py` - 38.5% (8/13 missing)
- `services/datadome_scheduler.py` - 36.9% (41/65 missing)
- `services/plugin_task_rate_limiter.py` - 47.8% (24/46 missing)

#### Repositories
- `repositories/vinted_job_repository.py` - 38.4% (69/112 missing)
- `repositories/product_repository.py` - 38.8% (60/98 missing)
- `repositories/ebay_payment_dispute_repository.py` - 20.4% (90/113 missing)
- `repositories/vinted_conversation_repository.py` - 34.6% (85/130 missing)
- `repositories/ebay_order_repository.py` - 34.9% (56/86 missing)
- `repositories/ebay_cancellation_repository.py` - 40.0% (60/100 missing)
- `repositories/vinted_error_log_repository.py` - 40.7% (51/86 missing)
- `repositories/ebay_inquiry_repository.py` - 41.3% (54/92 missing)
- `repositories/ebay_return_repository.py` - 41.4% (51/87 missing)
- `repositories/user_repository.py` - 42.2% (59/102 missing)
- `repositories/vinted_product_repository.py` - 42.6% (54/94 missing)
- `repositories/ai_credit_pack_repository.py` - 44.7% (26/47 missing)
- `repositories/ebay_refund_repository.py` - 44.9% (54/98 missing)
- `repositories/product_attribute_repository.py` - 46.9% (78/147 missing)

#### Models
- `models/public/category.py` - 41.8% (32/55 missing)

---

## 🟡 NEEDS IMPROVEMENT (50-80% coverage)

These files have moderate coverage but don't meet the 80% target:

### Services
- `services/plugin_websocket_helper.py` - 52.4% (10/21 missing)
- `services/etsy/etsy_adapter.py` - 52.9% (8/17 missing)
- `services/ebay/ebay_inventory_client.py` - 55.2% (13/29 missing)
- `services/ebay/ebay_importer.py` - 55.6% (106/239 missing)
- `services/etsy/etsy_shop_client.py` - 57.1% (6/14 missing)
- `services/etsy/etsy_shipping_client.py` - 60.0% (4/10 missing)
- `services/pricing_service.py` - 64.9% (34/97 missing)
- `services/vinted/vinted_mapping_service.py` - 71.6% (46/162 missing)
- `services/auth_service.py` - 71.7% (60/212 missing)

### Repositories
- `repositories/model_repository.py` - 54.3% (16/35 missing)
- `repositories/brand_group_repository.py` - 54.8% (14/31 missing)

### Models
- `models/user/vinted_connection.py` - 61.3% (29/75 missing)
- `models/public/ebay_aspect_mapping.py` - 63.6% (12/33 missing)
- `models/user/ebay_payment_dispute.py` - 66.3% (28/83 missing)
- `models/public/ebay_marketplace_config.py` - 66.7% (8/24 missing)
- `models/user/ebay_promoted_listing.py` - 71.4% (14/49 missing)
- `models/public/ebay_category_mapping.py` - 77.8% (6/27 missing)

---

## ✅ WELL-COVERED (>=80% coverage)

**126 files** meet the 80% coverage target, including:
- Most unit test modules in `tests/unit/`
- Core services with good test coverage from earlier phases
- Most models in `models/public/` and `models/user/`
- Several repositories with comprehensive tests

---

## Recommended Testing Strategy

### Phase 10-01 Focus (Current Plan)

Based on the gaps analysis, prioritize testing in this order:

1. **Zero Coverage Files** (Priority 1)
   - Start with new handler pattern files (Phase 7-9)
   - Focus on job services and repositories

2. **Services from Phases 6-9** (Priority 2-3)
   - Vinted services extraction (Phase 6)
   - Handler refactoring (Phases 4-7)
   - Stats system (Phase 8)
   - Unified marketplace system (Phase 9)

3. **Critical Business Logic** (Priority 2-3)
   - validators.py
   - product_text_generator.py
   - auth_service.py

### Target for Phase 10-01

Realistically achievable in this plan:
- Bring **0% coverage files to >50%** (handlers, core services)
- Bring **<20% files to >50%** (selected critical services)
- Focus on **Phases 6-9 services** (most recent refactoring work)

Expected outcome:
- **Overall coverage: 51.1% → 65-70%**
- **Files needing work: 124 → 60-80**

### What to Test

#### Services (Most Important)
- Mock external dependencies (WebSocket, HTTP APIs)
- Test public API only (not private helpers)
- Success paths + error paths
- Following Phase 7 test patterns

#### Repositories
- Mock database session
- Test CRUD operations
- Test query filters

#### Models
- Test relationships
- Test property methods
- Test validation

### What NOT to Test (Out of Scope)

- Private methods (prefixed with `_`)
- Database internals (SQLAlchemy behavior)
- External API calls (integration tests in Phase 10-02)
- Handlers themselves (Phase 7 already tested)

---

## Next Steps

1. ✅ Coverage audit complete
2. ⏳ Write unit tests for prioritized services (Task 2)
3. → Phase 10-02: Integration tests
4. → Phase 10-03: Documentation

---

*Generated: 2026-01-16 09:23 UTC*
*Command: `pytest --cov=services --cov=models --cov=repositories --cov-report=html`*
