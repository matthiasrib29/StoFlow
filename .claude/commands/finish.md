Termine la feature actuelle (mode automatique) :

## 🚀 Mode AUTO par défaut

Tout est automatique sauf en cas d'erreur critique (conflits merge).

## ⚠️ Gestion des erreurs

**Stratégies automatiques :**
- Push rejeté → Pull + retry automatique
- Divergence git develop → Auto-merge (pull --no-rebase)
- Multiple heads Alembic → Auto-merge heads
- Suppression worktree → Automatique

**Arrêt + question SEULEMENT si :**
- Conflit de merge dans la PR
- Erreur Alembic critique lors du merge heads
- ⚠️ **Commits locaux non poussés détectés sur develop** (NOUVEAU)

---

## Étapes

### 1. Vérifications
```bash
git branch --show-current  # Vérifie qu'on n'est pas sur develop/prod
git status
```

### 2. Commit & Push (avec support GSD)

```bash
# Détecte si GSD utilisé dans ce worktree
if [ -d .planning/ ]; then
  echo "📊 GSD détecté - inclusion de .planning/ dans le commit"
  HAS_GSD=true
else
  HAS_GSD=false
fi

# Stage tous les fichiers
git add .

# Si GSD utilisé, ajouter aussi .planning/
if [ "$HAS_GSD" = true ]; then
  git add .planning/
fi

# Commit
git commit -m "feat/fix/chore: [déduis du contexte]

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"

# Push
git push -u origin $(git branch --show-current)
```

**Si push rejeté** → `git pull --no-rebase && git push` (retry auto)

### 2.5 Validation pre-merge (optionnel mais recommandé)

```bash
cd ~/StoFlow-[nom]

# Run backend tests
echo "🧪 Running backend tests..."
cd backend
source .venv/bin/activate 2>/dev/null || source venv/bin/activate
pytest tests/ -x --tb=short -q 2>/dev/null
BACKEND_TESTS=$?
cd ..

# Run frontend type check
echo "🔍 Running frontend type check..."
cd frontend
npm run typecheck 2>/dev/null
FRONTEND_TYPES=$?
cd ..
```

**Si tests échouent** (BACKEND_TESTS != 0) :
```
╔══════════════════════════════════════════════════════════════╗
║  ⚠️ TESTS BACKEND ÉCHOUÉS                                    ║
╠══════════════════════════════════════════════════════════════╣
║  Les tests unitaires ont échoué.                             ║
║                                                              ║
║  Options:                                                    ║
║  1. Corriger les tests avant de merger                       ║
║  2. Continuer quand même (non recommandé)                    ║
║                                                              ║
║  Que voulez-vous faire?                                      ║
╚══════════════════════════════════════════════════════════════╝
```

**Si typecheck échoue** (FRONTEND_TYPES != 0) :
```
╔══════════════════════════════════════════════════════════════╗
║  ⚠️ ERREURS TYPESCRIPT                                       ║
╠══════════════════════════════════════════════════════════════╣
║  Le type check frontend a échoué.                            ║
║                                                              ║
║  Options:                                                    ║
║  1. Corriger les erreurs TypeScript avant de merger          ║
║  2. Continuer quand même (non recommandé)                    ║
║                                                              ║
║  Que voulez-vous faire?                                      ║
╚══════════════════════════════════════════════════════════════╝
```

### 3. PR & Merge
```bash
gh pr create --fill --base develop
gh pr merge --merge --delete-branch  # Depuis ~/StoFlow si erreur worktree
```

**Si conflit merge** → ⛔ ARRÊTER et DEMANDER à l'utilisateur comment résoudre

### 4. 🛡️ BACKUP automatique avant opérations critiques (ajouté 2026-01-13)

**Créer un point de restauration AVANT de toucher à ~/StoFlow :**

```bash
cd ~/StoFlow

# Créer un stash de sécurité avec timestamp
BACKUP_NAME="backup-before-finish-$(date +%Y%m%d-%H%M%S)"

# Sauvegarder l'état actuel (même si pas de changements)
git stash push -m "$BACKUP_NAME" --include-untracked 2>/dev/null

# Afficher confirmation
if [ $? -eq 0 ]; then
  echo "✅ Backup créé: $BACKUP_NAME"
  echo "   Pour restaurer: git stash apply stash@{0}"
else
  echo "ℹ️ Aucun changement à sauvegarder"
fi
```

