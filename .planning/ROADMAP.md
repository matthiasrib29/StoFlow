# Roadmap: Multi-Tenant Schema Migration

## Overview

Migration de l'architecture multi-tenant StoFlow depuis `SET LOCAL search_path` (fragile, perdu après COMMIT/ROLLBACK) vers `schema_translate_map` (robuste, persistant). Cette migration élimine une source majeure de bugs d'isolation tenant et améliore la compatibilité avec les pools de connexions.

## Domain Expertise

- ./.claude/skills/expertise/sqlalchemy/SKILL.md (si existe)
- Backend CLAUDE.md pour patterns multi-tenant

Or: None (patterns établis dans la documentation SQLAlchemy)

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

- [x] **Phase 1: Préparation Modèles Tenant** - Ajouter placeholder schema "tenant" aux 20 modèles user/ ✅
- [x] **Phase 2: Session Factory & Dependencies** - Implémenter schema_translate_map dans get_user_db() ✅
- [ ] **Phase 3: Migration Requêtes text()** - Convertir 28 fichiers avec requêtes SQL brutes
- [ ] **Phase 4: Nettoyage Code Legacy** - Supprimer fonctions SET search_path obsolètes
- [ ] **Phase 5: Tests & Validation** - Vérifier isolation multi-tenant et rollback

## Phase Details

### Phase 1: Préparation Modèles Tenant
**Goal**: Ajouter `__table_args__ = {"schema": "tenant"}` à tous les modèles dans `models/user/`
**Depends on**: Nothing (foundation phase)
**Research**: Unlikely (established SQLAlchemy pattern)
**Plans**: 2 plans

Plans:
- [x] 01-01: Modifier modèles principaux (product, vinted_*, marketplace_*) ✅ 2026-01-13
- [x] 01-02: Modifier modèles secondaires (ebay_*, etsy_*, ai_*, pending_*) ✅ 2026-01-13

**Files (20)**:
```
models/user/
├── product.py
├── vinted_product.py
├── vinted_connection.py
├── vinted_conversation.py
├── vinted_error_log.py
├── vinted_job_stats.py
├── marketplace_job.py
├── marketplace_task.py
├── batch_job.py
├── ebay_product.py
├── ebay_credentials.py
├── ebay_order.py
├── ebay_product_marketplace.py
├── ebay_promoted_listing.py
├── etsy_credentials.py
├── ai_generation_log.py
├── pending_instruction.py
├── product_attributes_m2m.py
└── publication_history.py
```

---

### Phase 2: Session Factory & Dependencies
**Goal**: Implémenter `schema_translate_map` dans la création de sessions
**Depends on**: Phase 1
**Research**: Unlikely (SQLAlchemy documentation clear)
**Plans**: 2 plans

Plans:
- [x] 02-01: Modifier shared/database.py - Ajouter get_tenant_schema() et helpers ✅ 2026-01-13
- [x] 02-02: Modifier api/dependencies/__init__.py - Remplacer SET par schema_translate_map ✅ 2026-01-13

**Key Change**:
```python
# AVANT (fragile)
db.execute(text(f"SET LOCAL search_path TO {schema_name}, public"))

# APRÈS (robuste)
db = db.execution_options(schema_translate_map={"tenant": schema_name})
```

---

### Phase 3: Migration Requêtes text()
**Goal**: Supprimer les appels deprecated `set_user_search_path()`, `schema_utils` et `SET search_path`
**Depends on**: Phase 2
**Research**: Unlikely (refactoring patterns)
**Plans**: 3 plans

Plans:
- [x] 03-01: Remove set_user_search_path from API files (6 files) ✅ 2026-01-13
- [x] 03-02: Remove schema_utils from services (9 files) ✅ 2026-01-13
- [x] 03-03: Migrate schedulers, scripts & remaining files (10 files) ✅ 2026-01-13

**Strategies**:
1. **Routes API avec get_user_db()**: Supprimer appels redundants (schema déjà configuré)
2. **Services avec schema_utils**: Remplacer par simple commit()/rollback()
3. **Schedulers itérant schemas**: Utiliser execution_options(schema_translate_map=...)

