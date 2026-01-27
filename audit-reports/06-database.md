# Rapport d'Audit - Architecture Base de Données

**Projet**: StoFlow Backend
**Date d'analyse**: 2026-01-27
**Stack**: FastAPI + SQLAlchemy 2.0 + PostgreSQL + Alembic
**Architecture**: Multi-tenant avec isolation par schema PostgreSQL

---

## État Global : BON - Production-ready avec corrections mineures

---

## Points Forts (Production-Ready)

### 1. SQLAlchemy 2.0 Modern Syntax ✅ EXCELLENT

100% des modèles utilisent la syntaxe moderne `Mapped[T]` et `mapped_column()`.

```python
class Product(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    price: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
```

### 2. Connection Pool Configuration ✅

```python
engine = create_engine(
    pool_size=10,        # Augmenté de 5 → 10
    max_overflow=20,     # Augmenté de 10 → 20
    pool_timeout=30,
    pool_recycle=3600,   # 1h
    pool_pre_ping=True,  # Détecte connexions mortes
)
```

### 3. Multi-Tenant Architecture ✅

Schema-per-tenant avec `schema_translate_map` (meilleure pratique SQLAlchemy 2.0) + validation regex des noms de schema.

### 4. Naming Convention Standardisée ✅

Convention explicite pour ix, uq, ck, fk, pk → migrations Alembic prévisibles.

### 5. N+1 Prevention ✅

- `lazy="raise"` pour forcer eager loading explicite
- `lazy="selectin"` pour relations souvent accédées
- Repository pattern avec `selectinload()` systématique

### 6. Timezone-Aware Timestamps ✅

100% des 115 colonnes DateTime utilisent `timezone=True`.

### 7. Cascade Delete Configuration ✅

Toutes les FK ont des stratégies `ondelete` explicites (SET NULL pour attributs, CASCADE pour M2M).

### 8. Migrations ✅

184 migrations bien structurées, idempotentes (IF NOT EXISTS), multi-tenant aware.

---

## Problèmes Critiques

### 1. CRITIQUE: Float pour données monétaires

**Fichiers affectés**:
- `models/user/ebay_return.py:96` - `refund_amount: Float`
- `models/user/vinted_product.py:128-142`
- `models/public/ebay_exchange_rate.py:28-44`

**Impact**: Erreurs d'arrondi garanties (`0.1 + 0.2 = 0.30000000000000004`)

**Fix**: Remplacer tous les `Float` par `DECIMAL(10, 2)` pour les montants monétaires.

```python
# ❌ ERREUR
refund_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

# ✅ CORRECT
refund_amount: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 2), nullable=True)
```

**Migration nécessaire**: ADD colonne DECIMAL, COPY données arrondies, DROP ancienne colonne, RENAME.

---

## Problèmes Moyens

### 2. Services avec commit/rollback explicites (ANTI-PATTERN)

15 services contiennent `db.commit()` ou `db.rollback()` au lieu de laisser `get_db()` gérer les transactions.

**Impact**: Transactions imbriquées impossibles, tests difficiles, double-commit possible.

**Fix**: Remplacer `db.commit()` par `db.flush()` dans les services, laisser la route gérer le commit.

### 3. Indexes manquants sur colonnes fréquemment requêtées

| Table | Colonne(s) | Justification |
|-------|-----------|---------------|
| `marketplace_jobs` | `(status, created_at)` | Query principale du dispatcher |
| `marketplace_jobs` | `(user_id, status, created_at)` | Query multi-tenant |
| `products` | `size_normalized` | Filtrage par taille |
| `vinted_products` | `price` | Tri par prix |
| `vinted_products` | `created_at` | Tri chronologique |

**Priorité**: `marketplace_jobs` composite index en premier (performance dispatcher).

---

## Problèmes Faibles

### 4. Raw SQL non paramétré dans migrations

```python
# Migrations utilisent f-string pour schema name
f"CREATE TABLE IF NOT EXISTS {schema}.pending_actions (...)"
```

Risque faible car `validate_schema_name()` est appelé avant, mais défensivement on devrait utiliser le quoting PostgreSQL.

### 5. Pas de Savepoints

Aucune utilisation de `db.begin_nested()` pour les opérations composites multi-marketplace. En cas d'échec partiel (Vinted OK, eBay KO), tout est rollback.

---

## Statistiques Globales

| Métrique | Valeur | État |
|----------|--------|------|
| Modèles SQLAlchemy | 76+ | ✅ Tous en SQLAlchemy 2.0 |
| Migrations Alembic | 184 | ⚠️ Proposer squash à 200+ |
| Repositories | 19 | ✅ Pattern uniforme |
| Timezone-aware | 115/115 (100%) | ✅ Excellent |
| Lazy loading strategy | Toutes relations | ✅ N+1 prevention |
| Float pour argent | 5-7 colonnes | 🔴 CRITIQUE |
| Indexes manquants | ~6 | 🟡 Optimisation |
| Connection pool | pool_pre_ping=True | ✅ Production-ready |

---

## Plan d'Action

### Priorité 1 (Urgent)
1. **Float → Decimal** pour données monétaires (migration + tests)

### Priorité 2 (Important)
2. **Indexes composites** sur `marketplace_jobs`
3. **Refactorer services** : `db.flush()` au lieu de `db.commit()`

### Priorité 3 (Amélioration)
4. Indexes sur colonnes de recherche
5. Savepoints pour opérations multi-marketplace
6. Squash migrations à 200+

---

**Rapport généré le**: 2026-01-27
**Analyste**: Claude Code (PostgreSQL/SQLAlchemy Expert)
