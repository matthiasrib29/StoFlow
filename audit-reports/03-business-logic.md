# Rapport d'Audit - Logique Métier

**Projet**: StoFlow
**Date d'analyse**: 2026-01-27
**Scope**: Backend services, models, API routes

---

## Résumé Exécutif

47 vulnérabilités de logique métier identifiées dans 10 catégories. Les problèmes les plus critiques concernent les race conditions dans les opérations concurrentes, l'isolation des données multi-tenant, et la validation manquante pour les transactions financières.

---

## 1. Product Lifecycle - Status Transitions

### CRITICAL #1: Race condition dans la transition vers SOLD

**Fichier**: `backend/services/product_service.py`

Quand un produit est vendu sur une marketplace, il n'est pas automatiquement retiré des autres. Deux ventes simultanées peuvent aboutir à un overselling.

**Recommandation**: Ajouter `SELECT FOR UPDATE` sur le produit, implémenter un delisting cross-marketplace atomique.

### CRITICAL #12: Pas de synchronisation stock cross-marketplace

Quand un produit est vendu sur Vinted, il reste listé sur eBay et Etsy. Violation de stock.

**Recommandation**: Event-driven delisting (quand un produit passe SOLD → delist sur toutes les marketplaces).

### HIGH #2: Transitions de statut invalides non bloquées

Le modèle permet certaines transitions invalides (ex: ARCHIVED → PUBLISHED directement).

**Recommandation**: Implémenter une state machine stricte avec transitions autorisées.

---

## 2. Price Algorithm

### CRITICAL #4: Overflow de calcul de prix

**Fichier**: `backend/models/user/product.py`

Le prix est `DECIMAL(10,2)` ce qui limite à 99,999,999.99€. Des calculs intermédiaires pourraient dépasser cette limite.

**Recommandation**: Ajouter validation avant persistance, CHECK constraint en DB.

### MEDIUM #31: Pas d'historique des changements de prix

Pas de `ProductPriceHistory`. Impossible de retracer les modifications.

**Recommandation**: Créer une table `product_price_history` avec trigger sur changement de prix.

---

## 3. Order Processing

### CRITICAL #8: Race condition - Double création de commande

**Fichier**: `backend/services/vinted/vinted_order_sync.py`

Si le sync s'exécute deux fois en parallèle, la même commande peut être créée en double.

**Recommandation**: Ajouter contrainte UNIQUE sur `transaction_id` dans la table orders.

### CRITICAL #9: eBay order sync race condition similaire

Même problème pour la synchronisation des commandes eBay.

**Recommandation**: UNIQUE constraint sur `ebay_order_id`.

---

## 4. Multi-Tenant Isolation

### CRITICAL #14: Schema translate_map contournable

**Fichier**: `backend/shared/database.py:199-235`

Les requêtes SQL brutes avec `text()` peuvent contourner le `schema_translate_map`, permettant un accès cross-tenant.

**Recommandation**: Ajouter une validation `validate_tenant_isolation()` en début d'opérations sensibles.

### HIGH #15: Foreign Keys cross-schema boundaries

Les FK vers `product_attributes` sont hardcodées. Si le search_path est incorrect, les FK pointent vers les mauvaises données.

### HIGH #16: Pas de tenant_id dans le contexte de session

`get_db()` crée une session sans contexte tenant. Les background jobs pourraient traiter les données du mauvais utilisateur.

**Recommandation**: Utiliser `contextvars.ContextVar` pour stocker le tenant_id.

---

## 5. Stock/Inventory

### MEDIUM #28: Stock peut devenir négatif

Le CHECK constraint `stock_quantity >= 0` n'empêche pas les opérations atomiques concurrent (5 - 3 - 3 - 3 = -4).

**Recommandation**: Trigger PostgreSQL pour empêcher le stock négatif.

---

## 6. Payment/Stripe Integration

### HIGH #17: Checkout sans idempotence

**Fichier**: `backend/services/stripe/webhook_handlers.py:18-58`

Si Stripe envoie le webhook deux fois, l'utilisateur reçoit le double de crédits.

