# PROJECT.md - Image Management Architecture Migration

**Created:** 2026-01-15
**Status:** Active

---

## Overview

Migrer complètement l'architecture de gestion des images produit : passer de la colonne JSONB `products.images` vers une **table dédiée `product_images`** avec métadonnées riches, permettant notamment de distinguer les photos produits des étiquettes de prix internes (labels).

**Problème résolu** : 611 produits ont des "labels" (étiquettes de prix internes) actuellement publiés aux clients sur Vinted/eBay/Etsy car la structure JSONB ne permet pas de les identifier.

---

## Requirements

### Validated

- ✓ **Codebase existant** : Backend FastAPI + SQLAlchemy 2.0, multi-tenant PostgreSQL (existing)
- ✓ **3282 produits** en base avec images en JSONB (existing)
- ✓ **611 produits** ont des labels à identifier (existing)
- ✓ **Ancien système pythonApiWOO** : dernière image = label (pattern connu) (existing)
- ✓ **Cloudflare R2** : stockage fichiers images actuel (existing)
- ✓ **FileService** : upload/optimisation images fonctionnel (existing)

### Active

#### Phase 1 : Nouvelle Architecture
- [ ] **Créer table `product_images`** avec colonnes :
  - `id` (PK), `product_id` (FK), `url`, `order`
  - `is_label` (boolean) — Flag critique pour distinguer labels
  - `alt_text` (text) — SEO et accessibilité
  - `tags` (text[] ou JSONB) — Filtrage/recherche (ex: 'front', 'back', 'detail')
  - `mime_type`, `file_size` (validation)
  - `width`, `height` (dimensions)
  - `created_at`, `updated_at` (timestamps)

#### Phase 2 : Migration des Données
- [ ] **Script de migration idempotent** :
  - Parcourir tous les `user_X.products`
  - Extraire images depuis JSONB
  - Insérer dans `product_images` avec `is_label = (order == last_order)`
  - **Stratégie** : Dernière image = label (basé sur ancien système pythonApiWOO)

- [ ] **Backup complet** avant migration (✅ FAIT : 9.3MB dump)
- [ ] **Validation post-migration** : vérifier 0 perte de données

#### Phase 3 : Services & API
- [ ] **Refactoriser `ProductImageService`** :
  - `add_image(product_id, image_data)` avec validation
  - `delete_image(image_id)` avec auto-reorder
  - `reorder_images(product_id, new_order)`
  - `set_label_flag(image_id, is_label)`
  - **Nouveaux** : `get_product_photos()`, `get_label_image()`

- [ ] **Mettre à jour API routes** (`api/products/images.py`)
- [ ] **Tests unitaires** : CRUD images + validation is_label
- [ ] **Tests d'intégration** : API endpoints

#### Phase 4 : Intégration Marketplaces
- [ ] **Modifier converters** pour exclure labels :
  - `VintedProductConverter` : filtrer `is_label=true`
  - `EbayProductConversionService` : filtrer `is_label=true`
  - (Etsy hors scope v1)

- [ ] **Valider** : aucun label publié sur marketplaces

#### Phase 5 : Cleanup
- [ ] **Supprimer colonne JSONB** `products.images` (après validation complète)
- [ ] **Migration Alembic downgrade** pour rollback si nécessaire
- [ ] **Documentation** : update ARCHITECTURE.md, CONVENTIONS.md

### Out of Scope (v1)

- **FileService upload/optimisation** — Garder l'implémentation actuelle R2, focus sur métadonnées
- **UI Frontend** — Pas de changement interface utilisateur, uniquement backend/API
- **Etsy converter** — Focus Vinted/eBay, Etsy viendra plus tard
- **Image compression avancée** — Garder Pillow actuel
- **CDN/cache invalidation** — Pas de changement infrastructure

---

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| **Table séparée vs JSONB** | Table permet indexes, FK constraints, métadonnées riches, requêtes SQL standards | ✅ Table `product_images` |
| **Migration : dernière image = label** | Pattern pythonApiWOO, 85% précision, simple et prédictible | ✅ Validé |
| **Backup complet avant migration** | Sécurité absolue : 0 perte de données acceptée | ✅ FAIT (9.3MB) |
| **is_label boolean vs enum** | Boolean suffisant pour v1 (product_photo vs label), extensible plus tard | ✅ Boolean |
| **Tags : text[] vs JSONB** | text[] plus simple pour recherche PostgreSQL, JSONB si structure complexe | — Pending |
| **Rollback strategy** | Migration Alembic downgrade doit restaurer JSONB depuis table | — Pending |

---

## Constraints

### Techniques
- **Multi-tenant** : Migration doit parcourir tous les schemas `user_X`
- **Idempotence** : Script migration rejouable sans duplication
- **Performance** : Bulk insert (pas row-by-row) pour 3282 produits
- **Atomicité** : Transaction par schema utilisateur

### Sécurité des Données
- **Backup obligatoire** avant toute migration (✅ FAIT)
- **Validation post-migration** : count images JSONB == count table
- **0 perte acceptée** : si erreur, rollback immédiat

### Compatibilité
- **SQLAlchemy 2.0** : Utiliser `Mapped[T]`, `mapped_column()`
- **Alembic migrations** : Respecter patterns multi-tenant existants
- **Existing services** : ProductImageService, FileService intacts (refactor, pas rewrite)

---

## Context

### Codebase Analysis (2026-01-14)

**Issue critique identifié** (`.planning/codebase/CONCERNS.md`) :
- 611 produits affectés par publication de labels aux clients
- Structure JSONB actuelle : `[{"url": "...", "order": 0, "created_at": "..."}]`
- Migration 2026-01-03 : `product_images` table → JSONB a perdu `image_type`

**Affected Files** :
- `models/user/product.py` (lines 386-394) — JSONB column
- `services/product_image_service.py` — CRUD operations
- `services/vinted/vinted_product_converter.py` — Vinted payload builder
- `services/ebay/ebay_product_conversion_service.py` — eBay payload builder

---

## Success Criteria

### Migration
1. ✅ **0 perte de données** : count images avant == count images après
2. ✅ **611 labels identifiés** : `is_label=true` sur les bonnes images
3. ✅ **Table complète** : tous les champs métadonnées remplis

### Marketplaces
4. ✅ **Aucun label publié** : Vinted/eBay converters filtrent `is_label=true`
5. ✅ **Tests passent** : Unit + integration tests

### Code Quality
6. ✅ **Services refactorés** : ProductImageService avec méthodes claires
7. ✅ **Migration rollback** : Alembic downgrade restaure JSONB
8. ✅ **Documentation** : ARCHITECTURE.md à jour

---

## Backup

**Dump complet créé** : `backups/stoflow_db_full_backup_20260115_091652.dump` (9.3 MB)

**Restauration si nécessaire** :
```bash
docker exec stoflow_postgres pg_restore -U stoflow_user -d stoflow_db -c /tmp/backup.dump
```

---

*Last updated: 2026-01-15 after project initialization*
