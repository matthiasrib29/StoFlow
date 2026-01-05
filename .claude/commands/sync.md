Synchronise le worktree actuel avec develop :

1. `git status` - vérifier s'il y a des changements non commités
2. Si changements non commités :
   - `git add .`
   - `git commit -m "wip: save changes before sync"` (ou demander un message)
3. `git fetch origin` - récupère les derniers changements
4. `git rebase origin/develop` - rebase la branche actuelle sur develop
5. Si conflits → les afficher et demander comment procéder
6. Rapport : succès ou conflits à résoudre
