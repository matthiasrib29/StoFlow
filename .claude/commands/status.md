Montre l'etat complet du projet :

1. git worktree list

2. Pour chaque worktree :
   - Branche actuelle
   - Commits ahead/behind develop
   - Fichiers modifies
   - **État GSD** (si .planning/ existe) :
     ```bash
     WORKTREE_PATH=$(git worktree list | grep [branche] | awk '{print $1}')
     if [ -d "$WORKTREE_PATH/.planning/" ]; then
       echo "  📊 GSD actif:"
       # Affiche phase actuelle
       grep "^Phase:" "$WORKTREE_PATH/.planning/STATE.md" 2>/dev/null || echo "  - Pas encore de STATE.md"
       # Affiche progression
       grep "^Progress:" "$WORKTREE_PATH/.planning/STATE.md" 2>/dev/null
     fi
     ```

3. Branches locales vs remote : git branch -vv

4. PRs ouvertes : gh pr list

5. docker ps (services)

6. ports 8000/3000/8001/3001/8002/3002/8003/3003 utilises (lsof -i :PORT)
