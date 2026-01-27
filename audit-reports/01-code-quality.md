# Rapport d'Audit - Qualité du Code

**Projet**: StoFlow (Monorepo: Backend FastAPI + Frontend Nuxt.js + Plugin Browser Extension)
**Date d'analyse**: 2026-01-27
**Scope**: `/home/maribeiro/StoFlow-improve-price-algo/`

---

## Résumé Exécutif

- **Total de problèmes identifiés**: 127+
- **Critiques**: 8
- **Haute priorité**: 34
- **Moyenne priorité**: 52
- **Basse priorité**: 33+

### Top 3 zones nécessitant attention

1. **Fichiers trop volumineux** (backend) - Plusieurs fichiers dépassent largement la limite de 500 lignes
2. **Print statements** - 185 fichiers contiennent des `print()` au lieu de logging approprié
3. **TODOs/FIXMEs oubliés** - 70+ TODOs dans le backend, certains sans contexte ou ticket associé

---

## Problèmes CRITIQUES

### 1. Fichiers excessivement longs (Backend)

| Fichier | Lignes | Limite | Dépassement |
|---------|--------|--------|-------------|
| `backend/migrations/versions/20260105_0001_initial_schema_complete.py` | 1581 | 500 | +1081 (316%) |
| `backend/services/vinted/vinted_order_sync.py` | 1059 | 500 | +559 (212%) |
| `backend/services/product_text_generator.py` | 1014 | 500 | +514 (203%) |
| `backend/temporal/activities/vinted_activities.py` | 974 | 500 | +474 (195%) |
| `backend/services/ebay/ebay_importer.py` | 881 | 500 | +381 (176%) |

**Sévérité**: CRITIQUE
**Impact**: Maintenabilité très dégradée, difficulté à comprendre et tester le code
**Recommandation**: Refactoriser immédiatement en extraisant des classes/fonctions séparées

### 2. Print statements au lieu de logging

**Fichiers affectés**: 185 fichiers
**Impact**: Debugging difficile en production, pas de niveaux de log, sortie non structurée
**Recommandation**: Remplacer TOUS les `print()` par `logger.info()`, `logger.debug()`, etc.

### 3. Duplication de logique d'extraction de données

**Fichiers concernés**:
- `backend/services/vinted/vinted_order_sync.py`
- `backend/services/vinted/vinted_data_extractor.py`

**Lignes dupliquées**:
- `_extract_invoice_pricing()` (L90-103)
- `_parse_amount()` (L971-985)
- Logique de parsing de dates répétée 5+ fois

**Impact**: Bugs potentiels si une copie est corrigée mais pas l'autre
**Recommandation**: Centraliser dans `VintedDataExtractor`

### 4. Code mort détecté - Colonne 'batch_id' dans MarketplaceJob

**Fichier**: `backend/services/marketplace/marketplace_job_service.py`
**Lignes**: 150, 204
**Impact**: Confusion du code, paramètre inutile transmis
**Recommandation**: Supprimer complètement le paramètre `batch_id` et mettre à jour tous les appelants

### 5. Logique métier complexe sans tests unitaires

**Fichier**: `backend/services/product_service.py`
**Méthode**: `update_product()` (L299-462, 163 lignes)
**Complexité**: Gestion M2M, optimistic locking, conditions imbriquées (3+ niveaux)
**Recommandation**: Extraire `ProductM2MManager` et `ProductUpdateValidator`

### 6. Gestion d'erreurs avec bare `except Exception`

**Fichier**: `backend/services/vinted/vinted_order_sync.py`
**Méthodes**: `_fetch_transaction_details()`, `_fetch_invoices_page()`
**Recommandation**: Attraper exceptions spécifiques, implémenter retry avec backoff

### 7. Anti-pattern: Commits multiples dans une transaction

**Fichier**: `backend/services/vinted/vinted_order_sync.py`
**Méthode**: `_process_and_save_order()` (L188, 200)
**Recommandation**: Supprimer `db.commit()` de la méthode, utiliser `db.flush()`, laisser l'appelant gérer la transaction

---

## Problèmes HAUTE PRIORITÉ

### 1. TODOs sans contexte ou tickets associés

**Total**: 70+ TODOs dans le backend

