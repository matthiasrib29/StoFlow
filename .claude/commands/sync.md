Synchronise le worktree actuel avec develop :

## ⚠️ Pré-requis de sécurité (CRITIQUE)

**AVANT toute synchronisation, vérifier :**

```bash
# 1. S'assurer qu'on est dans un WORKTREE, pas dans ~/StoFlow
CURRENT_DIR=$(pwd)
if [ "$CURRENT_DIR" = "$HOME/StoFlow" ]; then
  echo "⚠️ ATTENTION: Tu es dans ~/StoFlow (repo principal)!"
  echo "Le /sync est conçu pour les WORKTREES uniquement."
  echo "Utilise plutôt: git pull origin develop"
  # ⛔ ARRÊTER et DEMANDER confirmation
fi

# 2. Vérifier la branche actuelle
BRANCH=$(git branch --show-current)
if [ "$BRANCH" = "develop" ] || [ "$BRANCH" = "prod" ] || [ "$BRANCH" = "main" ]; then
  echo "⚠️ ATTENTION: Tu es sur la branche $BRANCH!"
  echo "Le /sync est pour les branches feature/hotfix."
  # ⛔ ARRÊTER et DEMANDER confirmation
fi
```

---

## Étapes

### 1. Sauvegarder le travail en cours
```bash
git status
```

Si changements non commités :
```bash
git add .
git commit -m "wip: save changes before sync"
```
(ou demander un message de commit à l'utilisateur)

### 2. Récupérer les derniers changements
```bash
git fetch origin
```

### 3. 🛡️ BACKUP automatique avant rebase (ajouté 2026-01-13)

**Créer un point de restauration AVANT le rebase :**

```bash
# Créer un stash de sécurité avec timestamp
BACKUP_NAME="backup-before-sync-$(date +%Y%m%d-%H%M%S)"
BRANCH=$(git branch --show-current)

# Créer une branche de backup (plus sûr que stash pour les rebases)
git branch "${BRANCH}-backup-$(date +%Y%m%d-%H%M%S)" 2>/dev/null

echo "✅ Backup branch créée"
echo "   En cas de problème: git checkout ${BRANCH}-backup-*"
```

### 4. Rebase sur develop
```bash
git rebase origin/develop
```

### 5. Gestion des conflits

**Si conflits détectés** → Afficher les fichiers en conflit et DEMANDER comment procéder :
- Option 1: Résoudre manuellement
- Option 2: `git rebase --abort` pour annuler

### 6. 🗄️ Appliquer les nouvelles migrations (ajouté 2026-01-13)

**Après rebase réussi**, vérifier et appliquer les migrations :

```bash
cd backend
source .venv/bin/activate

# ✨ AUTOMATIQUE: Les migrations manquantes sont auto-copiées depuis d'autres worktrees
# La fonction auto_copy_missing_migrations() cherche et copie automatiquement
# les fichiers de migration manquants depuis ~/StoFlow-* et ~/StoFlow

# Source utilities
source ../scripts/alembic-utils.sh

# Appliquer migrations avec auto-copy
if auto_copy_missing_migrations "."; then
  echo "✅ Migrations appliquées avec succès"
else
  echo "❌ Erreur lors de l'application des migrations"
  # La fonction affiche déjà les suggestions (sync, diagnostic, etc.)
  # ⛔ ARRÊTER et DEMANDER à l'utilisateur
fi
```

**Comment fonctionne l'auto-copy** :
1. Détecte l'erreur "Can't locate revision XXXXX"
2. Cherche la migration manquante dans tous les worktrees (~/StoFlow-*)
3. Copie automatiquement le fichier trouvé
4. Réessaye `alembic upgrade head`
5. Maximum 3 tentatives (pour gérer plusieurs migrations manquantes)

**Si erreur persistante** → Afficher l'erreur et proposer :
- Option 1: `alembic upgrade head` manuellement après diagnostic
- Option 2: Voir section "Migrations en Multi-Worktree" dans CLAUDE.md
- Option 3: Lister migrations disponibles avec `source scripts/alembic-utils.sh && list_all_migrations`

### 7. Rapport final

```
╔══════════════════════════════════════════╗
║  ✅ SYNC TERMINÉ                         ║
╠══════════════════════════════════════════╣
║  🌿 Branche : [nom]                      ║
║  📍 Worktree : [chemin]                  ║
║  ✅ Rebasé sur origin/develop            ║
║  🗄️ Migrations : [à jour / X appliquées] ║
╚══════════════════════════════════════════╝
```

---

## 🛡️ Règles de sécurité (mises à jour 2026-01-13)

> Ces règles protègent contre la perte de données lors de sync.

1. **JAMAIS** utiliser /sync dans ~/StoFlow (repo principal)
2. **JAMAIS** utiliser /sync sur develop/prod/main
3. **TOUJOURS** commiter le travail en cours avant sync
4. **JAMAIS** de `git reset --hard` - utiliser rebase
5. **EN CAS DE CONFLIT** → ARRÊTER et DEMANDER
