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

---

## Étapes

### 1. Vérifications
```bash
git branch --show-current  # Vérifie qu'on n'est pas sur develop/prod
git status
```

### 2. Commit & Push
```bash
git add .
git commit -m "feat/fix/chore: [déduis du contexte]

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
git push -u origin $(git branch --show-current)
```

**Si push rejeté** → `git pull --no-rebase && git push` (retry auto)

### 3. PR & Merge
```bash
gh pr create --fill --base develop
gh pr merge --merge --delete-branch  # Depuis ~/StoFlow si erreur worktree
```

**Si conflit merge** → ⛔ ARRÊTER et DEMANDER à l'utilisateur comment résoudre

### 4. Update develop
```bash
cd ~/StoFlow
git checkout develop
git pull --no-rebase origin develop  # Auto-merge si divergence
git push origin develop  # Push le merge commit si créé
```

### 5. Alembic check & auto-merge
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

### 6. Cleanup automatique
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