**Exemples critiques**:
- `backend/api/ebay_webhook.py:118` - `TODO: Créer/mettre à jour EbayOrder dans DB`
- `backend/api/ebay_webhook.py:140` - `TODO: Mettre à jour statut paiement`
- `backend/api/ebay_webhook.py:162` - `TODO: Mettre à jour statut produit`
- `backend/models/user/marketplace_task.py:78` - `TODO(2026-01-16): Re-enable when 'position' column is added`

**Recommandation**: Créer un ticket GitHub pour chaque TODO, supprimer les obsolètes

### 2. Imports potentiellement inutilisés

**Estimation**: 15-20% des 3500+ imports dans le backend
**Recommandation**: Exécuter `autoflake` ou `pylint`

### 3. Fonctions trop longues

- `sync_orders()` dans `vinted_order_sync.py` (L307-401, 95 lignes, complexité cyclomatique ~15+)
- Duplication ~85% entre `sync_orders()` et `sync_purchases()` (L403-496)

**Recommandation**: Extraire `_sync_orders_generic(order_type)` et factoriser

### 4. Magic numbers et strings hardcodés

**Exemple**: `per_page=100` dans `vinted_order_sync.py:781` sans explication
**Recommandation**: Extraire en constantes nommées

### 5. Méthodes dépréciées encore présentes

**Fichier**: `backend/services/marketplace/marketplace_job_service.py`
- `create_batch_jobs()` (L170-215) - marqué deprecated
- `_update_job_stats()` (L738-744) - no-op
- `get_stats()` (L746-752) - no-op

**Recommandation**: Identifier les appelants, migrer, puis supprimer

---

## Problèmes MOYENNE PRIORITÉ

### 1. Inconsistances de nommage
- Certaines constantes en lowercase au lieu de UPPER_SNAKE_CASE
- Commentaires/docstrings mélangés français/anglais

### 2. Manque de type hints sur méthodes helper privées

### 3. Conditions imbriquées excessives (3+ niveaux)
- `update_product()` dans `product_service.py`
- Recommandation: Early returns et guard clauses

### 4. Pattern try-except-return None masque les erreurs
- Multiple méthodes dans `vinted_order_sync.py`
- L'appelant ne peut pas distinguer "pas de données" vs "erreur réseau"

### 5. Absence de pagination sur requêtes potentiellement volumineuses
- `get_job_tasks()` charge tout en mémoire sans limit

### 6. Classes avec uniquement des @staticmethod
- `ProductService` - toutes les méthodes sont statiques
- Documenter le pattern ou ajouter `__init__(self, db: Session)`

---

## Problèmes BASSE PRIORITÉ

- TODOs avec dates passées à vérifier
- Frontend TODOs peu prioritaires (demo modal, localStorage cleanup)
- Absence de `.editorconfig`
- Absence de métriques/observability (Prometheus, OpenTelemetry)
- Tests manuels dans `/backend/tests/_manual/` à convertir ou supprimer

---

## Score de Dette Technique

| Module | Score | Niveau |
|--------|-------|--------|
| **Backend** | 6.5/10 | MOYEN |
| **Frontend** | 8/10 | FAIBLE |
| **Plugin** | 9/10 | TRÈS FAIBLE |
| **Global** | **7.2/10** | **MOYEN** |

### Contributeurs principaux à la dette
1. Fichiers > 500 lignes : -1.5 points
2. Print statements (185 fichiers) : -1.0 point
3. TODOs non résolus (70+) : -0.8 point
4. Duplication de code : -0.7 point
5. Complexité des méthodes : -0.5 point

---

## Plan d'Action Recommandé

### Phase 1 : CRITIQUE
1. Remplacer tous les `print()` par logger
2. Refactoriser les 5 plus gros fichiers
3. Corriger les bugs de transaction (`db.commit()` en boucle → `db.flush()`)

### Phase 2 : HAUTE PRIORITÉ
4. Nettoyer les TODOs (créer tickets, supprimer obsolètes)
5. Factoriser les duplications (`sync_orders` vs `sync_purchases`)
6. Supprimer le code mort (batch_id, méthodes no-op, imports inutilisés)

### Phase 3 : MOYENNE PRIORITÉ
7. Améliorer gestion d'erreurs (exceptions spécifiques, retry backoff)
8. Uniformiser nommage et style
9. Enrichir documentation (docstrings, ADR)

---

**Rapport généré le**: 2026-01-27
**Analyste**: Claude Code (Code Quality Analyzer)