### 5. ⚠️ PROTECTION: Vérifier ~/StoFlow avant update (CRITIQUE)

**AVANT de toucher à ~/StoFlow, TOUJOURS exécuter ces vérifications :**

```bash
cd ~/StoFlow

# 1. Vérifier les changements non commités
if [ -n "$(git status --porcelain)" ]; then
  echo "⚠️ ATTENTION: ~/StoFlow a des changements non commités!"
  git status --short
  # ⛔ ARRÊTER et DEMANDER à l'utilisateur
fi

# 2. Vérifier les commits locaux non poussés
LOCAL_COMMITS=$(git log origin/develop..develop --oneline 2>/dev/null)
if [ -n "$LOCAL_COMMITS" ]; then
  echo "⚠️ ATTENTION: ~/StoFlow develop a des commits locaux NON POUSSÉS!"
  echo "$LOCAL_COMMITS"
  # ⛔ ARRÊTER et DEMANDER à l'utilisateur:
  # - Option 1: Pousser ces commits d'abord
  # - Option 2: Créer une branche de sauvegarde
  # - Option 3: Les abandonner (avec confirmation explicite)
fi

# 3. Vérifier si develop est derrière origin
git fetch origin develop
BEHIND=$(git rev-list develop..origin/develop --count 2>/dev/null)
if [ "$BEHIND" -gt 0 ]; then
  echo "ℹ️ develop est $BEHIND commits derrière origin/develop"
fi
```

**⛔ Si commits locaux détectés** → ARRÊTER et afficher :
```
╔══════════════════════════════════════════════════════════════╗
║  ⚠️ COMMITS LOCAUX DÉTECTÉS SUR ~/StoFlow develop           ║
╠══════════════════════════════════════════════════════════════╣
║  Les commits suivants ne sont pas sur origin:                ║
║  [liste des commits]                                         ║
║                                                              ║
║  Options:                                                    ║
║  1. Pousser ces commits maintenant (git push)                ║
║  2. Sauvegarder dans une branche (git branch backup-XXX)     ║
║  3. Abandonner ces commits (PERTE DE DONNÉES)                ║
║                                                              ║
║  Que voulez-vous faire?                                      ║
╚══════════════════════════════════════════════════════════════╝
```

### 6. Update develop (seulement après vérifications OK)
```bash
cd ~/StoFlow
git checkout develop
git pull --no-rebase origin develop  # Auto-merge si divergence
git push origin develop  # Push le merge commit si créé
```

### 7. Alembic check & auto-merge
```bash
cd ~/StoFlow/backend
HEADS=$(alembic heads 2>/dev/null | grep -c "head")
```

**Si HEADS > 1** (multiple heads détectés) :
```bash
alembic merge -m "merge: unify migration heads" heads
alembic upgrade head
git add migrations/
git commit -m "chore: merge alembic heads"
git push origin develop
```

**Si erreur Alembic** → ⛔ ARRÊTER et DEMANDER

### 8. Cleanup automatique
```bash
BRANCH=$(git branch --show-current)
WORKTREE=$(git worktree list | grep $BRANCH | awk '{print $1}')
git worktree remove $WORKTREE
cd ~/StoFlow
git branch -d $BRANCH
```

---

## 📊 Résumé final

Afficher un tableau récapitulatif :

```
╔══════════════════════════════════════════╗
║  ✅ FEATURE/HOTFIX TERMINÉ               ║
╠══════════════════════════════════════════╣
║  🌿 Branche : [nom]                      ║
║  🔗 PR : #[numero]                       ║
║  ✅ Mergé dans develop                   ║
║  ✅ Alembic : [status]                   ║
║  ✅ Worktree supprimé                    ║
╠══════════════════════════════════════════╣
║  📍 Tu es maintenant sur ~/StoFlow       ║
║     (branche develop)                    ║
╚══════════════════════════════════════════╝
```

---

## 🛡️ Règles de sécurité (ajoutées 2026-01-12)

> Ces règles ont été ajoutées après une perte de ~8000 lignes de code
> causée par un reset accidentel lors d'un /finish.

1. **JAMAIS** de `git reset --hard` sur develop sans vérification
2. **TOUJOURS** vérifier les commits locaux avant de toucher à ~/StoFlow
3. **TOUJOURS** utiliser `git pull --no-rebase` (pas de reset)
4. **EN CAS DE DOUTE** → ARRÊTER et DEMANDER
