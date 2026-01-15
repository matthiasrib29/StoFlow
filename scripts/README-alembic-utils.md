# Alembic Utils - Auto-Copy Migrations

Utilitaire automatique pour gérer les migrations Alembic en environnement multi-worktree.

## 🎯 Problème Résolu

Quand plusieurs worktrees partagent la même base PostgreSQL, il arrive qu'un worktree tente d'appliquer une migration qui n'existe pas dans ses fichiers locaux mais qui est déjà appliquée dans la DB par un autre worktree.

**Erreur typique** :
```
alembic.util.exc.CommandError: Can't locate revision identified by 'a1b2c3d4'
```

## ✨ Solution Automatique

Le script `alembic-utils.sh` détecte automatiquement ces erreurs et copie les migrations manquantes depuis d'autres worktrees.

## 📋 Fonctions Disponibles

### `auto_copy_missing_migrations [backend_dir]`

Fonction principale qui :
1. Détecte les erreurs "Can't locate revision"
2. Cherche la migration dans tous les worktrees (`~/StoFlow-*` et `~/StoFlow`)
3. Copie automatiquement le fichier
4. Réessaye `alembic upgrade head`
5. Maximum 3 tentatives

**Exemple** :
```bash
cd ~/StoFlow-feature-X/backend
source .venv/bin/activate
source ../scripts/alembic-utils.sh
auto_copy_missing_migrations "."
```

### `find_migration_in_worktrees <revision_id>`

Cherche une migration spécifique dans tous les worktrees.

**Exemple** :
```bash
source scripts/alembic-utils.sh
find_migration_in_worktrees "a1b2c3d4"
# Retourne: /home/user/StoFlow-other/backend/migrations/versions/a1b2c3d4_add_table.py
```

### `list_all_migrations`

Liste toutes les migrations disponibles dans tous les worktrees.

**Exemple** :
```bash
source scripts/alembic-utils.sh
list_all_migrations
# Affiche:
# StoFlow (5 migrations)
#   001_initial.py
#   002_add_users.py
# StoFlow-feature-A (6 migrations)
#   001_initial.py
#   ...
#   003_add_products.py
```

## 🔄 Intégration Automatique

Cette fonctionnalité est **automatiquement intégrée** dans :

### `/X-dev` (scripts/dev.sh)
- Appelé avant de démarrer uvicorn
- Copie automatiquement les migrations manquantes au démarrage

### `/sync` (.claude/commands/sync.md)
- Appelé après le rebase sur develop
- Garantit que toutes les nouvelles migrations sont disponibles

### `/finish` (.claude/commands/finish.md)
- Appelé lors du merge des heads Alembic
- Assure que toutes les migrations sont présentes avant le merge final

## 🛠️ Utilisation Manuelle

Si besoin de l'exécuter manuellement (hors des commandes automatiques) :

```bash
# Se placer dans un worktree
cd ~/StoFlow-ma-feature

# Source le script
source scripts/alembic-utils.sh

# Exécuter l'auto-copy
cd backend
auto_copy_missing_migrations "."

# OU depuis la racine du worktree
auto_copy_missing_migrations "backend"
```

## 🔍 Diagnostic

Si l'auto-copy échoue, le script affiche des suggestions :

```
❌ Migration a1b2c3d4 introuvable dans les worktrees
Worktrees vérifiés:
  StoFlow-feature-A
  StoFlow-hotfix-B

Suggestions:
  1. Exécuter /sync pour récupérer les migrations depuis develop
  2. Vérifier dans ~/StoFlow: cd ~/StoFlow && git pull origin develop
  3. Créer manuellement la migration manquante
```

## 📊 Workflow Typique

```
Worktree A                    Worktree B
    │                             │
    │ Crée migration X            │
    │ /finish                     │
    │ (merge dans develop)        │
    │                             │
    │                             │ /sync (rebase sur develop)
    │                             │ ✅ Git récupère le fichier migration X
    │                             │ /1-dev
    │                             │ ✨ auto_copy détecte que migration X
    │                             │    existe dans ~/StoFlow
    │                             │ ✅ Copie automatique
    │                             │ ✅ alembic upgrade head réussit
```

## 🚨 Limites

- **Maximum 3 tentatives** : Si plus de 3 migrations sont manquantes en chaîne, le script s'arrête et suggère un `/sync`
- **Cherche uniquement dans `~/StoFlow-*` et `~/StoFlow`** : N'ira pas chercher dans d'autres répertoires
- **Ne crée pas de migrations** : Copie uniquement les migrations existantes

## 🔗 Voir Aussi

- [CLAUDE.md](../CLAUDE.md) - Documentation complète du projet
- [finish.md](../.claude/commands/finish.md) - Documentation de /finish
- [sync.md](../.claude/commands/sync.md) - Documentation de /sync
