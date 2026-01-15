# ✨ Auto-Copy Migrations - Guide Complet

> **Date d'ajout** : 2026-01-15
> **Auteur** : Claude Code + Maribeiro
> **Objectif** : Éliminer les erreurs "Can't locate revision" en multi-worktree

---

## 🎯 Problème Résolu

Quand plusieurs worktrees travaillent en parallèle sur la même base PostgreSQL, il arrive qu'un worktree essaye d'appliquer une migration qui :
- Est déjà appliquée dans la DB (par un autre worktree)
- Mais n'existe pas dans ses fichiers locaux

**Erreur typique** :
```
alembic.util.exc.CommandError: Can't locate revision identified by 'a1b2c3d4'
```

## ✅ Solution Implémentée

Un système automatique qui :
1. **Détecte** l'erreur "Can't locate revision"
2. **Cherche** la migration dans tous les worktrees (`~/StoFlow-*` et `~/StoFlow`)
3. **Copie** automatiquement le fichier trouvé
4. **Réessaye** `alembic upgrade head`
5. **Maximum 3 tentatives** pour gérer les migrations en chaîne

---

## 📁 Fichiers Créés

| Fichier | Description |
|---------|-------------|
| `scripts/alembic-utils.sh` | Fonctions réutilisables (auto_copy, find, list) |
| `scripts/README-alembic-utils.md` | Documentation technique détaillée |
| `scripts/test-alembic-utils.sh` | Script de test automatique |
| `AUTO-COPY-MIGRATIONS.md` | Ce guide (résumé utilisateur) |

## 🔄 Fichiers Modifiés

| Fichier | Modification |
|---------|--------------|
| `scripts/dev.sh` | Intégration auto-copy au démarrage (avant uvicorn) |
| `.claude/commands/sync.md` | Documentation auto-copy après rebase |
| `.claude/commands/finish.md` | Documentation auto-copy lors merge heads |
| `CLAUDE.md` | Nouvelle section "Auto-Copy de Migrations" |

---

## 🚀 Utilisation Automatique

L'auto-copy est **automatiquement déclenché** dans :

### `/X-dev` (Démarrage serveurs)
```bash
/1-dev  # Lance backend + frontend
# ✨ Auto-copy avant démarrage uvicorn
# 🔍 Détecte migrations manquantes
# 📋 Copie depuis autres worktrees
# ✅ alembic upgrade head réussit
```

### `/sync` (Synchronisation develop)
```bash
/sync  # Rebase sur origin/develop
# ✨ Auto-copy après rebase
# 🔍 Détecte nouvelles migrations de develop
# 📋 Copie depuis ~/StoFlow
# ✅ DB à jour avec nouveau code
```

### `/finish` (Merge & Cleanup)
```bash
/finish  # Merge PR et cleanup
# ✨ Auto-copy avant merge heads Alembic
# 🔍 Détecte migrations des autres features
# 📋 Copie depuis develop
# ✅ Merge heads sans erreur
```

---

## 🛠️ Utilisation Manuelle

Si besoin de l'exécuter manuellement :

### Depuis le backend d'un worktree
```bash
cd ~/StoFlow-ma-feature/backend
source .venv/bin/activate
source ../scripts/alembic-utils.sh

# Auto-copy et upgrade
auto_copy_missing_migrations "."
```

### Depuis la racine d'un worktree
```bash
cd ~/StoFlow-ma-feature
source scripts/alembic-utils.sh

# Auto-copy en spécifiant le répertoire backend
auto_copy_missing_migrations "backend"
```

### Commandes de diagnostic
```bash
source scripts/alembic-utils.sh

# Liste toutes les migrations de tous les worktrees
list_all_migrations

# Cherche une migration spécifique
find_migration_in_worktrees "a1b2c3d4"

# Affiche le chemin complet si trouvé
```

---

## 📊 Workflow Complet

```
┌─────────────────────────────────────────────────────────────┐
│  Worktree A                    Worktree B                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Jour 1                                                      │
│  ├─ Crée migration X                                         │
│  ├─ alembic upgrade head                                     │
│  └─ /finish → Merge dans develop                            │
│                                                              │
│  Jour 2                        /sync (rebase develop)        │
│                                ├─ Git récupère migration X   │
│                                └─ /1-dev                     │
│                                   └─ ✨ AUTO-COPY            │
│                                      ├─ Détecte révision X   │
│                                      ├─ Trouve dans StoFlow  │
│                                      ├─ Copie fichier X      │
│                                      └─ ✅ upgrade head OK   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🧪 Tests

### Test automatique complet
```bash
./scripts/test-alembic-utils.sh
```

**Ce test vérifie** :
- ✅ Chargement de `alembic-utils.sh`
- ✅ Définition des 3 fonctions principales
- ✅ Détection des worktrees existants
- ✅ Liste des migrations disponibles
- ✅ Syntaxe bash correcte

### Test en situation réelle

Pour tester l'auto-copy dans un vrai worktree :

```bash
# 1. Créer un nouveau worktree
/1-new-feature "test-auto-copy"