```python
# VULNÉRABLE: Pas de vérification de duplicat
user.ai_credits_purchased += credits
```

**Recommandation**: Table `processed_webhooks` avec l'event_id Stripe comme clé unique.

### MEDIUM #18: Downgrade subscription sans grace period

Downgrade immédiat sur `past_due`, pas de période de grâce.

### MEDIUM #19: Pas de gestion des remboursements

Pas de handler pour `charge.refunded`. Un utilisateur remboursé garde ses crédits.

---

## 7. Marketplace API Error Handling

### HIGH #20: Pas de Circuit Breaker

Quand une API marketplace est down, le système continue de réessayer tous les jobs, causant des cascading failures.

**Recommandation**: Implémenter un circuit breaker (failure_threshold=10, timeout=10min).

### HIGH #21: Retry sans distinction du type d'erreur

Erreurs 400 Bad Request retryées comme des erreurs 503 Server Error.

**Recommandation**: Classifier erreurs en retryable/non-retryable.

### MEDIUM #22: Pas d'exponential backoff

Jobs failed immédiatement remis en PENDING, martelant les APIs.

---

## 8. Concurrent Operations - Race Conditions

### CRITICAL #23: Race condition M2M tables

**Fichier**: `backend/services/product_service.py:676-746`

`_replace_product_colors()` fait DELETE puis INSERT sans lock. Deux updates concurrents peuvent interleaver.

**Recommandation**: `SELECT FOR UPDATE` sur le produit avant modification M2M.

### HIGH #24: Optimistic locking incomplet

Le version_number ne couvre pas les tables M2M (colors, materials).

### MEDIUM #25: Job cancellation race condition

Cancellation peut arriver entre le mark-as-running et le check.

---

## 9. Data Validation

### HIGH #26: Pas de validation longueur titre/description par marketplace

Titre DB: 500 chars. Vinted max: 100 chars. eBay max: 80 chars. Publication échoue sans message clair.

**Recommandation**: Validation marketplace-specific avant publication.

### MEDIUM #27: Dimensions sans contrainte de range

`dim1` à `dim6` acceptent des valeurs négatives ou absurdes.

---

## 10. Missing Business Rules

### HIGH #29: Pas de durée maximale de listing

Produits restent PUBLISHED indéfiniment. Risque de listings obsolètes.

### HIGH #30: Pas de prévention de listing duplicate

Rien n'empêche de publier le même produit deux fois sur la même marketplace → overselling.

### MEDIUM #32: Pas de détection de fraude

Aucun mécanisme pour détecter les patterns suspects (mass price changes, rapid cancellations).

---

## Résumé des Issues Critiques

| # | Issue | Sévérité | Impact |
|---|-------|----------|--------|
| 1 | Race condition SOLD status | CRITICAL | Overselling |
| 4 | Price calculation overflow | CRITICAL | DB constraint violation |
| 8 | Duplicate order creation | CRITICAL | Double-counting revenue |
| 9 | eBay order sync race | CRITICAL | Duplicate orders |
| 12 | No cross-marketplace stock sync | CRITICAL | Overselling violation |
| 14 | Schema translate map bypass | CRITICAL | GDPR violation, data leak |
| 23 | M2M table race condition | CRITICAL | Data corruption |

---

## Plan d'Action

### Immédiat (1 semaine)
1. UNIQUE constraints sur transaction IDs
2. Cross-marketplace delisting on sale
3. Schema isolation validation
4. Fix price calculation overflow
5. Advisory locks pour status transitions

### Haute Priorité (1 mois)
6. Webhook idempotency (Stripe)
7. Circuit breakers marketplace APIs
8. Retry logic error type distinction
9. Marketplace-specific validation
10. Invalid status transitions prevention

### Moyenne Priorité (3 mois)
11. Exponential backoff retries
12. Pending action TTL
13. Price change history
14. Fraud detection
15. Dimension range validation

---

**Rapport généré le**: 2026-01-27
**Analyste**: Claude Code (Business Logic Analyst)
