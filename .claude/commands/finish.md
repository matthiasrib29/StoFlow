Termine la feature actuelle (tout automatique) :

## ⚠️ RÈGLE IMPORTANTE - Gestion des conflits

**En cas de conflit ou d'erreur à N'IMPORTE quelle étape :**
1. **NE PAS essayer de résoudre automatiquement** si tu n'es pas sûr à 100%
2. **POSER UNE QUESTION** à l'utilisateur pour comprendre comment procéder
3. Afficher clairement le conflit/erreur et proposer des options

## 1. Vérifications
- Vérifie qu'on n'est pas sur develop ou prod
- git status

## 2. Commit & Push
- git add .
- git commit -m "feat: [déduis le message des changements]"
- git push -u origin $(git branch --show-current)
- **Si erreur push** (divergence, rejected, etc.) → DEMANDER à l'utilisateur : "Push rejeté, voulez-vous force push, pull + rebase, ou autre ?"

## 3. PR & Merge
- gh pr create --fill --base develop
- gh pr merge --merge --delete-branch
- **Si conflit de merge** → ARRÊTER et DEMANDER :
  - Afficher les fichiers en conflit
  - Demander : "Des conflits ont été détectés. Comment voulez-vous procéder ?"
  - Proposer des options (résoudre manuellement, abandonner, etc.)

## 4. Update develop
- cd ~/StoFlow
- git checkout develop
- git pull origin develop

## 5. ALEMBIC - Merge des heads si nécessaire
- cd ~/StoFlow/backend
- HEADS=$(alembic heads 2>/dev/null | grep -c "head")
- Si HEADS > 1 :
  - Affiche : "⚠️ Plusieurs heads Alembic détectés, merge en cours..."
  - alembic merge -m "merge: unify migration heads" heads
  - **Si erreur Alembic** → DEMANDER à l'utilisateur comment procéder
  - alembic upgrade head
  - git add migrations/
  - git commit -m "chore: merge alembic heads"
  - git push origin develop
  - Affiche : "✅ Heads Alembic mergés"
- Sinon :
  - Affiche : "✅ Alembic OK (1 seul head)"

## 6. Cleanup worktree & branch
- Sauvegarde le nom de la branche actuelle : BRANCH=$(git branch --show-current)
- Demande : "Supprimer le worktree et la branche '$BRANCH' ? (o/n)"
- Si oui :
  - git worktree remove [worktree actuel]
  - cd ~/StoFlow
  - git branch -d $BRANCH (supprime la branche locale)
  - Affiche : "✅ Worktree et branche '$BRANCH' supprimés"