# 2. Lancer les serveurs
/1-dev

# 3. Observer les logs
# ✅ "📦 Checking database migrations..."
# ✅ "🔍 Checking for missing Alembic migrations..."
# ✅ Si migration manquante détectée :
#    - "⚠️ Migration manquante détectée: XXXXX"
#    - "🔎 Recherche dans les autres worktrees..."
#    - "✅ Migration trouvée dans: StoFlow"
#    - "📋 Copie de: XXXXX_description.py"
#    - "✅ Migration copiée avec succès"
#    - "✅ Database up to date"
```

---

## 🔍 En Cas de Problème

### "Migration XXXXX introuvable"

**Cause** : La migration n'existe dans aucun worktree.

**Solutions** :
1. Synchroniser avec develop : `/sync`
2. Pull dans repo principal : `cd ~/StoFlow && git pull origin develop`
3. Vérifier l'état DB : `cd backend && alembic current`

### "Maximum de tentatives atteint (3)"

**Cause** : Plus de 3 migrations manquantes en chaîne.

**Solutions** :
1. `/sync` pour récupérer toutes les migrations
2. Vérifier l'état : `alembic current` vs `alembic heads`
3. Manuel : `list_all_migrations` pour voir ce qui manque

### Auto-copy ne se déclenche pas

**Vérifications** :
1. Le script est bien sourcé : `type auto_copy_missing_migrations`
2. Les worktrees existent : `ls -d ~/StoFlow-*`
3. Permissions : `ls -l scripts/alembic-utils.sh` (doit être exécutable)

---

## 💡 Bonnes Pratiques

### Travailler sur plusieurs worktrees en parallèle

1. **Synchroniser régulièrement** : `/sync` toutes les 1-2 heures
2. **Créer migrations en fin de feature** : Réduit les conflits
3. **Une feature avec migrations à la fois** : Idéal si possible
4. **Vérifier avant de créer migration** : `/sync` puis `alembic current`

### Diagnostic rapide

```bash
# État de la DB
cd backend
alembic current           # Révision actuelle
alembic heads             # Heads disponibles
alembic history --verbose # Historique complet

# Migrations disponibles
source ../scripts/alembic-utils.sh
list_all_migrations       # Voir toutes les migrations

# Chercher une migration spécifique
find_migration_in_worktrees "a1b2c3d4"
```

---

## 🎓 Pour Aller Plus Loin

### Fonctionnement Interne

Le script `alembic-utils.sh` utilise :
- `grep` pour détecter l'erreur "Can't locate revision"
- `find` pour chercher dans `~/StoFlow*/backend/migrations/versions`
- `cp` pour copier les fichiers trouvés
- Boucle jusqu'à 3 tentatives pour gérer les migrations en chaîne

### Limites Connues

| Limite | Raison | Workaround |
|--------|--------|------------|
| Max 3 tentatives | Éviter boucles infinies | `/sync` si plus de 3 manquantes |
| Cherche uniquement `~/StoFlow*` | Performance | Ajouter d'autres chemins si besoin |
| Ne crée pas de migrations | Sécurité | Créer manuellement avec `alembic revision` |

### Améliorations Futures (Optionnel)

1. **Cache des migrations** : Éviter recherches répétées
2. **Mode dry-run** : Simuler sans copier
3. **Notifications** : Slack/Discord lors d'auto-copy
4. **Metrics** : Logger nombre d'auto-copies
5. **Support Git LFS** : Si migrations très volumineuses

---

## 📚 Documentation Associée

- [CLAUDE.md](CLAUDE.md) - Documentation complète du projet
- [scripts/README-alembic-utils.md](scripts/README-alembic-utils.md) - Doc technique
- [.claude/commands/sync.md](.claude/commands/sync.md) - Commande `/sync`
- [.claude/commands/finish.md](.claude/commands/finish.md) - Commande `/finish`

---

## ✅ Résumé

| Avant | Après |
|-------|-------|
| ❌ Erreur "Can't locate revision" | ✅ Auto-copy automatique |
| ⏱️ 5-10 min diagnostic | ⏱️ 0 secondes |
| 🔧 Copie manuelle risquée | 🤖 Copie automatique sûre |
| 😤 Frustration | 😊 Workflow fluide |

---

**🎉 Félicitations ! Tu peux maintenant travailler sur plusieurs worktrees sans te soucier des migrations manquantes.**

*Pour toute question ou amélioration, voir `scripts/README-alembic-utils.md` ou demander à Claude Code.*