**Files identified (24+)**:
```
api/
├── vinted/messages.py
├── vinted/orders.py
├── vinted/products.py
├── vinted/publishing.py
├── products/ai.py
├── ebay/orders.py
├── ebay/products.py
└── dependencies/__init__.py

services/
├── marketplace/job_cleanup_scheduler.py
├── marketplace/marketplace_job_processor.py
├── etsy_polling_cron.py
├── ai/vision_service.py
├── datadome_scheduler.py
└── vinted/vinted_product_enricher.py

scripts/
├── cleanup_abandoned_drafts.py
├── migrate_existing_jobs_to_batch.py
├── migrate_from_pythonapiwoo.py
└── migrate_oauth_tokens_encryption.py

migrations/
├── versions/20260106_*.py
└── env.py

tests/
├── conftest.py
├── unit/api/test_dependencies.py
└── integration/api/*.py
```

---

### Phase 4: Nettoyage Code Legacy
**Goal**: Supprimer tout le code `SET search_path` obsolète
**Depends on**: Phase 3
**Research**: Unlikely (deletion task)
**Plans**: 1 plan

Plans:
- [ ] 04-01: Supprimer fonctions et appels SET search_path

**Functions to Remove**:
```python
# shared/database.py
- set_search_path_safe()
- set_user_schema()
- set_user_search_path()

# shared/schema_utils.py
- restore_search_path()
- restore_search_path_after_rollback()
- commit_and_restore_path()
- SchemaManager class
```

**Grep pattern for verification**:
```bash
grep -r "set_search_path\|restore_search_path\|SET.*search_path" --include="*.py" backend/
```

---

### Phase 5: Tests & Validation
**Goal**: Vérifier que l'isolation multi-tenant fonctionne parfaitement
**Depends on**: Phase 4
**Research**: Unlikely (testing patterns established)
**Plans**: 2 plans

Plans:
- [ ] 05-01: Tests unitaires - Vérifier schema_translate_map sur modèles
- [ ] 05-02: Tests d'intégration - Vérifier isolation après COMMIT/ROLLBACK

**Test Scenarios**:
1. ✓ Modèles utilisent correct schema après création session
2. ✓ Schema persiste après `db.commit()`
3. ✓ Schema persiste après `db.rollback()`
4. ✓ Deux users simultanés restent isolés
5. ✓ Requêtes `text()` utilisent correct schema
6. ✓ Connection pool ne pollue pas entre requests

---

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Préparation Modèles | 2/2 | ✅ Complete | 2026-01-13 |
| 2. Session Factory | 2/2 | ✅ Complete | 2026-01-13 |
| 3. Migration text() | 3/3 | ✅ Complete | 2026-01-13 |
| 4. Nettoyage Legacy | 0/1 | Not started | - |
| 5. Tests & Validation | 0/2 | Not started | - |

---

## Comparison: Before vs After

| Aspect | SET search_path (Before) | schema_translate_map (After) |
|--------|--------------------------|------------------------------|
| Survie COMMIT | ❌ Perdu | ✅ Persistant |
| Survie ROLLBACK | ❌ Perdu | ✅ Persistant |
| PgBouncer | ❌ Transaction mode only | ✅ Tous modes |
| Sécurité | ⚠️ SQL injection risk | ✅ Paramétré |
| Debug | ❌ Invisible dans SQL | ✅ Schema visible |
| Maintenabilité | ❌ restore_* partout | ✅ Déclaratif |

---

## Success Criteria

- [x] Tous les modèles `user/` ont `schema: "tenant"` placeholder ✅
- [x] `get_user_db()` utilise `schema_translate_map` au lieu de `SET` ✅
- [ ] Aucun appel `SET search_path` ne reste dans le code
- [ ] Tests prouvent que schema persiste après COMMIT et ROLLBACK
- [ ] Vinted sync fonctionne sans erreur "relation does not exist"

---

*Roadmap created: 2026-01-13*
