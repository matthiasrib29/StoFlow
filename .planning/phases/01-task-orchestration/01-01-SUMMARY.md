# Plan 01-01 Summary: Database Foundation

## Accomplissements

✅ **Modèle MarketplaceTask amélioré** avec structure minimale:
- Champ `position` (Integer, nullable) ajouté pour l'ordre d'exécution
- Réutilisation du champ existant `description` comme `name` (texte libre)
- Indexes créés: `(job_id, position)` et `(job_id, status)`
- Compatibilité préservée avec le système existant (task_type, payload, etc.)

✅ **Migration Alembic réversible** créée:
- Fichier: `20260115_1730_add_position_to_marketplace_tasks.py`
- Révision: `20260115_1730`
- Révise: `077dc55ef8d0` (dernière migration du repo principal)

## Choix Techniques

### 1. Amélioration vs Création
**Décision**: Améliorer le modèle existant au lieu d'en créer un nouveau

**Rationale**:
- Le modèle `MarketplaceTask` existant (créé 2026-01-07) est activement utilisé
- Utilisé dans 6 fichiers dont `base_handler.py`, `marketplace_job_service.py`
- Ajout du champ `position` permet retry intelligent sans casser l'existant
- Le champ `description` existant sert déjà de "name" (texte libre)

### 2. Modèle Minimal
**Colonnes ajoutées**: 1 seule (`position`)

**Colonnes réutilisées**:
- `description` → sert de `name` (ex: "Upload image 1/3", "Validate product")
- `status` → déjà existant avec valeurs appropriées (PENDING, PROCESSING, SUCCESS, FAILED)
- `result` → déjà JSONB pour flexibilité
- `error_message` → déjà présent
- `created_at`, `started_at`, `completed_at` → déjà présents

**Pas ajouté** (épuration du plan original):
- ❌ `step_type` enum → trop rigide, `description` texte libre suffit
- ❌ `is_idempotent` boolean → over-engineering
- ❌ `side_effects` JSONB → `result` existant suffit

### 3. Indexes pour Performance
**Créés**:
- `ix_marketplace_tasks_job_position` sur `(job_id, position)` → tri ordonné des tasks
- `ix_marketplace_tasks_job_status` sur `(job_id, status)` → requêtes retry (FAILED tasks)

**But**: Support queries type:
```sql
-- Récupérer tasks ordonnées d'un job
SELECT * FROM marketplace_tasks
WHERE job_id = 123
ORDER BY position;

-- Trouver tasks à retry
SELECT * FROM marketplace_tasks
WHERE job_id = 123 AND status IN ('FAILED', 'PENDING')
ORDER BY position;
```

### 4. Migration Multi-Tenant
**Fan-out vers**:
- `public.marketplace_tasks` (template schema)
- Tous les `user_X.marketplace_tasks` (tenant schemas)

**Idempotente**:
- Vérifie existence de colonne avant `ADD COLUMN`
- Try/except sur création d'index (skip si existe)

**Réversible**:
- `downgrade()` drop colonne + indexes dans tous les schemas
- Ordre inverse: user_X d'abord, puis public

## Révision Migration

**Hash Alembic**: `20260115_1730`

**Down revision**: `077dc55ef8d0` (create product_images table with label flag)

## Vérifications

✅ Import Python réussit:
```python
from models.user.marketplace_task import MarketplaceTask
# Position field accessible: task.position
```

✅ Migration prête à appliquer:
```bash
cd backend
source venv/bin/activate
alembic upgrade head
```

✅ Worktree créé avec changements:
- Path: `/home/maribeiro/StoFlow-task-orchestration-foundation/`
- Branch: `feature/task-orchestration-foundation`
- Fichiers modifiés présents et vérifiés

## Prochaine Étape

**Plan 01-02**: Implémentation TaskOrchestrator avec TDD

**Objectif**: Service qui crée, exécute et retry les tasks de manière intelligente (skip COMPLETED, retry FAILED).

**Approche**: Test-Driven Development strict
- 8 tâches alternant RED/GREEN/REFACTOR
- Tests unitaires pytest
- Test d'intégration PostgreSQL

---

*Créé: 2026-01-15*
*Worktree: StoFlow-task-orchestration-foundation*
*Durée: ~45 minutes (découverte + implémentation + worktree setup)*
